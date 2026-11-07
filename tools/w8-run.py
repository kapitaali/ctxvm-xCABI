#!/usr/bin/env python3
"""W8 grid runner — one row per run, per-run trace relocation, all assertions in code.

Design of record: design/w8-run-plan.md (P2/P4). Two facts measured at P0 shape this file:

  * Hermes v0.23.0 loads plugins in the gateway (hermes_cli/cli_single_query.py:486, PLG-7),
    so a run's CTXVM_TRACE_DIR/NAME come from the gateway's environment, not from the
    runner's. Owner ruling A′: the gateway carries ONE shared pool; each run's capture is
    located by the session id the run itself reports (--usage-file) and copied into
    <runs>/<task>/<arm>-r<round>/.
  * A capture is only evidence if it verifies: coverage_check must accept it and `ctxvm
    replay` must be divergence-free AND byte-identical across two derivations.

Usage:
  python3 tools/w8-run.py --grid benchmarks/w8/grid.json --dry-run
  python3 tools/w8-run.py --grid benchmarks/w8/grid.json --rounds 1 --tasks t1

Exit: 0 grid complete · 1 an assertion or a checker failed · 2 usage/IO · 3 stopped by budget
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRICES = REPO / "benchmarks/metrics/prices.json"
LEDGER_HEADER = """# W8 spend ledger

Control variable for the $25 hard cap (design/w8-run-plan.md §6). One row per run:
date · arm · task · round · model · provider-receipt tokens · USD from the pinned price row ·
running total. The est columns are page-table-only (`cacheEstimate`), the receipt columns are
the provider's own numbers; cached reads are unpriced in the catalogue, so USD prices them at
the input rate — an upper bound, labelled as one.

