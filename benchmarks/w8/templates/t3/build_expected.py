#!/usr/bin/env python3
"""T3 expected-artefact builder — five conformance behaviours, each a mechanical predicate.

The freeze rule (w8-run-plan.md §3b finding 2): the expected violator lists must be
AUTHORED, NON-EMPTY and computed by a stated mechanical rule, with per-file evidence.
A tree where every list is empty would let five empty arrays pass a checker without
reading a byte, so emptiness is treated as a freeze failure here and in checker.py.

Each behaviour is an implication over the file text:

  B1  a module that parses trace JSON (`JSON.parse` or `json.loads`) must declare an
      allowlist (`allowlist` or `ALLOW`)                       — RFC-0's strict codec law
  B2  a module that reads `providerUsage` must also read `latencyMs`
                                                              — the wire order D12 fixes
  B3  a module that emits a trace line (`page.declare` or `turn.render`) must name
      `schemaVersion`                                         — every line carries it
  B4  a module that handles `page.fault` must name an RFC-0.1 fault source
      (`identifier_scan` or `tool_recall`)                    — the W8 fault taxonomy
  B5  a module that handles `page.evict` must name `evictedTokens`
                                                              — the eviction Tally field

A violator row is {"file": <logical path>, "trigger": <the token that fired the
antecedent>}. Files are listed in path order; behaviours in id order.

Usage: python3 build_expected.py <repo-root> <out.json>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BEHAVIOURS = [
    ("B1", "Strict codec: a module that parses trace JSON must reject unknown fields, so it must declare an allowlist.",
     (("JSON.parse", "json.loads"), ("allowlist", "ALLOW"))),
    ("B2", "Wire order: a module that reads providerUsage must also read latencyMs.",
     (("providerUsage",), ("latencyMs",))),
    ("B3", "Every trace line carries schemaVersion: a module that emits a line must name it.",
     (("page.declare", "turn.render"), ("schemaVersion",))),
    ("B4", "Fault taxonomy: a module that handles page.fault must name an RFC-0.1 fault source.",
     (("page.fault",), ("identifier_scan", "tool_recall"))),
    ("B5", "Eviction tally: a module that handles page.evict must name evictedTokens.",
     (("page.evict",), ("evictedTokens",))),
]


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    spec = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    files = sorted(spec["files"])
    texts = {rel: (root / rel).read_text(encoding="utf-8") for rel in files}

    out = {"specSource": "02-xcabi-events-v0.md", "filesExamined": len(files), "behaviours": []}
    for bid, text, (ante, cons) in BEHAVIOURS:
        violators = []
        for rel in files:
            body = texts[rel]
            hit = next((t for t in ante if t in body), None)
            if hit is None:
                continue
            if not any(c in body for c in cons):
                violators.append({"file": rel, "trigger": hit})
        if not violators:
            raise SystemExit(f"freeze failure: {bid} has an EMPTY violator set")
        out["behaviours"].append({
            "id": bid,
            "behaviour": text,
            "predicate": f"{' | '.join(ante)}  ⇒  {' | '.join(cons)}",
            "examined": len(files),
            "violators": violators,
            "violatorCount": len(violators),
        })
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("behaviours=%d files=%d violators=%s" % (
        len(out["behaviours"]), len(files),
        [b["violatorCount"] for b in out["behaviours"]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
