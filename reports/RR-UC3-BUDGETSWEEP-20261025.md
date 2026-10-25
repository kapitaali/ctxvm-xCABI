# RR-UC3-BUDGETSWEEP — budget-parametric policy curves (UC3 §3→§4)

**Card executed:** UC3 budget-parametric sweep (RR-UC3-POLICYSIM §Next 2, user-directed queue) · **Date:** 2026-10-25
**State:** analysis-only through the **committed CLI** (`56ae0c1` — `metrics.py --policy/--budget`), 150 invocations, rc=0 each. No code, no corpus, no rust/ts changes. Artifacts: `/tmp/opencode/uc3-budget/` (`summary.json`, 150 per-cell JSONs, `sweep.py`). Fresh **ALL GATES GREEN** CI witness re-run this same session (rust suite · TS 12+8 · hermes python 21 · schema 435 checks incl. m4 checksums · export round-trip · hub byte-identity) — the repo is green at the card's evidence commit.

## Method

Grid per trace × policy: `budget = round(f × Σdemanded)`, f ∈ {12.5%, 25%, 50%, 75%, 100%}, where
Σdemanded = the declared-token sum over the *demanded* page set (union of demand keys). Policies:
`lru`, `fault-pin`, `size-based` (semantics per RR-UC3-POLICYSIM; unchanged). Two analytic anchors
are built into the grid and *asserted*, not assumed:

- **A1 (reactive law, bulk):** f = 100% ⇒ budget = whole demanded roster ⇒ **0 evictions by construction** — held on all 30 curves (the bulk form of pytest S7, which asserts it on the thrashing fixture at exact roster capacity).
- **A2 (unserviceability wall):** budget < max demanded page tokens ⇒ that page can never be resident. Programmatic equivalence `unserved>0 ⟺ budget < maxPage` **held on all 150 cells**.

Honest-scope caveat carries over verbatim: simulation runs **without the model in the loop**; every simulated number is an estimate over the recorded reference string.

## The corpus curves

Cells are `ev/f/NTR%` = sim evictions / sim serving misses / net-token-reduction, per budget fraction. `wall` = f below which the wall exists (= maxPage/Σdemanded, checked against A2).

