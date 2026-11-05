#!/usr/bin/env python3
"""Render index.md (the website source) from white-paper.md (the PDF source).

The two files used to be maintained by hand and drifted. This script makes one the
single source of the body: everything from `## Abstract` onwards is copied verbatim
from white-paper.md, and index.md keeps only its own front block (title, working
title, status line, separator).

Usage:
  python3 sync-index.py            # rewrite index.md, report what changed
  python3 sync-index.py --check    # exit 1 if index.md is out of date (CI-able)
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "white-paper.md"
TARGET = HERE / "index.md"
BODY_MARKER = "## Abstract"
FRONT_FALLBACK = (
    "# ctxvm / xCABI — A white paper\n\n"
    "**Working title.** Virtual memory for LLM agent context: the xCABI standard and the ctxvm engine.\n\n"
    "**Status.** Phase 6 of 6 complete (safety sections added 2026-11-05). "
    "Sources: all external claims web-verified or marked UNVERIFIED; repo facts from the repository checkout.\n\n"
    "---\n\n"
)


def front_block(text: str) -> str:
    """Everything in index.md before the body marker, or a default front matter."""
    idx = text.find(BODY_MARKER)
    if idx < 0:
        return FRONT_FALLBACK
    return text[:idx]


def render() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    body_at = source.find(BODY_MARKER)
    if body_at < 0:
        raise SystemExit(f"sync-index: {SOURCE.name} has no '{BODY_MARKER}' heading")
    existing = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    return front_block(existing) + source[body_at:]


def main(argv: list[str]) -> int:
    rendered = render()
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if "--check" in argv:
        if rendered != current:
            print("sync-index: index.md is out of date — run python3 sync-index.py")
            return 1
        print("sync-index: OK — index.md matches white-paper.md")
        return 0
    if rendered == current:
        print("sync-index: unchanged")
        return 0
    TARGET.write_text(rendered, encoding="utf-8")
    print(f"sync-index: wrote {TARGET.name} ({len(rendered)} chars) from {SOURCE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
