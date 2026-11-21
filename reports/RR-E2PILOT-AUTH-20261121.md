# RR-E2PILOT-AUTH-20261121 — owner authorizes the E2 answer-change pilot at a $3 ceiling, with a dual-gate smoke

Owner decision 2026-11-21, verbatim: **"authorise your recommendation"** — my recommendation was to sign the
staged `RR-E2PILOT-PLAN-20261121.md`'s hard **$3** ceiling for the smoke + 40 pilot calls, with one addition: the
smoke call is a **dual gate** (it must both fix the real per-request rate *and* actually expose `debited_usd`), and
the frozen anti-fishing PASS/FAIL rules stand.

Review lane, verify-then-record. No call, no spend, no landing of the staged file, and no runner implementation by
this lane. Date 2026-11-21.

## 1. What is authorized

- **The $3 pilot ceiling** — hard cap for 1 smoke call + 40 pilot calls (5 items × 8 calls), with the §3.2 stop-if
  (`41 × r > $3` → stop and re-rule; never drop items/conditions to fit).
- **The dual-gate smoke (my addition):** the first hosted call must expose a `debited_usd` receipt. If the chosen
  route does not return `debited_usd`, **stop and re-rule** — do **not** fall back to `providerUsage`, which
  `RR-SPEND-VERIFY-20261110:37,69` records as an uncalibrated instrument, not a billing quantity.
- **The frozen decision rules** from the staged plan: PASS = ≥4/5 clean targeted changes **and** pooled targeted
  answer-change rate > matched-random rate; FAIL = anything less → stop, no grader broadening, no re-labeling of
  "change", no re-scoring, no model switch without a fresh ruling. Record FAIL with equal prominence.
- **Full-cell boundary:** the ~1,320-call / ~$11 full E2 cell is **not** authorized. PASS only authorizes a
  *proposal* for a separate ruling re-derived from the smoke receipt. The $3 ceiling and the E0 $5–10 GPU ceiling
  are distinct; neither transfers.

## 2. What is NOT authorized — the blocking gap

The staged plan's §7 sign-off lines remain **blank**. A pilot cannot run until the owner names:

- **hosted model snapshot + revision/hash** (free routes are exhausted: Zen 429, Explabs no credits, Nous 401);
- **route + API-key source** — note `~/.config/opencode/opencode.jsonc` configures an `explabs` provider
  (`@ai-sdk/openai-compatible`, base URL `https://api.experientiallabs.ai/v1`, key from `EXPLABS_API_KEY`), but the
  plan records that route as credit-exhausted; I did not verify key availability or make a call;
- capability-uplift ruling, deviation authority, decision/date/owner.

**No model call or spend is authorized by this card alone.** The dual-gate smoke is the first thing that would run
once those lines are filled, and it is itself the test of `debited_usd` availability.

## 3. Landing state (verified)

- The staged plan lives at
  `/home/theb/Documents/deepseek-harness/default-workspace/tb-dsh-smoke-20261117/staging/reports/RR-E2PILOT-PLAN-20261121.md`
  (7,045 B) and is **not** in the repo (`reports/RR-E2PILOT-PLAN-20261121.md` absent). Landing is the owner-run
  `copy-staging.sh`; I did not run it.
- Its anchor was verified earlier: the committed v2 bank at HEAD `8b139d6` has sha `cba643d2ef105d744786…`,
  matching the plan's claim; `research/e2-proposal/PREREG-E2-DRAFT-20261119.md` remains PARKED at $0.
- I preserved the research lane's uncommitted v3 bank WIP and staged prereg fold-in through this commit.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261121.md`. No
`research/**` byte by review, no code, no model call, no spend, no push.