| trace | Σdem/max | wall | policy | 12.5% | 25% | 50% | 75% | 100% |
|---|---|---|---|---|---|---|---|---|
| m1/opencode-echo | 41/26 | 0.6341 | lru | 0/4/83.3 | 0/4/83.3 | 0/2/52.8 | 1/2/30.5 | 0/2/0.0 |
| m1/opencode-echo | 41/26 | 0.6341 | fault-pin | 0/4/83.3 | 0/4/83.3 | 0/2/52.8 | 0/2/52.8 | 0/2/0.0 |
| m1/opencode-echo | 41/26 | 0.6341 | size-based | 0/4/83.3 | 0/4/83.3 | 0/2/52.8 | 1/2/30.5 | 0/2/0.0 |
| m1/session-healthy | 8960/8200 | 0.9152 | lru | 0/3/90.8 | 0/3/90.8 | 0/3/90.8 | 0/3/90.8 | 0/3/0.0 |
| m1/session-healthy | 8960/8200 | 0.9152 | fault-pin | 0/3/90.8 | 0/3/90.8 | 0/3/90.8 | 0/3/90.8 | 0/3/0.0 |
| m1/session-healthy | 8960/8200 | 0.9152 | size-based | 0/3/90.8 | 0/3/90.8 | 0/3/90.8 | 0/3/90.8 | 0/3/0.0 |
| m1/session-thrashing | 1400/1000 | 0.7143 | lru | 0/11/97.9 | 0/11/97.9 | 0/7/69.9 | 8/9/28.0 | 0/2/0.0 |
| m1/session-thrashing | 1400/1000 | 0.7143 | fault-pin | 0/11/97.9 | 0/11/97.9 | 0/7/69.9 | 2/7/28.0 | 0/2/0.0 |
| m1/session-thrashing | 1400/1000 | 0.7143 | size-based | 0/11/97.9 | 0/11/97.9 | 0/7/69.9 | 8/9/28.0 | 0/2/0.0 |
| m1/tracer-healthy | 34/13 | 0.3824 | lru | 0/4/80.0 | 0/4/80.0 | 3/4/49.4 | 1/3/28.2 | 0/3/0.0 |
| m1/tracer-healthy | 34/13 | 0.3824 | fault-pin | 0/4/80.0 | 0/4/80.0 | 3/4/49.4 | 1/3/28.2 | 0/3/0.0 |
| m1/tracer-healthy | 34/13 | 0.3824 | size-based | 0/4/80.0 | 0/4/80.0 | 3/4/49.4 | 2/4/28.2 | 0/3/0.0 |
| m1/tracer-recall | 47/19 | 0.4043 | lru | 0/5/80.0 | 0/5/59.6 | 3/4/47.7 | 1/3/20.4 | 0/3/0.0 |
| m1/tracer-recall | 47/19 | 0.4043 | fault-pin | 0/5/80.0 | 0/5/59.6 | 2/4/52.8 | 1/3/20.4 | 0/3/0.0 |
| m1/tracer-recall | 47/19 | 0.4043 | size-based | 0/5/80.0 | 0/5/59.6 | 3/4/47.7 | 1/3/27.2 | 0/3/0.0 |
| m2/live-echo | 144/69 | 0.4792 | lru | 0/5/79.8 | 0/5/79.8 | 2/3/44.6 | 1/3/38.7 | 0/3/0.0 |
| m2/live-echo | 144/69 | 0.4792 | fault-pin | 0/5/79.8 | 0/5/79.8 | 0/4/47.0 | 0/3/41.1 | 0/3/0.0 |
| m2/live-echo | 144/69 | 0.4792 | size-based | 0/5/79.8 | 0/5/79.8 | 2/3/44.6 | 1/3/38.7 | 0/3/0.0 |
| m2/live-thrash | 289/69 | 0.2388 | lru | 0/15/85.7 | 14/15/69.4 | 13/15/51.0 | 12/15/30.5 | 0/5/0.0 |
| m2/live-thrash | 289/69 | 0.2388 | fault-pin | 0/15/85.7 | 5/14/70.9 | 5/13/50.4 | 5/12/34.7 | 0/5/0.0 |
| m2/live-thrash | 289/69 | 0.2388 | size-based | 0/15/85.7 | 14/15/69.4 | 11/13/54.6 | 8/11/38.9 | 0/5/0.0 |
| m3/hermes-echo-synthetic | 19/10 | 0.5263 | lru | 0/5/74.6 | 0/5/74.6 | 2/3/39.5 | 1/3/30.7 | 0/3/0.0 |
| m3/hermes-echo-synthetic | 19/10 | 0.5263 | fault-pin | 0/5/74.6 | 0/5/74.6 | 0/3/43.9 | 0/3/43.9 | 0/3/0.0 |
| m3/hermes-echo-synthetic | 19/10 | 0.5263 | size-based | 0/5/74.6 | 0/5/74.6 | 2/3/39.5 | 1/3/30.7 | 0/3/0.0 |
| m3/hermes-thrash-synthetic | 24/5 | 0.2083 | lru | 0/10/83.3 | 9/10/66.0 | 8/10/48.6 | 7/10/31.2 | 0/5/0.0 |
| m3/hermes-thrash-synthetic | 24/5 | 0.2083 | fault-pin | 0/10/83.3 | 5/10/66.0 | 5/10/52.1 | 5/10/34.7 | 0/5/0.0 |
| m3/hermes-thrash-synthetic | 24/5 | 0.2083 | size-based | 0/10/83.3 | 9/10/66.0 | 7/9/52.1 | 5/8/34.7 | 0/5/0.0 |
| m4/hermes-live-session-01 | 961/421 | 0.4381 | lru | 0/5/93.1 | 0/5/91.3 | 3/5/89.9 | 3/5/89.9 | 0/5/82.2 |
| m4/hermes-live-session-01 | 961/421 | 0.4381 | fault-pin | 0/5/93.1 | 0/5/91.3 | 3/5/89.9 | 3/5/89.9 | 0/5/82.2 |
| m4/hermes-live-session-01 | 961/421 | 0.4381 | size-based | 0/5/93.1 | 0/5/91.3 | 2/5/89.3 | 1/5/87.5 | 0/5/82.2 |

Hand-locked cells (defended in the verification chain): thrashing@700 (f 50%, lru) — 7 faults = 6 wall-misses on the 1000-tok `schema.sql` + 1 cold on the 400-tok page, NTR 69.9%; thrashing@1400 (f 100%) — ev 0 / faults 2 / NTR 0.0, **identical to pytest S7's library-asserted values through the CLI**; live-thrash size-based family is monotone toward the prior card's one-out point 239 (ev 14→11→8→0 across 72→144→217→289; 239 interpolates to ev ≈ 5, f ≈ 9, NTR ≈ 20.5% — the exact figures RR-UC3-POLICYSIM recorded).

## Readings

