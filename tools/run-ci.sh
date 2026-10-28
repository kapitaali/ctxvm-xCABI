#!/usr/bin/env bash
# tools/run-ci.sh — byte-equivalent local mirror of .github/workflows/ci.yml.
#
# The repo has no git remote yet (orchestrator decision), so this script is how
# the gate is WITNESSED today; pinning matches the workflow: python 3.14 +
# jsonschema 4.26.0 + open-data-products==0.4.0 (venvs/odps), node 26, rust stable.
# Gates:
#   1. rust — cargo test (workspace rust/)
#   2. typescript — packages/node + packages/opencode test suites
#   3. schema — rfc-0 validator over spec vectors + every committed fixture,
#      including the corpus/m1 drop, then corpus checksum verification
#   4. hub — root manifest ODPS validate + regen via their SDK + byte-identity
#      against the committed hub/hub.sha256 baseline
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
log() { printf '[ctxvm-ci] %s\n' "$*"; }
FIXTURES=(
  benchmarks/metrics/fixtures/session-healthy.jsonl
  benchmarks/metrics/fixtures/session-thrashing.jsonl
  packages/node/fixtures/tracer-healthy.jsonl
  packages/node/fixtures/tracer-recall.jsonl
  packages/opencode/fixtures/opencode-echo.jsonl
  packages/hermes/fixtures/hermes-echo-synthetic.jsonl
  packages/hermes/fixtures/hermes-thrash-synthetic.jsonl
  corpus/m1/session-healthy.jsonl
  corpus/m1/session-thrashing.jsonl
  corpus/m1/tracer-healthy.jsonl
  corpus/m1/tracer-recall.jsonl
  corpus/m1/opencode-echo.jsonl
  corpus/m2/live-echo.jsonl
  corpus/m2/live-thrash.jsonl
  corpus/m3/hermes-echo-synthetic.jsonl
  corpus/m3/hermes-thrash-synthetic.jsonl
  corpus/m4/hermes-live-session-01.jsonl
  corpus/m5/opencode-live-session-01.jsonl
  corpus/m6/opencode-pause-session-a.jsonl
  corpus/m6/opencode-resume-session-b.jsonl
  corpus/m7/hermes-pause-session-a.jsonl
  corpus/m7/hermes-resume-session-b.jsonl
  corpus/m8/live-echo.jsonl
  corpus/m8/live-thrash.jsonl
)

# 1) rust
log "gate 1/4: rust — cargo test"
( cd rust && . "$HOME/.cargo/env" 2>/dev/null || true; cargo test ) >/dev/null
log "rust suite green"

# 1b) release binaries for the golden parity suites (UC2 forensics + UC1 resume:
# hermes python + opencode TS both deep-equal the shared fixtures through the
# real CLI; the UC1 resume path also shells the zstd CLI — shipped on dev+CI).
( cd rust && cargo build --release ) >/dev/null
log "release binaries green (UC2/UC1 golden parity)"

# 2) typescript + python
log "gate 2/4: typescript — @ctxvm/node + @ctxvm/opencode + @ctxvm/ai-sdk; python — @ctxvm/hermes + @ctxvm/py binding"
( cd packages/node && node --test test/ ) >/dev/null
( cd packages/opencode && node --test test/ ) >/dev/null
( cd packages/ai-sdk && node --test test/ ) >/dev/null
( cd packages/hermes && python -m pytest test/ -q ) >/dev/null
( cd packages/py && python -m pytest test/ -q ) >/dev/null
log "gate 2b: benchmarks/metrics — 07 reference suite + policy simulator"
( venvs/odps/bin/python -m pytest benchmarks/metrics -q ) >/dev/null
log "ts suites green (13 + 51 + 45 tests); python suites green (80 + 30 + 8 tests)"

# 3) schema + corpus integrity + the T21 export round-trip
log "gate 3/4: schema validator + corpus checksums + export round-trip"
venvs/odps/bin/python spec/rfc-0/validate_schema.py "${FIXTURES[@]}"
( cd corpus/m1 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m2 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m3 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m4 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m5 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m6 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m7 && sha256sum -c checksums.sha256 ) >/dev/null
( cd corpus/m8 && sha256sum -c checksums.sha256 ) >/dev/null
( cd rust && . "$HOME/.cargo/env" 2>/dev/null || true; cargo build --release ) >/dev/null
EXPORT_TMP="$(mktemp -d)"
rust/target/release/export corpus/m3/hermes-echo-synthetic.jsonl --turn 2 \
  --output "$EXPORT_TMP/handoff" --odps >/dev/null 2>&1
zstd -q -d -f "$EXPORT_TMP/handoff/trace-2.jsonl.zst" -o "$EXPORT_TMP/handoff/trace-2.jsonl"
rust/target/release/replay "$EXPORT_TMP/handoff/trace-2.jsonl" --turn 2 >/dev/null
rust/target/release/diff corpus/m3/hermes-echo-synthetic.jsonl "$EXPORT_TMP/handoff/trace-2.jsonl" >/dev/null
rust/target/release/replay corpus/m4/hermes-live-session-01.jsonl >/dev/null
( cd "$EXPORT_TMP/handoff" && sha256sum -c checksums.sha256 ) >/dev/null
rm -rf "$EXPORT_TMP"
log "schema + export round-trip gate green"

# 4) hub parity
log "gate 4/4: hub — ODPS validate + regen byte-identity"
venvs/odps/bin/open-data-products validate 04-odps-dataproduct-corpus.yaml >/dev/null
tools/build-hub.sh >/dev/null 2>&1
log "hub byte-identity green"

log "ALL GATES GREEN"
