#!/usr/bin/env bash
# KIT-1 (09-plugin-parity.md §5) — shared post-capture verification stack for
# BOTH harness plugins (hermes ⇄ opencode). Operates on the trace file only;
# the same tool proves the same wire format on either side's capture.
#
#   tools/verify-capture.sh <trace.jsonl>          # prints each gate's result
#   OUT=/tmp/x tools/verify-capture.sh <trace>     # artifacts under $OUT
#
# Optional step: harness stop sequences live in the harness recipes, not here:
#   opencode: graceful TUI exit (SIGTERM; TUI holds the plugin) — see
#             packages/opencode/live/README.md (erratum).
#   hermes:   /ctxvm-trace stop, or session end (on_session_end flush).
set -euo pipefail
R="${CTXVM_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
T="$1"
OUT="${OUT:-/tmp/opencode/capture-verify}"
mkdir -p "$OUT"

[ -f "$T" ] || { echo "no trace file: $T" >&2; exit 1; }

echo "== replay (engine law) =="
"$R/rust/target/release/replay" "$T"

echo "== profile =="
"$R/rust/target/release/profile" "$T" --output "$OUT/profile.json"
python3 - "$OUT/profile.json" <<'PY'
import json, sys
s = json.load(open(sys.argv[1])).get("summary", {})
print("pages=%s faults=%s evictions=%s residentAtEnd=%s" % (
    s.get("pages"), s.get("faults"), s.get("evictions"), s.get("residentAtEnd")))
PY

echo "== export round-trip =="
"$R/rust/target/release/export" "$T" --output "$OUT/export" >/dev/null
echo "export ok -> $OUT/export"

echo "== metrics (UC3 KPIs) =="
"$R/venvs/odps/bin/python" "$R/benchmarks/metrics/metrics.py" "$T"

echo "== one-out policy sim (UC3 §3) =="
python3 - "$T" "$R" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[2])
from benchmarks.metrics.metrics import net_token_reduction, summarize
from benchmarks.metrics.policies import reference_string, simulate
events = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
dec, dem, anc = reference_string(events)
if not dem:
    sys.exit("no demands in capture — not promotable to corpus (needs echo + reads + >=1 fault shape)")
sizes = {k: dec[k]["tokens"] for k in dec}
keys = {(d["page"].get("logicalRef"), d["page"].get("contentHash")) for d in dem}
budget = max(sum(sizes[k] for k in keys) - min(sizes[k] for k in keys), max(sizes[k] for k in keys))
print(f"events={len(events)} turns={len(anc)} pages={len(dec)} demanded={len(keys)} tokens={sum(sizes[k] for k in keys)} one-out-budget={budget}")
for pol in ("lru", "fault-pin", "size-based"):
    out = simulate(events, pol, budget)
    m, s = out["meta"], summarize(out["sim_events"])
    rec = s["faultRecall"]
    rec = "null" if rec is None else f"{100*rec:.1f}%"
    print(f"{pol:12s} ev={m['simEvictions']:3d} faults={m['simFaults']:3d} "
          f"NTR={net_token_reduction(out['sim_events']):.3f} rec={rec} "
          f"pinCrunch={m.get('pinCrunch', 0)}")
PY

echo "== sidecar (if captured through the KIT-1 contract) =="
META="${T%.jsonl}.meta.json"
if [ -f "$META" ]; then
  cat "$META"
  python3 - "$META" <<'PY'
import json, sys
CANON = ["budgetTokens", "capturedAt", "harness", "harnessVersion", "hookStats",
         "model", "pluginVersion", "provider", "sessionID", "traceStats"]
meta = json.load(open(sys.argv[1]))
missing = [k for k in CANON if k not in meta]
extra = [k for k in meta if k not in CANON]
print("sidecar canonical keys:", "MATCH" if not (missing or extra) else f"missing={missing} extra={extra}")
PY
else
  echo "(no sidecar next to $T — synthesized fixtures ship without one)"
fi

echo "VERIFY-CAPTURE DONE: $T"
