#!/usr/bin/env python3
"""W8 workspace materializer (shared by every template) — deterministic chunking.

Why chunks: the design caps every tool result at ~1.5k tokens (RR-ENGINEGAP: six large
tail results push the protected floor above vBudget and the paged arm goes inert). A 51 KB
source read in one call is ~13k tokens, so a template presents the same bytes as
line-aligned parts of at most CHUNK_BYTES plus a MANIFEST.tsv mapping each part back to
its logical path and line range. Concatenating a file's parts in manifest order
reproduces the source exactly; the template's checker may verify that.

Usage: python3 benchmarks/w8/materialize.py <template-dir> <repo-root> <workspace-root>
"""
import hashlib
import json
import sys
from pathlib import Path

CHUNK_BYTES = 5600  # ~1.4k apx4-char tokens, under the 1.5k page cap


def chunk(text: str, limit: int = CHUNK_BYTES):
    parts, cur, start, n = [], [], 1, 0
    for i, line in enumerate(text.splitlines(keepends=True), 1):
        b = len(line.encode("utf-8"))
        if cur and n + b > limit:
            parts.append((start, i - 1, "".join(cur)))
            cur, start, n = [], i, 0
        cur.append(line)
        n += b
    if cur:
        parts.append((start, start + len(cur) - 1, "".join(cur)))
    return parts


def main() -> int:
    tdir = Path(sys.argv[1]).resolve()
    root = Path(sys.argv[2]).resolve()
    ws = Path(sys.argv[3]).resolve()
    spec = json.loads((tdir / "fixture.json").read_text(encoding="utf-8"))
    limit = int(spec.get("chunkBytes", CHUNK_BYTES))
    rows = []
    for rel in spec["files"]:
        src = (root / rel).read_text(encoding="utf-8")
        for idx, (lo, hi, body) in enumerate(chunk(src, limit), 1):
            out = ws / (rel + f".part{idx:02d}")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(body, encoding="utf-8")
            rows.append((rel + f".part{idx:02d}", rel, lo, hi,
                         len(body.encode("utf-8")),
                         hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]))
    lines = ["part\tlogical_path\tlines\tbytes\tsha256_16"]
    lines += [f"{p}\t{l}\t{lo}-{hi}\t{b}\t{h}" for p, l, lo, hi, b, h in rows]
    (ws / "MANIFEST.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{tdir.name}: files={len(spec['files'])} parts={len(rows)} bytes={sum(r[4] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
