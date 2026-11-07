#!/usr/bin/env python3
"""T4 checker — mechanical PASS/FAIL on the audit text.

Usage: python3 checker.py <workspace>          (expects <workspace>/release.md)
Exit:  0 PASS · 1 FAIL (reasons on stdout) · 2 usage / unreadable artefact

Comparison is line-exact after trailing-whitespace normalisation. A table row that differs
in one cell fails, and the failing line is named. The DQ rule is enforced here too: an
answer that copies prose out of a LOG row (the trap of w8-run-plan.md §3b finding 5) is
rejected, because the artefact is ids, dates, tracks and counts only.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROSE = re.compile(r"\b(VERIFIED|SHIP-UNBLOCKED|MEASURED|CARD|THE RUN)\b")


def norm(text: str):
    return [line.rstrip() for line in text.strip().splitlines()]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: checker.py <workspace>")
        return 2
    ws = Path(sys.argv[1]).resolve()
    path = ws / "release.md"
    try:
        got = norm(path.read_text(encoding="utf-8"))
    except OSError:
        print(f"FAIL release.md: not found at {path}")
        return 1
    want = norm((HERE / "expected" / "release.md").read_text(encoding="utf-8"))

    if not got:
        print("FAIL release.md: empty")
        return 1
    for k, line in enumerate(got, 1):
        if PROSE.search(line):
            print(f"FAIL release.md:{k}: row prose in the artefact (DQ rule: ids, dates, "
                  f"tracks and counts only)")
            return 1
    if got == want:
        print("PASS T4: release.md equals the frozen audit")
        return 0
    for k in range(min(len(got), len(want))):
        if got[k] != want[k]:
            print(f"FAIL line {k + 1}: expected {want[k]!r}, got {got[k]!r}")
            break
    else:
        print(f"FAIL line count: expected {len(want)}, got {len(got)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
