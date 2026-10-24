# RR-UC3-BASELINE — corpus-wide capacity-planning baseline, two KPI lenses

**Card executed:** UC3 baseline analysis (post-T21 queue) · **Date:** 2026-10-24
**Scope:** read-only analysis sweep + this report. No tool code changed; no gates renamed.
Tools at tree `59f6091` (workspace 52 tests, the T21 GREEN state): `replay`, `profile`,
`export` (rust target/release) + `benchmarks/metrics/metrics.py`.

## What was done

Full sweep over **all 9 committed corpus traces** (m1×5, m2×2, m3×2 — fixtures are
byte-identical to `benchmarks/metrics/fixtures/*`, `cmp`-verified), four tools per trace:

| tool | role in the sweep | result |
|---|---|---|
| `replay` | determinism fact gate | **9/9 exit 0, divergences-free** |
| `profile` | page/eviction/fault anatomy | 9/9 exit 0 |
| `metrics.py` | UC3 formula lens (counterfactual baseline) | 9/9 exit 0 |
| `export` | T21 snapshot lens @last turn | 9/9 exit 0, DQ `replayDeterminism`+`sourceFidelity` true, relation `identical`, warnings empty |

Witness artifacts: `/tmp/opencode/uc3/` (`sweep.sh`, per-trace `profile-*`/`metrics-*`/`export-*`
JSON, `merge.py`, `summary.json`, slice dirs `dyn-0..9`). Provenance per drop: m1 = 2 reference
vectors + 2 @ctxvm/node tracer fixtures + 1 T9 adapter-spike fixture (T10); m2 = 2 real OpenCode
live captures (T12); m3 = 2 synthetic Hermes-plugin captures (T17).

## Table 1 — UC3 formula lens (`metrics.py`, counterfactual no-paging baseline)

| trace | ev/pgs/tokens | evict/fault (sources) | rendered+miss | netTokRed | faultRecall | touch/waste | thrashIdx |
|---|---|---|---|---|---|---|---|
| m1/opencode-echo | 17/2/41 | 0 / 2 (id:1, tool:1) | 205+41 | 0.0% | null | 7.3%/92.7% | 0.4 |
| m1/session-healthy | 12/3/8960 | 0 / 1 (id:1) | 26880+200 | 0.0% | null | 0.2%/99.8% | 0.33 |
| m1/session-thrashing | 41/2/1400 | **4 / 3** (id:1, tool:2) | 6200+300 | **54.5%** | **50.0%** | 22.6%/77.4% | 0.3 |
| m1/tracer-healthy | 16/3/34 | 0 / 1 (id:1) | 136+34 | 0.0% | null | 9.6%/90.4% | 0.25 |
| m1/tracer-recall | 19/3/47 | 0 / 2 (id:1, tool:1) | 188+47 | 0.0% | null | 8.5%/91.5% | 0.5 |
| m2/live-echo | 22/3/144 | 0 / 3 (id:2, tool:1) | 864+144 | 0.0% | null | 8.7%/91.3% | 0.5 |
| m2/live-thrash | 33/5/289 | 0 / **10** (id:5, tool:5) | 1734+289 | 0.0% | null | 16.7%/83.3% | 1.67 |
| m3/hermes-echo-synthetic | 20/3/19 | 0 / 3 (id:2, tool:1) | 95+19 | 0.0% | null | 9.5%/90.5% | 0.6 |
| m3/hermes-thrash-synthetic | 26/5/24 | 0 / 5 (tool:5) | 120+24 | 0.0% | null | 20.0%/80.0% | 1.0 |

Arithmetic spot-checks (all reproduced from event streams): netTokRed 54.5% = `1 − 6500/14300`
(paged 6200 rendered + 300 misses vs counterfactual 1400 × 10 turns + 300); faultRecall 50% =
2 covering recoveries ÷ **4 evictions** (07's denominator, not faults; page A's fault@9 has no
later full render — unrecovered by fixture design); rendered 26880 = 8960 × 3 full turns.