| # | date | arm | task | round | model | in | out | cached | USD | run total | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
"""
COLUMNS = "| {n} | {date} | {arm} | {task} | {rnd} | {model} | {inp} | {out} | {cached} | {usd} | {total} | {note} |"


def die(msg: str, code: int = 2):
    print(f"w8-run: {msg}", file=sys.stderr)
    raise SystemExit(code)


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


# --- assertions -------------------------------------------------------------

def assert_profiles_differ_only_in_engine() -> None:
    a = (Path.home() / ".hermes/profiles/w8-naive/config.yaml").read_text().splitlines()
    b = (Path.home() / ".hermes/profiles/w8-paged/config.yaml").read_text().splitlines()
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    if len(a) != len(b) or len(diff) != 1:
        die(f"profiles differ in {len(diff)} lines, expected exactly 1 (context.engine)", 1)
    old, new = diff[0]
    if "engine:" not in old or old.split(":")[-1].strip() != "compressor" \
       or new.split(":")[-1].strip() != "ctxvm":
        die(f"the one differing line is not context.engine (compressor|ctxvm): {diff}", 1)
    print("  assert profiles: one differing line = context.engine compressor|ctxvm  OK")


def assert_safe_worker_off() -> None:
    for name in ("w8-naive", "w8-paged"):
        cfg = (Path.home() / f".hermes/profiles/{name}/config.yaml").read_text()
        for banned in ("safe_mode: true", "safe_worker: true"):
            if banned in cfg:
                die(f"{name} carries {banned}; a safe worker loads no plugins", 1)
    if os.environ.get("HERMES_SAFE_MODE") or os.environ.get("HERMES_SAFE_WORKER"):
        die("HERMES_SAFE_MODE/HERMES_SAFE_WORKER is set in the runner environment", 1)
    print("  assert safe worker: off in both profiles  OK")


def assert_model_and_price(model: str) -> dict:
    prices = json.loads(PRICES.read_text())
    entries = (prices.get("catalogue") or {}).get("entries") or []
    rows = [r for r in entries if r.get("model") == model]
    if not rows:
        die(f"no catalogue row named {model!r} in {PRICES}", 1)
    row = rows[0]
    print(f"  assert price row: {model} in={row.get('usdPer1mInput')} "
          f"out={row.get('usdPer1mOutput')} cached={row.get('usdPer1mCachedRead')}  OK")
    return row


# --- capture location -------------------------------------------------------

def locate_capture(session_id: str, pools: list[Path]) -> tuple[Path, Path, Path] | None:
    for pool in pools:
        if not pool.is_dir():
            continue
        for meta in pool.glob("*.meta.json"):
            try:
                d = json.loads(meta.read_text())
            except (OSError, ValueError):
                continue
            if d.get("sessionID") != session_id:
                continue
            stem = meta.name[: -len(".meta.json")]
            return (pool / f"{stem}.jsonl", meta, pool / f"{stem}.coverage.json")
    return None


def verify_capture(jsonl: Path, coverage: Path, outdir: Path) -> tuple[bool, str]:
    """coverage_check + two replay derivations, byte-identical."""
    r = sh([sys.executable, str(REPO / "tools/coverage_check.py"), str(jsonl), str(coverage)])
    if r.returncode != 0:
        return False, f"coverage_check exit {r.returncode}: {(r.stdout + r.stderr).strip()[:300]}"
    replay = REPO / "rust/target/release/replay"
    if not replay.exists():
        return False, "rust/target/release/replay missing (build the workspace first)"
    r1, r2 = sh([str(replay), str(jsonl)]), sh([str(replay), str(jsonl)])
    if r1.returncode not in (0, 1):
        return False, f"replay exit {r1.returncode}: {r1.stderr.strip()[:200]}"
    if r1.stdout != r2.stdout:
        return False, "replay is not byte-identical across two derivations"
    (outdir / "replay.json").write_text(r1.stdout, encoding="utf-8")
    return True, f"coverage ok; replay exit {r1.returncode}, byte-identical"


# --- one run ----------------------------------------------------------------

def run_cell(task: str, arm: str, rnd: int, *, grid: dict, runs: Path, dry: bool) -> dict:
    tdir = REPO / "benchmarks/w8/templates" / task
    spec = json.loads((tdir / "fixture.json").read_text())
    outdir = runs / task / f"{arm}-r{rnd}"
    if outdir.exists():
        shutil.rmtree(outdir)
    ws = outdir / "ws"
    ws.mkdir(parents=True)
    r = sh([sys.executable, str(REPO / "benchmarks/w8/materialize.py"), str(tdir), str(REPO), str(ws)])
    if r.returncode != 0:
        die(f"materialize {task} failed: {r.stderr}", 1)

    prompt_path = outdir / "prompt.txt"
    prompt_path.write_text((tdir / "task.md").read_text(encoding="utf-8"), encoding="utf-8")
    usage_path = outdir / "usage.json"
    cmd = ["hermes", "-z", prompt_path.read_text(encoding="utf-8"),
           "-m", grid["model"], "--provider", grid["provider"],
           "--in", str(ws), "--usage-file", str(usage_path), "-t", grid["toolsets"]]
    (outdir / "cmd.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")

    if dry:
        usage = {"estimated_cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0,
                 "cache_read_tokens": 0, "cache_write_tokens": 0, "api_calls": 0,
                 "model": grid["model"], "provider": grid["provider"],
                 "session_id": "dry-run", "completed": True}
        (outdir / "DRY_RUN").write_text("no API call was made\n", encoding="utf-8")
    else:
        env = dict(os.environ)
        for k in [k for k in env if k.startswith("CTXVM")]:
            env.pop(k)                     # the gateway carries the contract, never the caller
        p = subprocess.run(cmd, text=True, capture_output=True, env=env,
                           timeout=int(grid.get("runTimeoutSec", 1800)))
        (outdir / "stdout.txt").write_text(p.stdout, encoding="utf-8")
        (outdir / "stderr.txt").write_text(p.stderr, encoding="utf-8")
        if not usage_path.exists():
            die(f"{task}/{arm}-r{rnd}: no usage file; run failed (exit {p.returncode})", 1)
        usage = json.loads(usage_path.read_text())

    # capture
    note = "dry"
    if not dry:
        pools = [Path(os.path.expanduser(p)) for p in grid["pools"]]
        got = locate_capture(usage.get("session_id", ""), pools)
        if not got:
            die(f"{task}/{arm}-r{rnd}: no capture for session {usage.get('session_id')} "
                f"in {[str(p) for p in pools]}", 1)
        jsonl, meta, cov = got
        ok, msg = verify_capture(jsonl, cov, outdir)
        for src in (jsonl, meta, cov):
            if src.exists():
                shutil.copy2(src, outdir / src.name)
        note = msg if ok else f"VERIFY FAILED: {msg}"
        if not ok:
            die(f"{task}/{arm}-r{rnd}: {msg}", 1)

        # G8: the redaction DQ gate runs on every captured run, before the run counts.
        dq = sh([sys.executable, str(REPO / "tools/dq-secret-scan.py"),
                 str(outdir / jsonl.name), str(outdir / meta.name)])
        (outdir / "dq.txt").write_text(dq.stdout + dq.stderr, encoding="utf-8")
        if dq.returncode != 0:
            die(f"{task}/{arm}-r{rnd}: DQ scan exit {dq.returncode} — the capture cannot be "
                f"used as evidence: {(dq.stdout + dq.stderr).strip()[:300]}", 1)

    # checker on the produced artefact (a dry run pretends a perfect solver answered,
    # so the whole check lane is proven without spending anything)
    artefact = spec.get("artefact")
    if dry and artefact:
        exp = tdir / "expected" / artefact
        if exp.exists():
            shutil.copy2(exp, ws / artefact)
    verdict = "n/a"
    if artefact and (ws / artefact).exists():
        c = sh([sys.executable, str(tdir / "checker.py"), str(ws)])
        verdict = "PASS" if c.returncode == 0 else "FAIL"
        (outdir / "checker.txt").write_text(c.stdout + c.stderr, encoding="utf-8")

    seen_model = str(usage.get("model") or "")
    if not dry and not seen_model.endswith(grid["model"]):
        die(f"{task}/{arm}-r{rnd}: the run reports model {seen_model!r}, grid pins "
            f"{grid['model']!r} — refusing to record a run under the wrong model", 1)

    inp = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    cached = int(usage.get("cache_read_tokens") or 0)
    written = int(usage.get("cache_write_tokens") or 0)
    # `input_tokens` is the WHOLE prompt (cached included). Pricing it whole and then
    # pricing the cached class again charges the cache twice — measured 2026-11-07:
    # $2.4954 charged against $0.3207 true for the same run. Uncached = prompt - cache.
    uncached = max(inp - cached - written, 0)
    usd = grid["_price"]("usdPer1mInput", uncached) + grid["_price"]("usdPer1mOutput", out) \
        + grid["_price"]("usdPer1mCachedRead", cached)
    return {"arm": arm, "task": task, "round": rnd, "model": usage.get("model", grid["model"]),
            "in": inp, "out": out, "cached": cached, "usd": usd, "checker": verdict,
            "note": note, "session": usage.get("session_id", "")}


# --- ledger -----------------------------------------------------------------

def _ledger_state(path: Path) -> tuple[float, int]:
    """(spent, runs) read from the ledger's existing rows."""
    if not path.exists():
        return 0.0, 0
    spent, runs = 0.0, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| #") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 11 or not cells[0].isdigit():
            continue
        runs += 1
        try:
            spent = float(cells[10])
        except ValueError:
            pass
    return spent, runs


