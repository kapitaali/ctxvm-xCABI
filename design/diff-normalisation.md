# Cross-harness diff normalisation — a consumer-side profile, proposed

**Status:** PROPOSAL-ONLY (no schema byte, validator byte, emitter byte, or capture behavior changes;
this file is input to a decision, healthy to reject). Waits on the reviewer's D13 verdicts of
2026-11-08 (Packet 1, recorded in `handoff/QUESTIONS.md` + PROJECT-STATE), relayed and cleared by the
owner. If any analysis ever shows a wire field is required, it opens an additive RFC-0.1 card with all
five touchpoints — no field is proposed today.
**Date:** 2026-11-08. **Evidence basis:** W5's classified cross-harness pair (`08-HANDOFF.md:970`,
`reports/RR-W5-20261030.md`), verified against the books by the packet flow the same day.

## 1. The problem (recorded, not new)

Raw `ctxvm diff` between the one-identical-task W5 pair diverges at event 0 — the classification
(08-HANDOFF.md:970) found:
D1/D2 tool vocabulary + args shape = harness-faithful minting + spec ambiguity (W7#1);
D3 hash divergence with matching refs under name canonicalisation (receipt bodies dominate tokens;
W7#2 page-body semantics);
D4 turn units 3 vs 1 = unit mismatch, hermes `pre_llm` once per user turn (W4 F2 confirmed live),
never behaviour (W7#3);
D6 page visibility granularity differences. The paper's Pillar-1 sentence (committed HEAD
`research/white-paper/white-paper.md:115`, working-tree WIP `:117`) claims "cross-harness … diffable"
outright; the reviewer verdict: replayable and conformance-testable are supported, "diffable" is not
supported as written — it needs this normalisation wrapped around it, and "reconstructs any turn
without knowing which harness" needs the within-trace qualifier.

## 2. Where normalisation lives: diff time, one side only

The adapters are faithful to their harness's vocabulary, and that faithfulness is a feature worth
keeping: canonicalising at capture would destroy it and would need a wire change. So normalisation is
a **versioned profile of mapping tables per harness consumed at diff time**. It needs no wire change;
only additive analysis could justify one (none shown so far — §5).

## 3. The profile rules (from the verdicts)

- **N1 — name and args canonicalisation** (W7#1): a RULE, consumer-side. Each profile carries a
  harness→canonical tool table and an args-shape normaliser (e.g. pathleness, id order). Applied to
  `logical_ref` for comparison only; the wire `page_id` is never rewritten (R2's law: pin/seed-style
  identity stays untouched).
- **N3 — turn unit mapping** (W7#3): a RULE. Per-harness units: opencode/ai-sdk = one per model
  request; hermes = one per user turn (`pre_llm` fires once per user turn — W4 F2, live-confirmed).
  CHECKED 2026-11-08: the RFC-0.1 `turn` field carries NO unit definition —
  `spec/rfc-0.1/x-cabi.schema-v0.1.json` types it `integer >= 0` with no description, and normative
  R5 ("`page.declare` gains an optional `turn` (integer >= 0)") likewise; so the profile must define
  the mapping itself. Turn alignment is per profile: a hermes user-turn maps to the first model
  request its group emits.
- **OP-N2 — page-body semantics** (W7#2): NOT a rule yet. Hashes are computed over harness-formatted
  tool output, so the same file can get different page IDs in two harnesses, and no diff-time rule
  fixes that without content. The verdict's options, adopted per its recommendation: **(a) now** —
  diff on `logical_ref` after N1, and report hash mismatches as their own divergence class
  (informatively, not as an error); **(b) canonical-hash additive field — DEFERRED** (owner-gated; it
  ties to the content-bearing capture decision in Part II §9.7); **(c) accept divergence** — the
  residual risk of (a).

## 4. Fail-closed and falsifiable

Unknown harness value in a profile lookup → the consumer refuses to diff (trusts nothing it cannot
map). Falsifier for the whole profile: a same-scripted-task pair whose events fail to align after
N1+N3 — since W5 classified every divergence of today's pair as harness-faithful, a misclassification
or a non-alignment would falsify the profile law, at W5-grade evidence.

## 5. Explicitly out of scope (this card mints nothing)

No capture-side canonicalisation; no schema/validator/emitter edit (§0 status); no new corpus drop;
no paid runs; no claim about "the same bytes" (the determinism law stays scoped to render geometry —
AGENTS.md 4-L8). Implementation into `ctxvm diff` (a `--profile` flag) is a FUTURE card, not this
proposal; this file is the law a consumer implements.

## 6. Open questions for the owner

1. Profile registry: how does a consumer learn which profile to load — session.open's
   provider/model/harness fields per the W5 D7/R2 evidence, or an explicit profile id?
2. N3 tie-breaks: confirm hermes `pre_llm`-per-user-turn placement rule against a live replay before
   any implementation card (RR-W4/W5 locators carry the pair).
3. OP-N2 (b): keep deferred until Part II §9.7 rules on content-bearing capture?
