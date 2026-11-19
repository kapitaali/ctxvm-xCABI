# PREREG-E0-DRAFT-20261119 — open-weight page ablation (Route B primary)

**Status: PARKED on open-weight model snapshot & compute-route ruling — owner ruling
RR-E0ENRICH-20261119, $0 spend. NOT a runnable preregistration.** No model call, no spend,
no commit beyond this note's landing authorized. Compute-only by design (no API spend), but
it cannot run without an open-weight model snapshot + a GPU compute route (owner decisions).
Authority: Part III §9.0 (E0) and Route B; **Part II §12.1 is the protocol of record — this
note cross-references it and only instantiates parameters, it does not fork it.** Data:
`research/fixture-bank/` **v2** (2-hop enrichment, RR-E0ENRICH-20261119). Nothing here is
pooled with E1, E2, M1, M2 or M3.

## 0. Question and hypothesis

Part II §12.1 hypothesis: pages with a high identifier-touch count have more causal
influence on the next action than matched pages with a low count. Part III §9.0 question:
does page-level causal importance beat matched random ablation?

H1: touch count predicts leave-one-out ablation effect (positive rank correlation), and
targeted leave-one-out beats matched-random ablation. H0: no correlation / no difference.

## 1. Data (fixture bank v2, 2-hop causal chain)

- 20 items (`fb01–fb20`), each with **10 `file` pages** (the primary ablation set, matching
  §9.0's "10 pages per trace") plus 1 `tool_result` recall target scored separately (§5).
- **2-hop chain:** `target.md` (the `tool_recall`-faulted page) holds `target_threshold = 42`
  and numeric pointers `primary_document = j1`, `fallback_document = j2` (varied, distinct,
  per item). The setting values `doc<j>_value = <val>` and reference tags `<topic>-doc-<j>`
  live **only** inside `doc-<j>.md`. The prompt asks for the primary page's value **and** tag
  and the fallback page's value only — so answering requires visiting `doc-<j1>` and
  `doc-<j2>` (a genuine 2-hop dependency, not answerable from `target.md` alone).
- τ and τ\p are actual text via `buildContext(item, excludeRef)`. Frozen by
  `research/fixture-bank/manifest.sha256`. Phase 0 verifies a deterministic `referenceAnswer`
  per item (never exposed in τ or the trace) yields a **3-tier touch count** T(p) ∈ {2,1,0}
  with Var(T) > 0 (442/442 checks, BANK_PHASE0_OK).
- All 10 file pages per item are `kind=file`, `tokens=76` (uniform): the §12.1 "matched on
  kind and token count" control is well-defined but degenerate (any file page matches any
  other). Recorded as a limitation.

## 2. Model and compute (OWNER DECISION — not chosen here)

- **One frozen open-weight snapshot** with per-token log-probability access. Name,
  revision/hash, tokenizer, inference settings frozen in Phase 0 once the owner names the route.
- Compute route: local GPU marginal (GTX 1050 Ti, 4 GB); cloud GPU is a real cost needing an
  owner ceiling. **No model is called until this is ruled.**
- Reference decoding: **greedy** (deterministic on one machine/build); baseline-repeat
  confirms the noise floor.

## 3. Arms (Part II §12.1; interleaved across items)

1. **Baseline** — generate a(τ) per item (20 runs).
2. **Baseline repeat** — noise floor (20 runs).
3. **Leave-one-out per page** — score a(τ) under τ\p for each of the 10 file pages (200 runs).
4. **Matched random page** — remove a different uniformly-sampled file page (same kind/token
   count), seeded per item (200 runs).

≈ 440 open-weight evaluations; interleaved so a compute failure cannot concentrate in one
arm; hard evaluation ceiling in the driver; no retry.

## 4. Metrics (frozen definitions) + constant-T degeneracy guard

- **Ablation effect** Δ(p) = mean per-token log-prob of the teacher-forced baseline answer
  a(τ) under τ minus under τ\p. Larger Δ ⇒ p more causally important (requires log-prob access).
