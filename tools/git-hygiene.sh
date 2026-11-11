#!/usr/bin/env bash
# git-hygiene.sh — catch a STALE SHARED INDEX before it reaches a commit.
#
# The failure this exists for (2026-11-11): a commit made through a private index
# (GIT_INDEX_FILE=…) leaves the shared .git/index pointing at an older tree. Later commits move
# HEAD, and `git status` then shows the newly added files as STAGED DELETIONS with untracked twins
# beside them — the normal shape of a delete-then-rewrite, which is why it can pass review.
# A commit of that shared index would drop those files from history without a diff that looks wrong.
#
# Rule: a commit through a private index is followed by `git read-tree HEAD` on the shared one.
# This check is what proves it happened.
#
# Exit 0 clean, 1 stale index (with the offending paths named).
set -uo pipefail

if ! command -v git >/dev/null 2>&1; then
  echo "SKIP: git not available"
  exit 0
fi

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "SKIP: not a git tree"; exit 0; }

unset GIT_INDEX_FILE

stale=0

# 1. Staged deletions of paths that exist in HEAD.
while read -r path; do
  [ -z "$path" ] && continue
  if git cat-file -e "HEAD:$path" 2>/dev/null; then
    echo "STALE: index stages a DELETION of '$path', which exists in HEAD"
    stale=1
  fi
done < <(git diff --cached --name-only --diff-filter=D)

# 2. Staged modifications whose working-tree bytes already equal HEAD — the same staleness,
#    seen from the other side: the index has an older blob than both HEAD and the tree.
while read -r path; do
  [ -z "$path" ] && continue
  wt=$(git hash-object "$path" 2>/dev/null || true)
  hd=$(git rev-parse "HEAD:$path" 2>/dev/null || true)
  if [ -n "$wt" ] && [ "$wt" = "$hd" ]; then
    echo "STALE: index stages a CHANGE to '$path' whose working tree already matches HEAD"
    stale=1
  fi
done < <(git diff --cached --name-only --diff-filter=M)

if [ "$stale" -ne 0 ]; then
  echo
  echo "Fix: git read-tree HEAD    (resets the index only; the working tree is untouched)"
  exit 1
fi

echo "OK: the shared index agrees with HEAD"
