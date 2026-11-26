#!/usr/bin/env python3
"""gen-tb-fixture.py — deterministic T-B fixture: N CSV files of (id, category, value) rows.

The fixture is *sized by a residency curve, not by a declared floor*. T-B.md computed 60,200 tokens at
40 bytes per row by hand; a row of `1234,epsilon,-500` is 18 bytes, so the hand figure was about 2x the
truth. What decides this experiment is when the cumulative resident set crosses the arm's budget, so the
generator takes `--files` and `--rows` and `--measure` prints the curve.

Format (pinned by design/past-experiments/w8-tasks/REVIEW.md F5, so the task is aggregation and not CSV parsing):
  header exactly `id,category,value`, no quoting, no embedded commas, no padding, LF endings.

Determinism: one `random.Random(seed)` consumed in file order, rows drawn as
`rng.sample(range(1, 10000), rows)` for unique per-file ids, then category and value per row. `--check`
regenerates into a temporary directory and compares bytes, so a changed generator cannot pass silently.

Usage:
  python3 tools/gen-tb-fixture.py --out <dir> --files 36 --rows 600 [--seed 7]
  python3 tools/gen-tb-fixture.py --out <dir> --files 36 --rows 600 --check
  python3 tools/gen-tb-fixture.py --out <dir> --files 36 --rows 600 --measure --budget 60000

Exit 0 clean, 1 mismatch (--check), 2 cannot proceed.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

CATEGORIES = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta")
HEADER = "id,category,value"


def generate(out: Path, files: int, rows: int, seed: int) -> list[Path]:
    """Write `files` CSVs of `rows` data rows each. Returns the paths in file order."""
    import random

    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for n in range(1, files + 1):
        ids = rng.sample(range(1, 10_000), rows)          # unique within a file, may repeat across files
        lines = [HEADER]
        for row_id in ids:
            category = CATEGORIES[rng.randrange(len(CATEGORIES))]
            value = rng.randint(-500, 500)
            lines.append(f"{row_id},{category},{value}")
        path = out / f"data-{n:02d}.csv"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        written.append(path)
    return written


def digest_map(paths: list[Path]) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def fixture_digest(paths: list[Path]) -> str:
    """One digest over the sorted per-file hashes: the value a cell key carries."""
    h = hashlib.sha256()
    for name, digest in sorted(digest_map(paths).items()):
        h.update(f"{name}:{digest}\n".encode())
    return h.hexdigest()


def measure(out: Path, files: int, rows: int, budget: int) -> int:
    """Print the residency curve using the ENGINE's own tokenizer, not a byte guess."""
    # The engine is imported from its own file so the curve uses the tokenizer the arm will use.
    # No packaging makes that import resolvable to a language server; it is a runtime path insert.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "hermes" / "live"))
    from context_engine import _MSG_OVERHEAD_TOKENS, _estimate_tokens  # noqa: E402

    paths = sorted(out.glob("data-*.csv"))
    if len(paths) != files:
        print(f"gen-tb-fixture: expected {files} files, found {len(paths)}", file=sys.stderr)
        return 2

    def tokens_of(text: str) -> int:
        return _MSG_OVERHEAD_TOKENS + _estimate_tokens(text)

    cumulative = 0
    crossing = None
    total_bytes = 0
    for k, path in enumerate(paths, start=1):
        text = path.read_text(encoding="utf-8")
        total_bytes += len(path.read_bytes())
        cumulative += tokens_of(text)
        if crossing is None and cumulative >= budget:
            crossing = k
        print(f"  file {k:02d}  {len(path.read_bytes()):7d} B  {tokens_of(text):6d} tok  cumulative {cumulative:7d}")
    print()
    print(f"files             {len(paths)}   rows/file {rows}   seed-pinned")
    print(f"total bytes       {total_bytes} ({total_bytes/1000:.0f} kB)")
    print(f"fixture tokens    {cumulative}  (engine tokenizer, 4 B/token rounded up + {_MSG_OVERHEAD_TOKENS}/msg)")
    print(f"budget            {budget}")
    print(f"crossing turn     {crossing if crossing is not None else 'NEVER — the task is too small'}")
    if crossing is not None:
        print(f"pressure turns    {len(paths) - crossing + 1} of {len(paths)}")
        ratio = f"{cumulative / budget:.2f}x budget"
        print(f"fixture/budget    {ratio}  (plan target 1.6-2.0x)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="deterministic T-B fixture")
    ap.add_argument("--out", required=True)
    ap.add_argument("--files", type=int, default=36)
    ap.add_argument("--rows", type=int, default=600)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--check", action="store_true",
                    help="regenerate elsewhere and prove the output is byte-identical")
    ap.add_argument("--measure", action="store_true", help="print the residency curve")
    ap.add_argument("--budget", type=int, default=60_000)
    args = ap.parse_args(argv)

    out = Path(args.out).expanduser()
    if out.exists() and any(out.glob("data-*.csv")) and not args.check:
        print(f"gen-tb-fixture: {out} already holds data-*.csv — refusing to mix fixtures", file=sys.stderr)
        return 2

    if args.check:
        if not out.exists():
            print(f"gen-tb-fixture: {out} does not exist", file=sys.stderr)
            return 2
        with tempfile.TemporaryDirectory(prefix="tb-fixture-") as tmp:
            fresh = generate(Path(tmp) / "fixture", args.files, args.rows, args.seed)
            fresh_map, live_map = digest_map(fresh), digest_map(sorted(out.glob("data-*.csv")))
            if fresh_map != live_map:
                only_fresh = sorted(set(fresh_map) - set(live_map))
                only_live = sorted(set(live_map) - set(fresh_map))
                differing = sorted(k for k in fresh_map.keys() & live_map.keys()
                                   if fresh_map[k] != live_map[k])
                print(f"gen-tb-fixture: MISMATCH — missing here {only_fresh}, extra here {only_live}, "
                      f"differing {differing}", file=sys.stderr)
                return 1
        print(f"gen-tb-fixture: OK — {len(live_map)} files re-derive byte-identically "
              f"(seed {args.seed}, {args.files}x{args.rows}), fixture digest {fixture_digest(sorted(out.glob('data-*.csv')))}")
        return 0

    paths = generate(out, args.files, args.rows, args.seed)
    print(f"gen-tb-fixture: wrote {len(paths)} files to {out} (seed {args.seed}, {args.rows} rows each), "
          f"fixture digest {fixture_digest(paths)}")
    if args.measure:
        return measure(out, args.files, args.rows, args.budget)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
