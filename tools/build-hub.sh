#!/usr/bin/env bash
# tools/build-hub.sh — hub.ctxvm.dev as an ODPC repo: regenerate hub/ from the root
# ODPS manifest using the open-data-products SDK itself (task T5, 08-HANDOFF.md).
#
# Proof chain (their SDK end to end, no bespoke tooling):
#   1. root manifest re-validated by their SDK (source gate)
#   2. `odpc-build` on a staged copy → hub/catalog.yaml + hub/index.html
#   3. $ref rewritten hub-relative (../04-…) so hub/ can live beside the root
#      manifest WITHOUT duplicating it — root manifest stays the single source
#   4. committed catalog re-validated (`validate` → valid:true) + odpc-summary
# Idempotent: the SDK emits no timestamps; two runs are byte-identical.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="04-odps-dataproduct-corpus.yaml"
SDK="$ROOT/venvs/odps/bin/open-data-products"
PY="$ROOT/venvs/odps/bin/python"
log() { printf '[ctxvm-hub] %s\n' "$*"; }

# 1) source gate — the manifest must still validate against the ODPS schema
"$SDK" validate "$ROOT/$MANIFEST" >/dev/null
log "source manifest validates: $MANIFEST"

# 2) stage + build (staged basename = root basename keeps the emitted $ref meaningful)
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp "$ROOT/$MANIFEST" "$STAGE/$MANIFEST"
mkdir -p "$ROOT/hub"
"$SDK" odpc-build "$STAGE" \
  --output "$ROOT/hub/catalog.yaml" \
  --html "$ROOT/hub/index.html" \
  --id hub.ctxvm.dev \
  --name "ctxvm hub" \
  --description "Open hub catalog for the ctxvm project: xCABI trace corpus, conformance vectors, benchmarks."
log "odpc-build done (productReferences=1)"

# 3) make the product reference hub-relative
"$PY" - "$ROOT/hub/catalog.yaml" <<'PYEOF'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
t = p.read_text()
old = "$ref: 04-odps-dataproduct-corpus.yaml"
new = "$ref: ../04-odps-dataproduct-corpus.yaml"
n = t.count(old)
assert n == 1, f"expected exactly 1 productModel $ref, found {n}"
p.write_text(t.replace(old, new))
PYEOF
log "hub-relative ref: ../$MANIFEST"

# 4) committed artifacts self-check ("their SDK validates what we ship")
"$SDK" validate "$ROOT/hub/catalog.yaml" --json > "$STAGE/cat-validate.json"
"$PY" - "$STAGE/cat-validate.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["valid"] is True and d["errors"] == [], d
print("catalog validates: spec %s kind %s v%s" % (d["spec"], d["kind"], d["version"]))
PYEOF
"$SDK" odpc-summary "$ROOT/hub/catalog.yaml" | head -4
log "OK: hub/catalog.yaml + hub/index.html regenerated from $MANIFEST"
