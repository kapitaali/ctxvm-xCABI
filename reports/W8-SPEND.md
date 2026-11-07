# W8 spend ledger

Control variable for the $25 hard cap (design/w8-run-plan.md §6). One row per run:
date · arm · task · round · model · provider-receipt tokens · USD from the pinned price row ·
running total. The receipt columns are the provider's own numbers; cached reads are priced at
the input rate — an upper bound, labelled as one.

Model pinned: `gpt-6-luna` on provider `explabs`, catalogue row `OpenAI: GPT-6 Luna`
(`benchmarks/metrics/prices.json` v2, row-013, $0.10 in / $0.50 out / $0.01 cached per 1M).
No paid call has been made as of the row below.

| # | date | arm | task | round | model | in | out | cached | USD | run total | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-11-07 | both | t1 | 0 | gpt-6-luna | 0 | 0 | 0 | 0.0000 | 0.0000 | dry run: zero API calls, every assertion passed, checker=PASS |
