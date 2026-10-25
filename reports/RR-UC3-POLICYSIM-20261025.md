# RR-UC3-POLICYSIM — eviction-policy simulator build-first (UC3 §3)

**Card executed:** UC3 §3 build-first (post-UC3-BASELINE queue, user-directed) · **Date:** 2026-10-25
**State:** `benchmarks/metrics/policies.py` (new, ~250 lines) + `metrics.py` CLI `--policy/--budget`
+ `test_policies.py` (9 tests; suite **27/27 green**, 0 warnings). No rust changes; corpus unchanged.

## What was built

**Reference-string reconstruction** — from a real trace, the demand surface the simulator
consumes (stream order preserved):

| demand kind | source fact | meaning |
|---|---|---|
| `serve` | recorded `page.render` (mode=full) | content WAS in context |
| `recall` | recorded `page.fault` | model/tool asked for the page |

Recorded `page.render` stub facts, `page.evict` facts, and `page.pin`/`page.unpin` rows are the
**answers of the pager that ran** — the realization being replaced (all dropped; pin rows
counted in meta as `droppedPinFacts` so the drop is visible). Policies (v0, deterministic):
`lru` (LRU victim, declaration-order tie-break), `fault-pin` (Pichay-style: a page's SECOND
demand pins it; `pinCrunch` counts demands unservable because pinned pages fill the budget),
`size-based` (largest resident first, declaration-order ties).

**Simulated stream, evaluated by the same 07 formulas.** `simulate()` walks the reference
string and synthesises an in-memory xCABI event list (verbatim `page.declare`/`session.open`/
`call.meta`; sim `page.evict` rows before each demand's answer; sim `page.fault`+
`page.render(mode=full)` per miss; per-anchor `turn.render.residentTokens`) and `metrics.py`
runs its **existing aggregation functions unchanged** over it — formula fidelity by
construction, not re-implementation. Recorded cache-miss estimates (`call.meta`) are kept on
BOTH sides of `netTokenReduction`, so the reduction isolates slot math.

**Semantics locked by tests (every number hand-summed):**
- cold entry = OS-faithful demand-page miss: a `page.fault` then its serve (`S1/S5`);
- a recorded recall landing on a sim-resident page is a **real double-fetch fact** — preserved
  verbatim in the simulated stream (`S5`), not a pager answer;
- unserviceable serving miss: a page larger than the budget can never be resident
  (`S4`, sim `unservicedPages`);
- reactive engine law: eviction only when a bring-in would overflow — no proactivity (`S7`);
- recorded `page.pin` facts are dropped-but-counted (`S8`);
- contract errors fail fast: unknown policy / budget ≤ 0 / undeclared-page demand →
  `ValueError` (`S8`); CLI pairs `--policy`+`--budget` or exits 2 (argparse).

## Honest scope (verbatim duty, memo §3 + §5)

Policy simulation runs **without the model in the loop**: the reference string was recorded
under whichever policy actually ran, and a different pager would have produced different
stubs, hence different model behavior, hence different demands. Every simulated metric is an
**estimate**, printed with `policySim.scope` in the JSON. The simulated event list is never
persisted or emitted as xCABI output.

**Capacity convention (one-out).** The RR's headline table uses the deterministic "one-out"
capacity: `budget = max(Σdemanded − min_demanded, max_demanded)` over the *demanded* page set —
the largest demanded page always fits, the whole demanded roster does not, so evictions are
forced exactly once pressure exists. (An earlier half-roster convention hit the
unserviceability wall on unequal pages — m1/thrash at 700 tok < its 1000-tok page, m4 at
3770 — 0 policy evictions by construction, 0 information.) `--budget` stays free-form for
custom-pressure sweeps; `unserviceablePages`/`pinCrunch` remain first-class outputs.

## Corpus sweep — one-out capacity, all 10 traces (incl. m4, post-T17.8)

| trace | ev/dem/anc | roster→demanded | budget | lru ev/f NTR rec | fault-pin ev/f NTR rec pC | size-based ev/f NTR rec |
|---|---|---|---|---|---|---|
| m1/opencode-echo | 17/4/5 | 41→41 | 26 | 1/2 · 30.5% · 100% | 0/2 · 52.8% · null · 1 | 1/2 · 30.5% · 100% |
| m1/session-healthy | 12/4/3 | 8960→8960 | 8900 | 1/3 · 7.8% · 0% | 1/3 · 7.8% · 0% · 0 | 1/3 · **90.8%** · 0% |
| m1/session-thrashing | 41/11/10 | 1400→1400 | 1000 | 8/9 · 28.0% · 100% | 2/9 · 28.0% · 100% · 4 | 8/9 · 28.0% · 100% |
| m1/tracer-healthy | 16/4/4 | 34→34 | 25 | 1/3 · 28.2% · 0% | 1/3 · 28.2% · 0% · 0 | 2/4 · 28.2% · 50% |
| m1/tracer-recall | 19/5/4 | 47→47 | 35 | 1/3 · 20.4% · 0% | 1/3 · 20.4% · 0% · 0 | 1/3 · 27.2% · 0% |
| m2/live-echo | 22/6/6 | 144→144 | 134 | 1/3 · 38.7% · **200%** | 0/3 · 41.1% · null · 1 | 1/3 · 38.7% · 200% |
| m2/live-thrash | 33/15/6 | 289→289 | 239 | 10/14 · 14.8% · 50% | 5/11 · 16.3% · 80% · 2 | 5/9 · **20.5%** · **100%** |
| m3/hermes-echo-synthetic | 20/6/5 | 19→19 | 17 | 1/3 · 30.7% · 100% | 0/3 · 43.9% · null · 1 | 1/3 · 30.7% · 100% |
| m3/hermes-thrash-synthetic | 26/10/5 | 24→24 | 20 | 6/10 · 17.4% · 0% | 5/10 · 17.4% · 0% · 1 | 3/7 · 17.4% · 0% |
| m4/hermes-live-session-01 | 23/5/2 | 7540→961 | 918 | 1/5 · 82.9% · 0% | 1/5 · 82.9% · 0% · 0 | 1/5 · 87.5% · 0% |

