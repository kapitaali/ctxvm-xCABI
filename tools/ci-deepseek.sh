#!/usr/bin/env bash
# ci-deepseek.sh — whole @ctxvm/dsh suite plus adapter-aware checker tests.
#
# The adapter consumes @ctxvm/node as an exact external package. This gate builds
# and packs the node tracer, then installs the tarball into the adapter package;
# it never creates a repository-relative workspace symlink.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

PKG="packages/deepseek"
NODE_PKG="packages/node"
SUITE="$PKG/test/"
MIN_TESTS=22
ALLOWED_SKIP="captured trace validates and replays without divergence"

[ -d "$SUITE" ] || { echo "ci-deepseek: $SUITE is missing — the package moved?" >&2; exit 2; }
[ -d "$NODE_PKG/node_modules" ] || {
  echo "ci-deepseek: run npm i in $NODE_PKG first" >&2; exit 2;
}

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tools/test_coverage_check.py || exit 1

TMPDIR_PACK="$(mktemp -d)"
export npm_config_cache="$TMPDIR_PACK/npm-cache"
mkdir -p "$npm_config_cache"
trap 'rm -f "$TMPDIR_PACK"/*.tgz' EXIT
(
  cd "$NODE_PKG" || exit 2
  npm run build --silent || exit 2
  npm pack --silent --pack-destination "$TMPDIR_PACK" >"$TMPDIR_PACK/name.txt" || exit 2
)
TARBALL="$TMPDIR_PACK/$(cat "$TMPDIR_PACK/name.txt")"
[ -f "$TARBALL" ] || { echo "ci-deepseek: npm pack produced no tarball" >&2; exit 2; }

# --legacy-peer-deps avoids installing DSH's private peer packages in this bare
# ctxvm checkout; the adapter's runtime tests import those peers only as types.
npm install --prefix "$PKG" --no-save --ignore-scripts --legacy-peer-deps "$TARBALL" || exit 2
[ -f "$PKG/node_modules/@ctxvm/node/dist/index.js" ] || {
  echo "ci-deepseek: external @ctxvm/node tarball did not install dist/index.js" >&2; exit 2;
}

echo "ci-deepseek: suite: $SUITE (external @ctxvm/node tarball)"
echo "ci-deepseek: one skip is declared, by name: $ALLOWED_SKIP"

OUT="$(mktemp)"
trap 'rm -f "$OUT" "$TMPDIR_PACK"/*.tgz' EXIT
env -u CTXVM_TRACE_TS node --test "$SUITE" >"$OUT" 2>&1
rc=$?
cat "$OUT"

pass="$(sed -n 's/^ℹ pass \([0-9][0-9]*\)$/\1/p' "$OUT" | tail -1)"
fail="$(sed -n 's/^ℹ fail \([0-9][0-9]*\)$/\1/p' "$OUT" | tail -1)"
skip="$(sed -n 's/^ℹ skipped \([0-9][0-9]*\)$/\1/p' "$OUT" | tail -1)"
echo "ci-deepseek: run — pass=${pass:-?} fail=${fail:-?} skipped=${skip:-?} (minimum ${MIN_TESTS} passing)"

while IFS= read -r name; do
  [ -n "$name" ] || continue
  if [ "$name" = "$ALLOWED_SKIP" ]; then
    echo "ci-deepseek: skipped (declared, named): $name"
  else
    echo "ci-deepseek: FAILED — unexpected SKIP: $name (a skip is not a pass)" >&2
    exit 1
  fi
done < <(grep -oE '^﹣ .* # SKIP' "$OUT" | sed -e 's/^﹣ //' -e 's/ # SKIP$//' -e 's/ ([0-9.]*ms)$//')

[ "$rc" -eq 0 ] || { echo "ci-deepseek: FAILED — node --test exited $rc" >&2; exit 1; }
[ "${fail:-1}" -eq 0 ] || { echo "ci-deepseek: FAILED — ${fail} test(s) failed" >&2; exit 1; }
[ "${pass:-0}" -ge "$MIN_TESTS" ] || {
  echo "ci-deepseek: FAILED — only ${pass:-0} passing test(s), expected at least ${MIN_TESTS}" >&2
  exit 1
}
[ "${skip:-99}" -le 1 ] || {
  echo "ci-deepseek: FAILED — ${skip} skips; only one is declared (${ALLOWED_SKIP})" >&2
  exit 1
}
echo "ci-deepseek: OK — ${pass} passing, 0 failed, ${skip} declared skip, whole test directory"
