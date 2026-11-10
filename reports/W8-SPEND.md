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

## Reconciliation 2026-11-09 — the ledger was short by $3.14

`hermes sessions` carries a per-session cost estimate, and it disagrees with the table above. Three
driver attempts on `w8-paged` were never written into this file:

| session (w8-paged) | api calls | messages | estimated USD |
|---|---|---|---|
| `w8-drv-paged-h7` | 98 | 296 | 1.3117 |
| `w8-drv-paged-h8` | 194 | 608 | 1.1107 |
| `w8-drv-paged-h9` | 148 | 148 | 0.7171 |
| **unledgered total** | **440** | — | **3.1395** |

The reviewed H6 capture (`local-8a98048c`) prices from its own receipts at **$0.0030**, not the
"~$0.03" in `RR-W8H6-20261109`: 13 calls, 190,520 input tokens, **all cached** (uncached 0), 2,215
output. So W8 has actually spent

```
ledger rows (7)                  $1.4327
unledgered driver attempts       $3.1395
H6 capture (receipts)            $0.0030
                        total    $4.5752   of a $25 cap
```

Per-call cost across the four runs spans 58×, and the whole difference is the cache:

```
h7  $1.3117 / 98 calls  = $0.01338 per call
h8  $1.1107 / 194 calls = $0.00573
h9  $0.7171 / 148 calls = $0.00485
h6  $0.0030 / 13 calls  = $0.00023     (prefix stable, every token a cache read)
```

Projections at the measured rates (Luna $0.10 in / $0.50 out / $0.01 cached, per 1M):

```
one clean cell, good cache          $0.016   48 cells  $0.75
one paged cell, prefix rewritten    $0.055   48 cells  $2.65
one cell at h7's rate, 20 calls     $0.112   48 cells  $5.39
sustained h7-h9 behaviour (~$1.05/attempt)     48 attempts ~ $50  -> over cap
```

The earlier $15.39 projection came from a 150-call thrashing cell and no longer describes the shape.
What would blow the cap is not token economics but an uncapped driver: 440 calls across three
attempts is the risk, so a per-cell call ceiling belongs in the driver, and every session's cost
belongs in this file on the day it runs.
