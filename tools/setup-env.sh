#!/usr/bin/env bash
# CtxVM environment setup — idempotent. Task T0 (08-HANDOFF.md).
# Creates two local venvs under venvs/:
#   venvs/odps/  — open-data-products (ODPS manifest validation; any modern python)
#   venvs/odcs/  — open-data-products[contracts] + datacontract-cli (ODCS lint + audit)
#                  MUST be built on python <= 3.12: datacontract-cli is gated
#                  python_version < "3.13" and pip SILENTLY SKIPS it on >= 3.13.
# Safe to re-run: existing, working venvs are skipped.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/venvs"
log() { printf '[ctxvm-setup] %s\n' "$*"; }

# ───────────────────────── venv A: ODPS validation ─────────────────────────
if [[ -x "$ROOT/venvs/odps/bin/open-data-products" ]]; then
  log "venvs/odps already OK (skipped)"
else
  PYA="$(command -v python3 || command -v python)"
  "$PYA" -m venv "$ROOT/venvs/odps"
  "$ROOT/venvs/odps/bin/python" -m pip install --quiet --disable-pip-version-check open-data-products
  log "venvs/odps built with $("$PYA" --version 2>&1)"
fi
PYA_MAJOR="$("$ROOT/venvs/odps/bin/python" -c 'import platform; print(platform.python_version())')"
case "$PYA_MAJOR" in
  3.14|3.13) log "NOTE: venvs/odps is python $PYA_MAJOR — contracts extra is skipped by pip there. Use venvs/odcs for contracts." ;;
esac

# ───────────────────── venv B: contracts (python <= 3.12) ─────────────────────
find_py_le_312() {
  # Prefer an existing interpreter; else an existing conda env; else create "ctxvm-odcs" via conda.
  for c in python3.12 python3.11 python3.10; do
    if command -v "$c" >/dev/null 2>&1; then printf '%s' "$c"; return 0; fi
  done
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3"; do
    if [[ -x "$base/envs/ctxvm-odcs/bin/python" ]]; then printf '%s' "$base/envs/ctxvm-odcs/bin/python"; return 0; fi
  done
  if command -v conda >/dev/null 2>&1; then
    log "creating conda env 'ctxvm-odcs' (python=3.12)…"
    conda create -y -q -n ctxvm-odcs python=3.12 >/dev/null 2>&1
    for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3"; do
      if [[ -x "$base/envs/ctxvm-odcs/bin/python" ]]; then printf '%s' "$base/envs/ctxvm-odcs/bin/python"; return 0; fi
    done
  fi
  return 1
}

if [[ -x "$ROOT/venvs/odcs/bin/datacontract" ]]; then
  log "venvs/odcs already OK (skipped)"
else
  if PYB="$(find_py_le_312)"; then
    "$PYB" -m venv "$ROOT/venvs/odcs"
    "$ROOT/venvs/odcs/bin/python" -m pip install --quiet --disable-pip-version-check "open-data-products[contracts]"
    log "venvs/odcs built with $("$PYB" --version 2>&1)"
  else
    log "ERROR: no python <= 3.12 and no conda available."
    cat <<'HUMAN'
ACTION REQUIRED (5 lines):
  1. Install conda or a python 3.12 binary (e.g. miniforge: https://github.com/conda-forge/miniforge).
  2. Run: conda create -y -n ctxvm-odcs python=3.12
  3. Re-run this setup script.
  4. Contract validation (odps docs: ODCS 2.2.2-era era expired) NEEDS this env.
  5. Everything else (manifest validation) keeps working via venvs/odps.
HUMAN
    exit 0
  fi
fi

# ─────────────────────── verification (fast, fail-loud) ───────────────────────
PROD="$ROOT/04-odps-dataproduct-corpus.yaml"
CONTRACT="$ROOT/contracts/corpus-0.1.odcs.yaml"

"$ROOT/venvs/odps/bin/open-data-products" validate "$PROD" --json >/dev/null \
  && log "verify: ODPS manifest valid ✓"

if "$ROOT/venvs/odcs/bin/datacontract" lint "$CONTRACT" >/dev/null 2>&1; then
  log "verify: ODCS contract lint ✓"
else
  log "ERROR: contract lint failed under venvs/odcs — see: venvs/odcs/bin/datacontract lint $CONTRACT"
  exit 1
fi

log "setup complete:"
log "  ODPS validation : $ROOT/venvs/odps/bin/open-data-products"
log "  Contracts tool  : $ROOT/venvs/odcs/bin/datacontract"
