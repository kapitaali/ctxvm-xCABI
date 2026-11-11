#!/usr/bin/env bash
# w8b-profiles.sh — the two-profile rule, checkable at any time.
#
# W8B needs exactly one profile pair: <prefix>-naive (control) and <prefix>-paged (treatment).
# Every extra profile came from provisioning per provider or per model, which is how eight appeared
# in the owner's install and had to be deleted. This script prints the pair, the one-key difference,
# and fails if the count is not two.
set -uo pipefail

PREFIX="${1:-w8bn}"
ROOT="${HERMES_HOME:-$HOME/.hermes}"
DIR="$ROOT/profiles"

mapfile -t found < <(find "$DIR" -maxdepth 1 -type d -name "$PREFIX-*" -printf '%f\n' 2>/dev/null | sort)
if [ "${#found[@]}" -ne 2 ]; then
  echo "FAIL: expected exactly 2 profiles matching $PREFIX-*, found ${#found[@]}: ${found[*]:-none}"
  exit 1
fi

for p in "${found[@]}"; do
  cfg="$DIR/$p/config.yaml"
  [ -f "$cfg" ] || { echo "FAIL: $p has no config.yaml"; exit 1; }
  printf '%-14s engine=%-12s model=%s\n' "$p" \
    "$(grep -m1 '^  engine:' "$cfg" | sed 's/.*engine: *//; s/"//g')" \
    "$(grep -m1 '^  default:' "$cfg" | sed 's/.*default: *//; s/"//g')"
done

diff <(grep -v '^_config_version' "$DIR/${PREFIX}-naive/config.yaml") \
     <(grep -v '^_config_version' "$DIR/${PREFIX}-paged/config.yaml") > /tmp/w8b_profile_diff.$$
if [ "$(grep -c '^>' /tmp/w8b_profile_diff.$$)" -ne 6 ] || \
   [ "$(grep -c '^<' /tmp/w8b_profile_diff.$$)" -ne 1 ]; then
  echo "WARN: the pair differs by more than context.engine + the paged budget block; review:"
  cat /tmp/w8b_profile_diff.$$
else
  echo "OK: the pair differs only in context.engine and the paged budget block"
fi
rm -f /tmp/w8b_profile_diff.$$
