# RR-E2PILOT-MODEL-20261121 — owner names gpt-6-luna as the E2 pilot model (partial sign-off)

Owner decision 2026-11-21: **"you can add gpt-6-luna as the model"** — this fills the *model* line of the staged
`RR-E2PILOT-PLAN-20261121.md` §7 sign-off, under the $3-ceiling authorization in `RR-E2PILOT-AUTH-20261121`
(`373e01f`). Review lane, verify-then-record. No call, no spend, no landing, no runner by this lane.

## 1. Verified configuration (no key value recorded)

| item | verified from | value |
|---|---|---|
| model id | `~/.config/opencode/opencode.jsonc:214` | `gpt-6-luna` (name `gpt-6-luna`, context 1,050,000, output 128,000) |
| provider | same config, `provider.explabs` | `@ai-sdk/openai-compatible`, base URL `https://api.experientiallabs.ai/v1`, `apiKey` from `EXPLABS_API_KEY` |
| key presence | shell test, **value hidden** | `EXPLABS_API_KEY` is **SET** in this shell |
| list price | `benchmarks/metrics/prices.json` catalogue | row-013 `GPT-6 Luna`: input $0.1 / output $0.5 / cached-read $0.01 per 1M tokens |

## 2. Caveats that keep this short of a call

- **Route tension:** the staged plan records Explabs as credit-exhausted ("Explabs no credits"), yet `gpt-6-luna`
  is configured on that route. I did not test the route or spend anything. The **dual-gate smoke** is exactly the
  empirical test: it must (a) succeed on the route and (b) return `debited_usd`. If either fails, stop and re-rule
  (`RR-E2PILOT-AUTH-20261121`), never fall back to `providerUsage`.
- **List price ≠ per-request rate.** The $0.1/$0.5 per-1M rates do not fix the smoke rate; the $3 ceiling's
  ~$0.35 expected figure rests on the historical blended Luna rate $0.00861/req (`W8-SPEND:82`), which is
  UNVERIFIED for E2's actual calls. Only the smoke receipt's `debited_usd` sets `r`.
- **Revision/hash:** the sign-off asks for a model *revision/hash*, not just an id. `gpt-6-luna` is a route alias; I
  have no pinned revision for it. The smoke record must capture whatever the provider reports as the exact model
  revision, or flag it UNVERIFIED.
- **Still blank in §7:** route/API-key *source* confirmation (implied Explabs, not explicitly signed),
  capability-uplift ruling, deviation authority, decision/date/owner. These are owner-only.

## 3. State

The staged plan is **not landed** (`reports/RR-E2PILOT-PLAN-20261121.md` absent); owner-run `copy-staging.sh` not
run by me. E2 remains HELD at $0 until the remaining lines are filled and the plan is landed; **no model call or
spend is authorized by this card alone**. Research lane's v3 bank WIP and staged prereg fold-in preserved.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261121.md`.