`unservicedPages` = 0 across the entire sweep (the one-out convention guarantees the corner
case is gone). columns: ev = sim evictions, f = sim serving misses (faults), NTR = net token
reduction vs counterfactual, rec = fault recall, pC = `pinCrunch` (fault-pin only).

## Readings

1. **Only sustained demand separates policies — the healthy traces cannot.** The healthy and
   low-demand traces (3–4 demands, no repeat pressure) differ by ≤1 eviction between policies;
   the thrash-shaped traces (m1/thrash: 11 demands over 2 pages; m2/live-thrash: 15 over 5) show
   real separation. This empirically re-validates the memo's P-pathology premise on recorded
   data: policy benchmarking needs sustained-pressure workloads to mean anything.
2. **m2/live-thrash is the corpus's live policy discriminator**: under one-out pressure,
   LRU thrashes under double-demand pressure (10 evictions, 50% recall, NTR 14.8%); **size-based keeps
   the same workload at 5 evictions, 100% recall, NTR 20.5%** with lower thrash (2.0 vs 2.5).
   The best policy on recorded live-session data is size-based — pending the model-in-the-loop
   caveat, which would change which pages are demanded.
3. **`fault-pin`'s pinCrunch is a visible capacity bill**: m1/thrash crunches 4 demands
   (2nd-demand pinning fills exactly the one-out budget with two pinned pages), live-thrash 2.
   Pichay-style pinning buys recovery (80% on live-thrash) at the cost of unshrinkable
   residency; under one-out pressure this pinning rule can starve the remaining workload.
4. **`m2/live-echo`'s "200% recall" is formula-faithful, not a bug.** 07 defines recall =
   recovered_faults / evictions; the sim had 2 covering recoveries over 1 eviction. Reporting
   raw values with the note ("recoveries can outpace evictions; the ≥95% gate reads fine, the
   ratio reads odd above 100%") is the honest form — capping at 1.0 would hide the asymmetry.
5. **m4's 87% sim NTR mostly measures the roster-stub story, not the policy.** The live Hermes
   session served only 961 of its 7540 declared tokens; under one-out pressure the sim keeps
   ~90% of the naive hypothetical out of context — but the same would happen with no policy at
   all. The policy effect (1 eviction) is real but small; the memo's net-token target (40%)
   passes trivially here for reasons that have nothing to do with eviction quality.
6. **memo's §3 example commands now run** as `metrics.py TRACE --policy lru|fault-pin|size-based
   --budget N`, with recorded-baseline `--baseline <trace>` unchanged. The memo's exact CLI
   spelling was a design-stage placeholder (RR-UC3-BASELINE finding 3) — now both halves exist.

## Verification chain

- `venvs/odps/bin/python -m pytest benchmarks/metrics` → **27/27** (18 pre-existing hand-summed
  T3 tests untouched-green + 9 policy tests, incl. integration on the real thrashing fixture at
  roster capacity: sim reproduces 0 policy evictions / NTR 0.0 / preserved double-fetch faults,
  confirming the fixture's recorded evictions are policy-induced, not capacity-induced);
- CLI ≡ library path on `corpus/m2/live-thrash --policy size-based --budget 239` (5/9 identical);
- default-mode output byte-compatible (healthy fixture: rendered 26880 + 200 misses, as recorded
  in RR-UC3-BASELINE Table 1);
- sweep artifacts: `/tmp/opencode/uc3-sim/` (30 per-trace-policy JSONs + `summary.json` + sweep.py).

## Errata direction

The UC3 memo §3's example block (`--baseline lru`, `--baseline fault-pin`, `--baseline size-based`)
should be re-labeled to the shipped spellings (`--policy`/`--budget`) — same resolution path the
RR-UC3-BASELINE doc noted for CLI spelling errata; the memo §5 disclaimer ("no built-in policy
library; must be implemented by the user or as v1 plugins") was accurate until this card and now
deserves a pointer to `benchmarks/metrics/policies.py`.

## Next proposed

1. **Windowed P-pathology reference sheet** — `profile --turns` / `metrics --windows` canonical
   window families per trace, committed as fixtures (thrash claims become reproducible).
2. **UC3 policy-sweep parametrics** — `--budget` sweeps per trace (e.g., 25%–100% of demanded) to
   chart eviction-count/fault-vs-capacity curves per policy (memo §4's illustrative table, now
   with a real generator).
3. **T15 (Vercel adapter)** and other queued cards unchanged; live m4 capture with an
   artificially small budget entry remains the operator-side lever for a real eviction stream.
