#!/usr/bin/env bash
# ci-deepseek.sh — the gate's coverage of @ctxvm/dsh (`packages/deepseek`). Whole test directory.
#
# History, because the scope changed and why matters:
#   2026-11-16 (interim): the adapter landed (9a87ba2) and the gate ran nothing in it — `grep deepseek
#     tools/run-ci.sh` returned 0 while every run printed ALL GATES GREEN. `page-table.test.ts` could not
#     even import `@deepseek-ai/schemastery` (private registry, npm install E404) and `replay.test.ts`
#     skips without `CTXVM_TEST_TRACE`, so the step ran one file and printed the other two as NOT GATED.
#   2026-11-16 (now): option (ii) landed — `a57592b` made the schemastery import lazy and injectable
#     (`src/page-table.ts`, `makePageTableStateSchema`), so page-table runs in a bare checkout and the
#     step covers the whole directory.
#
# Two rules survive the widening, because they are what makes the step evidence rather than decoration:
#   1. The workspace link is created HERE, `ln -sfn ../../../node`, relative and repo-computed. The tree
#      once carried a hand-made ABSOLUTE link; no clone has one, and every test fails with
#      ERR_MODULE_NOT_FOUND from src/tracer.ts without it.
#   2. A skip is not a pass. Exactly one skip is expected and is named on every run — the replay
#      integration test, which needs a captured trace nobody has committed. Any OTHER skip fails, and so
#      does a short count. When a tracked fixture lands, delete ALLOWED_SKIP and the per-name check.
#
# Exit 0 clean, 1 a failing test, an unexpected skip, or a short count, 2 a missing prerequisite.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

PKG="packages/deepseek"
LINK="$PKG/node_modules/@ctxvm/node"
SUITE="$PKG/test/"
MIN_TESTS=7                                                                # event-map 5 + page-table 2
ALLOWED_SKIP="captured trace validates and replays without divergence"     # replay.test.ts, no fixture

[ -d "$SUITE" ] || { echo "ci-deepseek: $SUITE is missing — the package moved?" >&2; exit 2; }

# 1. the link, created here every run, with a target that holds in any checkout
mkdir -p "$(dirname "$LINK")"
ln -sfn ../../../node "$LINK"
if [ ! -f "$LINK/dist/index.js" ]; then
  echo "ci-deepseek: $LINK/dist/index.js is missing — the gate must build @ctxvm/node first" >&2
  exit 2
fi

echo "ci-deepseek: suite: $SUITE (link $LINK -> ../../../node)"
echo "ci-deepseek: one skip is declared, by name: $ALLOWED_SKIP (needs CTXVM_TEST_TRACE)"

out="$(mktemp)"
trap 'rm -f "$out"' EXIT
node --test "$SUITE" >"$out" 2>&1
rc=$?
cat "$out"

pass="$(sed -n 's/^ℹ pass \([0-9][0-9]*\)$/\1/p' "$out" | tail -1)"
fail="$(sed -n 's/^ℹ fail \([0-9][0-9]*\)$/\1/p' "$out" | tail -1)"
skip="$(sed -n 's/^ℹ skipped \([0-9][0-9]*\)$/\1/p' "$out" | tail -1)"
echo "ci-deepseek: run — pass=${pass:-?} fail=${fail:-?} skipped=${skip:-?} (minimum ${MIN_TESTS} passing)"

# every skip by name: the declared one is reported, anything else is a failure
while IFS= read -r name; do
  [ -n "$name" ] || continue
  if [ "$name" = "$ALLOWED_SKIP" ]; then
    echo "ci-deepseek: skipped (declared, named): $name"
  else
    echo "ci-deepseek: FAILED — unexpected SKIP: $name (a skip is not a pass)" >&2
    exit 1
  fi
done < <(grep -oE '^﹣ .* # SKIP' "$out" | sed -e 's/^﹣ //' -e 's/ # SKIP$//' -e 's/ ([0-9.]*ms)$//')

[ "$rc" -eq 0 ] || { echo "ci-deepseek: FAILED — node --test exited $rc" >&2; exit 1; }
[ "${fail:-1}" -eq 0 ] || { echo "ci-deepseek: FAILED — ${fail} test(s) failed" >&2; exit 1; }
[ "${pass:-0}" -ge "$MIN_TESTS" ] || {
  echo "ci-deepseek: FAILED — only ${pass:-0} passing test(s), expected at least ${MIN_TESTS}; a suite that runs fewer is a coverage regression" >&2
  exit 1
}
[ "${skip:-99}" -le 1 ] || {
  echo "ci-deepseek: FAILED — ${skip} skips; only one is declared (${ALLOWED_SKIP})" >&2
  exit 1
}
echo "ci-deepseek: OK — ${pass} passing, 0 failed, ${skip} declared skip, whole test directory"
