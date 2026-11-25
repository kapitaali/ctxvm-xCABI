#!/usr/bin/env python3
"""Offline validator for ctxvm-shadow-selection/v1 JSONL records.

Usage: python3 tools/shadow-selection-validate.py RECORD.jsonl [RECORD.jsonl ...]
Exit 0 = all records valid; 1 = schema violation; 2 = usage / IO error.
The writer enforces the same validator before any record reaches disk.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "packages" / "hermes" / "live" / "shadow_schema.py"
spec = importlib.util.spec_from_file_location("shadow_schema", SCHEMA)
if spec is None or spec.loader is None:
    print("shadow schema: cannot load validator", file=sys.stderr)
    sys.exit(2)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main(argv):
    if not argv:
        print("usage: shadow-selection-validate.py RECORD.jsonl [...]", file=sys.stderr)
        return 2
    count = 0
    for name in argv:
        path = Path(name)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            print(f"shadow schema: IO error: {path}: {exc}", file=sys.stderr)
            return 2
        for line_no, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                mod.validate_record(record)
            except (ValueError, mod.ShadowSchemaError) as exc:
                print(f"shadow schema: invalid: {path}:{line_no}: {exc}", file=sys.stderr)
                return 1
            count += 1
    print(f"shadow schema: OK ({count} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))