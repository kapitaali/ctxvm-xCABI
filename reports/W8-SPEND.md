# W8 spend ledger

Control variable for the $25 hard cap (design/w8-run-plan.md §6). One row per run:
date · arm · task · round · model · provider-receipt tokens · USD from the pinned price row ·
running total. The receipt columns are the provider's own numbers; cached reads are priced at
the input rate — an upper bound, labelled as one.

Model pinned: `gpt-6-luna` on provider `explabs`, catalogue row `OpenAI: GPT-6 Luna`
(`benchmarks/metrics/prices.json` v2, row-013, $0.10 in / $0.50 out / $0.01 cached per 1M).

Projected for the frozen grid (T1–T4 × 6 rounds × 2 arms = 48 runs, `benchmarks/w8/grid.json`):
≈ $3.30 at the pinned row, 13% of the $25 cap. The stopping rule below is enforced in
`tools/w8-run.py` before every run: projected = mean USD of that arm so far; stop when
spent + 2 × projected > 25.

No paid call has been made as of the row below.

| # | date | arm | task | round | model | in | out | cached | USD | run total | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-11-07 | both | t1 | 0 | gpt-6-luna | 0 | 0 | 0 | 0.0000 | 0.0000 | dry run: zero API calls, every assertion passed, checker=PASS |
| 1 | 2026-11-07 | naive | t1 | 1 | gpt-6-luna | 59691 | 6323 | 37302 | 0.0095 | 0.0095 | PASS; coverage ok; replay exit 0, byte-identical |
| 2 | 2026-11-07 | paged | t1 | 1 | gpt-6-luna | 59355 | 5958 | 37298 | 0.0093 | 0.0188 | PASS; coverage ok; replay exit 0, byte-identical |
| 1 | 2026-11-07 | naive | t1 | 1 | openai/gpt-6-luna | 1298978 | 68762 | 1229752 | 0.1766 | 0.1766 | n/a; coverage ok; replay exit 0, byte-identical |
| 3 | 2026-11-07 | naive | t1 | 1 | openai/gpt-6-luna | 1298978 | 68762 | 1229752 | 0.1766 | 0.1954 | RE-NUMBERED: this is the re-pilot naive run the row above recorded as #1 after the runner restarted its counter; no flags.json (model declined), coverage ok, replay byte-identical. Counter + running total fixed in tools/w8-run.py. |
