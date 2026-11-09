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
| 2 | 2026-11-07 | naive | t1 | 1 | openai/gpt-6-luna | 24248569 | 135061 | 24016030 | 0.3077 | 1.1541 | ABORTED 2026-11-07T17:07Z: arm witness mismatch (engine=ctxvm, profile=.hermes under -p w8-naive); no artefact, max_iterations 150/150; USD 0.3077 spent, cell is not data (RR-W8CHUNK-20261107-2) |
| 2026-11-09 | naive | T-A | 1 | openai/gpt-6-luna | 73392 | 2740 | 57564 | 0.0039 | 1.1626 | PILOT execute_code shortcut; checker PASS; not a cell |
| 2026-11-09 | paged | T-A | 1 | openai/gpt-6-luna | 448446 | 6534 | 83766 | 0.0497 | 1.2123 | PILOT engineSelections 0; checker PASS; not a cell |
| 2026-11-09 | naive | T-A | 1 | openai/gpt-6-luna | 336358 | 3231 | 227410 | 0.0175 | 1.2298 | cell pair2-1 -t file, selections 14 (shared caveat) |
| 2026-11-09 | paged | T-A | 1 | openai/gpt-6-luna | 1057053 | 7607 | 83042 | 0.1264 | 1.3562 | cell pair2-2 -t file, selections 14 |
| 2026-11-09 | paged | T-A | 1 | openai/gpt-6-luna | 633104 | 7192 | 54476 | 0.0765 | 1.4327 | NO-OP evictedTokens 0, budget 24000 settings, selections 9, checker PASS-parsed |
