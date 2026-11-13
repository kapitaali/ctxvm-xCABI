#!/usr/bin/env bash
# sync-plugin.sh — copy the hermes plugin into the installed location and prove the copy by hash.
#
# The failure this exists for: a running gateway keeps the module it imported at startup, and the
# installed directory is what it imports. Three separate wrong conclusions in this lane came from a
# copy that was one build behind (0.10.4/0.10.5), a partially synced directory (a sibling module
# missing, so the plugin dies at import at the next gateway start), or a version string on disk that
# disagreed with what was loaded. All three are silent; this script makes them loud.
#
# What "the module set" means, and why it is derived rather than listed: `__init__.py` imports its
# siblings by bare name (`from plugin import …`, `from uc_registry import …`), which resolves through
# `sys.modules` from the PLUGIN ROOT. A sibling that lives only under `src/` or is forgotten in the
# list therefore breaks the next import with a stack trace that reads like a policy defect. The set is
# derived from the imports in `live/__init__.py` and resolved against `live/` or `src/`, so adding a
# module cannot leave the installed copy behind.
#
# Usage:
#   bash tools/sync-plugin.sh            # copy + verify + report
#   bash tools/sync-plugin.sh --check    # verify only, write nothing; exit 1 on any drift
#   bash tools/sync-plugin.sh --help
#
# Exit 0 clean, 1 drift (--check) or a hash/version mismatch, 2 cannot proceed.
# A running gateway older than the installed files is reported, not failed: the fix is a restart from
# a shell OUTSIDE the gateway's process tree (the gateway refuses to restart itself).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="sync"
case "${1:-}" in
  --check) MODE="check" ;;
  "" ) : ;;
  --help|-h) sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "usage: bash tools/sync-plugin.sh [--check]" >&2; exit 2 ;;
esac

HERMES_HOME_DIR="${HERMES_HOME:-$HOME/.hermes}"
DEST="$HERMES_HOME_DIR/plugins/ctxvm-tracer"
LIVE="$ROOT/packages/hermes/live"

[ -f "$LIVE/__init__.py" ] || { echo "sync-plugin: no $LIVE/__init__.py — wrong repo root?" >&2; exit 2; }
[ -d "$DEST" ] || { echo "sync-plugin: installed plugin not found at $DEST (is the plugin installed?)" >&2; exit 2; }

echo "repo root : $ROOT"
echo "installed : $DEST"
echo "mode      : $MODE"
echo

# --- the module set, derived from the code ------------------------------------------------------
SET="$(cd "$ROOT" && python3 - <<'PY'
import ast, pathlib
live = pathlib.Path("packages/hermes/live")
src = pathlib.Path("packages/hermes/src")
tree = ast.parse((live / "__init__.py").read_text(encoding="utf-8"))
names = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        names.add(node.module.split(".")[0])
    elif isinstance(node, ast.Import):
        for alias in node.names:
            names.add(alias.name.split(".")[0])
pairs = {}
for name in sorted(names):
    if (live / f"{name}.py").exists():
        pairs[f"live/{name}.py"] = f"{name}.py"
    elif (src / f"{name}.py").exists():
        pairs[f"src/{name}.py"] = f"{name}.py"
pairs["live/__init__.py"] = "__init__.py"
pairs["live/plugin.yaml"] = "plugin.yaml"
for a, b in pairs.items():
    print(a, b, sep="\t")
# sibling sources that exist but are NOT imported by the entry point: named, never silently dropped
dest_names = set(pairs.values())
for path in sorted(live.glob("*.py")) + sorted(src.glob("*.py")):
    if path.name not in dest_names and path.name != "__init__.py":
        print(path.as_posix(), "-", sep="\t")
PY
)" || { echo "sync-plugin: could not derive the module set" >&2; exit 2; }

# --- copy and verify ----------------------------------------------------------------------------
drift=0
copied=0
while IFS=$'\t' read -r src_rel dest_rel; do
  [ -n "$src_rel" ] || continue
  if [ "$dest_rel" = "-" ]; then
    echo "  not synced  $src_rel (not imported by __init__.py)"
    continue
  fi
  src="$ROOT/packages/hermes/$src_rel"
  dst="$DEST/$dest_rel"
  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
    printf '  same        %-22s %s\n' "$dest_rel" "$(sha256sum "$src" | cut -c1-16)"
    continue
  fi
  if [ "$MODE" = "check" ]; then
    printf '  DRIFT       %-22s repo %s installed %s\n' "$dest_rel" \
      "$(sha256sum "$src" | cut -c1-16)" "$([ -f "$dst" ] && sha256sum "$dst" | cut -c1-16 || echo missing)"
    drift=$((drift+1))
    continue
  fi
  cp -p "$src" "$dst" || { echo "sync-plugin: copy failed for $dest_rel" >&2; exit 2; }
  if [ "$(sha256sum "$src" | cut -d' ' -f1)" != "$(sha256sum "$dst" | cut -d' ' -f1)" ]; then
    echo "sync-plugin: HASH MISMATCH after copy: $dest_rel" >&2
    exit 1
  fi
  printf '  copied      %-22s %s\n' "$dest_rel" "$(sha256sum "$dst" | cut -c1-16)"
  copied=$((copied+1))