def ledger_append(path: Path, row: dict, n: int, total: float) -> None:
    if not path.exists():
        path.write_text(LEDGER_HEADER, encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(COLUMNS.format(n=n, date=dt.date.today().isoformat(), arm=row["arm"],
                                task=row["task"], rnd=row["round"], model=row["model"],
                                inp=row["in"], out=row["out"], cached=row["cached"],
                                usd=f"{row['usd']:.4f}", total=f"{total:.4f}",
                                note=f"{row['checker']}; {row['note']}") + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default=str(REPO / "benchmarks/w8/grid.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tasks", default=None, help="comma list, default from the grid")
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--runs", default=None)
    ap.add_argument("--ledger", default=str(REPO / "reports/W8-SPEND.md"))
    args = ap.parse_args()

    grid = json.loads(Path(args.grid).read_text())
    if len(grid.get("pools", [])) == 0:
        die("grid.pools is empty: the gateway's capture pool must be named", 2)
    price = assert_model_and_price(grid["catalogueModel"])
    assert_profiles_differ_only_in_engine()
    assert_safe_worker_off()
    vbudget = int(grid["vbudget"])

    def _price(key: str, tokens: int) -> float:
        rate = price.get(key)
        if rate is None:
            die(f"price row has no {key}: the grid cannot price cached reads", 1)
        return tokens * float(rate) / 1_000_000.0

    grid["_price"] = _price
    tasks = (args.tasks.split(",") if args.tasks else grid["tasks"])
    rounds = args.rounds or grid["rounds"]
    runs = Path(args.runs or grid["runs"])
    runs.mkdir(parents=True, exist_ok=True)
    ledger = Path(args.ledger)
    if not ledger.exists():
        ledger.write_text(LEDGER_HEADER, encoding="utf-8")
    # The ledger is append-only across invocations: numbering and the running total
    # continue from the rows already there (a second invocation used to restart at 1 and
    # at 0.0000, which made the control variable lie).
    spent, n = _ledger_state(ledger)

    for rnd in range(1, rounds + 1):
        for task in tasks:
            for arm in ("naive", "paged"):       # per-task alternation (plan §6)
                projected = spent / n if n else 0.0
                if not args.dry_run and spent + 2 * projected > grid["capUsd"]:
                    print(f"STOPPED BY BUDGET at coverage {n} of {rounds * len(tasks) * 2}")
                    return 3
                if arm == "paged":
                    os.environ["W8_VBUDGET"] = str(vbudget)
                row = run_cell(task, arm, rnd, grid=grid, runs=runs, dry=args.dry_run)
                spent += row["usd"]
                n += 1
                ledger_append(ledger, row, n, spent)
                print(f"  run {n}: {task} {arm} r{rnd} in={row['in']} out={row['out']} "
                      f"cached={row['cached']} usd={row['usd']:.4f} checker={row['checker']}")
    print(f"grid done: {n} runs, USD {spent:.4f} of cap {grid['capUsd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
