#!/usr/bin/env python3
"""xCABI RFC-0 conformance validator (T4 DoD artifact, CI-gettable).

Checks (against spec/rfc-0/x-cabi.schema-v0.json):
  1. Every line of every vector fixture validates (events-v0, session-clean,
     session-divergent).
  2. Negative gates produce validator failures: unknown tag / unknown field /
     float-encoded integer / null where omission is the norm.
Exit 0 = all pass. Any failure prints the offending line + validator error.

Run:  venvs/odps/bin/python spec/rfc-0/validate_schema.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "spec/rfc-0/x-cabi.schema-v0.json"
DIRS = [
    ROOT / "rust/crates/ctxvm-conformance/vectors",
]

VALIDATORS = [
    "events-v0.jsonl",
    "session-clean.jsonl",
    "session-divergent.jsonl",
]

NEGATIVE_CASES = [
    ("unknown tag", '{"type":"page.crash"}'),
    ("unknown field", '{"type":"page.pin","page":{"logicalRef":"x","contentHash":"h"},"reason":"r","xShadow":"evil"}'),
    ("float tokens", '{"type":"turn.render","turn":0,"residentTokens":47.5,"evictedTokens":0}'),
    ("null optional", '{"type":"call.meta","turn":0,"provider":"p","cacheEstimate":{"estHitTokens":1,"estMissTokens":0,"providerReported":false},"latencyMs":null}'),
    ("missing required", '{"type":"session.open"}'),
]


def load_schema() -> jsonschema.protocols.Validator:
    with SCHEMA.open() as f:
        schema = json.load(f)
    v = jsonschema.Draft202012Validator(schema)
    v.check_schema(schema)
    return v


def validate_line(validator, line: str, origin: str) -> None:
    event = json.loads(line)
    validator.validate(event)


def main() -> int:
    validator = load_schema()
    failures: list[str] = []
    checked = 0

    for name in VALIDATORS:
        path = DIRS[0] / name
        for idx, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            try:
                validate_line(validator, line, f"{name}:{idx}")
                checked += 1
            except jsonschema.ValidationError as e:
                failures.append(f"{name}:{idx}: {e.message}")

    print(f"positive: {checked} event lines validated across {len(VALIDATORS)} fixtures")

    for label, line in NEGATIVE_CASES:
        try:
            validate_line(validator, line, "negative")
            failures.append(f"NEGATIVE GATE NOT CAUGHT ({label}): {line}")
        except jsonschema.ValidationError:
            checked += 1

    print(f"negative: {len(NEGATIVE_CASES)} engineered bad cases correctly rejected")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        return 1

    print(f"\nSCHEMA CONFORMANCE: PASS ({checked} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
