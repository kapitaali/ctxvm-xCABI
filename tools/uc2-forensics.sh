#!/usr/bin/env bash
# tools/uc2-forensics.sh — UC2 forensics kit entry (09-plugin-parity.md §5).
#
# Why a kit entry: the opencode v2.1.2 promise-plugin surface exposes NO
# command-registration hook (the pinned contract is session.context +
# tool.execute.before/after only — packages/opencode/src/opencode-contract.ts),
# so the opencode lane cannot carry /ctxvm-forensics the way hermes does. The
# SAME verdicts are provided here by driving the parity-pinned TS mirror module
# (packages/opencode/src/uc2-forensics.ts); both implementations deep-equal the
# shared golden fixture (packages/opencode/test/fixtures/uc2-diagnose-golden.json).
#
# Usage:
#   tools/uc2-forensics.sh diagnose <trace.jsonl> <fault-turn>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "${1:-}" != "diagnose" ] || [ "$#" -ne 3 ]; then
  echo "usage: tools/uc2-forensics.sh diagnose <trace.jsonl> <fault-turn>" >&2
  exit 2
fi
if ! command -v node >/dev/null 2>&1; then
  echo "node not found on PATH (UC2 mirror module is node-run)" >&2
  exit 2
fi

exec node "$ROOT/packages/opencode/src/uc2-forensics.ts" "$@"
