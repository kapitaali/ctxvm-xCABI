#!/usr/bin/env python3
"""T1 checker — mechanical PASS/FAIL, no model judgement.

Usage: python3 checker.py <workspace>          (expects <workspace>/flags.json)
Exit:  0 = artefact equals the frozen expected vector
       1 = FAIL, one reason per line on stdout
       2 = usage / unreadable artefact

The expected vector is `expected/flags.json`, rebuilt by `build_expected.py` from the
same fixture paths (see task.md for the rule). Comparison is exact: same binaries in the
same order, same flags in the same order, same core functions, same files, same items.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path: Path, label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        print(f"FAIL {label}: not found at {path}")
        raise SystemExit(1)
    except ValueError as exc:
        print(f"FAIL {label}: not valid JSON ({exc})")
        raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: checker.py <workspace>")
        return 2
    ws = Path(sys.argv[1]).resolve()
    got = load(ws / "flags.json", "flags.json")
    want = json.loads((HERE / "expected" / "flags.json").read_text(encoding="utf-8"))
    bad = []

    if not isinstance(got, dict):
        print("FAIL flags.json: top level must be an object")
        return 1
    extra = set(got) - {"binaries", "publicSurface"}
    if extra:
        bad.append(f"unexpected top-level keys: {sorted(extra)}")

    gb, wb = got.get("binaries") or [], want["binaries"]
    if [b.get("binary") for b in gb if isinstance(b, dict)] != [b["binary"] for b in wb]:
        bad.append(f"binaries: expected {[b['binary'] for b in wb]}, "
                   f"got {[b.get('binary') if isinstance(b, dict) else b for b in gb]}")
    else:
        for g, w in zip(gb, wb):
            if g.get("flags") != w["flags"]:
                bad.append(f"{w['binary']} flags: expected {w['flags']}, got {g.get('flags')}")
            if g.get("coreFunction") != w["coreFunction"]:
                bad.append(f"{w['binary']} coreFunction: expected {w['coreFunction']}, "
                           f"got {g.get('coreFunction')}")

    gs, ws = got.get("publicSurface") or [], want["publicSurface"]
    if [f.get("file") for f in gs if isinstance(f, dict)] != [f["file"] for f in ws]:
        bad.append("publicSurface: file list or order differs from the fixture")
    else:
        for g, w in zip(gs, ws):
            gi = g.get("items") if isinstance(g.get("items"), list) else []
            if gi != w["items"]:
                gi_names = [f"{i.get('kind')} {i.get('name')}" if isinstance(i, dict) else i for i in gi]
                wi_names = [f"{i['kind']} {i['name']}" for i in w["items"]]
                missing = [x for x in wi_names if x not in gi_names]
                surplus = [x for x in gi_names if x not in wi_names]
                detail = "order differs" if not missing and not surplus else \
                         f"missing={missing[:4]} surplus={surplus[:4]}"
                bad.append(f"{w['file']} items: expected {len(wi_names)}, got {len(gi_names)} ({detail})")

    if bad:
        for line in bad[:20]:
            print("FAIL " + line)
        if len(bad) > 20:
            print(f"FAIL … {len(bad) - 20} more")
        return 1
    print("PASS T1: flags.json equals the frozen vector")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
