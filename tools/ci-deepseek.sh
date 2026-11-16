#!/usr/bin/env bash
# ci-deepseek.sh — the gate's coverage of @ctxvm/dsh (`packages/deepseek`), INTERIM scope.
#
# The false green this exists for: `packages/deepseek` landed (9a87ba2) and the gate ran nothing in it.
# `grep deepseek tools/run-ci.sh` returned 0 while every run printed ALL GATES GREEN, so an adapter
# with a failing page-table and an unrun integration test looked covered. This step is the minimum that
# ends that, and it names exactly what it does NOT cover.
#
# Three things it does that a naive step would not:
#   1. Creates the workspace link ITSELF, relative and repo-computed. The tree carries a hand-made
#      ABSOLUTE link (/home/<user>/…/packages/node); a fresh clone has no link at all and every test
#      fails with ERR_MODULE_NOT_FOUND from src/tracer.ts. A gate must not depend on either.
#   2. Runs ONE FILE explicitly, because the directory run cannot pass yet: page-table.test.ts needs
#      `@deepseek-ai/schemastery` (a private registry package — `npm install` gets E404), and
#      replay.test.ts skips unless CTXVM_TEST_TRACE points at a captured trace.
#   3. Fails on a skip and on a zero count. "rc=0 with the step" is worthless if the tests never ran —
#      a skip must not read as a pass.
#
# Interim until the dsh lane makes the schemastery import injectable (reviewer option ii); then switch
# GATED to the whole directory and delete the NOT-GATED line.
#
# Exit 0 clean, 1 a failing or skipped or absent test, 2 the prerequisite is missing.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

PKG="packages/deepseek"
LINK="$PKG/node_modules/@ctxvm/node"
GATED="$PKG/test/event-map.test.ts"
MIN_TESTS=5

[ -f "$GATED" ] || { echo "ci-deepseek: $GATED is missing — the package moved?" >&2; exit 2; }

# 1. the link, created here every run, with a target that holds in any checkout
mkdir -p "$(dirname "$LINK")"
ln -sfn ../../../node "$LINK"
if [ ! -f "$LINK/dist/index.js" ]; then
  echo "ci-deepseek: $LINK/dist/index.js is missing — the gate must build @ctxvm/node first" >&2
  exit 2
fi

echo "ci-deepseek: gated file: $GATED (link $LINK -> ../../../node)"
echo "ci-deepseek: NOT GATED: $PKG/test/page-table.test.ts (needs @deepseek-ai/schemastery, private registry)"
echo "ci-deepseek: NOT GATED: $PKG/test/replay.test.ts (skips without CTXVM_TEST_TRACE; no tracked fixture)"

out="$(mktemp)"
trap 'rm -f "$out"' EXIT
node --test "$GATED" >"$out" 2>&1
rc=$?
cat "$out"

pass="$(sed -n 's/^ℹ pass \([0-9][0-9]*\)$/\1/p' "$out" | tail -1)"
fail="$(sed -n 's/^ℹ fail \([0-9][0-9]*\)$/\1/p' "$out" | tail -1)"
skip="$(sed -n 's/^ℹ skipped \([0-9][0-9]*\)$/\1/p' "$out" | tail -1)"
echo "ci-deepseek: gated run — pass=${pass:-?} fail=${fail:-?} skipped=${skip:-?} (minimum ${MIN_TESTS} passing)"

[ "$rc" -eq 0 ] || { echo "ci-deepseek: FAILED — node --test exited $rc" >&2; exit 1; }
[ "${fail:-1}" -eq 0 ] || { echo "ci-deepseek: FAILED — ${fail} test(s) failed" >&2; exit 1; }
[ "${pass:-0}" -ge "$MIN_TESTS" ] || {
  echo "ci-deepseek: FAILED — only ${pass:-0} passing test(s), expected at least ${MIN_TESTS}; a gated file that runs fewer is a coverage regression" >&2
  exit 1
}
[ "${skip:-1}" -eq 0 ] || {
  echo "ci-deepseek: FAILED — ${skip} gated test(s) SKIPPED; a skip is not a pass" >&2
  exit 1
}
echo "ci-deepseek: OK — ${pass} passing, 0 failed, 0 skipped in the gated file"
