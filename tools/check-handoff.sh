#!/bin/sh
# check-handoff.sh - verifies the continuity kit: files exist, byte limits hold, required
# headings are present, and no secret-shaped content slipped in. Never prints matched bytes
# (DQ law) — only counts and pattern-class names. POSIX sh, coreutils only.

set -u

here=$(dirname "$0")
cd "$here/.." || exit 1
fail=0

limit_of() {
  case "$1" in
    handoff/PROJECT-STATE.md) echo 6144 ;;
    handoff/CONTEXT-PACK.md)  echo 8192 ;;
    handoff/WORKFLOW.md)      echo 4096 ;;
    handoff/QUESTIONS.md)     echo 3072 ;;
    handoff/packets/*)        echo 3072 ;;
    *)                        echo 0 ;;
  esac
}

for f in handoff/PROJECT-STATE.md handoff/CONTEXT-PACK.md handoff/WORKFLOW.md handoff/QUESTIONS.md handoff/packets/*.md; do
  if [ ! -e "$f" ]; then
    echo "MISSING $f"
    fail=1
    continue
  fi
  lim=$(limit_of "$f")
  if [ "$lim" -eq 0 ]; then
    echo "NOLIMIT $f"
    fail=1
    continue
  fi
  size=$(wc -c < "$f")
  if [ "$size" -gt "$lim" ]; then
    echo "OVERSIZE $f: $size > $lim"
    fail=1
  else
    echo "OK $f: $size/$lim"
  fi
done

need_heading() {
  f=$1
  shift
  for h in "$@"; do
    grep -Fq -- "$h" "$f" || { echo "MISSINGHEADING $f: $h"; fail=1; }
  done
}

need_heading handoff/PROJECT-STATE.md \
  '## Goal' \
  '## Artifacts and versions' \
  '## Done (last 7 items: one line each, with report path)' \
  '## In progress (one item: what, blocker, next command)' \
  '## Next three (ordered, one line each)' \
  '## Decisions made (date, decision, reason)' \
  '## Open decisions for the owner (D-numbered, options, your recommendation)' \
  '## Do not touch (sealed specs, frozen fixtures, plugin defaults)' \
  '## Evidence rules (the integrity rules, three lines)' \
  '## Verification status (UNVERIFIED items and what would verify each)' \
  '## Blocked (item, what it waits for)'

if [ -e handoff/packets/TEMPLATE.md ]; then
  need_heading handoff/packets/TEMPLATE.md \
    '# Packet <number>: <short title>' \
    '## Question (one specific question)' \
    '## Output wanted (numbered verdicts, one line each; rewrites only if asked)'
else
  echo "MISSING handoff/packets/TEMPLATE.md"
  fail=1
fi

for f in handoff/packets/P*-*.md; do
  [ -e "$f" ] || continue
  need_heading "$f" '## Question' '## Constraints' '## Evidence' '## Output wanted'
done

# Secret-shape scan. Patterns deliberate: only shapes that look like a key/token/private key
# or an expanded home path (never a tilde shortcut). Prints the class name only.
for f in handoff/*.md handoff/packets/*.md; do
  [ -e "$f" ] || continue
  if grep -Eq '/home/[A-Za-z]' "$f"; then
    echo "SECRET-SHAPE $f: expanded-home-path pattern"
    fail=1
  fi
  if grep -Eq 'sk-[A-Za-z0-9_-]{12}|ghp_[A-Za-z0-9]{20}|github_pat_[A-Za-z0-9]|AKIA[A-Z0-9]{16}|BEGIN [A-Z. ]*PRIVATE KEY' "$f"; then
    echo "SECRET-SHAPE $f: credential-shaped pattern"
    fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "ALL HANDOFF CHECKS PASS"
else
  echo "HANDOFF CHECKS FAILED"
  exit 1
fi