- **Touch count** T(p) = number of distinct identifier tokens of page p appearing in the
  model's actual a(τ). **Identifier rule (frozen):** the page's reference tag
  `<topic>-doc-<j>` and setting name `doc<j>_value`, whole-token, case-insensitive; hashed
  into the Phase 0 manifest. (The bank's `referenceAnswer` guarantees the bank *can* yield
  Var(T) > 0; the model's actual a(τ) is what is scored at run time.)
- **Primary (§9.0):** Spearman rank correlation between T(p) and Δ(p) across the 10 file
  pages, per item; **bootstrap CI over the 20 items**. Unit: correlation coefficient.
  20 items ⇒ wide interval; **report it, no significance claim**.
- **Constant-T degeneracy guard (RR-E0ENRICH):** if a model's a(τ) yields **zero variance**
  in T(p) across an item's 10 file pages (e.g. an uncooperative or empty generation), that
  item's correlation is **NOT** evaluated as `NaN`. It is counted **ungradable** against a
  minimum graded threshold: **≥ 15 of 20 items must have Var(T(p)) > 0**, else the run is
  **`INVALID — constant T`** (no result). This fixes the v1 degeneracy where every item was
  0/0 = NaN.
- **Secondary tie-safe contrasts (reported alongside, robust to ties/constant T):**
  mean Δ(p) on pages with T(p) > 0 vs T(p) = 0; and mean Δ(p) on the ground-truth causal set
  {p_j1, p_j2} vs the 8 distractors. Plus §12.1 pair ablations on the top pages and
  page-then-span vs flat leave-one-out agreement.

## 5. The 2-hop causal profile and the tool_result probe

- **Causal necessity (structural, verified offline in Phase 0):** removing `p_j1` removes
  two required facts (Δ(p_j1) > 0); removing `p_j2` removes one (Δ(p_j2) > 0); removing
  `target.md` removes `target_threshold` and both pointers (Δ(p_target) > 0); removing any of
  the 8 distractor file pages removes no required fact (Δ(p_k) ≈ 0). On the referenceAnswer
  this gives T(p_j1) = 2, T(p_j2) = 1, T(p_k) = 0 — Var(T) > 0 by construction.
- **The 11th page (`tool_result` recall target)** is the answer-pointer probe: it has no
  same-kind match within an item, so it is **excluded from the matched primary comparison**
  and reported separately (its Δ shows the pointer/threshold source's influence).
- **v1 → v2 history:** bank v1 (12a9809) put both answers directly in `target.md` and never
  asked for any file-page token, so a faithful answer gave T(p) = [0,…,0], Var(T) = 0, and
  Spearman ρ = 0/0 = NaN on every item. The review lane formalized this (RR-E0ENRICH §1);
  v2's 2-hop chain removes the degeneracy. Recorded, not hidden.

## 6. Stop rule, falsifier, noise floor

- **Stop rule (§9.0):** the correlation CI includes zero → **negative result**.
- **Falsifier:** T(p) does not predict Δ(p); or leave-one-out Δ indistinguishable from
  matched-random; or < 15/20 items gradable (`INVALID — constant T`); or bank manifest fails.
- **Noise floor:** baseline-vs-baseline Δ under greedy (expected ≈ 0 on one build); any
  non-zero floor reported and subtracted before interpretation.

## 7. Controls and integrity

- Frozen bank manifest + model snapshot + identifier rule + seed + prompt→page mapping before
  any evaluation; per-item `START/OK/FAIL`, flushed output; counts before conclusions.
- No leakage: model input is τ text only; `referenceAnswer` never in τ or the trace (Phase 0
  asserts both); no bank/sandbox paths in model input.
- Determinism scope: only the fold/scoring is byte-reproducible on one machine/build;
  open-weight generation deterministic only under greedy on a fixed build (law 8 scope).
- **No cost-saving claim** (law 7); GPU cost is real and owner-bracketed, not a saving. No
  model-quality claim beyond this synthetic task.
- Capability-uplift probe (Part III §8, agenda 8); human gate on any policy/weight update
  (E0 ships no policy; it is measurement).

## 8. Procedure

1. **Phase 0 (offline, zero spend, zero model call):** freeze model snapshot name/hash,
   tokenizer, identifier rule, grader, seed, prompt→page mapping; verify τ\p, the bank
   manifest, and the 3-tier touch profile; emit a Phase 0 card. Not a result.
2. **Phase 1 (compute; only after owner compute-route ruling + GPU ceiling):** bounded
   interleaved open-weight runner with the constant-T guard; `result.json`; negative and
   inconclusive outcomes recorded with equal prominence.

## 9. Owner sign-off (required before Phase 1)

- Open-weight model snapshot + revision/hash + tokenizer: ______________________
- Compute route + GPU cost ceiling: ______________________
- Capability-uplift ruling: ______________________
- Deviation authority: ______________________
- Decision / date / owner: ______________________

Until every line is filled this is a parked design note, not a result; no model call or spend
is authorized. No push, no plugin install, no wire/corpus change. LOG row + day section owed
to the review lane.
