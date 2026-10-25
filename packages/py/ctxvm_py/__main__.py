"""ctxvm-py command-line entry point.

Thin wrapper around the committed Rust CLI binaries — same surface as the
Python API, usable from the shell:

    ctxvm-py replay <trace> [--turn N] [--pin ...]
    ctxvm-py profile <trace> [--event <type>]... [--turns spec] [--source <src>]
    ctxvm-py diff <a.jsonl> <b.jsonl>
    ctxvm-py export <trace> [--turn N] [--odps]
"""

from __future__ import annotations

import json
import sys

from ctxvm_py._cli import diff, export, profile, replay


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: ctxvm-py <replay|profile|diff|export> <trace> [args...]",
            file=sys.stderr,
        )
        return 2
    sub = sys.argv[1]
    rest = sys.argv[2:]

    try:
        if sub == "replay":
            if not rest:
                print("ctxvm-py: replay <trace> [--turn N] [--pin ...]", file=sys.stderr)
                return 2
            report = replay(rest[0])
        elif sub == "profile":
            if not rest:
                print(
                    "ctxvm-py: profile <trace> [--event <type>]...",
                    file=sys.stderr,
                )
                return 2
            report = profile(rest[0])
        elif sub == "diff":
            if len(rest) < 2:
                print("ctxvm-py: diff <a.jsonl> <b.jsonl>", file=sys.stderr)
                return 2
            report = diff(rest[0], rest[1])
        elif sub == "export":
            if not rest:
                print(
                    "ctxvm-py: export <trace> [--turn N] [--odps]",
                    file=sys.stderr,
                )
                return 2
            report = export(rest[0])
        else:
            print(f"ctxvm-py: unknown subcommand '{sub}'", file=sys.stderr)
            return 2
    except RuntimeError as exc:
        print(f"ctxvm-py: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
