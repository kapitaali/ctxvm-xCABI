#!/usr/bin/env bash
# T21 export round-trip — the chain that proves a handoff snapshot is a faithful slice.
#
# Extracted from tools/run-ci.sh gate 3 so the local gate and .github/workflows/ci.yml run
# the SAME text instead of two copies that drift. Expects the release binaries to exist
# (`cargo build --release`); it builds nothing itself.
#
#   export corpus/m3 @2 --odps  → zstd slice → replay --turn 2 → diff (a_extends_b)
#   → replay the m4 live capture → per-dir checksums
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
BIN="rust/target/release"
[ -x "$BIN/export" ] || { echo "export-roundtrip: build the release binaries first" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

"$BIN/export" corpus/m3/hermes-echo-synthetic.jsonl --turn 2 \
  --output "$TMP/handoff" --odps >/dev/null 2>&1
zstd -q -d -f "$TMP/handoff/trace-2.jsonl.zst" -o "$TMP/handoff/trace-2.jsonl"
"$BIN/replay" "$TMP/handoff/trace-2.jsonl" --turn 2 >/dev/null
"$BIN/diff" corpus/m3/hermes-echo-synthetic.jsonl "$TMP/handoff/trace-2.jsonl" >/dev/null
"$BIN/replay" corpus/m4/hermes-live-session-01.jsonl >/dev/null
( cd "$TMP/handoff" && sha256sum -c checksums.sha256 ) >/dev/null

echo "export-roundtrip: OK — slice @2 replays, diff a_extends_b, m4 replay clean, checksums verified"
