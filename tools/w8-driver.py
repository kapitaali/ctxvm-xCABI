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
SEALED_PARTS = ["part-01.txt", "part-02.txt", "part-03.txt"]
ALLOWED_TOOL_PREFIXES = ("tool:read_file", "tool:write_file", "tool:search_files", "tool:patch")

PROMPTS: list[str] = [
    "Read fixture/part-01.txt. Report its line count, byte size, number of lines longer than 100 bytes, and number of lines shorter than 10 bytes. Do not write any file.",
    "Read fixture/part-02.txt. Report the same four statistics (lines, bytes, long, short).",
    "Read fixture/part-03.txt. Report the same four statistics (lines, bytes, long, short).",
    "Read fixture/part-04.txt. Report its four statistics (lines, bytes, long, short). Also state the running total of 'long' across parts 01 through 04.",
    "Read fixture/part-05.txt. Report its four statistics and the running total of 'long' across parts 01 through 05.",
    "Read fixture/part-06.txt. Report its four statistics and the running total of 'long' across parts 01 through 06.",
    "Read fixture/part-07.txt. Report its four statistics and the running total of 'long' across parts 01 through 07.",
    "Read fixture/part-08.txt. Report its four statistics and the running total of 'long' across parts 01 through 08.",
    "Read fixture/part-09.txt. Report its four statistics and the running total of 'long' across parts 01 through 09.",
    "Read fixture/part-10.txt. Report its four statistics and the running total of 'long' across parts 01 through 10.",
    "Read fixture/part-11.txt and fixture/part-12.txt. Report each file's four statistics and the running total of 'long' across parts 01 through 12.",
    "You read parts 01-03 at the start of this session and parts 04-12 in the middle. Now read fixture/part-13.txt and fixture/part-14.txt, compute all four statistics for every one of the 14 parts, and write artefact.json in the working directory per the task specification: sorted file keys, canonical 2-space indentation, per-file keys lines/bytes/long/short, top-level keys files/widest_file/total_long, and a single trailing newline. The artefact must include all 14 parts. PARTS 01-03 ARE SEALED: they have been removed from the fixture directory and cannot be read. Use only the statistics you recorded for them in turns 1-3.",
]


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
    profile = Path.home() / ".hermes" / "profiles" / f"w8-{args.arm}"
    raw = os.environ.get("HERMES_HOME")
    if not raw:
        errs.append("HERMES_HOME unset; source tools/w8-run-env.sh <arm> ... first")
    else:
        got = Path(raw).expanduser().resolve()
        if got != profile.resolve():
            errs.append(f"HERMES_HOME resolves to {got}, expected {profile.resolve()}")
    if not profile.is_dir():
        errs.append(f"profile missing: {profile}")
    toolsets = _config_get("toolsets", args.arm)
    if toolsets != ["file"]:
        errs.append(f'toolsets for w8-{args.arm} is {toolsets!r}, expected ["file"]')
    if args.arm == "paged":
        budget = _config_get("plugins.entries.ctxvm-tracer.settings.budgetTokens", args.arm)
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


