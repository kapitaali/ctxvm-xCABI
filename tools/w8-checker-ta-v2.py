#!/usr/bin/env python3
"""T-A v2 checker — takes fixture-dir + artefact-path as arguments.

v2 asks only for values read_file reports (total_lines, file_size) plus the exact text of line 137 of
part-12.txt. v1 asked for lines over 100 bytes and under 10 bytes; the tool does not report those, so
models counted by reproducing the file and truncated their own output (measured 2026-11-11).

Usage: w8-checker-ta-v2.py <fixture-dir> <artefact-path>
Parsed equality is the gate (ruled 2026-11-09); canonical formatting is a non-gating observation.
Prints which paths it read. Exit 0 PASS, 1 FAIL.
"""
import glob
import json
import os
import sys

MARKER_FILE = "part-12.txt"
MARKER_LINE = 137


def ground_truth(fixture: str) -> dict:
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(fixture, "part-*.txt")))
    gt = {}
    for fn in files:
        data = open(os.path.join(fixture, fn), "rb").read()
        text = data.decode("ascii")
        lines = text.split("\n")
        if text.endswith("\n"):
            lines = lines[:-1]
        gt[fn] = {"lines": len(lines), "bytes": len(data)}
    widest = max(gt, key=lambda k: (gt[k]["bytes"], -files.index(k)))
    marker = None
    if MARKER_FILE in gt:
        raw = open(os.path.join(fixture, MARKER_FILE), "rb").read().decode("ascii").split("\n")
        marker = raw[MARKER_LINE - 1]
    return {"files": gt, "widest_file": widest, "marker_line": marker}


def main() -> int:
    if len(sys.argv) != 3:
        print(f"FAIL: need <fixture-dir> <artefact-path>, got {sys.argv}", file=sys.stderr)
        return 1
    fixture, artefact_path = sys.argv[1], sys.argv[2]
    print(f"checker v2: fixture={fixture} artefact={artefact_path}")
    try:
        gt = ground_truth(fixture)
    except Exception as exc:
        print(f"FAIL: cannot read fixture: {exc}")
        return 1
    if len(gt["files"]) != 20:
        print(f"FAIL: fixture has {len(gt['files'])} parts, expected 20")
        return 1
    try:
        art = json.load(open(artefact_path))
    except Exception as exc:
        print(f"FAIL: artefact not valid json: {exc}")
        return 1

    fails = []
    if list(art.keys()) != ["files", "widest_file", "marker_line"]:
        fails.append(f"top-level keys {list(art.keys())} != [files, widest_file, marker_line]")
    files = art.get("files") or {}
    if list(files.keys()) != sorted(files.keys()):
        fails.append("files keys not sorted ascending")
    if sorted(files) != sorted(gt["files"]):
        fails.append(f"file key set mismatch: missing {sorted(set(gt['files']) - set(files))} "
                     f"extra {sorted(set(files) - set(gt['files']))}")
    for fn, want in gt["files"].items():
        got = files.get(fn)
        if got != want:
            fails.append(f"{fn}: {got} vs {want}")
    if art.get("widest_file") != gt["widest_file"]:
        fails.append(f"widest_file {art.get('widest_file')!r} vs {gt['widest_file']!r}")
    if art.get("marker_line") != gt["marker_line"]:
        got = art.get("marker_line")
        fails.append(f"marker_line {str(got)[:40]!r} vs {str(gt['marker_line'])[:40]!r}")

    canonical = json.dumps(gt, indent=2) + "\n"
    try:
        raw = open(artefact_path, encoding="utf-8").read()
    except Exception:
        raw = ""
    note = "canonical bytes match" if raw == canonical else "canonical bytes differ (non-gating)"

    if fails:
        for f in fails[:6]:
            print(f"FAIL: {f}")
        if len(fails) > 6:
            print(f"FAIL: … {len(fails) - 6} more")
        print(f"note: {note}")
        return 1
    print("PASS: parsed equality (20 files, widest_file, marker_line)")
    print(f"note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
