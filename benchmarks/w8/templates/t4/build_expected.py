#!/usr/bin/env python3
"""T4 expected-artefact builder — the LOG audit, by a stated mechanical rule.

Rules (also in task.md; frozen with the checker):

  row            a line of reports/LOG.md whose first field starts with `| RR-`. The id is
                 that first field, stripped of the leading pipe and spaces.
  date           the LAST run of exactly eight digits inside the id, rendered YYYY-MM-DD.
                 (Some ids carry a suffix after the date — "-FIX", "-CI", "(RESOLUTION)" —
                 so the last run is the one that means a date.)
  track          the id with the `RR-` prefix and the date run removed; surrounding
                 hyphens and spaces trimmed.
  irregular      an id that has any non-space text after the date run; recorded with that
                 trailing text.
  order          a row whose date is earlier than the date of the row before it. Reported
                 as (id, previous date) — the second such row is the finding.
  duplicates     ids appearing more than once, with counts (or `none`).
  last60         the final 60 rows in file order.

NOTHING from a row's prose is copied: the artefact carries ids, dates, tracks and counts
only. That is the DQ rule the first attempt broke (w8-run-plan.md §3b finding 5).

Usage: python3 build_expected.py <repo-root> <out.md>
"""
import re
import sys
from collections import Counter
from pathlib import Path

DATE = re.compile(r"(?<!\d)(\d{8})(?!\d)")


def parse_id(row_id: str):
    runs = list(DATE.finditer(row_id))
    if not runs:
        return None, None, None
    last = runs[-1]
    date = last.group(1)
    rest = row_id[: last.start()] + row_id[last.end():]
    track = rest[3:] if rest.startswith("RR-") else rest
    track = track.strip(" -")
    trailing = row_id[last.end():].strip(" -") or ""
    return f"{date[:4]}-{date[4:6]}-{date[6:]}", track, trailing


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    ids = []
    for line in (root / "reports/LOG.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("| RR-"):
            ids.append(line.strip().strip("|").split("|")[0].strip())

    parsed = [(i, *parse_id(i)) for i in ids]
    missing = [i for i, d, _, _ in parsed if d is None]
    if missing:
        raise SystemExit(f"ids without a date run: {missing[:3]}")

    lines = ["# LOG audit", "", "## Last 60 rows", "",
             "| n | id | date | track |", "|---|----|------|-------|"]
    for n, (i, d, t, _) in enumerate(parsed[-60:], 1):
        lines.append(f"| {n} | {i} | {d} | {t} |")

    lines += ["", "## Irregular ids", ""]
    irregular = [(i, tr) for i, _, _, tr in parsed if tr]
    lines += [f"- {i} → `{tr}`" for i, tr in irregular] or ["none"]

    lines += ["", "## Date order violations", ""]
    order = [(parsed[k][0], parsed[k - 1][1], parsed[k][1])
             for k in range(1, len(parsed)) if parsed[k][1] < parsed[k - 1][1]]
    lines += [f"- {i} ({d} after {prev})" for i, prev, d in order] or ["none"]

    dups = {k: v for k, v in Counter(ids).items() if v > 1}
    lines += ["", "## Summary", "",
              f"rows={len(ids)} last60={min(60, len(ids))} duplicates={len(dups)} "
              f"orderViolations={len(order)} irregular={len(irregular)}"]
    lines += [f"- {k} ×{v}" for k, v in sorted(dups.items())]

    out = "\n".join(lines) + "\n"
    Path(sys.argv[2]).write_text(out, encoding="utf-8")
    print(f"rows={len(ids)} irregular={len(irregular)} order={len(order)} dups={len(dups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
