#!/usr/bin/env python3
"""T3 checker — mechanical PASS/FAIL on the structured fields only.

The prose fields (`behaviour`, `predicate`) are not judged: a paraphrase is not a failure.
What is judged: the five ids, the file count examined, and each violator list (file +
trigger, exact, in path order).

Two guards carry the freeze rule (w8-run-plan.md §3b finding 2):
  * the expected vector must have five non-empty violator lists — if it does not, the
    fixture itself is broken and the checker exits 2 rather than pass anything;
  * an answer whose violator lists are ALL empty fails even if it is otherwise shaped
    like the truth, because an empty artefact must never be a solution.

Usage: python3 checker.py <workspace>
Exit:  0 PASS · 1 FAIL (reasons on stdout) · 2 usage / broken fixture / unreadable artefact
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: checker.py <workspace>")
        return 2
    ws = Path(sys.argv[1]).resolve()
    try:
        want = json.loads((HERE / "expected" / "deltas.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"checker: broken fixture: {exc}")
        return 2
    if any(not b.get("violators") for b in want["behaviours"]):
        print("checker: frozen fixture has an EMPTY violator list — rebuild before using")
        return 2
    try:
        got = json.loads((ws / "deltas.json").read_text(encoding="utf-8"))
    except OSError:
        print(f"FAIL deltas.json: not found at {ws / 'deltas.json'}")
        return 1
    except ValueError as exc:
        print(f"FAIL deltas.json: not valid JSON ({exc})")
        return 1

    gb = got.get("behaviours") if isinstance(got, dict) else None
    if not isinstance(gb, list) or not gb:
        print("FAIL deltas.json: no behaviours — an empty artefact cannot be a solution")
        return 1
    if all(not (b.get("violators") or []) for b in gb if isinstance(b, dict)):
        print("FAIL deltas.json: every violator list is empty; this tree is not conformant "
              "on all five behaviours (see the fixture's predicates)")
        return 1

    bad = []
    if [b.get("id") for b in gb] != [b["id"] for b in want["behaviours"]]:
        print(f"FAIL behaviours: expected ids {[b['id'] for b in want['behaviours']]}, "
              f"got {[b.get('id') for b in gb]}")
        return 1
    for g, w in zip(gb, want["behaviours"]):
        if g.get("examined") != w["examined"]:
            bad.append(f"{w['id']}.examined: expected {w['examined']}, got {g.get('examined')}")
        gv = [(v.get("file"), v.get("trigger")) for v in (g.get("violators") or []) if isinstance(v, dict)]
        wv = [(v["file"], v["trigger"]) for v in w["violators"]]
        if gv != wv:
            missing = [v for v in wv if v not in gv]
            surplus = [v for v in gv if v not in wv]
            bad.append(f"{w['id']}: expected {len(wv)} violators, got {len(gv)} "
                       f"(missing={missing[:3]} surplus={surplus[:3]})")
    if bad:
        for line in bad[:20]:
            print("FAIL " + line)
        return 1
    print("PASS T3: deltas.json equals the frozen vector")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
