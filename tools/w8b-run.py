#!/usr/bin/env python3
"""W8B end-to-end run: both arms, then verification, then a record. No spend (free tier).

One command runs the experiment and refuses to run it wrong. Every check in `preflight` exists
because one of them was missing at some point in this card:

  * profile must carry `toolsets: [file]`      (the H6 run shelled out 16 times without it)
  * paged profile must declare 70000           (a budget default is not a treatment)
  * model and provider must be the W8B pair    (a run on gpt-6-luna would silently cost money)
  * no stale artefact.json                     (a PASS on yesterday's file is not a measurement)
  * fixture must be 20 parts                   (a sealed prompt 12 needs the parts to exist)
  * gateway must be newer than the installed plugin file
  * a session that never flushes is NO RECORD, not a failed cell

It does not edit the repo. It writes a bundle under the state dir and prints the rows to paste.

Usage:
  python3 tools/w8b-run.py --dry-run                 # preflight + the exact commands, no calls
  python3 tools/w8b-run.py                           # both arms, 120 s per prompt
  python3 tools/w8b-run.py --arms paged              # one arm
  python3 tools/w8b-run.py --timeout 180 --record    # append the chunklog rows too
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "tools/w8-driver.py"
CHECKER = ROOT / "tools/w8-checker-ta.py"
PROFILES = Path.home() / ".hermes" / "profiles"
TRACES = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "ctxvm" / "traces"
MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"
PROVIDER = "nvidia"
BUDGET = 70000
PARTS = 20


def sh(cmd: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def cfg(key: str, arm: str) -> str:
    r = sh(["hermes", "config", "get", key, "-p", f"w8b-{arm}"])
    return (r.stdout if r.returncode == 0 else r.stderr).strip()


def preflight(arms: list[str]) -> list[str]:
    errs: list[str] = []
    plugin = Path.home() / ".hermes" / "plugins" / "ctxvm-tracer" / "__init__.py"
    if not plugin.exists():
        errs.append(f"installed plugin missing: {plugin}")
    else:
        gw = sh(["pgrep", "-af", "hermes.*gateway"])
        pid = next((line.split()[0] for line in gw.stdout.splitlines() if "gateway" in line), None)
        if pid:
            st = sh(["ps", "-o", "lstart=", "-p", pid]).stdout.strip()
            try:
                started = time.mktime(time.strptime(" ".join(st.split()), "%a %b %d %H:%M:%S %Y"))
                if started < plugin.stat().st_mtime:
                    errs.append(f"gateway PID {pid} started before the plugin file; restart before running")
            except Exception:
                pass
        else:
            errs.append("no hermes gateway process found")
    for arm in arms:
        prof = PROFILES / f"w8b-{arm}"
        if not prof.is_dir():
            errs.append(f"profile missing: {prof}")
            continue
        ts = cfg("toolsets", arm)
        if "file" not in ts:
            errs.append(f"w8b-{arm} toolsets is {ts!r}; expected [file]")
        model = cfg("model.default", arm)
        prov = cfg("model.provider", arm)
        if MODEL not in model:
            errs.append(f"w8b-{arm} model is {model!r}; expected {MODEL}")
        if PROVIDER not in prov:
            errs.append(f"w8b-{arm} provider is {prov!r}; expected {PROVIDER}")
        if arm == "paged":
            b = cfg("plugins.entries.ctxvm-tracer.settings.budgetTokens", arm)
            if str(BUDGET) not in b:
                errs.append(f"w8b-paged budget is {b!r}; expected {BUDGET}")
        ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
        fixture = ws / "fixture"
        if not fixture.is_dir():
            errs.append(f"workspace fixture missing: {fixture}")
        else:
            n = len(list(fixture.glob("part-*.txt")))
            if n != PARTS:
                errs.append(f"{fixture} has {n} parts; expected {PARTS}")
        # A stale artefact is archived, not deleted: the previous run's output is evidence.
        # It just must not be in place when the next run starts.archived in main().
    if not DRIVER.exists():
        errs.append(f"driver missing: {DRIVER}")
    return errs


def session_id(arm: str, title: str) -> str | None:
    db = PROFILES / f"w8b-{arm}" / "state.db"
    if not db.exists():
        return None
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    row = c.execute("select id from sessions where title=? order by rowid desc limit 1", (title,)).fetchone()
    return row[0] if row else None


def capture_for(sid: str) -> Path | None:
    p = TRACES / f"{sid}.jsonl"
    return p if p.exists() else None


def run_arm(arm: str, run_id: str, timeout: int) -> dict:
    title = f"{run_id}-{arm}"
    run_dir = Path.home() / ".local" / "state" / "ctxvm" / "w8-runs" / run_id / arm
    run_dir.mkdir(parents=True, exist_ok=True)
    ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
    env = dict(os.environ)
    env["HERMES_HOME"] = str(PROFILES / f"w8b-{arm}")
    started = time.time()
    print(f"\n[{arm}] driver -> {run_dir}")
    r = subprocess.run([sys.executable, str(DRIVER), "--arm", arm, "--session-name", title,
                        "--workspace", str(ws), "--run-dir", str(run_dir),
                        "--profile-prefix", "w8b", "--expect-budget", str(BUDGET),
                        "--timeout", str(timeout)],
                       text=True, capture_output=True, env=env, timeout=PARTS * timeout + 300)
    (run_dir / "driver.out").write_text(r.stdout, encoding="utf-8")
    (run_dir / "driver.err").write_text(r.stderr, encoding="utf-8")
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(no driver output)")
    out = {"arm": arm, "title": title, "driver_rc": r.returncode,
           "wall_s": round(time.time() - started, 1), "verdict": None, "checks": [],
           "capture": None, "cost_usd": None, "calls": None}
    if r.returncode != 0:
        out["verdict"] = "DATA-INVALID" if "TIMEOUT" not in r.stderr else "NO RECORD"
        print(f"[{arm}] driver stopped: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'rc=' + str(r.returncode)}")
        return out

    sid = session_id(arm, title)
    cap = capture_for(sid) if sid else None
    out["session_id"] = sid
    out["capture"] = str(cap) if cap else None
    if not cap:
        out["verdict"] = "NO RECORD"
        print(f"[{arm}] NO RECORD — session {sid} never flushed")
        return out

    v = sh([sys.executable, str(DRIVER), "--capture", str(cap), "--expect-budget",
            str(BUDGET) if arm == "paged" else "any"])
    (run_dir / "verify.txt").write_text(v.stdout + v.stderr, encoding="utf-8")
    for line in v.stdout.splitlines():
        if line.strip().startswith("["):
            out["checks"].append(line.strip())
        if line.startswith("verify: verdict"):
            out["verdict"] = line.split()[-1]
    print(v.stdout.strip())

    if arm == "paged":
        art = ws / "artefact.json"
        if art.exists():
            c = sh([sys.executable, str(CHECKER), str(ws / "fixture"), str(art)])
            (run_dir / "checker.txt").write_text(c.stdout + c.stderr, encoding="utf-8")
            print(f"[{arm}] checker exit {c.returncode}: {c.stdout.strip().splitlines()[-1] if c.stdout.strip() else ''}")
            out["checker_rc"] = c.returncode

    db = PROFILES / f"w8b-{arm}" / "state.db"
    if sid and db.exists():
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        row = c.execute("select api_call_count, estimated_cost_usd, input_tokens, output_tokens "
                        "from sessions where id=?", (sid,)).fetchone()
        if row:
            out["calls"], out["cost_usd"] = row[0], row[1]
            out["in"], out["out"] = row[2], row[3]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="naive,paged")
    ap.add_argument("--timeout", type=int, default=120, help="seconds per prompt (naive averages 4-7)")
    ap.add_argument("--run-id", default=time.strftime("w8b-%Y%m%d-%H%M%S"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--record", action="store_true", help="append the chunklog rows (repo edit)")
    args = ap.parse_args()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    errs = preflight(arms)
    if errs:
        print("PREFLIGHT FAILED — nothing ran:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 2

    bundle0 = Path.home() / ".local" / "state" / "ctxvm" / "w8-runs" / args.run_id / "stale"
    for arm in arms:
        ws = ROOT / "experiments" / "w8b" / f"ws-{arm}"
        art = ws / "artefact.json"
        if art.exists():
            bundle0.mkdir(parents=True, exist_ok=True)
            dst = bundle0 / f"{arm}-artefact.json"
            shutil.move(str(art), str(dst))
            print(f"archived stale artefact: {art} -> {dst}")

    if args.dry_run:
        for arm in arms:
            print(f"[{arm}] python3 tools/w8-driver.py --arm {arm} --session-name {args.run_id}-{arm} "
                  f"--workspace experiments/w8b/ws-{arm} --run-dir <state>/w8-runs/{args.run_id}/{arm} "
                  f"--profile-prefix w8b --expect-budget {BUDGET} --timeout {args.timeout}")
        print(f"dry-run OK — {len(arms)} arm(s), {PARTS} prompts each, {args.timeout}s cap, model {MODEL}")
        return 0

    results = [run_arm(a, args.run_id, args.timeout) for a in arms]

    bundle = Path.home() / ".local" / "state" / "ctxvm" / "w8-runs" / args.run_id
    (bundle / "summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    rows = []
    for r in results:
        rows.append(f"| {r['title']} | {r.get('calls')} | {r.get('in')} | {r.get('out')} | "
                    f"${r.get('cost_usd') or 0:.4f} | {r['verdict']} | {r.get('wall_s')}s |")
    md = ("| session | calls | in | out | cost | verdict | wall |\n|---|---|---|---|---|---|---|\n"
          + "\n".join(rows) + "\n")
    (bundle / "summary.md").write_text(md, encoding="utf-8")
    print("\n" + md)
    if args.record:
        log = ROOT / "reports" / "W8B-CHUNKLOG.md"
        with log.open("a", encoding="utf-8") as fh:
            for r in results:
                fh.write(f"| {time.strftime('%Y-%m-%dT%H:%M')} | {r['arm']} | {r.get('calls')} | "
                         f"${r.get('cost_usd') or 0:.4f} | {r['verdict']} | {r.get('capture') or 'none'} |\n")
        print(f"recorded -> {log}")
    bad = [r for r in results if r["verdict"] in (None, "DATA-INVALID", "NO RECORD")]
    print(f"bundle: {bundle}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
