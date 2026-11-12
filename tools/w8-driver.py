#!/usr/bin/env python3
"""W8 multi-turn driver + acceptance verifier.

Source of truth for the prompt sequence is design/w8-multi-turn-driver.md; this file
must keep PROMPTS in sync with it.

Why this file is in tools/ and not experiments/: the driver produces the experiment's
evidence, so it is versioned and gated. The run outputs are not.

Two modes:

  run     --arm {naive,paged} --session-name N --workspace W --run-dir R
  verify  --capture <capture.jsonl> [--fixture F] [--artefact A] [--expect-budget 55000]

Guarantees the driver enforces, each paid for by a defect already measured:

  * HERMES_HOME must resolve to the arm's profile. Without it the session row lands in
    the everyday profile and the run becomes visible in the owner's chat list.
  * The toolset must be `file`. -t is refused on resume, so the pin lives in the profile.
  * parts 01-03 are physically REMOVED after turn 3 and restored afterwards, so the
    final answer cannot be re-read out of the fixture. The prompt says so; the filesystem
    enforces it.
  * --max-turns bounds every invocation. An unbounded turn cost $3.14 over three
    attempts before this existed.
  * A stale artefact.json in the workspace is refused, not overwritten: a checker that
    passes on yesterday's file is not a measurement.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SEAL_AFTER_TURN = 3
# The model's failure mode on this task is an unbounded search_files loop: 21 tool calls for one
# "read this file and report four numbers" prompt (2026-11-11). The rule is part of what the model
# sees, so it belongs in the prompt digest, not only in the task text.
RULE_READ = " Use read_file only; do not use search_files."
RULE_FINAL = " Use read_file and write_file only; do not use search_files."
SEALED_PARTS = ["part-01.txt", "part-02.txt", "part-03.txt"]
ALLOWED_TOOL_PREFIXES = ("tool:read_file", "tool:write_file", "tool:search_files", "tool:patch")

ARTEFACT_PROMPT = (
    "You read parts 01-03 at the start of this session and parts 04-20 in the middle. Now write "
    "artefact.json in the working directory. The artefact is a JSON object with exactly three keys: "
    "\"files\", \"widest_file\", \"marker_line\". \"files\" maps each basename (sorted ascending) to "
    "an object with exactly two integer keys in this order: lines, bytes. lines and bytes are the "
    "values read_file reported for that file (total_lines and file_size). \"widest_file\" = the "
    "basename with the LARGEST bytes; ties break by basename ascending. \"marker_line\" = the exact "
    "text of line 137 of part-12.txt, with no line number and no quotes of your own. Write 2-space "
    "indentation and a single trailing newline if you can. PARTS 01-03 ARE SEALED: they have been "
    "removed from the fixture directory and cannot be read. Use only the values you recorded for "
    "them in turns 1-3."
)

# T-A v2: ask only for values read_file reports (total_lines, file_size) plus one exact line.
# Counting bytes per line was the v1 task and it is what stalled every free model: the tool does not
# report character or word counts, so the model counted by reproducing the file and truncated its own
# output. Measured 2026-11-11: counting prompt 180 s (nvidia) and 283 s of silence (longcat);
# extractive prompt 4 s on the same fixture and profile.
PROMPTS: list[str] = [
    f"Read fixture/part-{i:02d}.txt with read_file. Reply with exactly three things and nothing else: "
    f"total_lines, file_size, and the exact text of line 137."
    for i in range(1, 20)
] + [ARTEFACT_PROMPT]



# ----------------------------------------------------------------------------- run

def validate_prompts() -> list[str]:
    errors: list[str] = []
    if len(PROMPTS) < 10:
        errors.append(f"need >= 10 prompts, have {len(PROMPTS)}")
    for i in range(3):
        if f"part-0{i + 1}.txt" not in PROMPTS[i]:
            errors.append(f"prompt {i + 1} does not read part-0{i + 1}.txt")
    middle = PROMPTS[3:-1]
    if len(middle) < 6:
        errors.append(f"need >= 6 middle prompts, have {len(middle)}")
    if "artefact.json" not in PROMPTS[-1]:
        errors.append("final prompt does not require writing artefact.json")
    if "SEALED" not in PROMPTS[-1]:
        errors.append("final prompt does not state that parts 01-03 are sealed")
    return errors


def preflight(args) -> list[str]:
    errs: list[str] = []
    profile = Path.home() / ".hermes" / "profiles" / f"{getattr(args, 'profile_prefix', 'w8')}-{args.arm}"
    raw = os.environ.get("HERMES_HOME")
    if not raw:
        errs.append("HERMES_HOME unset; source tools/w8-run-env.sh <arm> ... first")
    else:
        got = Path(raw).expanduser().resolve()
        if got != profile.resolve():
            errs.append(f"HERMES_HOME resolves to {got}, expected {profile.resolve()}")
    if not profile.is_dir():
        errs.append(f"profile missing: {profile}")
    pp = getattr(args, "profile_prefix", "w8")
    toolsets = _config_get("toolsets", args.arm, pp)
    if toolsets != ["file"]:
        errs.append(f'toolsets for {pp}-{args.arm} is {toolsets!r}, expected ["file"]')
    if args.arm == "paged":
        budget = _config_get("plugins.entries.ctxvm-tracer.settings.budgetTokens", args.arm, pp)
        if isinstance(budget, list) and len(budget) == 1:
            budget = budget[0]
        if str(budget) != str(args.expect_budget):
            errs.append(f"budgetTokens for w8-paged is {budget!r}, expected {args.expect_budget}")
    artefact = Path(args.workspace) / "artefact.json"
    if artefact.exists():
        errs.append(f"stale artefact present: {artefact} — remove it, a PASS on it is not a measurement")
    if not (Path(args.workspace) / "fixture").is_dir():
        errs.append(f"workspace has no fixture/: {args.workspace}")
    return errs


def _config_get(key: str, arm: str, profile_prefix: str = "w8") -> object:
    try:
        out = subprocess.run(["hermes", "config", "get", key, "-p", f"{profile_prefix}-{arm}"],
                             capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    raw = out.stdout.strip()
    if raw[:1] in "[{":
        try:
            return json.loads(raw.replace("'", '"'))
        except Exception:
            return raw
    items = [line.strip().lstrip("-").strip() for line in raw.splitlines() if line.strip()]
    return items or None



REFUSAL_MARKERS = (
    "does not exist. Available tools",
    "Your request was not processed",
)


def _refusal_marker(stdout: str) -> str | None:
    """A prompt that ended without work: the model asked for a tool it does not have, or it
    replied with its stock 'not processed' line. Both were observed on nemotron-3.5-super-vl
    behind `-t file` (w8b-pair1-paged, 2026-11-10) and produced a 2.5-hour retry loop that was
    first mistaken for a provider throttle."""
    for marker in REFUSAL_MARKERS:
        if marker in stdout:
            return marker
    return None


def prompt_text(i: int, prompt: str) -> str:
    return prompt + (RULE_FINAL if i == len(PROMPTS) else RULE_READ)


def build_cmd(i: int, prompt: str, args) -> list[str]:
    cmd = ["hermes", "chat", "-q", prompt_text(i, prompt), "--oneshot", "-c", args.session_name,
           "--in", args.workspace]
    if i == 1:
        cmd.insert(5, "--create-if-missing")
    # --max-turns is REFUSED on this flow: a named session with --create-if-missing
    # rejects it as a creation override even on a fresh name (measured 2026-11-10).
    # The call ceiling is `agent.max_turns` in the profile instead, which survives
    # resume because it is not a CLI override.
    return cmd


def seal(ws: Path, run_dir: Path) -> list[str]:
    moved = []
    sealed_dir = run_dir / "sealed"
    sealed_dir.mkdir(parents=True, exist_ok=True)
    for name in SEALED_PARTS:
        src = ws / "fixture" / name
        if src.exists():
            shutil.move(str(src), str(sealed_dir / name))
            moved.append(name)
    return moved


def unseal(ws: Path, run_dir: Path) -> None:
    sealed_dir = run_dir / "sealed"
    for name in SEALED_PARTS:
        src = sealed_dir / name
        if src.exists():
            shutil.move(str(src), str(ws / "fixture" / name))


def run(args) -> int:
    errs = validate_prompts() + preflight(args)
    if errs:
        for e in errs:
            print(f"driver: {e}", file=sys.stderr)
        return 2
    run_dir = Path(args.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    ws = Path(args.workspace).expanduser().resolve()

    pp = getattr(args, "profile_prefix", "w8")
    manifest = {
        "session_name": args.session_name,
        "arm": args.arm,
        "profile": f"{pp}-{args.arm}",
        "workspace": str(ws),
        "prompts": len(PROMPTS),
        "prompt_rules": [RULE_READ, RULE_FINAL],
        "middle_prompts": len(PROMPTS[3:-1]),
        "seal_after_prompt": SEAL_AFTER_TURN,
        "sealed_parts": SEALED_PARTS,
        "max_turns": args.max_turns,
        "expect_budget": args.expect_budget,
        "dry_run": args.dry_run,
        "prompt_digest": __import__("hashlib").sha256(
            ("\n".join(PROMPTS) + "\n" + "artefact.json").encode()
        ).hexdigest()[:12],
    }
    (run_dir / "session.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if args.dry_run:
        for i, p in enumerate(PROMPTS, 1):
            print(f"[prompt {i:02d}] " + " ".join(build_cmd(i, p, args)))
        print(f"dry-run: session={args.session_name} prompts={len(PROMPTS)} "
              f"middle={len(PROMPTS[3:-1])} seal_after={SEAL_AFTER_TURN} (no model call made)")
        return 0

    env = dict(os.environ)
    prompts = PROMPTS[: args.limit] if args.limit else PROMPTS
    for k in [k for k in env if k.startswith("CTXVM")]:
        env.pop(k)                      # the profile settings are the contract
    moved: list[str] = []
    try:
        for i, p in enumerate(prompts, 1):
            if i == SEAL_AFTER_TURN + 1:
                moved = seal(ws, run_dir)
                print(f"[seal] removed {len(moved)} parts from the fixture: {', '.join(moved)}")
            cmd = build_cmd(i, p, args)
            (run_dir / f"cmd-{i:02d}.txt").write_text(" ".join(cmd) + "\n")
            print(f"[prompt {i:02d}] running...", flush=True)
            # SIGTERM first, SIGKILL only as a last resort: a hard kill leaves the session open,
            # the gateway reaps it (end_reason ws_orphan_reap) and NOTHING flushes, so a timeout
            # becomes NO RECORD instead of a readable partial. Measured 2026-11-11.
            proc = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, env=env)
            try:
                out, err = proc.communicate(timeout=args.timeout)
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    out, err = proc.communicate(timeout=20)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    out, err = proc.communicate()
                rc = -15
                (run_dir / f"stdout-{i:02d}.txt").write_text(out or "", encoding="utf-8")
                (run_dir / f"stderr-{i:02d}.txt").write_text(
                    f"TIMEOUT after {args.timeout}s (SIGTERM sent so the session can flush)\n", encoding="utf-8")
                print(f"driver: prompt {i} TIMEOUT after {args.timeout}s — terminated", file=sys.stderr)
                return 1
            r = subprocess.CompletedProcess(cmd, rc, out, err)
            (run_dir / f"stdout-{i:02d}.txt").write_text(r.stdout, encoding="utf-8")
            (run_dir / f"stderr-{i:02d}.txt").write_text(r.stderr, encoding="utf-8")
            if r.returncode != 0:
                print(f"driver: prompt {i} failed (exit {r.returncode})", file=sys.stderr)
                print(r.stderr[-800:], file=sys.stderr)
                return 1
            bad = _refusal_marker(r.stdout)
            if bad:
                print(f"driver: prompt {i} aborted — {bad} — cell DATA-INVALID", file=sys.stderr)
                return 1
            print(f"[prompt {i:02d}] ok")
            if args.max_calls:
                used = _calls_so_far(args.session_name)
                print(f"[calls] {used}/{args.max_calls} after prompt {i}")
                if used >= args.max_calls:
                    # A ceiling is a booked OUTCOME, never a void: the session is sound and the
                    # capture still flushes, it simply stopped short of the prompt set.
                    (run_dir / "CEILING").write_text(
                        f"calls={used} ceiling={args.max_calls} after_prompt={i}\n", encoding="utf-8")
                    print(f"driver: CEILING reached ({used} >= {args.max_calls}) after prompt {i} "
                          f"— stopping; this is an outcome, not an error", file=sys.stderr)
                    break
    finally:
        unseal(ws, run_dir)
    print(f"driver: done — {len(prompts)} prompts, session={args.session_name}")
    print(f"driver: next is `--verify` on the newest capture; a run is not a cell until it passes")
    return 0


# --------------------------------------------------------------------------- verify

def verify(args) -> int:
    from collections import Counter
    cap = Path(args.capture).expanduser().resolve()
    cov_path = Path(str(cap).replace(".jsonl", ".coverage.json"))
    if not cap.exists() or not cov_path.exists():
        # NO RECORD: the session never closed, so nothing flushed. This is not DATA-INVALID
        # (that implies a bad record); it cannot be classified at all.
        print(f"verify: NO RECORD — no capture or coverage sidecar for {cap} (session never flushed)",
              file=sys.stderr)
        return 2
    rows = [json.loads(line) for line in open(cap) if line.strip()]
    cov = json.load(open(cov_path))
    plugin = cov.get("plugin", {})
    session = cov.get("session", {})
    declares = [r for r in rows if r.get("type") == "page.declare"]
    turns = {r.get("turn") for r in declares}
    evicted = sum(r.get("evictedTokens") or 0 for r in rows if r.get("type") == "turn.render")
    refs = [r["page"]["id"]["logicalRef"] for r in declares]
    tools = Counter(r.split("(", 1)[0] for r in refs)
    # Only count NEW read_file calls for sealed parts after the seal (not re-declarations
    # of already-read pages, not search_files, not write_file artefact content).
    first_decl_turn: dict[str, int] = {}
    for r in declares:
        lr = r["page"]["id"]["logicalRef"]
        if "read_file" in lr:
            for name in SEALED_PARTS:
                if name in lr:
                    t = r.get("turn") or 0
                    if name not in first_decl_turn or t < first_decl_turn[name]:
                        first_decl_turn[name] = t
    sealed_reads = [r for r in declares
                    if (r.get("turn") or 0) > SEAL_AFTER_TURN
                    and "read_file" in r["page"]["id"]["logicalRef"]
                    and any(name in r["page"]["id"]["logicalRef"] and first_decl_turn.get(name, 0) > SEAL_AFTER_TURN
                            for name in SEALED_PARTS)]

    checks: list[tuple[str, bool, str]] = []
    checks.append(("session id single", len({session.get("sessionID")}) == 1, session.get("sessionID", "")[:16]))
    checks.append(("turn spread >= 10", len(turns) >= 10, f"{len(turns)} distinct: {sorted(turns)}"))
    expect = str(args.expect_budget)
    budget_ok = (expect == "any") or (
        str(plugin.get("budgetTokens")) == expect and plugin.get("budgetSource") == "settings")
    checks.append(("budget from settings" if expect != "any" else "budget recorded",
                   budget_ok,
                   f"{plugin.get('budgetTokens')} / {plugin.get('budgetSource')}"))
    # Arm-aware: a CONTROL session must select nothing — zero is the correct answer there, and
    # requiring > 0 labelled a correct control VOID (measured 2026-11-11, W8C cell-01).
    _sel = plugin.get("engineSelections") or 0
    _control = (plugin.get("arm") == "control") or (plugin.get("engineSetting") == "compressor")
    if _control:
        checks.append(("control selects nothing", _sel == 0, str(_sel)))
    else:
        checks.append(("engine selections > 0", _sel > 0, str(_sel)))
    checks.append(("no code/shell tools",
                   not any(t in ("tool:terminal", "tool:execute_code") for t in tools),
                   ", ".join(f"{k}x{v}" for k, v in sorted(tools.items()))))
    checks.append(("no sealed part read after seal", not sealed_reads, f"{len(sealed_reads)} reads"))
    checks.append(("evictions > 0", evicted > 0, f"{evicted} tokens evicted"))

    # sealed reads are informational only: a failed attempt is recorded, not fatal.
    # Only a SUCCESSFUL sealed-part read invalidates the run.
    ok = all(passed for name, passed, _detail in checks if name not in ("evictions > 0", "no sealed part read after seal"))
    print(f"verify: capture {cap.name}")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'FAIL'}] {name}: {detail}")

    # record integrity
    root = Path(__file__).resolve().parent.parent
    cov_rc = subprocess.run([sys.executable, str(root / "tools/coverage_check.py"), str(cap), str(cov_path)],
                            capture_output=True, text=True)
    binary = root / "rust/target/release/replay"
    rep_rc = subprocess.run([str(binary), str(cap)], capture_output=True, text=True) if binary.exists() else None
    print(f"  [{'ok' if cov_rc.returncode == 0 else 'FAIL'}] coverage_check exit {cov_rc.returncode}")
    print(f"  [{'ok' if rep_rc and rep_rc.returncode == 0 else 'FAIL'}] replay exit {rep_rc.returncode if rep_rc else 'missing binary'}")

    verdict = "VOID" if not ok else ("CELL" if evicted > 0 else "NO-OP")
    print(f"verify: verdict {verdict}")
    return 0 if verdict == "CELL" else 1


def _calls_so_far(session_name: str) -> int:
    """API calls the provider has been asked for in this session, read from the profile's DB.

    The ceiling has to be checked BETWEEN prompts: the driver launches one `hermes chat` per prompt and
    cannot see inside it. `agent.max_turns` bounds one prompt; this bounds the arm.
    """
    home = os.environ.get("HERMES_HOME")
    if not home:
        return 0
    db = Path(home) / "state.db"
    if not db.exists():
        return 0
    try:
        import sqlite3
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        row = c.execute("select api_call_count from sessions where title=? "
                        "order by rowid desc limit 1", (session_name,)).fetchone()
        c.close()
        return int(row[0] or 0) if row else 0
    except Exception:
        return 0



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["naive", "paged"])
    ap.add_argument("--session-name")
    ap.add_argument("--workspace")
    ap.add_argument("--run-dir")
    ap.add_argument("--max-turns", type=int, default=8,
                    help="tool-calling iterations per prompt (cost ceiling; h7-h9 ran unbounded)")
    ap.add_argument("--expect-budget", default="55000",
                    help="expected budgetTokens, or \"any\" to record whatever the plugin saw")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--limit", type=int, default=0, help="run only the first N prompts (smoke check)")
    ap.add_argument("--max-calls", type=int, default=0,
                    help="stop the arm once the session has made this many provider calls (0 = no ceiling)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--capture", help="verify mode: capture .jsonl to accept or reject")
    ap.add_argument("--profile-prefix", default="w8",
                    help="profile name prefix (default w8; use w8b for the free-model re-run)")
    args = ap.parse_args()
    if args.capture:
        return verify(args)
    missing = [k for k in ("arm", "session_name", "workspace", "run_dir") if not getattr(args, k)]
    if missing:
        ap.error("run mode needs " + ", ".join("--" + m.replace("_", "-") for m in missing))
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
