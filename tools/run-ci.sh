#!/usr/bin/env bash
# tools/run-ci.sh — byte-equivalent local mirror of .github/workflows/ci.yml.
#
# The repo has no git remote yet (orchestrator decision), so this script is how
# the gate is WITNESSED today; pinning matches the workflow: python 3.14 +
# jsonschema 4.26.0 + open-data-products==0.4.0 (venvs/odps), node 26, rust stable.
# Gates:
#   1. rust — cargo test (workspace rust/)
#   2. typescript — packages/node + packages/opencode test suites; node build +
#      src-vs-dist byte parity (W10 — the publishable artifact)
#   3. schema — rfc-0 validator over spec vectors + every committed fixture,
#      including the corpus/m1 drop, then corpus checksum verification
#   4. hub — root manifest ODPS validate + regen via their SDK + byte-identity
#      against the committed hub/hub.sha256 baseline
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
log() { printf '[ctxvm-ci] %s\n' "$*"; }

# Hermetic environment: this script's job is to be a MIRROR of .github/workflows/ci.yml,
# and that workflow sets no CTXVM_* variable at all - but an interactive shell does
# (`.bashrc` exports CTXVM_BUDGET_TOKENS=200000, CTXVM_TRACE_TS=0, CTXVM_TRACE_DIR,
# CTXVM_FEATURES, CTXVM_AGENT_ID, CTXVM_MODEL, CTXVM_PROVIDER, CTXVM_TRACE_NAME,
# CTXVM_HERMES_VERSION). A leaked variable has broken the gate twice, both times by
# making a test assert about a value the test did not set:
#   - CTXVM_TRACE_TS=0 broke `node --test` (RR-ENVLEAK-20261110);
#   - CTXVM_BUDGET_TOKENS=200000 made the arm-policy test read 'env' where it means
#     'default' (2026-11-11, RR-CTXVMENV-20261111).
# Unsetting them here is what makes the local gate a mirror of CI rather than of
# whichever shell happened to run it. The steps below are unchanged.
for _v in CTXVM_TRACE_TS CTXVM_HERMES_VERSION CTXVM_BUDGET_TOKENS CTXVM_TRACE_DIR \
          CTXVM_TRACE_NAME CTXVM_FEATURES CTXVM_AGENT_ID CTXVM_MODEL CTXVM_PROVIDER; do
  unset "$_v" || true
done

# Counts are DERIVED, never typed. The summary used to be a literal, so adding
# five tests printed "177" while 182 ran (2026-11-09). A counted step keeps its
# log and appends "count<TAB>kind<TAB>name"; the summary reads that file.
CI_LOG_DIR="$(mktemp -d -t ctxvm-ci-logs-XXXXXX)"
COUNTS="$CI_LOG_DIR/counts.tsv"
: > "$COUNTS"
count_of() { # kind file
  case "$1" in
    node)   grep -oE 'pass [0-9]+' "$2" | awk '{s+=$2} END{print s+0}' ;;
    pytest) grep -oE '[0-9]+ passed' "$2" | tail -1 | awk '{print $1+0}' ;;

    *)      echo 0 ;;
  esac
}
run_counted() { # name kind cmd...
  local name="$1" kind="$2"; shift 2
  local out n
  out="$CI_LOG_DIR/$(printf '%s' "$name" | tr -c 'A-Za-z0-9' '_').log"
  if ! "$@" >"$out" 2>&1; then
    printf '\n[ctxvm-ci] FAILED: %s\n' "$name" >&2
    printf '[ctxvm-ci] last 40 lines of its output:\n' >&2
    tail -n 40 "$out" >&2
    printf '\n[ctxvm-ci] full output kept at %s\n' "$out" >&2
    exit 1
  fi
  n="$(count_of "$kind" "$out")"
  printf '%s\t%s\t%s\n' "$n" "$kind" "$name" >> "$COUNTS"
}
suite_line() { # kind -> "a + b + c"
  awk -F'\t' -v k="$1" '$2==k {printf "%s%s", sep, $1; sep=" + "}' "$COUNTS"
}

