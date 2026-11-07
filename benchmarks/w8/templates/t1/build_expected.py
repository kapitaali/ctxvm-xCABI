#!/usr/bin/env python3
"""T1 expected-artefact builder — the MECHANICAL RULE, executable.

Rule (stated in benchmarks/w8/templates/t1/task.md and frozen with the checker):

  flags        A long flag is ACCEPTED by a binary iff its literal appears as a
               match pattern in that binary's argument loop (`match arg.as_str()`
               arms, or a `"--x" =>` arm of an equivalent loop). Patterns in doc
               comments (/// or //!), in USAGE constants and in help() bodies are
               NOT accepted — they are prose, and at least one of them is wrong.
               Flags are listed in the source order of their first pattern.
  core         The core entry point is the first `cli::<name>(` call in the
               binary's main(), i.e. the conformance library function the binary
               hands its parsed arguments to. A binary with no such call records
               null.
  surface      For each fixture file, the public items are every top-level
               declaration whose line starts with `pub ` at column 0, in source
               order: pub fn / struct / enum / trait / const / type / mod.
               `pub(crate)` and nested `pub` inside impl blocks are excluded.

Usage: python3 build_expected.py <repo-root> <out.json>
"""
import json
import re
import sys
from pathlib import Path

FIXTURE = json.loads((Path(__file__).with_name("fixture.json")).read_text())["files"]
BINS = json.loads((Path(__file__).with_name("fixture.json")).read_text())["binaries"]

ARM = re.compile(r'^\s*"(--[a-z0-9-]+)"(?:\s*\|\s*"(-[a-z])")?\s*=>')
PUB = re.compile(r'^pub (fn|struct|enum|trait|const|type|mod) ([A-Za-z_][A-Za-z0-9_]*)', re.M)
CORE = re.compile(r'\bcli::([a-z_][a-z0-9_]*)\(', re.M)


def flags_of(text: str):
    out, seen = [], set()
    for line in text.splitlines():
        m = ARM.match(line)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
    return out


def routine_of(text: str) -> str:
    """Signature line of the function that calls parse_args (the bin's main)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "parse_args" in line and "fn " not in line:
            for j in range(i, -1, -1):
                if lines[j].lstrip().startswith("fn ") or " fn " in lines[j]:
                    return lines[j].strip()
    return ""


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    out = {"binaries": [], "publicSurface": []}
    for rel in BINS:
        text = (root / rel).read_text(encoding="utf-8")
        m = CORE.search(text[text.find("fn main"):]) if "fn main" in text else CORE.search(text)
        out["binaries"].append({
            "binary": Path(rel).name,
            "flags": flags_of(text),
            "coreFunction": f"cli::{m.group(1)}" if m else None,
        })
    for rel in FIXTURE:
        text = (root / rel).read_text(encoding="utf-8")
        items = [{"kind": k, "name": n} for k, n in PUB.findall(text)]
        out["publicSurface"].append({"file": rel, "items": items})
    # Line-shape section (2026-11-07 rebuild): per-file integers that no match list yields.
    # A content search returns the lines that MATCH a pattern; it cannot report how many
    # lines a file has or which line is longest without the whole file being read.
    out["lineShape"] = []
    for rel in FIXTURE:
        body = (root / rel).read_text(encoding="utf-8")
        lines = body.split("\n")
        if lines and lines[-1] == "":
            lines = lines[:-1]            # a trailing newline does not open a line
        widths = [len(l.encode("utf-8")) for l in lines]
        out["lineShape"].append({"file": rel, "lines": len(lines),
                                 "maxLineBytes": max(widths) if widths else 0,
                                 "overlong100": sum(1 for w in widths if w > 100)})
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    total = sum(len(b["flags"]) for b in out["binaries"])
    print(f"binaries={len(out['binaries'])} flags={total} files={len(out['publicSurface'])} "
          f"items={sum(len(f['items']) for f in out['publicSurface'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
