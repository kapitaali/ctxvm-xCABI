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
import hashlib
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


def assert_arm_engines_resolve() -> None:
    """The two arms must resolve DIFFERENT engines through the CLI a cell uses.

    Reading the two config files is not the same test: a cell names its profile on the
    command line (`-p w8-<arm>`), and that is the path the run actually takes. Ask the
    CLI the same question, once per arm (RR-W8PREFLIGHT-20261107).
    """
    seen = {}
    for arm, want in (("naive", "compressor"), ("paged", "ctxvm")):
        r = sh(["hermes", "-p", f"w8-{arm}", "config", "get", "context.engine"])
        lines = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
        got = lines[-1] if lines else ""
        if got != want:
            die(f"hermes -p w8-{arm} config get context.engine -> {got!r}, expected {want!r}"
                f" (exit {r.returncode}): the arm's profile does not resolve its engine", 1)
        seen[arm] = got
    if seen["naive"] == seen["paged"]:
        die(f"both arms resolve context.engine {seen['naive']!r}: one factor, no difference", 1)
    print(f"  assert arm engines: naive={seen['naive']} paged={seen['paged']}  OK")


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
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "fixture.sha256").write_text(_fixture_digest(task) + "\n", encoding="utf-8")
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
    # The arm IS the profile. Profile selection is client-side
    # (hermes_cli/main.py:430: --profile/-p is pre-parsed and sets HERMES_HOME), so a
    # command that names no profile runs the caller's profile for BOTH arms and the
    # factor disappears (RR-W8PREFLIGHT-20261107: every cell would have run the default
    # profile's compressor). `-p w8-<arm>` is the ratified fix.
    cmd = ["hermes", "-p", f"w8-{arm}", "-z", prompt_path.read_text(encoding="utf-8"),
           "-m", grid["model"], "--provider", grid["provider"],
           "--in", str(ws), "--usage-file", str(usage_path), "-t", grid["toolsets"]]
    if cmd[1:3] != ["-p", f"w8-{arm}"]:
        die(f"{task}/{arm}-r{rnd}: the command does not name the arm's profile: {cmd[:4]}", 1)

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
    text = path.read_text(encoding="utf-8")
    # A grid ledger carries the archived pilot's total forward: the cap is cumulative
    # across the whole card, so a fresh file must not look like zero spend.
    for line in text.splitlines():
        if line.lower().startswith("carried forward:"):
            digits = "".join(ch for ch in line.split("$")[-1].split()[0] if ch.isdigit() or ch == ".")
            try:
                spent = float(digits)
            except ValueError:
                pass
    for line in text.splitlines():
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


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ledger_start(path: Path, n: int, task: str, arm: str, rnd: int, model: str,
                 total: float) -> None:
    """Write-ahead row: a cell exists in the record BEFORE its first API call.

    A cell killed by a signal cannot write its own epitaph (measured 2026-11-07: exit 143
    after ~15 minutes left no row at all), so the record says STARTED first and is settled
    when the cell ends; a stale STARTED row is reconciled to ABORTED on the next run.
    """
    if not path.exists():
        path.write_text(LEDGER_HEADER, encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(COLUMNS.format(n=n, date=dt.date.today().isoformat(), arm=arm, task=task,
                                rnd=rnd, model=model, inp="—", out="—", cached="—",
                                usd="0.0000", total=f"{total:.4f}",
                                note=f"STARTED {_now()}") + "\n")


def _rewrite_row(path: Path, n: int, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for k, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and cells and cells[0] == str(n):
            lines[k] = row
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reconcile_started(path: Path, ceiling_s: int) -> int:
    """Rewrite STARTED rows older than the cell ceiling as ABORTED; return how many."""
    if not path.exists():
        return 0
    now = dt.datetime.now(dt.timezone.utc)
    fixed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 12 or not c[0].isdigit() or not c[11].startswith("STARTED"):
            continue
        try:
            started = dt.datetime.strptime(c[11].split()[1], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=dt.timezone.utc)
        except (IndexError, ValueError):
            continue
        age = (now - started).total_seconds()
        if age > ceiling_s:
            note = (f"ABORTED after {int(age)}s (killed or crashed; ceiling {ceiling_s}s); "
                    f"cost unknown — reconcile from the run's usage file if present")
            _rewrite_row(path, int(c[0]), COLUMNS.format(
                n=c[0], date=c[1], arm=c[2], task=c[3], rnd=c[4], model=c[5],
                inp="—", out="—", cached="—", usd="0.0000", total=c[10], note=note))
            fixed += 1
    return fixed


def _fixture_digest(task: str) -> str:
    """Digest of what a cell actually measured: the task text, the fixture and its
    expected vector. The resume key includes it because a re-scoped fixture invalidates
    the cells that measured the old one — on 2026-11-07 T1 went from 33 parts to 13 after
    cell 1 hit the iteration ceiling, and a key of (round, task, arm) would have skipped
    the naive cell and compared a paged run on the new fixture against a naive run on the
    old one, silently."""
    h = hashlib.sha256()
    tdir = REPO / "benchmarks/w8/templates" / task
    for name in ("task.md", "fixture.json", "profile.json"):
        f = tdir / name
        if f.exists():
            h.update(name.encode() + b"\0" + f.read_bytes() + b"\0")
    exp = tdir / "expected"
    if exp.is_dir():
        for f in sorted(exp.glob("*.json")):
            h.update(f.name.encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:12]


def _ledger_cells(path: Path, runs: Path) -> set:
    """(round, task, arm) already recorded AND measured on the current fixture."""
    cells = set()
    if not path.exists():
        return cells
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| #") or line.startswith("|---"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5 or not c[0].isdigit():
            continue
        if len(c) > 11 and (c[11].startswith("STARTED") or c[11].startswith("ABORTED")):
            continue      # an unsettled cell is not done; a chunk may retry it
        try:
            rnd, task, arm = int(c[4]), c[3], c[2]
        except (ValueError, IndexError):
            continue
        stamp = runs / task / f"{arm}-r{rnd}" / "fixture.sha256"
        if not stamp.exists() or stamp.read_text(encoding="utf-8").strip() != _fixture_digest(task):
            continue      # measured on a fixture that no longer exists: not done
        cells.add((rnd, task, arm))
    return cells


def ledger_settle(path: Path, n: int, row: dict, total: float) -> None:
    """Settle a STARTED row with the cell's real numbers."""
    _rewrite_row(path, n, COLUMNS.format(
        n=n, date=dt.date.today().isoformat(), arm=row["arm"], task=row["task"],
        rnd=row["round"], model=row["model"], inp=row["in"], out=row["out"],
        cached=row["cached"], usd=f"{row['usd']:.4f}", total=f"{total:.4f}",
        note=f"{row['checker']}; {row['note']}"))


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
    ap.add_argument("--max-cells", type=int, default=0,
                    help="stop cleanly after N cells in this invocation (0 = no limit)")
    ap.add_argument("--skip-done", action="store_true",
                    help="skip cells the ledger already has a row for (resumable chunks)")
    ap.add_argument("--plan", action="store_true",
                    help="print the remaining cells and exit; no API call, no ledger row")
    ap.add_argument("--ledger", default=str(REPO / "reports/W8-SPEND.md"))
    args = ap.parse_args()

    grid = json.loads(Path(args.grid).read_text())
    if len(grid.get("pools", [])) == 0:
        die("grid.pools is empty: the gateway's capture pool must be named", 2)
    price = assert_model_and_price(grid["catalogueModel"])
    assert_profiles_differ_only_in_engine()
    assert_safe_worker_off()
    assert_arm_engines_resolve()
    vbudget = int(grid["vbudget"])

    def _price(key: str, tokens: int) -> float:
        rate = price.get(key)
        if rate is None:
            die(f"price row has no {key}: the grid cannot price cached reads", 1)
        return tokens * float(rate) / 1_000_000.0

    grid["_price"] = _price
    tasks = (args.tasks.split(",") if args.tasks else grid["tasks"])
    rounds = args.rounds or grid["rounds"]
    # Expand, then refuse a relative path: a literal "~" or "$HOME" directory is how an
    # evidence tree ends up somewhere nobody looks (2026-11-07, twice).
    raw_runs = os.path.expandvars(os.path.expanduser(str(args.runs or grid["runs"])))
    runs = Path(raw_runs)
    if not runs.is_absolute():
        die(f"runs dir must be absolute after expansion, got {raw_runs!r}", 2)
    runs.mkdir(parents=True, exist_ok=True)
    ledger = Path(args.ledger)
    if not ledger.exists():
        ledger.write_text(LEDGER_HEADER, encoding="utf-8")
    # The ledger is append-only across invocations: numbering and the running total
    # continue from the rows already there (a second invocation used to restart at 1 and
    # at 0.0000, which made the control variable lie).
    spent, n = _ledger_state(ledger)
    stale = reconcile_started(ledger, int(grid.get("runTimeoutSec", 1800)))
    if stale:
        print(f"  reconciled {stale} STARTED row(s) older than the cell ceiling to ABORTED")

    done = _ledger_cells(ledger, runs) if args.skip_done else set()
    plan = [(rnd, task, arm) for rnd in range(1, rounds + 1)
            for task in tasks for arm in ("naive", "paged")]
    if args.plan:
        todo = [c for c in plan if c not in done]
        for rnd, task, arm in todo:
            print(f"pending: round {rnd} {task} {arm}")
        print(f"{len(todo)} of {len(plan)} cells pending; "
              f"{len(done)} already in the ledger")
        return 0

    ran = 0
    for rnd, task, arm in plan:
                projected = spent / n if n else 0.0
                if not args.dry_run and spent + 2 * projected > grid["capUsd"]:
                    print(f"STOPPED BY BUDGET at coverage {n} of {rounds * len(tasks) * 2}")
                    return 3
                if args.max_cells and ran >= args.max_cells:
                    print(f"chunk complete: {ran} cells this invocation, "
                          f"{len(plan) - len(done) - ran} still pending")
                    print(f"grid so far: USD {spent:.4f} of cap {grid['capUsd']}")
                    return 0
                if (rnd, task, arm) in done:
                    print(f"  skip (in ledger): round {rnd} {task} {arm}")
                    continue
                if arm == "paged":
                    os.environ["W8_VBUDGET"] = str(vbudget)
                n += 1
                ledger_start(ledger, n, task, arm, rnd, grid["model"], spent)
                row = run_cell(task, arm, rnd, grid=grid, runs=runs, dry=args.dry_run)
                ran += 1
                spent += row["usd"]
                ledger_settle(ledger, n, row, spent)
                print(f"  run {n}: {task} {arm} r{rnd} in={row['in']} out={row['out']} "
                      f"cached={row['cached']} usd={row['usd']:.4f} checker={row['checker']}")
    print(f"grid done: {n} runs, USD {spent:.4f} of cap {grid['capUsd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
