# W8 chunk log — one row per cell, appended as it lands

Append-only. The executor writes the row BEFORE it asks for the next go, so the running
state is readable from this file without reading any transcript. A cell with no row is a
cell that did not happen.

Fields: time, chunk, cell k/N, task, arm, verdict, minutes, tokens in/cached/out, usd,
total usd, remaining. A literal pipe inside a field breaks the row — replace it with a slash.

| time | chunk | cell | task | arm | verdict | minutes | tokens in/cached/out | usd | total usd | remaining |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-07T15:57Z | c1 | 1/2 | t1 | naive | FAIL - no artefact, max_iterations 150/150 | 42.5 | 24802048/24552150/169443 | 0.3303 | 0.8464 | 24.1536 |
| 2026-11-07T17:07Z | c2 | 1/2 | t1 | naive | FAIL - no artefact, max_iterations 150/150; arm witness mismatch engine=ctxvm profile=.hermes | 37 | 24248569/24016030/135061 | 0.3077 | 1.1541 | 23.8459 |
| 2026-11-09T11:56Z | pair-T-A | pilot-naive | T-A | naive | PILOT - execute_code shortcut, 4 declares, checker PASS (not a cell) | - | 73392/57564/2740 | 0.0039 | 1.1626 | 23.8374 |
| 2026-11-09T11:56Z | pair-T-A | pilot-paged | T-A | paged | PILOT - engineSelections 0, checker PASS (not a cell) | - | 448446/83766/6534 | 0.0497 | 1.2123 | 23.7877 |
| 2026-11-09T15:35Z | pair2 | 1/2 | T-A | naive | PASS-parsed (byte-format) | 5 | 336358/227410/3231 | 0.0175 | 1.2298 | 23.7702 |
| 2026-11-09T15:35Z | pair2 | 2/2 | T-A | paged | PASS-parsed (counter shared) | 14 | 1057053/83042/7607 | 0.1264 | 1.3562 | 23.6438 |
| 2026-11-09T14:32Z | diag-24k | t-a-paged-24k | T-A | paged | NO-OP evictedTokens 0 selections 9 | - | 633104/54476/7192 | 0.0765 | 1.4327 | 23.5673 |