## Table 2 — T21 export lens (snapshot @ last turn; slice = source)

| trace | kept/src | replayDet + fidelity | faultRecall | netTokenRed | touchRatio |
|---|---|---|---|---|---|
| m1/opencode-echo | 17/17 | true + true | 100% | 0.0% | 100% |
| m1/session-healthy | 12/12 | true + true | 100% | 0.0% | 100% |
| m1/session-thrashing | 41/41 | true + true | 0.0% | **100%** | 100% |
| m1/tracer-healthy | 16/16 | true + true | 100% | 0.0% | 100% |
| m1/tracer-recall | 19/19 | true + true | 100% | 0.0% | 100% |
| m2/live-echo | 22/22 | true + true | 100% | 0.0% | 100% |
| m2/live-thrash | 33/33 | true + true | 100% | 0.0% | 100% |
| m3/hermes-echo-synthetic | 20/20 | true + true | 100% | 0.0% | 100% |
| m3/hermes-thrash-synthetic | 26/26 | true + true | 100% | 0.0% | 100% |

**Lens reconciliation (not a bug, but a naming hazard to document):** the three KPI names
appear in both artifacts with different pinned definitions and scopes.
- `faultRecall`: UC3 = recovered_faults/**evictions** over whole history; T21 = faults@≤N whose
  page is Full@N (end-state coverage). Same trace at N=9: 50% vs 0% — both correct *in law*.
- `netTokenReduction`: UC3 = 1 − paged_net/naive (process); T21 = stubbed/(resident+stubbed)
  at the cut (slot fraction). At N=9: 54.5% vs 100%.
- `touchRatio`: UC3 = faulted tokens/rendered (proxy); T21 = declared pages with a recorded full
  render ≤ N ÷ roster. 22.6% vs 100%.
An ODPS manifest should therefore state *which* KPI namespace it uses. The T21 manifest already
carries its formulas inline; consumers must not cross-compare the two namespaces. (RR-T21's
§ law confirmations: N=1 slice on the thrashing fixture reproduces `0.2857` exactly.)

## Table 3 — slice dynamics (`export --turn N`, m1/session-thrashing, N = 0…9)

| N | kept/src | faultRecall | netTokenRed | touchRatio | resident/stubbed tok |
|---|---|---|---|---|---|
| 0 | 31/41 | null | 0.0% | 100% | 1400/0 |
| 1 | 32/41 | null | 0.2857 | 100% | 1000/400 |
| 2 | 33/41 | 0.0% | 0.2857 | 100% | 1000/400 |
| 3 | 34/41 | 1.0 | 0.0% | 100% | 1400/0 |
| 4 | 35/41 | 0.0% | 0.2857 | 100% | 1000/400 |
| 5 | 36/41 | 0.0% | 1.0 | 100% | 0/1400 |
| 6 | 37/41 | 0.0% | 1.0 | 100% | 0/1400 |
| 7 | 38/41 | 1.0 | 0.7143 | 100% | 400/1000 |
| 8 | 39/41 | 0.0% | 1.0 | 100% | 0/1400 |
| 9 | 41/41 | 0.0% | 1.0 | 100% | 0/1400 |

The end-state lens hides the thrash sweep entirely; per-turn slices expose the
recovery/re-eviction oscillation (fault@2 → full@3 → 1.0 recall collapses to 0.0 the moment the
page is re-stubbed). This is the strongest argument yet for the T15/`--pin`-style and windowed
views `profile --turns` already provides at the stream level.

## Threshold reading (07 M0 gates + ODPS manifest KPI targets)

| KPI | target | observed on corpus | verdict |
|---|---|---|---|
| kpi-fault-recall | 95% (M0) | 50% on the one eviction-bearing trace; **null** on the other 8 | **unmeasurable beyond the fixture**; 50% ≠ gate (A@9 unrecovered by design) |
| kpi-net-token | 40% | 54.5% (thrashing fixture) | met **as labeled approximation** (counterfactual); not a live-token measurement |
| kpi-touch-ratio | 60% | max 22.6% | below target under the v0 fault-evidence proxy |
| net reduction ≥1.5× (M0) | equal accuracy | not applicable | v0 traces are observe-only: no accuracy arm, no A/B |
| replay determinism (M0) | 100% byte-identical | 9/9 exit 0 (+ T21 replay counterproofs) | **met** |
| corpus conformance (M0) | 100% | established by schema/replay gates (412 checks + 9/9 here) | **met** |

## Findings

1. **The corpus is eviction-starved by construction, and that is the honest v0 story.** 1 of 9
   traces has evictions (a designed fixture); everything else pages zero because budgets are
   never approached (largest live capture: 289 tok against a 200k budget). Every "reduction" the
   corpus can show is either a fixture's designed thrash or the counterfactual baseline.
2. **m2/live-thrash is the real-traffic headline of UC3 so far: fault-rate pathology without
   pressure.** A real OpenCode session (T12, deepseek free-tier, USD 0) emitted 10 faults over 5
   tiny pages (5 identifier_scan → full renders → 5 tool_recall double-fetches) with zero
   evictions — thrash_index 1.67/turn whole-trace.
3. **P-pathology windows change thrash_index by 3× and must be part of any thrash claim.**
   `--windows 0-1` on m2/live-thrash: 5.0/turn (vs 1.67); `--windows 2-3,6-9` on the thrashing
   fixture: 0.5 (vs 0.3). Default whole-trace is the only fair cross-trace number; windowed
   values need the window spec quoted.
4. **UC3 memo §3's policy-comparison commands are placeholders.** `metrics.py --baseline`
   takes a *recorded trace file*, not a policy name; no LRU/fault-pin/size-based implementation
   exists in the committed simulator (memo §5's "no built-in policy library" disclaimer states
   this accurately — §3's example block predates the implementation and should be re-labeled
   design-stage). Cross-session recorded baselines are invalid by construction: pairing
   thrashing↔healthy yields a meaningless "76%" (different page sets) — demonstrated and
   rejected. Counterfactual is the only honest measurable baseline for a single observe-managed
   trace; real A/B baselines need the model in the loop (v1).
5. **Touch-ratio targets are unreachable under the v0 proxy** for renders-heavy traces (0.2% on
   the healthy fixture) — expected: the proxy counts only fault-evidenced pages. Simulated
   policy SHIFTS (memo §4's illustrative table) remain simulation-design numbers, not observed
   ones; this sweep is the observed baseline they would be compared against.

## Repro

```bash
cd /home/theb/Documents/ctxvm
for t in corpus/m1/*.jsonl corpus/m2/*.jsonl corpus/m3/*.jsonl; do
  rust/target/release/replay "$t"                       # expect exit 0
  rust/target/release/profile "$t" --output /tmp/p.json # anatomy
  python benchmarks/metrics/metrics.py "$t"             # UC3 lens
  rust/target/release/export "$t" --output /tmp/exp-$(basename "$t" .jsonl)
done
# windows + slice dynamics:
python benchmarks/metrics/metrics.py corpus/m2/live-thrash.jsonl --windows 0-1
rust/target/release/export corpus/m1/session-thrashing.jsonl --turn 5 --output /tmp/dyn5
```

## Next proposed (orchestrator approval)

1. **UC3 §3 build-first** — policy simulator `--policy lru|fault-pin` as pure functions over
   the recorded event stream (RR-T3 pattern, honest-scope label "no model in the loop"), so the
   §4 illustrative table becomes a measured comparison.
2. **Windowed P-pathology reference sheet** — `profile --turns`/`metrics --windows` runs per
   trap-window family, committed as fixtures so windowed thrash claims have a canonical form.
3. **UC3-relevant live capture m4** — same 5-page echo shell under an artificially small
   budget entry so a real eviction-recovery stream is observed (operator lever, USD 0).

## Ledger

LOG row appended (registry format, 3 cells).
