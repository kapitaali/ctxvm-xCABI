# W8B chunk log — one row per cell, appended as it lands

Append-only. The executor writes the row BEFORE it asks for the next go, so the running
state is readable from this file without reading any transcript. A cell with no row is a
cell that did not happen.

Fields: time | chunk | cell | task | arm | verdict | minutes | tokens in/cached/out | usd | total usd | remaining
A literal pipe inside a field breaks the row — replace it with a slash.

| time | chunk | cell | task | arm | verdict | minutes | tokens in/cached/out | usd | total usd | remaining |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-11T13:02Z | c1 | 1/1 | T-A2 | naive | NO RECORD — prompt 1 TIMEOUT after 120s, no capture flushed | 2.05 | —/—/— | 0.0000 | 0.0000 | UNKNOWN |
| 2026-11-11T13:02Z | c1 | 1/1 | T-A2 | paged | NO RECORD — prompt 1 TIMEOUT after 120s, no capture flushed | 2.08 | —/—/— | 0.0000 | 0.0000 | UNKNOWN |
