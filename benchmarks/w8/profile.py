#!/usr/bin/env python3
"""Record a template's page profile mechanically (w8-run-plan.md §3b finding 1/3).

The minimum-read bound is the apx4-char token count of the logical fixture files —
the bytes a correct solution must actually read. apx4 is the repo's own counting law
(`rust/crates/ctxvm-tokenizer/src/lib.rs:51`: ceil(chars/4)), so the number is
reproducible by anyone with the fixture, and it is not a model claim.

Family law (frozen with the plan): a template whose bound is below 45,000 tokens cannot
test a 24,000 vBudget — both arms behave identically — so it is recorded as a
FLOOR CONTROL and never counts toward the NTR gate.

Usage: python3 benchmarks/w8/profile.py <templates/tN> [--repo-root DIR]
       Reads <tN>/fixture.json, writes <tN>/profile.json.
"""
import argparse
import json
from pathlib import Path

THRESHOLD = 45000


def apx4(text: str) -> int:
    return (len(text) + 3) // 4  # ceil(chars/4); fixture files are UTF-8, chars==codepoints


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--chunk-bytes", type=int, default=5600)
    args = ap.parse_args()
    tdir = Path(args.template).resolve()
    spec = json.loads((tdir / "fixture.json").read_text(encoding="utf-8"))
    root = Path(args.repo_root).resolve()

    tokens = 0
    pages = 0
    per_file = []
    for rel in spec["files"]:
        text = (root / rel).read_text(encoding="utf-8")
        t = apx4(text)
        tokens += t
        # parts the materializer will emit: line-aligned chunks of <= chunk_bytes
        n, cur = 1, 0
        for line in text.splitlines(keepends=True):
            b = len(line.encode("utf-8"))
            if cur and cur + b > args.chunk_bytes:
                n, cur = n + 1, 0
            cur += b
        pages += n
        per_file.append({"path": rel, "apx4Tokens": t, "parts": n})

    family = "pressure" if tokens >= THRESHOLD else "floor_control"
    out = {
        "template": tdir.name,
        "family": family,
        "thresholdTokens": THRESHOLD,
        "minReadTokens": tokens,
        "expectedPages": pages,
        "pageCapTokens": 1500,
        "artefact": spec.get("artefact"),
        "files": per_file,
    }
    (tdir / "profile.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"{out['template']}: family={family} minReadTokens={tokens} pages={pages} "
          f"files={len(per_file)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
