# RR-SPEND-VERIFY-20261110 — the provider bill, and why my estimate was wrong

Card: cost verification against the provider's own usage export
(`experiments/usage-day-summary-a93f8b06-2026-11-10.csv`). Supersedes the projections in
`reports/W8-SPEND.md` §Reconciliation and the cost line in `RR-W8H6-20261109`.

## 1. The bill

The export is dated 2026-11-10 because the provider bills in UTC; the late-evening EET runs of
2026-11-09 fall into that day.

| model | requests | input | cache read | cache write | debited |
|---|---|---|---|---|---|
| openai/gpt-6-luna (6 keys) | 819 | 115,377,888 | 113,109,046 | 33,459,752 | **$7.0519** |
| deepseek-v4.1-flash-1017 | 14 | 2,292,727 | 1,784,832 | 0 | $0.0858 |
| free rows (beam, step) | — | — | — | — | $0.0000 |
| **day total** | | | | | **$7.1377** |

## 2. What that says about my estimate

I reported W8 at **$4.58** and projected a 48-cell grid at **$0.75–$5.39**. Both are wrong, and the
error is systematic rather than arithmetic:

**A. I omitted cache writes.** They are **29% of input tokens** on the day (33.5 M of 115.4 M) and
they are billed at roughly the input rate. Holding in/read/out at $0.10/$0.01/$0.50 per 1M, the
implied cache-write price per key is:

```
$0.164  $0.440  $0.125  $0.128  $0.125  $0.125      median $0.128 per 1M
```

Five of six keys agree at **$0.125–0.164** (the outlier is the key with 81 M input and only 3.1 M
writes, a different traffic mix). On the two heavy keys, cache writes alone are $1.3–1.5 — the bulk
of the bill, and the term my model did not have.

**B. I priced the plugin's receipts, and they are broken.** The reviewed H6 capture's
`providerUsage` sums to **36 input tokens across 13 calls** plus 190,520 cached. The provider billed
on the order of 15 k tokens per request for that traffic. Pricing from that field yields $0.003 for a
session that cannot have cost that. `providerUsage.inputTokens` is not a billing quantity until the
mapping is fixed.

**C. I trusted a ledger that was short.** The table said $1.4327; the store held $3.14 of unrecorded
driver attempts. A ledger built by hand will always lag the bill.

## 3. Corrected figures

Blended provider rate for the day: **$7.0519 / 819 requests = $0.00861 per request.**

```
one cell, 13 API calls                 $0.112
one cell, 20 API calls                 $0.172
one thrashing attempt (h7, 98 calls)   $0.844
48 cells × 2 arms × 13 calls           $10.75
48 cells × 2 arms × 20 calls           $16.53
48 cells, single arm, 13 calls          $5.37
```

The session store's W8-shaped sessions total **$8.98** across three profiles and several days
(default $2.45, w8-naive $1.69, w8-paged $4.83) — the multi-day figure, of which today's share is a
subset of the $7.14 bill.

So the honest position: W8 has cost **$7–9**, not $1.43 and not $4.58, and a full grid costs
**$10.75–$16.53** at the observed per-request rate — the $25 cap leaves about 1.5×, not the 5× my
projection implied. My earlier "$15.39" was closer to the truth than the "$0.75–$5.39" that replaced
it.

## 4. The rule this card earns

**Price from the bill.** `debited_usd` in the provider export is the only number that reconciles;
`providerUsage` and the session-store estimate are instruments with unknown calibration, and the
hand ledger is a convenience that must be reconciled against the bill or dropped.

For each cell: take the key's `debited_usd` before and after; the delta is the cell's cost. One key
per arm makes that attribution exact. Until the export is per-hour (the file name says "day"), the
snapshot delta is the closest thing to a per-cell receipt.

## 5. Consequences for the plan

1. **A call ceiling belongs in the driver** (20 calls), because at $0.0086 per request the calls are
   the cost, and h7–h9 show what an uncapped loop does: 440 calls, $3.14.
2. **Do not run 48 cells at this rate without a decision.** $10.75–$16.53 against a $25 cap leaves no
   room for a re-run after a defect.
3. **Consider a cheaper subject model for the shape runs** and keep Luna for the cells that count.
4. **Fix `providerUsage.inputTokens`** before any cost claim is made from a trace; today's value makes
   the trace look free.
