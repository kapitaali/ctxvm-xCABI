#!/usr/bin/env python3
"""T2 checker — mechanical PASS/FAIL.

Usage: python3 checker.py <workspace>          (expects <workspace>/drops.json)
Exit:  0 = artefact equals the frozen expected vector · 1 = FAIL (reasons on stdout) ·
       2 = usage / unreadable artefact

The empty-set guard is explicit: an artefact with no drops, or with a drop whose file list
is empty, FAILS even if it matched — the freeze forbids a checker that can be satisfied
without reading (w8-run-plan.md §3b finding 2).
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
        got = json.loads((ws / "drops.json").read_text(encoding="utf-8"))
    except OSError:
        print(f"FAIL drops.json: not found at {ws / 'drops.json'}")
        return 1
    except ValueError as exc:
        print(f"FAIL drops.json: not valid JSON ({exc})")
        return 1
    want = json.loads((HERE / "expected" / "drops.json").read_text(encoding="utf-8"))
    bad = []

    gd = got.get("drops") if isinstance(got, dict) else None
    if not isinstance(gd, list) or not gd:
        print("FAIL drops.json: no drops — an empty digest cannot be a solution")
        return 1
    wd = want["drops"]
    if [d.get("drop") for d in gd] != [d["drop"] for d in wd]:
        print(f"FAIL drops: expected {[d['drop'] for d in wd]}, got {[d.get('drop') for d in gd]}")
        return 1
    for g, w in zip(gd, wd):
        name = w["drop"]
        if not isinstance(g.get("files"), list) or not g["files"]:
            bad.append(f"{name}: no files listed")
        else:
            gnames = [f.get("name") for f in g["files"]]
            wnames = [f["name"] for f in w["files"]]
            if gnames != wnames:
                bad.append(f"{name} files: expected {wnames}, got {gnames}")
            else:
                for gf, wf in zip(g["files"], w["files"]):
                    if gf.get("sha256") != wf["sha256"]:
                        bad.append(f"{name}/{wf['name']}: sha256 differs")
                    if gf.get("checksumStatus") != wf["checksumStatus"]:
                        bad.append(f"{name}/{wf['name']}: checksumStatus expected "
                                   f"{wf['checksumStatus']}, got {gf.get('checksumStatus')}")
        for key in ("eventsByType", "totalEvents", "pages", "faultsBySource", "sessions"):
            if g.get(key) != w[key]:
                bad.append(f"{name}.{key}: expected {w[key]!r}, got {g.get(key)!r}")
        if g.get("sessions") is None and "sessionsSource" in w:
            if not isinstance(g.get("sessionsSource"), str) or not g["sessionsSource"]:
                bad.append(f"{name}.sessionsSource: null sessions must name the files checked")

    if bad:
        for line in bad[:20]:
            print("FAIL " + line)
        if len(bad) > 20:
            print(f"FAIL … {len(bad) - 20} more")
        return 1
    print("PASS T2: drops.json equals the frozen vector")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
