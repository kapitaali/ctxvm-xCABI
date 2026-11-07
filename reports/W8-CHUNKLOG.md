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
