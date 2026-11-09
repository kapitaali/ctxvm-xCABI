#!/usr/bin/env bash
# W8 run environment contract — the ONLY place a run's settings are defined.
#
#   source tools/w8-run-env.sh <arm> <trace-dir> <trace-name>
#
# <arm> is `naive` or `paged`. The arm selects the HERMES_HOME profile, and those two
# profiles differ in exactly one key (`context.engine`), which is the experiment's
# one-factor property. Everything else here is shared by both arms.
#
# WHERE THESE VALUES MUST LAND (measured 2026-11-07, RR-PROVIDER-20261107):
# `hermes -z` does NOT run the turn in the client process. hermes_cli/main.py:2844 —
# "Every `hermes` / `hermes chat` turn (classic view, -q, -z, TUI) executes in the
# gateway". The client is a transport; the executing process is the GATEWAY for that
# profile. A probe that exported CTXVM_TRACE_DIR=/tmp/w8/probe wrote nothing there and
# landed in the gateway's own dir instead.
#
# So these variables must be in the environment of the gateway that will run the turn:
# source this script, then start/restart that profile's gateway under it, then send
# prompts. Exporting them in a client shell alone changes nothing about capture.
#
# Model: W8_MODEL defaults to the catalogue row "OpenAI: GPT-6 Luna". CONFIRM the
# provider's exact id at P0 and record the string actually used — a display name and a
# provider id are not guaranteed to match.
#
# vBudget: 24,000 for the paged arm only (preregistered; the T0 lock may confirm or RAISE
# it, never lower it). The naive arm must NOT set it: that variable is a paged-arm concept
# and exporting it for both arms would blur the factor.

set -euo pipefail

ARM="${1:?usage: source tools/w8-run-env.sh <naive|paged> <trace-dir> <trace-name>}"
TRACE_DIR="${2:?trace dir required}"
TRACE_NAME="${3:?trace name required}"

case "$ARM" in
  naive|paged) ;;
  *) echo "w8-run-env: arm must be 'naive' or 'paged', got '$ARM'" >&2; return 2 2>/dev/null || exit 2 ;;
esac

export HERMES_HOME="$HOME/.hermes/profiles/w8-$ARM"

# --- the trace --------------------------------------------------------------
export CTXVM_FEATURES=trace
export CTXVM_TRACE_DIR="$TRACE_DIR"
export CTXVM_TRACE_NAME="$TRACE_NAME"
export CTXVM_TRACE_WRITETHROUGH=1        # partial snapshots every N events
export CTXVM_TRACE_WRITETHROUGH_EVERY=10
# ts stays default-ON: a W8 capture is a fresh capture, never a byte-stability fixture.

# --- identity and budget ----------------------------------------------------
# The provider is NOT a trace stamp only: it decides which endpoint serves the model.
# On 2026-11-07 the profiles carried provider "nvidia" with an nvidia default model, so
# `openai/gpt-6-luna` fell through to another vendor's free tier and the run died on
# 429 org_token_rate_limit_day. Both profiles now say provider "nous".
export W8_PROVIDER="${W8_PROVIDER:-nous}"
export W8_MODEL="${W8_MODEL:-openai/gpt-6-luna}"
export CTXVM_MODEL="$W8_MODEL"
export CTXVM_PROVIDER="$W8_PROVIDER"
export CTXVM_BUDGET_TOKENS="${W8_BUDGET_TOKENS:-200000}"
# CTXVM_PROVIDER: set from W8_PROVIDER (owner-attested, not guessed). The plugin
# records "unknown" only when this is unset; the provider's own payload still wins
# when it carries one (precedence: payload > settings > env > "unknown").

# --- the factor -------------------------------------------------------------
if [ "$ARM" = "paged" ]; then
  export CTXVM_VBUDGET="${W8_VBUDGET:-24000}"
else
  unset CTXVM_VBUDGET || true
fi

# A stale environment id would be carried into session.open; let the plugin derive it.
unset CTXVM_ENVIRONMENT_ID 2>/dev/null || true
