#!/usr/bin/env bash
# Freeze gate: every expected artefact must be DQ-clean before the first paid call
# (design/w8-run-plan.md §3b finding 5, §8.7).
#
# tools/dq-secret-scan.py is extension-gated: it accepts *.jsonl, *.meta.json and
# *.provenance and refuses anything else with exit 2 ("not a drop-set shape"). The frozen
# artefacts are .json/.md, so each one is copied byte-for-byte to a temp dir under a
# .meta.json name and scanned there. The verdict is about the CONTENT — the scanner reads
# bytes, not extensions — and the re-extension is stated here and in the run report, never
# hidden.
#
# Exit 0 = every expected artefact scanned with zero matches. 1 = a match or a tool error.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 2
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
for f in benchmarks/w8/templates/t*/expected/*; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  cp "$f" "$tmp/$base.meta.json"
  out=$(python3 tools/dq-secret-scan.py "$tmp/$base.meta.json" 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "DQ FAIL ($rc) $f"
    echo "$out" | sed 's/^/    /'
    fail=1
  else
    echo "DQ ok   $f"
  fi
  rm -f "$tmp/$base.meta.json"
done
exit $fail
