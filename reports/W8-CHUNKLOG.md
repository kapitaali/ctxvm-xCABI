# W8 chunk log — one row per cell, appended as it lands

Append-only. The executor writes the row BEFORE it asks for the next go, so the running
state is readable from this file without reading any transcript. A cell with no row is a
cell that did not happen.

Fields: time, chunk, cell k/N, task, arm, verdict, minutes, tokens in/cached/out, usd,
total usd, remaining. A literal pipe inside a field breaks the row — replace it with a slash.

| time | chunk | cell | task | arm | verdict | minutes | tokens in/cached/out | usd | total usd | remaining |
|---|---|---|---|---|---|---|---|---|---|---|
