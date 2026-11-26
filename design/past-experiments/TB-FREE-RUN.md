# T-B free-tier run — Hermes free models, $0, phases 1 through 3

**Owner instruction, 2026-11-16:** call free models, and specifically **Hermes** free models — the ones the
gateway already serves — not third-party ones. This is the run plan for that, not a new experiment design:
`design/past-experiments/TB-PLAN.md` remains the plan of record for what is measured; this file fixes *what runs it*.

## 1. The subject

| Item | Value | Where it comes from |
|---|---|---|
| provider | `nous` (the owner's own gateway) | `hermes config get model.provider -p w8cn-naive` |
| model | **`meituan/longcat-2.5:free`** | `hermes config get model.default -p w8cn-naive` |
| arms | `w8cn-naive` (compressor) / `w8cn-paged` (ctxvm, **60000**) | both profiles, toolsets `[file]` |
| fallback subject | `stepfun/step-3.7-flash:free` (same provider, same profiles, one `config set`) | the runner's `nous` provider note |
| price | **$0 by tier.** No `prices.json` row names this model, so any cost figure would rest on the tier's word | `benchmarks/metrics/prices.json` |

Nothing about the profiles changes: the pair is reused, not created (the runner refuses to create), and
`budgetTokens: 60000` is the treatment. The fixture is 48 × 600 CSV rows, C = 107,867 tokens, F ≈ 27.7 k.

## 2. The sequence, with a stop at each step

| Phase | Calls | What runs | Stops when | Cost |
|---|---|---|---|---|
| **1** | 1 per arm | capability probe — can the model drive `read_file` on `fixture/data-01.csv` | no `read_file` in the trace, or a refusal marker | $0 |
| **1b** | 3 | **naive arm only**, `--limit 3`, replies scored by `tb-check --per-reply` | fewer than 2 of 3 replies exact → the shape is too hard for this model, and no paged cell is bought | $0 |
| **2** | 1 per arm | attestation: sidecar carries `enginePlan`, a reason in the closed set, a non-null `enginePlanTally`; control evictions exactly 0 | `enginePlan` absent or mistyped (instrument-blind, the W8B class) | $0 |
| **3** | ~100 per arm | R=3 interleaved rounds of the full 49 prompts | any hard stop (§4) | $0 |

Phase 1b is the important one. T-B's per-prompt work is arithmetic over 600 rows; longcat is a free flash
model, and arithmetic is exactly what killed T-A v1 (180 s on nvidia, 283 s of silence on longcat). Three
prompts decide whether a paged cell is worth anything, and three prompts cost nothing.

## 3. What the run must produce, even if it fails

- a capture per arm (or `NO RECORD`, named as such),
- `per-reply` accuracy per arm and the three lookup answers,
- `enginePlan.reason` counts per arm,
- and a verdict from the taxonomy: NO-OP / ARTEFACT-FAIL / CEILING / CELL, or DATA-INVALID out of the
  denominator.

A refusal, a timeout, or a NO-OP is a **result to record**, not a card to retry until green.

## 4. Hard stops

Any of these ends the run and the day's card, in the repo's own words: a prompt past the timeout cap; repeated
"does not exist" tool errors; auth 401/429; **any charge** (a free-tier run that bills is aborted, not
explained); NO RECORD on either arm; a context refusal near 90k (reduce the file count, never the budget);
`enginePlan` absent at phase 2.

## 5. What has to exist before prompt 1

1. `tools/w8b-run.py --limit N` — the runner does not forward a prompt limit today, and phase 1b needs
   three files without the other 45. Small, mechanical, and it must not change the T-A v2 path.
2. A dry run per phase (`--dry-run`) proving preflight: profiles, toolsets, budget 60000, 48 `data-*.csv`
   in `ws-tb-{arm}`, no stale artefact, checker present.
3. The instrument check of `TB-PLAN.md` §8.3: a diagnostic capture that carries `enginePlan`. The gateway
   holds 0.13.24 and a real capture already reads it, so this is a confirmation, not a build.

## 6. What this cannot prove, stated before it runs

- One free model, one shape. A result on longcat says nothing about a paid model's behaviour, and the
  cost claim (H2/P19/P20) needs the paid pair in phase 4, which stays owner-gated at a $1.00 cap.
- Free-tier limits are not the provider's limits: a rate-limit stop is an account fact, not a finding.
- If phase 1b fails, the record says "this shape is too hard for this model", and the honest next move is a
  smaller per-prompt workload — not a rerun on the same shape until it passes.
