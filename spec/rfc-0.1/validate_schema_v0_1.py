#!/usr/bin/env python3
"""xCABI-0.1 schema validator (RFC-0.1 addendum).

Additive: the sealed v0 validator (spec/rfc-0/validate_schema.py) is untouched.
This validator checks v0.1 traces (lines carrying schemaVersion "0.1" or the
RFC-0.1 additive fields) against spec/rfc-0.1/x-cabi.schema-v0.1.json, runs a
negative corpus, and asserts the sealed v0 schema still rejects v0.1-only lines
(the compatibility boundary, demonstrated mechanically).
"""
import json
import os
import sys
from datetime import datetime

try:
    import jsonschema
except ImportError:
    print("jsonschema not installed; pip install jsonschema", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "x-cabi.schema-v0.1.json")
V0_SCHEMA_PATH = os.path.join(HERE, "..", "rfc-0", "x-cabi.schema-v0.json")

with open(SCHEMA_PATH) as f:
    SCHEMA = json.load(f)
with open(V0_SCHEMA_PATH) as f:
    V0_SCHEMA = json.load(f)

# Negative corpus for v0.1 (each must be rejected).
NEGATIVES = [
    # unknown source
    {"type": "page.fault", "turn": 0, "page": {"logicalRef": "x", "contentHash": "h"}, "source": "replay_rewind"},
    # negative usage
    {"type": "call.meta", "turn": 0, "provider": "p", "cacheEstimate": {"estHitTokens": 0, "estMissTokens": 0, "providerReported": False}, "providerUsage": {"inputTokens": -5, "outputTokens": 1}},
    # malformed ts
    {"type": "session.open", "agentId": "a", "model": "m", "provider": "p", "budgetTokens": 1, "tokenizerId": "t", "schemaVersion": "0.1", "ts": "2026-13-99T99:99:99.999Z"},
    # negative turn
    {"type": "page.declare", "page": {"id": {"logicalRef": "x", "contentHash": "h"}, "kind": "file", "tokens": 1}, "turn": -1},
    # unknown schemaVersion
    {"type": "session.open", "agentId": "a", "model": "m", "provider": "p", "budgetTokens": 1, "tokenizerId": "t", "schemaVersion": "0.2"},
    # null providerUsage (must be omitted, never null)
    {"type": "call.meta", "turn": 0, "provider": "p", "cacheEstimate": {"estHitTokens": 0, "estMissTokens": 0, "providerReported": False}, "providerUsage": None},
]


def validate_line(obj):
    # jsonschema validation against v0.1 schema
    jsonschema.validate(obj, SCHEMA)
    # semantic ts check (real calendar date)
    ts = None
    for k in ("ts",):
        if k in obj and obj[k] is not None:
            ts = obj[k]
    if ts is not None:
        try:
            datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            raise ValueError(f"ts not a real calendar date: {ts}")


def main():
    failures = 0
    # Positive: validate any files passed as args
    for path in sys.argv[1:]:
        with open(path) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"{path}:{i}: JSON parse error: {e}")
                    failures += 1
                    continue
                try:
                    validate_line(obj)
                except (jsonschema.ValidationError, ValueError) as e:
                    print(f"{path}:{i}: FAIL {e}")
                    failures += 1
    # Negative corpus must be rejected
    for neg in NEGATIVES:
        try:
            validate_line(neg)
            print(f"NEGATIVE NOT REJECTED: {neg}")
            failures += 1
        except (jsonschema.ValidationError, ValueError):
            pass
    # compatibility boundary: sealed v0 schema must reject v0.1-only lines
    v0_1_only = [
        {"type": "page.fault", "turn": 0, "page": {"logicalRef": "x", "contentHash": "h"}, "source": "intentional_rerun"},
        {"type": "call.meta", "turn": 0, "provider": "p", "cacheEstimate": {"estHitTokens": 0, "estMissTokens": 0, "providerReported": False}, "providerUsage": {"inputTokens": 1, "outputTokens": 2}},
        {"type": "session.open", "agentId": "a", "model": "m", "provider": "p", "budgetTokens": 1, "tokenizerId": "t", "schemaVersion": "0.1"},
        {"type": "page.declare", "page": {"id": {"logicalRef": "x", "contentHash": "h"}, "kind": "file", "tokens": 1}, "turn": 1},
    ]
    for neg in v0_1_only:
        try:
            jsonschema.validate(neg, V0_SCHEMA)
            print(f"V0 DID NOT REJECT v0.1-only line: {neg}")
            failures += 1
        except jsonschema.ValidationError:
            pass
    if failures:
        print(f"{failures} failure(s)")
        sys.exit(1)
    print("OK: all checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
PY