# PREREG-NEEDLE-20261122 — needle-revisit damage curve (DRAFT, frozen before any run)

**Status: DRAFT. Zero model calls, zero spend, no commit.** Built from the reviewer's recipe
(read out a deterministic graded quantity, plant a truth with controls, force the gold string,
freeze instrument gates before any hypothesis step, run the product's own code path, bracketed
predictions). This card is the preregistration; the fixture/harness spec is a companion.
Nothing here is an E0/E2 retry — those are closed. No pooling with any prior experiment.
Authority: owner "draft it" 2026-11-22. No call or spend authorized by this card.

## 0. Why this design (the diagnosis it answers)

All eight prior attempts failed on instrument properties, not hypotheses: generated text as
the outcome (E0 identifier tokens, E2 answer-change), no planted-truth check, and a mismatch
between the hypothesis and the product (the live engine drops silently with no stub, so no
fault/re-fetch can occur). This design fixes all three: graded logprob readout of a **forced
gold value**, a planted needle with positive/negative controls, and Stage 1 runs the real
engine's selection on synthetic messages.

**Related-work boundary (literature scan 2026-11-24).** Recoverable placeholders are not new:
DTOC uses external tool-output storage plus compact placeholders and an explicit enable/disable
tool (arXiv:2609.26121, method §3.1–3.3); Scroll uses an append-only Event Log plus an eviction
index with stable addresses (arXiv:2608.21690, §2.2–2.4); ACM uses `manage_context` and
`query_memory` tools (arXiv:2607.23809, §3). FOCUS defines retention utility by counterfactual
future-trajectory divergence, not by later mention alone (arXiv:2609.37590, §3–4), and CoMem
shows that retained evidence is query-dependent (arXiv:2611.16384, §2.1–2.2). The distinct
question here is therefore **whether ctxvm's actual keep law damages a planted answer, and
whether its trace can attest recovery**, not whether recoverable stubs are novel.

## 1. Fixture (new, zero-spend to author)

- **36 synthetic tasks**: each a 24-turn trace ≈ 8–9k tokens, tool-result pages of key–value
  lines plus near-duplicate distractor keys. A final question asks one key's value; the answer
  sits on exactly one page — **the needle**. Size is shrinkable for CPU speed (record the
  shrink and re-freeze if changed).
- **Stratify needle position**: early (protected head), middle, late (protected tail), 12 tasks
  each. The head/tail bands are defined by the engine's own keep law
  (`protect_first_n=3, protect_last_n=6`, `context_engine.py:322,831`).
- **No raw prompt/case text in reports** (law 9): reports carry ids, counts, logprobs, bands.

## 2. Readout (deterministic, graded)

- Primary readout: **summed log-probability of the gold value string, with the gold forced**
  via GBNF (same mechanism Gate L already validated — byte-exact forced text, per-token
  logprobs, on both local models). No generation, no noise on the pinned build.
- Secondary: top-1 flag on the gold value (does the forced token rank first).
- This is the instrument: the outcome is a number from the model's *conditioned logprob*, not
  text the model chose to emit.

## 3. Stage 0 — instrument gate ($0, must PASS before anything else)

Contexts and forced-gold calls, four conditions per task: full context; needle removed;
random equal-size page removed; repeat. **Frozen thresholds (proposed by reviewer, adopt as
written unless owner changes before first call):**

| check | frozen gate |
|---|---|
| full-context top-1 | ≥ 90% of tasks |
| needle removal | drops summed logP by **≥ 3 nats** AND flips top-1 on ≥ 90% |
| random equal-size removal | moves logP **< 0.5 nats** on ≥ 90% |
| repeat | byte-identical logP (no variance) |

**Any failure ⇒ STOP.** The model or context length is wrong; fix the instrument and learn
nothing else. No re-scoring, no threshold relaxation after seeing numbers (anti-fishing).
Record the exact model hash, tokenizer, build, thresholds and observed values in the gate card.

## 4. Stage 1 — policy damage curve ($0, offline, runs the product's code path)