1. **Every trace passes through three regimes, and policy information exists only in the middle one.** Left of the wall (f < maxPage/Σdemanded): the starving regime — pages can never be resident, every demand misses (e.g. m2/live-thrash @12.5%: budget 36 < its smallest 50-tok page ⇒ all 5 pages unserved, all 15 demands miss, NTR 85.7% is *vacuous*), and all three policies produce **identical** cells — the wall erases policy differences exactly as it erased capacity information in the half-roster convention analysis. Right end (f = 100%): the quiescent plateau — 0 evictions by the reactive law, NTR converges to 0 (except m4, reading 6). Only the band in between separates policies.
2. **"Healthy" rosters are wall-dominated, so healthy traces have no discriminating band at any capacity.** m1/session-healthy: wall = 0.9152 — below **91.5%** capacity the 8200-tok dominant page is unserviceable, and the sim serves only the 700+60-token remainder (NTR pinned at 90.8%, policies identical curve for curve); above it the roster fits and the engine is silent. The trace offers no window in which any policy choice matters. Corollary for capacity planning: *workload shape, not budget level, decides whether policy comparison is even well-posed* — the memo's P-pathology premise now holds under budget-parametric pressure, not just at a single operating point.
3. **NTR is reward-inverted under famine — never quote it without a service metric beside it.** m1/opencode-echo @75%: fault-pin NTR 52.8% "beats" lru's 30.5% — but fault-pin got there by **serving less** (pin-crunch famine: `pinCrunch=1`, ev 0) while lru pays for its eviction with a re-render. Same failure family as m4's flat-90% curve: NTR rewards page *non-appearance*. The honest pairing for any budget decision is NTR ⊕ faults/pinCrunch/unserved/faultRecall. This hardens the prior card's reading 5 into a general curve-level rule.
4. **m2/live-thrash: size-based strictly dominates inside the band** — higher NTR at every in-band point (54.6 vs 51.0 lru / 50.4 fault-pin @50%; 38.9 vs 30.5 / 34.7 @75%), fewer evictions (11/8 vs 13/12), fewer faults (13/11 vs 15/15), higher faultRecall (45.5%/62.5% vs 38.5%/41.7%). LRU is dominated everywhere in-band. The prior card's single-point ranking survives the whole parametric band — and m3/hermes-thrash-synthetic **replicates the same ordering** on an independent (synthetic vs live) workload: 52.1/34.7 vs 48.6/31.2. The size-based result is not a one-trace artifact.
5. **fault-pin's cost signature scales down with budget** — `pinCrunch` = 8/6/4 on live-thrash and 4/3/2 on thrash-synthetic as capacity grows; its eviction count stays *flat* (5 on live-thrash across the entire band) while its faultRecall climbs (0.2 → 0.4 → 0.6). Pinning converts money (capacity) into recovery, but plateau NTR ≈ size-based's minus the serviceability gap — it never wins NTR in-band on either thrash-shaped trace. Symmetric finding on the echo-doubles traces: fault-pin is a clean winner there (zero evictions, NTR +23 pts) — *pinning pays for repeated-demand workload shapes, starves thrash-shaped ones*.
6. **m4's curve is flat high at every capacity — a declaration-discipline curve, not a policy curve.** NTR 82.2% at f = 100% (zero pressure): the roster it *declares* (7540 tok) dwarfs the roster it *demands* (961 tok), so the counterfactual stays ~90% regardless of eviction behavior; in-band evictions ≤ 3 and policy deltas ≤ 2.4 pts. Parametric confirmation of the prior card's roster-under-serving reading, now as a curve.
7. **Two honest non-monotonicities, both wall-boundary effects (documented, not smoothed):** (i) evictions not monotone in budget on wall-restricted traces — opencode-echo: 1 eviction @75% (budget 31 ≥ max 26, page serviceable → rotation starts) but **0** @50% (the same page is wall-frozen → no bring-ins → no rotation); (ii) fault counts *rise* when a wall clears — thrashing lru f7 @50% → f9 @75% (the newly serviceable page re-enters rotation and re-fetches). Both are real boundary interactions of the reference string; a finer grid (∆ 12.5% or finer) is a v1 nicety, not needed for these findings.

## Verification chain

- `tools/run-ci.sh` → **ALL GATES GREEN** fresh witness this session (4 gates; schema 435 checks; m1–m4 checksums; export round-trip incl. `corpus/m3`; hub parity).
- 150/150 CLI invocations rc=0; per-cell JSONs + `summary.json` + `sweep.py` at `/tmp/opencode/uc3-budget/`; **A1 asserted** (f=100% ⇒ 0 evict, all 30 curves); **A2 asserted-passed** (`unserved>0 ⟺ budget < maxPage`, all 150 cells).
- Hand anchors: thrashing@700 anatomy (6 wall-misses + 1 cold = 7 faults); thrashing@1400 = pytest S7 verbatim through the CLI; live-thrash size-based 72→144→217 curve interpolates the prior card's recorded @239 cell (ev 5 / f 9 / NTR 20.5%).
- CI-mirror gap flagged (not silently patched): `tools/run-ci.sh` gate 2 runs the hermes python suite (21 tests) but **not** `pytest benchmarks/metrics` (now 27 tests). Propose folding into the queued hygiene card (with the tracked-`.pyc` cleanup) — both are repo-bookkeeping edits needing an explicit go.

## Next proposed

1. **m5 promotion** (blocked on user's OpenCode exit): `/tmp/opencode/m5-self-capture/verify-m5.sh` is staged — one command runs replay → profile → export → metrics → one-out sim on the flushed capture; promote to `corpus/m5` if echo + reads + ≥1 fault shape appear, folding the v2.1.4 recipe erratum into the drop card.
2. Hygiene card (needs go): metrics-pytest CI gate + tracked-`.pyc` removal (`git rm --cached`) + `.gitignore` entry.
3. T15 (Vercel adapter) unchanged in queue.
