#!/usr/bin/env bash
# KIT-1 (09-plugin-parity.md §5) — era-snapshot helper, BOTH harness plugins.
#
#   tools/snapshot-capture.sh <capture-dir> <name> <era-label>
#
# Flushes overwrite ONE CTXVM_TRACE_NAME on both harnesses, so snapshot the
# flushed file IMMEDIATELY after a successful flush (the m5 lesson: the next
# flush would overwrite the previous era). cp -n never clobbers an existing
# era snapshot.
set -euo pipefail
D="${1:?capture dir}"; NAME="${2:?flushed name}"; LABEL="${3:?era label}"

for ext in jsonl meta.json; do
  src="$D/$NAME.$ext"
  dst="$D/$NAME-$label.$ext"
  [ -f "$src" ] || { echo "missing source: $src" >&2; exit 1; }
  cp -n "$src" "$dst" && echo "snapshot: $dst" || echo "kept: $dst (already snapshotted)"
done
wc -c "$D/$NAME-$label.jsonl" "$D/$NAME-$label.meta.json"