- **Harness:** drive the real `CtxvmFaultPinEngine(v_budget=…, protect_first_n=3,
  protect_last_n=6, selection_mode='fresh')` from `packages/hermes/live/context_engine.py`
  with a synthetic message list; `select_context()` returns the retained request; the gold
  logP is then scored on each retained context by the Stage 0 instrument. (The reviewer hadn't
  seen this code — verified here: constructor line 322, `select_context` line 422,
  `_budget_decision` line 900 returns dropped/repositioned/facts.)
- **Policies:** keep law (real engine); recency-only; random-middle; touch-aware (keep pages
  referenced later); oracle; anti-oracle.
- **Budgets:** 80%, 60%, 40% of full tokens.
- **No gate** — report damage (logP drop, top-1 loss) by policy × budget × needle band.
- This is an **upper bound** on damage: in a live loop an agent might re-read, which is why
  Stage 2 exists.

## 5. Stage 2 — live recovery (free tier, conditional only)

- **Run only if Stage 1 shows damage in the middle band at budgets the engine actually engages.**
- Arms: naive (no engine), drop (current engine), stub (new stub arm), same tasks, 3 repeats.
- **Stub arm:** replaces a dropped tool result with a short recoverable stub — name, arguments,
  "re-run to restore." This is a plugin change (companion spec), not in this prereg's scope.
- Outcome: accuracy against the gold value, paired by task.
- Also reported: hard-fault count and uncached input tokens from free-tier usage counters —
  **token counts, not a cost claim** (law 7).

## 6. Predictions with units and brackets (ratified rule)

Written before any run; each is a bracket, not a point claim:

- **P1 (Stage 0 instrument, if gates set):** full-context top-1 90–100%; needle-removal logP
  drop 3–8 nats; random-removal |ΔlogP| 0–0.5 nats.
- **P2 (Stage 1 keep law, middle band):** at 60% budget, keep-law logP drop within 0–2 nats if
  the keep law protects the needle; 2–6 nats if it does not. (Direction is what Stage 1 decides;
  the bracket is the resolution this design can achieve.)
- **P3 (Stage 1 oracle vs anti-oracle):** oracle damage ≤ keep law ≤ anti-oracle in ≥ 2/3 bands
  — a sanity-ordering check, not a hypothesis.
- **P4 (Stage 2 stub):** stub accuracy ≥ drop accuracy on paired tasks; hard-fault count > 0 in
  the stub arm if re-fetch occurs. No magnitude claim before Stage 1.

## 7. Result → action table (recorded, not executed)

| result | change |
|---|---|
| Stage 0 fails | Fix instrument (model/context). Nothing else learned |
| Stage 1 damage in middle band at engaged budgets | Add recoverable stubs as default + touch pin |
| Stage 1 no damage anywhere | Keep law safe for this shape; say so |
| Stage 2 stub holds accuracy + shows faults | Paging mechanism validated for the first time |
| Stage 2 stub fails to re-fetch | New prereg for stub text / fault hint |

## 8. Integrity and stop rules

Frozen gates before any hypothesis step; a failed gate stops the run. No generation-based
score, no post-hoc threshold change, no re-scoring, no pooling. Hard call ceiling per stage;
`START/OK/FAIL`, flushed output, counts before conclusions. Reports carry counts, ids, logprobs
and bands only. No cost-saving (law 7), no model-quality, no unscoped-determinism (law 8) claim.
Timing reality from E0 (~1 min/eval): Stage 0 ≈ 2.5 h, Stage 1 ≈ 8–10 h — chunked, with a
separate go-ahead between chunks.

## 9. Owner sign-off (blank until ruled)

- Approve fixture (36 tasks, 12 per band) and any size shrink: ______________________
- Adopt Stage 0 frozen thresholds as written: ______________________
- Approve Stage 1 offline harness using the real engine on synthetic messages: ______________________
- Stage 2 authorization (separate, conditional on Stage 1): ______________________
- Deviation authority / decision / date / owner: ______________________

Until signed, this is a design, not an experiment; no call or spend. Staged via `copy-staging.sh`;
no push, no plugin change. LOG row + day section owed to the review lane if landed.
