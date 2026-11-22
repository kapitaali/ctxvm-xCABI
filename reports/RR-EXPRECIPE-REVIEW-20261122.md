# RR-EXPRECIPE-REVIEW-20261122 — verified: reviewer's experiment recipe; locator fixes and evidence boundary recorded

Review lane, verify-then-record. Subject: the reviewer's recipe for successful experiments (needle-revisit damage
curve) and five plugin-change proposals, delivered in chat 2026-11-22. No card was staged in the repo for this one;
the recipe is recorded here from the owner's paste. Zero spend, no calls, no engine/fixture/harness code written.
The reviewer explicitly said they had not seen the engine source, the fixture-bank code, or the harness — I record
that boundary rather than treating the design as verified.

## 1. Verified root-cause claims

| claim | source verified | result |
|---|---|---|
| outcome was generated text (E0 free-form answer, E2 answer-change flag) | `RR-E0RESULT`, `RR-E2PILOT-REVIEW` | confirmed — both instruments failed on the output, not the hypothesis |
| instrument never checked against a planted truth | the three E0 precondition failures (`RR-E0RESULT` 12/20, `RR-E0V3PILOT` 2/5, `RR-E0RETRY-RESULT` 3/5) | confirmed — pilots were gradability checks, not sensitivity/positive-control checks |
| product drops messages silently and emits no stubs | `reports/RR-W8CEVICT-20261111.md:13–21` ("this policy drops, it does not stub … no stub substitution anywhere in this engine"); `research/uncommitted/white-paper-Part-II_reviewed.md:79–91` §2.4 ("The live Hermes policy removes messages and emits no stubs") | confirmed from the cited cards/view — the reviewer's own note says this is an inference from those sources, not engine source, and I keep that boundary |
| Gate L passed on both local models | `RR-E0GATE1-20261120.md` (1.7B), `RR-E0RETRY-RESULT-20261122.md` (1.5B: `forced_byte_exact=True`) | confirmed — the logprob + byte-exact GBNF instrument half exists |

**Locator fixes (shorthand → real filenames):** `RR-W8CEVICT` → `reports/RR-W8CEVICT-20261111.md`;
`Part II §2.4` → `research/uncommitted/white-paper-Part-II_reviewed.md` (the `white-paper-Part-II.md` name cited
does not exist at repo root). Recorded so future readers don't hit dead pointers.

## 2. The design, recorded as a proposal (not authorized)

- **Fixture:** 36 synthetic 24-turn tasks (~8–9k tokens), tool-result key/value pages with near-duplicate distractors,
  one needle page stratified early/middle/late (12 each).
- **Readout (the key fix):** summed log-prob of the **gold value, forced** — deterministic, graded, no generation,
  no noise on a pinned build; plus a top-1 flag. This breaks the common-method circularity: the readout is no longer
  the model's own answer.
- **Stage 0 (instrument, $0):** full context ≥90% top-1; needle removal drops logP ≥3 nats and flips top-1 on ≥90%;
  random equal-size removal moves logP <0.5 nats on ≥90%; repeat identical. Any failure stops the run.
- **Stage 1 (policy damage, $0):** real engine keep law offline vs recency-only / random-middle / touch-aware /
  oracle / anti-oracle at 80/60/40% of full tokens; report damage by policy × budget × band.
- **Stage 2 (live recovery, free tier):** naive / drop / stub arms, 3 repeats, only if Stage 1 shows middle-band
  damage; accuracy vs gold, plus hard-fault counts and uncached input tokens (token counts, not a cost claim — law 7).
- **Decision table** (Stage 0 fail → fix instrument; Stage 1 damage → stubs default + touch pin; no damage → keep law
  safe for this shape; Stage 2 stub holds → paging validated first time; stub fails → new prereg for stub text/hint).

## 3. Plugin changes — proposals only, not routed

Shadow mode (log plan, no request change — also addresses n=4 hard faults with volume); stub-don't-drop; hold/
watermark selection (P8, plus the unverified "repositioned pages change the prefix every call" cache-miss suspect);
per-request cache columns + scaffold tokens + omission list (P12); seed `plugin.evictedTokens` so the checker rule
isn't dormant. `packages/hermes/**` is hermes-lane owned; I did not write any of it, and no lane routing was given.

## 4. Verified risks and my answer to "which first"

Risks as stated: small local model may not retrieve at 8–9k (Stage 0 gate G0a); the offline harness must call the
engine's selection with a synthetic message list (reviewer hasn't seen that code); E0's ~1 min/eval puts Stage 0 near
2.5 h and Stage 1 near 8–10 h in chunks; Stage 1 is an upper bound because a live agent might re-read (hence Stage 2).

**My recommendation: the preregistration card first, not the stub/shadow spec.** Reason: the recipe's whole point is
to freeze Stage 0's instrument gates *before* any hypothesis step, and Stage 0 runs at $0 on the existing local
models with no plugin change. Writing the plugin spec first would commit to code changes before the instrument is
shown to work — the exact ordering error the diagnosis (R2) identifies. If Stage 0 passes, the plugin spec is then
grounded in a validated instrument; if it fails, no plugin work is needed at all. This is a recommendation for the
owner's decision, not an authorization.

## 5. Scope and applied

Diagnosis/design only — no new experiment authorized, no call, no spend, no engine/harness/fixture byte, no push.
E0 double negative published, E2 closed, D17 held; research and dsh WIP untouched. Applied: this card, an append-only
LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261122.md`.
