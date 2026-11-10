# RR-SPEND-RECON2-20261110 — C5: what W8 actually cost, and what cannot be known

Zero spend. Sources: `hermes sessions` stores (three profiles), the one provider export on disk
(`experiments/usage-day-summary-a93f8b06-2026-11-10.csv`), and the ledger.

## 1. Days on which W8 calls were made

```
UTC day     W8-shaped sessions   session-store estimate
2026-11-07          10                 $3.8463
2026-11-09          20                 $1.9903
2026-11-10           5                 $3.3231
                            total      $9.1597
```

## 2. Provider exports on disk

```
2026-11-10   present   ->  $7.1377  (Luna $7.0519 / 819 req, DeepSeek $0.0858)
2026-11-07   MISSING
2026-11-09   MISSING
```

## 3. The true cumulative spend is UNKNOWN

- The one bill we have ($7.1377) covers a single UTC day and is **2.1× the store's estimate for that
  day** ($3.3231). The store prices from its own table and omits cache writes; it is not a bill.
- Two of the three days have no export. Extrapolating the bill/store ratio to them would be an
  invention, not a measurement.

**Statement of record: W8 has spent at least $7.14 (billed, 2026-11-10) and the store estimates $9.16
across three days. The cumulative figure is UNKNOWN until the 11-07 and 11-09 exports exist.**

## 4. Consequences

1. The "USD 23.8459 left" line in `handoff/PROJECT-STATE.md` is **UNVERIFIED** and should be marked so;
   at ≥ $9 spent the remaining cap is ≤ $16, not $23.64.
2. Any grid decision must use the remaining-cap figure, which cannot be stated until the exports land.
   That is an owner action: download the 11-07 and 11-09 exports.
3. The ledger in `reports/W8-SPEND.md` is a convenience. It has been wrong twice today (short by
   $3.14, then short by the cache term). It should be reconciled against a bill or marked as
   indicative.

## 5. Data missing

- exports for 2026-11-07 and 2026-11-09
- per-key mapping from a JWT to a profile (the export carries keys, not profiles; six Luna keys exist)
- whether the store's `estimated_cost_usd` includes cache writes at all (evidence says no)
