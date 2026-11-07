# W8 spend ledger — grid

Control variable for the $25 hard cap (design/w8-run-plan.md §6), cumulative across the card.

carried forward: $0.5161 (7 rows, archived in reports/W8-SPEND-pilot-20261107.md)

One row per cell: date · arm · task · round · model · receipt tokens · USD from the pinned row
· running total. A cell writes a STARTED row before its first API call and is settled when it
ends; a STARTED row older than the cell ceiling is reconciled to ABORTED on the next run, so a
killed cell can never vanish from the record. Cached reads are priced at the catalogue's cached
rate; uncached input is prompt minus both cache buckets (the double-priced version overstated a
run 7.8× — measured 2026-11-07).

| # | date | arm | task | round | model | in | out | cached | USD | run total | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-07 | naive | t1 | 1 | openai/gpt-6-luna | 24802048 | 169443 | 24552150 | 0.3303 | 0.8464 | n/a; coverage ok; replay exit 0, byte-identical |
| 2 | 2026-11-07 | naive | t1 | 1 | openai/gpt-6-luna | 24248569 | 135061 | 24016030 | 0.3077 | 1.1541 | n/a; coverage ok; replay exit 0, byte-identical |