done <<< "$SET"

# --- bytecode: a stale .pyc survives a file copy -------------------------------------------------
if [ "$MODE" = "sync" ] && [ -d "$DEST/__pycache__" ]; then
  rm -rf "$DEST/__pycache__"
  echo "  cleared     __pycache__ (stale bytecode outlives the copy)"
fi

# --- versions: the repo constant, the installed constant, the manifest the host displays ----------
repo_ver="$(sed -n 's/^PLUGIN_VERSION = "\(.*\)"/\1/p' "$LIVE/__init__.py" | head -1)"
inst_ver="$(sed -n 's/^PLUGIN_VERSION = "\(.*\)"/\1/p' "$DEST/__init__.py" | head -1)"
manifest="$(sed -n 's/^version: *//p' "$DEST/plugin.yaml" | head -1)"
printf '\nPLUGIN_VERSION: repo %s | installed %s | manifest %s\n' "${repo_ver:-?}" "${inst_ver:-?}" "${manifest:-?}"
if [ -z "$repo_ver" ] || [ "$repo_ver" != "$inst_ver" ] || [ "$repo_ver" != "$manifest" ]; then
  echo "sync-plugin: VERSION DISAGREEMENT — the gate asserts repo==manifest, so one of them is wrong" >&2
  exit 1
fi

# --- load check: the only proof the installed set can actually import ----------------------------
loaded="$(cd "$DEST" && python3 -c '
import importlib.util as u
spec = u.spec_from_file_location("ctxvm_installed", "__init__.py")
mod = u.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.PLUGIN_VERSION)
' 2>&1 | tail -1)"
if [ "$loaded" != "$repo_ver" ]; then
  echo "load check: FAILED — installed copy does not import cleanly (or reports a different version):" >&2
  echo "  $loaded" >&2
  exit 1
fi
echo "load check: $loaded (imported from the installed copy with only it on sys.path)"

# --- is the running gateway older than these files? ----------------------------------------------
# The pid comes from the lock file, not from a pattern match on process command lines: a `-f` pattern
# naming the gateway is refused by the host's lifecycle guard, and the lock already carries the pid.
gw_pid=""
lock="$HERMES_HOME_DIR/gateway.lock"
if [ -f "$lock" ]; then
  gw_pid="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("pid",""))' "$lock" 2>/dev/null)"
  [ -n "$gw_pid" ] && ! ps -p "$gw_pid" >/dev/null 2>&1 && gw_pid=""
fi
if [ -n "$gw_pid" ]; then
  gw_start="$(date -d "$(ps -o lstart= -p "$gw_pid")" +%s 2>/dev/null)"
  file_mtime="$(stat -c %Y "$DEST/__init__.py")"
  if [ -n "$gw_start" ] && [ "$gw_start" -lt "$file_mtime" ]; then
    printf '\nGATEWAY STALE: pid %s started %s, before these files were written (%s).\n' \
      "$gw_pid" "$(ps -o lstart= -p "$gw_pid")" "$(stat -c %y "$DEST/__init__.py" | cut -c1-19)"
    echo "  The process holds the module it imported at startup. Restart it from a shell OUTSIDE the"
    echo "  gateway's process tree; the operator command is in handoff/LANES.md §'The gateway'."
    echo "  (The literal command is deliberately not embedded in this script: the host's lifecycle guard"
    echo "  refuses to run any script that contains it, which would make this tool unusable here.)"
  else
    printf '\ngateway: pid %s started after these files were written; it holds this build.\n' "$gw_pid"
  fi
else
  echo
  echo "gateway: no running process found (nothing to compare)"
fi

if [ "$MODE" = "check" ] && [ "$drift" -gt 0 ]; then
  echo
  echo "sync-plugin: $drift file(s) drifted — run bash tools/sync-plugin.sh" >&2
  exit 1
fi
echo
echo "sync-plugin: OK — $copied copied, the installed set imports, and the versions agree"
