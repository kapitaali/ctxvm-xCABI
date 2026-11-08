#!/bin/sh
# session-start.sh <packet-number> [--with-context]
# Writes handoff/SESSION-START.md = handoff/PROJECT-STATE.md, plus handoff/CONTEXT-PACK.md
# when --with-context is passed, plus the named packet handoff/packets/P<n>-*.md.
# POSIX sh, coreutils only. Prints byte size; exits non-zero if the result exceeds 16 KB,
# naming which part to cut.

set -u

n=${1:-}
with_context=0
[ "${2:-}" = "--with-context" ] && with_context=1

if [ -z "$n" ]; then
  echo "usage: tools/session-start.sh <packet-number> [--with-context]" >&2
  exit 2
fi

here=$(dirname "$0")
cd "$here/.." || exit 1

packet=
for f in handoff/packets/*; do
  case "$f" in
    handoff/packets/P"$n"-*) packet="$f" ;;
  esac
done
if [ -z "$packet" ]; then
  echo "no packet P$n in handoff/packets/ (expected handoff/packets/P$n-*.md)" >&2
  exit 2
fi

for need in handoff/PROJECT-STATE.md handoff/CONTEXT-PACK.md "$packet"; do
  if [ ! -e "$need" ]; then
    echo "missing $need (run tools/check-handoff.sh to see the full state)" >&2
    exit 2
  fi
done

out=handoff/SESSION-START.md
: > "$out"
cat handoff/PROJECT-STATE.md >> "$out"
if [ "$with_context" -eq 1 ]; then
  printf '\n\n' >> "$out"
  cat handoff/CONTEXT-PACK.md >> "$out"
fi
printf '\n\n' >> "$out"
cat "$packet" >> "$out"

size=$(wc -c < "$out")
if [ "$size" -gt 16384 ]; then
  s_project=$(wc -c < handoff/PROJECT-STATE.md)
  s_context=$(wc -c < handoff/CONTEXT-PACK.md)
  s_packet=$(wc -c < "$packet")
  echo "OVER 16 KB: session-start.md is $size bytes (limit 16384). Parts:" >&2
  echo "  PROJECT-STATE $s_project / CONTEXT-PACK $s_context / packet $s_packet" >&2
  cut_part=PROJECT-STATE
  cut_amt=$s_project
  [ "$s_context" -gt "$cut_amt" ] && { cut_part="CONTEXT-PACK"; cut_amt=$s_context; }
  [ "$s_packet" -gt "$cut_amt" ] && { cut_part="packet"; cut_amt=$s_packet; }
  if [ "$with_context" -eq 1 ] && [ "$s_context" -gt 8192 ]; then
    echo "CONTEXT-PACK itself is over its own 8 KB limit; run tools/check-handoff.sh and trim it first." >&2
  fi
  echo "cut from $cut_part (largest part, $cut_amt bytes) — drop glossary rows / Done rows / excerpt lines, never a required heading." >&2
  rm -f "$out"
  exit 1
fi

echo "SESSION-START: $size bytes ($out) — state + [$([ "$with_context" -eq 1 ] && echo with || echo no) context] + packet $packet"
