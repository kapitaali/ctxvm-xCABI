#!/usr/bin/env sh
# W5 OpenCode capture — one-shot. Run from the repo root after a release build.
# Requires: opencode on PATH, the ctxvm plugin shim installed
# (README quickstart / packages/opencode/live/README.md).
# Capture lands at $CTXVM_TRACE_DIR/$CTXVM_TRACE_NAME.jsonl (+ .meta.json sidecar).
set -eu
: "${CTXVM_RUST_BIN_DIR:=./rust/target/release}"
export CTXVM_TRACE_DIR="${CTXVM_TRACE_DIR:-/tmp/ctxvm-w5}"
export CTXVM_TRACE_NAME="${CTXVM_TRACE_NAME:-w5-opencode}"
export CTXVM_MODEL="${CTXVM_MODEL:-opencode/glm-5.3-flash-free}"
export CTXVM_PROVIDER="${CTXVM_PROVIDER:-opencode}"
export CTXVM_AGENT_ID="${CTXVM_AGENT_ID:-ctxvm-w5}"
export CTXVM_BUDGET_TOKENS="${CTXVM_BUDGET_TOKENS:-200000}"
export CTXVM_OPENCODE_VERSION="$(opencode --version | awk '{print $2}')"
export CTXVM_HANDOFF_STOP=1          # no mid-session pause — W5 wants a plain full trace
mkdir -p "$CTXVM_TRACE_DIR"
opencode run --standalone --auto -m "$CTXVM_MODEL" "$(cat "$(dirname "$0")/task.md")"
