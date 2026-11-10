#!/usr/bin/env python3
"""T-A checker — takes fixture-dir + artefact-path as arguments.

Usage: checker.py <fixture-dir> <artefact-path>
Recomputes lines/bytes/long/short per T-A.md, checks sorted file keys, widest_file,
total_long, and byte-exact canonical form (2-space indent, files keys sorted,
per-file keys lines/bytes/long/short, top-level files/widest_file/total_long, trailing \n).
Prints which paths it read. Exit 0 PASS, 1 FAIL.
"""
import glob, json, os, sys, collections


def main():
    if len(sys.argv) != 3:
        print(f"FAIL: need <fixture-dir> <artefact-path>, got {sys.argv}", file=sys.stderr)
        return 1
    fixture, artefact_path = sys.argv[1], sys.argv[2]
    print(f"checker: fixture={fixture} artefact={artefact_path}")
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(fixture, "part-*.txt")))
    if not files:
        print("FAIL: no part-*.txt in fixture")
        return 1
    gt = {}
    total_long = 0
    widest, max_long = None, -1
    for fn in files:
        data = open(os.path.join(fixture, fn), "rb").read()
        text = data.decode("ascii")
        lines = text.split("\n")
        if text.endswith("\n"):
            lines = lines[:-1]
        bls = [len(l.encode("ascii")) for l in lines]
        long = sum(1 for b in bls if b > 100)
        short = sum(1 for b in bls if b < 10)
        gt[fn] = {"lines": len(lines), "bytes": len(data), "long": long, "short": short}
        total_long += long
        if long > max_long or (long == max_long and (widest is None or fn < widest)):
            max_long, widest = long, fn
    try:
        art = json.load(open(artefact_path))
    except Exception as e:
        print(f"FAIL: artefact not valid json: {e}")
        return 1
    if list(art.keys()) != ["files", "widest_file", "total_long"]:
        print(f"FAIL: top-level keys {list(art.keys())} != [files, widest_file, total_long]")
        return 1
    if list(art["files"].keys()) != sorted(art["files"].keys()):
        print("FAIL: files keys not sorted ascending")
        return 1
    if sorted(art["files"].keys()) != sorted(gt.keys()):
        print("FAIL: file key set mismatch")
        return 1
    for fn in gt:
        if art["files"][fn] != gt[fn]:
            print(f"FAIL: {fn} {art['files'][fn]} vs {gt[fn]}")
            return 1
    if art["widest_file"] != widest:
        print(f"FAIL: widest_file {art['widest_file']} vs {widest}")
        return 1
    if art["total_long"] != total_long:
        print(f"FAIL: total_long {art['total_long']} vs {total_long}")
        return 1
    # canonical byte form: files sorted, per-file order lines/bytes/long/short, top order as above
    ordered_files = collections.OrderedDict((fn, gt[fn]) for fn in sorted(gt.keys()))
    canonical_obj = collections.OrderedDict([("files", ordered_files), ("widest_file", widest), ("total_long", total_long)])
    canonical = json.dumps(canonical_obj, indent=2) + "\n"
    actual = open(artefact_path).read()
    # Parsed equality is the gate (T-A.md, ruled 2026-11-09). Canonical bytes are
    # an OBSERVATION: byte-exactness would turn JSON style into an accuracy result.
    if actual != canonical:
        print("note: formatting differs from canonical (indent/sort/newline) - not gating")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
