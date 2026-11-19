# PREREG-E2-DRAFT-20261119 — hosted page ablation (Route B secondary)

**Status: PARKED / BLOCKED on a content-bearing fixture bank — owner ruling
`RR-E2HOLD-20261119` (801ef6b), $0 spend. NOT a runnable preregistration.** No Phase 1
call, smoke call, or paid spend is authorized; the standing paid-spend stop remains in
force. This note records the design and the physical blockers so a future reopen has a
frozen starting point. Authority chain: Part III §9.2 / Route B; `plan-E1` §7 step 6;
E1 recorded mixed (`research/e1-offline/RR-E1-RESULT.md`, a1bd004); owner "approve E2
hold and Part III typo fix" (2026-11-19). Nothing here is pooled with E1, M1, M2 or M3.

## 0. Ratified parameters and hold (owner ruling RR-E2HOLD-20261119)

1. **E0 ordering — RATIFIED option (b).** Standalone hosted question: *"does removing a
   named page change hosted answers more than matched random removal above the baseline
   noise floor?"* Explicitly a **narrower, non-transfer** question, because open-weight
   E0 has not run. No claim that an open-weight effect transfers.
2. **Sample count — RATIFIED 3 samples per arm across 2 arms** (leave-one-out + matched
   random = 6 ablation calls per page-prompt pair; baseline + baseline-repeat = 6 baseline
   calls per prompt), matching Route B's formula
   `(20×10×3×2)+(20×3×2) = 1,320` calls (Part III :232, :248). The §9.2 "6 samples"
   wording was a typo; fixed in en/zh by the same ruling.
3. **Route + cost — HELD at $0.** Free routes are quota-exhausted (Zen 429; Explabs no
   credits; Nous direct 401). The $0.00861/req rate is Luna's historical blended rate
   (`RR-SPEND-VERIFY-20261110`, `reports/W8-SPEND.md`), model-specific and **UNVERIFIED**
   for any E2 model. 1,320 calls ≈ $11.37 at that rate — an order-of-magnitude, not a
   quote. A reopen needs a named model snapshot, a smoke receipt read from `debited_usd`
   (never `providerUsage`), and a fresh owner cost-ceiling sign-off.

## 1. Question and hypothesis (option b wording)

On hosted-model calls, does removing a named page change the answer more than removing a
matched random page, above the baseline noise floor? H1: ablation answer-change rate >
matched-random rate. H0: no difference. Unit: proportion (answer-change rate per page).

## 2. Data — BLOCKED on the frozen corpus (verified 2026-11-19)

The original draft proposed "20 prompts drawn from frozen corpus traces; 10 pages per
trace." Direct inspection of `corpus/m1–m8` (via the byte-identical
`research/e1-offline/traces/` copies) proves even Phase 0 cannot run that design:

- **Blocker A — traces are content-blind.** 0 of 17 traces carry page body text or user
  prompt text; `page.declare` holds only `page.id.{logicalRef,contentHash}`, `kind`,
  `tokens`. Part III §4.1 (:144): *"A trace holds identities and hashes, not page
  content."* An ablated context τ\p cannot be constructed from the JSONL alone — there is
  no text to remove.
- **Blocker B — the corpus lacks 20 traces × 10 pages.** Only 17 traces exist (118
  `page.declare` events total); only **3 of 17 have ≥10 unique declared pages**:
  `m4/hermes-live-session-01` (13 pages, **1** tool_recall fault),
  `m5/opencode-live-session-01` (17 pages, **0** tool_recall — all 17 faults are
  identifier_scan, which E1 scored **negative at 2.4%**), and
  `m7/hermes-resume-session-b` (34 pages, **0** faults). Eleven of the other 14 traces
  have ≤3 unique pages.

**Precondition for any reopen:** a content-bearing prompt + page fixture bank paired with
its xCABI trace (so τ and τ\p exist as actual text), stratified on `tool_recall` rather
than the negative `identifier_scan` stratum, plus a fresh owner cost-ceiling sign-off.
Until that bank exists, E2 cannot reach Phase 0 on real data.

## 3. Design (carried forward for the reopen; not executable today)

- 20 prompts × 10 pages from the content-bearing bank; page set and prompt→page mapping
  frozen before any call; full path as unit (E1's naming law).
- Arms interleaved (not blocked by arm): baseline; baseline-repeat (noise floor);
  leave-one-out per page; matched random page (same removal count, seeded). Interleaving
  prevents quota attrition concentrating in one arm (M2 lesson).
- Metric Δ(p) = (1/n) Σ 1[a_i(τ) ≠ a_i(τ\p)] (Route B); binomial interval per page and
  pooled by arm. Noise floor = baseline-vs-baseline change rate at the same temperature.
- Answer-change grader frozen: exact match after a hashed normalization (trim + collapse
  whitespace + casefold for free text; exact token for structured answers). No judge model.
- Temperature and seed preregistered; 3 samples per arm. Minimum graded count ≥15 of 20
  prompts per arm else INVALID. Hard call ceiling 1,320 in the driver.

## 4. Leakage and integrity controls (M2/M3 lessons)

Task/page/grader/mapping files outside the model cwd; no file tools; prompts carry only
task text and the ablated context, never a path or bank filename. Exact prompt→record map
frozen before call 1; per-item `START/OK/FAIL`, flushed stdout. Hard stop on
quota/auth/over-ceiling/tool-refusal/second-session; FAIL recorded, never retried. No raw
prompt/case body in reports; counts and ids only. Determinism scope: only the fold/grader
is byte-reproducible on one machine/build; hosted answers are stochastic (law 8). No
cost-saving claim (law 7).

## 5. Stop rule, falsifier, uplift, human gate

- Stop rule (§9.2): ablation interval overlaps matched-random → negative result.
- Falsifier: Δ(p) indistinguishable from random above the noise floor; corpus counts fail
  to reproduce; manifest mismatch.
- Downstream (not E2): Route B's ranker falsifier — a ranker trained on these labels must
  beat random ablation on held-out task success; a later cell.
- Capability uplift (Part II; Part III §8, agenda 8): include the harmful-task probe; a
  negative uplift check stops the route. Human gate on any policy/weight update (E2 ships
  no policy; it is measurement).

## 6. Procedure (on reopen only)

1. Phase 0 (offline, zero spend): build/verify the content-bearing bank; freeze
   prompts/pages/mapping/grader/manifest; verify no leakage and the grader self-test;
   record model snapshot and seed. Emit a Phase 0 card. Not a result.
2. Phase 1 (only after a fresh owner sign-off + smoke receipt): bounded interleaved
   runner, hard ceiling, counts before conclusions, `result.json`. Negative/inconclusive
   outcomes recorded with equal prominence.

## 7. Owner sign-off (required before any reopen Phase 1)

- Content-bearing fixture bank available + stratified on tool_recall: ______________________
- Model snapshot + route + cost ceiling (USD): ______________________
- Capability-uplift ruling: ______________________
- Deviation authority: ______________________
- Decision / date / owner: ______________________

Until every line is filled this is a parked design note, not a result; no call or spend is
authorized. No commit beyond this note's landing, no push, no plugin install, no wire or
corpus change. LOG row + day section owed to the review lane.