# A red gate must say WHAT failed. Steps used to send their output to /dev/null,
# so a failure produced one bare exit code and no name — that cost a full
# investigation on 2026-11-03 when the gate went red on a docs-only commit.
# run_step captures the output, prints the tail and the log path on failure, and
# stays silent on success so the log reads the same as before.
run_step() {
  local name="$1"; shift
  local out rc=0
  out="$(mktemp -t ctxvm-ci-XXXXXX)"
  # `|| rc=$?` before any `if`: bash reports 0 for an `if` whose condition failed
  # and whose then-branch never ran, so capturing the status afterwards masks the
  # failure (found by probing this helper with an exit-7 step).
  "$@" >"$out" 2>&1 || rc=$?
  if [ "$rc" -eq 0 ]; then
    rm -f "$out"
    return 0
  fi
  printf '\n[ctxvm-ci] FAILED: %s\n' "$name" >&2
  printf '[ctxvm-ci] last 40 lines of its output:\n' >&2
  tail -n 40 "$out" >&2
  printf '\n[ctxvm-ci] full output kept at %s\n' "$out" >&2
  exit "$rc"
}
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
run_step "cargo test (rust suite)" bash -c 'cd rust && { . "$HOME/.cargo/env" 2>/dev/null || true; } && cargo test' 
log "rust suite green"
run_step "cargo test -p ctxvm-tokenizer --features tiktoken" bash -c 'cd rust && { . "$HOME/.cargo/env" 2>/dev/null || true; } && cargo test -p ctxvm-tokenizer --features tiktoken' 
log "tokenizer tiktoken feature green (real BPE backends)"

# 1b) release binaries for the golden parity suites (UC2 forensics + UC1 resume:
# hermes python + opencode TS both deep-equal the shared fixtures through the
# real CLI; the UC1 resume path also shells the zstd CLI — shipped on dev+CI).
run_step "cargo build --release" bash -c 'cd rust && cargo build --release' 
log "release binaries green (UC2/UC1 golden parity)"

# 2) typescript + python
log "gate 2/4: typescript — @ctxvm/node + @ctxvm/opencode + @ctxvm/ai-sdk; python — @ctxvm/hermes + @ctxvm/py binding"
run_counted "@ctxvm/node suite" node bash -c 'cd packages/node && node --test test/' 
# W10 build: the source suite above proves the in-repo story; these two prove the
# PUBLISHABLE artifact. Mirrors ci.yml's ts job step for step.
run_step "npm ci (@ctxvm/node)" bash -c 'cd packages/node && npm ci --no-audit --no-fund' 
bash tools/check-node-build.sh
run_counted "@ctxvm/opencode suite" node bash -c 'cd packages/opencode && node --test test/' 
run_counted "@ctxvm/ai-sdk suite" node bash -c 'cd packages/ai-sdk && node --test test/' 
run_counted "@ctxvm/hermes suite" pytest bash -c 'cd packages/hermes && python -m pytest test/ -q' 
run_counted "@ctxvm/py suite" pytest bash -c 'cd packages/py && python -m pytest test/ -q' 
run_step "plugin.yaml version matches PLUGIN_VERSION" bash -c 'ver=$(sed -n "s/^version: *//p" packages/hermes/live/plugin.yaml); grep -q "PLUGIN_VERSION = \"$ver\"" packages/hermes/live/__init__.py'
# W10 node build: the package ships a copy of the root LICENSE so `npm pack` carries it.
# The copy must never drift from the single source of truth.
run_step "packages/node/LICENSE must match the root LICENSE" cmp -s LICENSE packages/node/LICENSE
# D3-c exporter promotion: the OTLP projection is a supported surface now — its
# field-set sync, golden bytes, OTLP structure and CLI determinism are the gate.
run_step "otel-export drift guard (D3-c: schema sync + goldens + OTLP structure)" node --test tools/otel-export.test.mjs
log "gate 2b: benchmarks/metrics — 07 reference suite + policy simulator"
run_counted "benchmarks/metrics suite" pytest venvs/odps/bin/python -m pytest benchmarks/metrics -q
log "ts suites green ($(suite_line node) tests); python suites green ($(suite_line pytest) tests)"

# 3) schema + corpus integrity + the T21 export round-trip
log "gate 3/4: schema validator + corpus checksums + export round-trip"
venvs/odps/bin/python spec/rfc-0/validate_schema.py "${FIXTURES[@]}"
# RFC-0.1 gate: the hand-built vector + the two EMITTER-produced committed
# artifacts (hermes live-echo fixture, ai-sdk echo-thrash trace) — proof that
# the v0.1 emission surface validates, not just the hand-built vector (RR-RFC01E1).
venvs/odps/bin/python spec/rfc-0.1/validate_schema_v0_1.py rust/crates/ctxvm-conformance/vectors/events-v0-1.jsonl packages/hermes/fixtures/hermes-live-echo-synthetic.jsonl packages/ai-sdk/fixtures/echo-thrash.trace.jsonl
for drop in m1 m2 m3 m4 m5 m6 m7 m8; do
  run_step "corpus/$drop checksums" bash -c "cd corpus/$drop && sha256sum -c checksums.sha256"
done
bash tools/export-roundtrip.sh
log "schema + export round-trip gate green"

# 4) hub parity
log "gate 4/4: hub — ODPS validate + regen byte-identity"
run_step "ODPS validate (root manifest)" venvs/odps/bin/open-data-products validate 04-odps-dataproduct-corpus.yaml
run_step "hub regen (build-hub.sh)" tools/build-hub.sh
log "hub byte-identity green"

log "ALL GATES GREEN"