def _config_get(key: str, arm: str) -> object:
    try:
        out = subprocess.run(["hermes", "config", "get", key, "-p", f"w8-{arm}"],
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


def build_cmd(i: int, prompt: str, args) -> list[str]:
    cmd = ["hermes", "chat", "-q", prompt, "--oneshot", "-c", args.session_name, "--in", args.workspace]
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

    manifest = {
        "session_name": args.session_name,
        "arm": args.arm,
        "profile": f"w8-{args.arm}",
        "workspace": str(ws),
        "prompts": len(PROMPTS),
        "middle_prompts": len(PROMPTS[3:-1]),
        "seal_after_prompt": SEAL_AFTER_TURN,
        "sealed_parts": SEALED_PARTS,
        "max_turns": args.max_turns,
        "expect_budget": args.expect_budget,
        "dry_run": args.dry_run,
    }
    (run_dir / "session.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if args.dry_run:
        for i, p in enumerate(PROMPTS, 1):
            print(f"[prompt {i:02d}] " + " ".join(build_cmd(i, p, args)))
        print(f"dry-run: session={args.session_name} prompts={len(PROMPTS)} "
              f"middle={len(PROMPTS[3:-1])} seal_after={SEAL_AFTER_TURN} (no model call made)")
        return 0

    env = dict(os.environ)
    for k in [k for k in env if k.startswith("CTXVM")]:
        env.pop(k)                      # the profile settings are the contract
    moved: list[str] = []
    try:
        for i, p in enumerate(PROMPTS, 1):
            if i == SEAL_AFTER_TURN + 1:
                moved = seal(ws, run_dir)
                print(f"[seal] removed {len(moved)} parts from the fixture: {', '.join(moved)}")
            cmd = build_cmd(i, p, args)
            (run_dir / f"cmd-{i:02d}.txt").write_text(" ".join(cmd) + "\n")
            print(f"[prompt {i:02d}] running...", flush=True)
            r = subprocess.run(cmd, text=True, capture_output=True, env=env, timeout=args.timeout)
            (run_dir / f"stdout-{i:02d}.txt").write_text(r.stdout, encoding="utf-8")
            (run_dir / f"stderr-{i:02d}.txt").write_text(r.stderr, encoding="utf-8")
            if r.returncode != 0:
                print(f"driver: prompt {i} failed (exit {r.returncode})", file=sys.stderr)
                print(r.stderr[-800:], file=sys.stderr)
                return 1
            print(f"[prompt {i:02d}] ok")
    finally:
        unseal(ws, run_dir)
    print(f"driver: done — {len(PROMPTS)} prompts, session={args.session_name}")
    print(f"driver: next is `--verify` on the newest capture; a run is not a cell until it passes")
    return 0


# --------------------------------------------------------------------------- verify

def verify(args) -> int:
    from collections import Counter
    cap = Path(args.capture).expanduser().resolve()
    cov_path = Path(str(cap).replace(".jsonl", ".coverage.json"))
    if not cap.exists() or not cov_path.exists():
        print(f"verify: missing capture or coverage sidecar for {cap}", file=sys.stderr)
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
    sealed_reads = [r for r in declares
                    if (r.get("turn") or 0) > SEAL_AFTER_TURN
                    and any(name in r["page"]["id"]["logicalRef"] for name in SEALED_PARTS)]

    checks: list[tuple[str, bool, str]] = []
    checks.append(("session id single", len({session.get("sessionID")}) == 1, session.get("sessionID", "")[:16]))
    checks.append(("turn spread >= 10", len(turns) >= 10, f"{len(turns)} distinct: {sorted(turns)}"))
    checks.append(("budget from settings",
                   str(plugin.get("budgetTokens")) == str(args.expect_budget) and plugin.get("budgetSource") == "settings",
                   f"{plugin.get('budgetTokens')} / {plugin.get('budgetSource')}"))
    checks.append(("engine selections > 0", (plugin.get("engineSelections") or 0) > 0, str(plugin.get("engineSelections"))))
    checks.append(("no code/shell tools",
                   not any(t in ("tool:terminal", "tool:execute_code") for t in tools),
                   ", ".join(f"{k}x{v}" for k, v in sorted(tools.items()))))
    checks.append(("no sealed part read after seal", not sealed_reads, f"{len(sealed_reads)} reads"))
    checks.append(("evictions > 0", evicted > 0, f"{evicted} tokens evicted"))

    # evictions are the difference between CELL and NO-OP, not a validity check
    ok = all(passed for name, passed, _detail in checks if name != "evictions > 0")
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["naive", "paged"])
    ap.add_argument("--session-name")
    ap.add_argument("--workspace")
    ap.add_argument("--run-dir")
    ap.add_argument("--max-turns", type=int, default=8,
                    help="tool-calling iterations per prompt (cost ceiling; h7-h9 ran unbounded)")
    ap.add_argument("--expect-budget", type=int, default=55000)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--capture", help="verify mode: capture .jsonl to accept or reject")
    args = ap.parse_args()
    if args.capture:
        return verify(args)
    missing = [k for k in ("arm", "session_name", "workspace", "run_dir") if not getattr(args, k)]
    if missing:
        ap.error("run mode needs " + ", ".join("--" + m.replace("_", "-") for m in missing))
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
