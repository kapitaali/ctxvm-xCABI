# RR-E2PILOT-ROUTE-20261121 — owner rules route: NOT Explabs; Nous or OpenRouter (model/route conflict surfaced)

Owner decision 2026-11-21, verbatim: **"do not use explabs but nous or openrouter"** — this overrides the implied
route from `RR-E2PILOT-MODEL-20261121.md`, which had verified `gpt-6-luna` as configured under the `explabs`
provider. Review lane, verify-then-record. No call, no spend, no config edit, no push.

## 1. Verified state (values hidden where credentials are involved)

| item | verified | implication |
|---|---|---|
| configured providers in `~/.config/opencode/opencode.jsonc` | **only `explabs`** (line 31) — no `nous`, no `openrouter` block | the chosen routes are **not configured** in this harness |
| `gpt-6-luna` location | only in the `explabs` provider block (line 214) | the named model is **not available** on either permitted route as configured |
| `OPENROUTER` env var | present, key-shaped (value hidden); no `OPENROUTER_API_KEY` / `NOUS_API_KEY` | an OpenRouter credential exists in env but is not wired into any configured provider |
| plan's recorded route status | "free routes are quota-exhausted (Zen 429; Explabs no credits; **Nous direct 401**)" (`RR-E2HOLD`, staged plan §2) | Nous is recorded as an **auth failure**, not a working paid route |

## 2. The conflict — not silently resolved

The owner's two rulings combine into an unresolvable tuple as things stand:

- **model:** `gpt-6-luna` (`RR-E2PILOT-MODEL`) — configured **only** under Explabs, which is now forbidden.
- **route:** Nous or OpenRouter — Nous recorded 401; OpenRouter has a key in env but no provider config and no
  verified `gpt-6-luna` availability.

I did **not**: edit `opencode.jsonc` to add a provider, assume OpenRouter carries a model literally named
`gpt-6-luna`, test either route, make a smoke call, or spend. Doing any of those would be inventing a config and a
model mapping the owner has not specified.

## 3. What is needed before any call (owner inputs)

1. **Which of the two routes** — Nous *or* OpenRouter (the ruling says "or"; I need one named).
2. **Provider config** — a provider block for that route (base URL + key source); OpenRouter's `OPENROUTER` env var
   is present but unwired; Nous has no key/config found and is recorded 401.
3. **Model id on that route** — whether `gpt-6-luna` exists there under that exact id, or the route's actual id for
   that model. If the model cannot be had on either permitted route, the owner must re-name the model.
4. The remaining §7 sign-off lines from `RR-E2PILOT-AUTH` (uplift, deviation authority, decision/date/owner) and
   landing of the staged plan (`copy-staging.sh`) — both still outstanding.

## 4. Standing limits unchanged

The $3 ceiling, dual-gate smoke (route success **and** `debited_usd`, else stop/re-rule, never `providerUsage`), and
the frozen PASS/FAIL rules from `RR-E2PILOT-AUTH-20261121` stand. E2 remains HELD at $0 until the conflict is
resolved and every sign-off line is filled. No model call or spend is authorized by this card alone.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261121.md`.
