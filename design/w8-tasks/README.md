# W8 paging tasks — design

Two tasks designed for the W8 paging experiment: does context selection (ctxvm at 24,000-token budget) reduce tokens without hurting accuracy?

## Side-by-side

| | T-A: Cross-file line-length census | T-B: Cross-file category histogram |
|---|---|---|
| **What the agent produces** | `artefact.json` with per-file `lines`/`bytes`/`long`/`short` + `widest_file` + `total_long` (no line measurements — see T-A) | `artefact.json` with per-category count/sum/min_id/max_id + `top_category` + `top_file` + `grand_total` |
| **Fixture** | 14 files, `part-01.txt` … `part-14.txt`, 200 lines each | 20 files, `data-01.csv` … `data-20.csv`, 300 data rows each |
| **Floor (declared tokens)** | ≈ 56,000 (14 × 200 × ~80 bytes) | ≈ 60,200 (20 × 301 × ~40 bytes) |
| **Estimated calls** | 16 (1 list + 14 read + 1 write) | 22 (1 list + 20 read + 1 write) |
| **Anti-search property** | Byte length of a line is not a searchable property; aggregates (counts, sums, maxima) across files are not produced by search | Count/sum per category across files is not an aggregate search returns; per-file contribution to a category is not derivable from search hits |
| **Falsifier (search shortcut)** | Would need per-file counts of lines >100 bytes and <10 bytes plus byte totals — no search returns counts, and a truncated search dump gives wrong ones | Would need per-category count and sum across 20 files plus per-file row counts for the top category — no search produces aggregates |
| **What PASS at 150 iterations proves** | A naive agent can read all files, compute per-line measurements, and aggregate cross-file — without search shortcutting, so token pressure is real and paging is exercised | A naive agent can read all files, parse all rows, and aggregate across files — search cannot shortcut, so the context grows and paging is exercised |

## Why previous attempts failed and how these differ

**Cell 1 and Cell A** (T1 fixture, 33 and 13 parts): the task asked for "flags each binary accepts" — answerable from one grep hit per binary. The agent searched 686 times and read 14 files, never producing `flags.json`. Shrinking the fixture didn't help because the binding constraint was behaviour (search looks like progress), not page size.

**This design differs:** the answer is an *aggregate* that search cannot produce. `search_files` returns matching lines, not counts, sums, byte lengths, or cross-file maxima. The agent cannot shortcut; it must read every file. The task is completable in ~16–22 calls with a large margin below 150, so a competent agent finishes. The failure mode for a weak model is "wrong answer" (caught by the checker), not "infinite loop."

## Design honesty notes

- Both tasks are measurement/aggregation exercises. They are not artificially tedious: reading N files and aggregating is the natural workflow. The search-hostility comes from the aggregate nature of the answer, not from repetition.
- T-A's floor (≈56,000 tokens) is above 45,000 but not by a large margin. The lane must verify the floor with the actual generated fixture before running.
- T-B was revised from 150 to 300 rows per file to clear the 45,000-token floor. The checker and artefact scale accordingly.
- Neither design requires shell, network, or writes beyond `artefact.json`. Both are read-only source material.

## What search can and cannot do here (corrected in review)

The first draft claimed search *cannot* shortcut these tasks. That is too strong and it matters,
because a claim the experiment rests on has to be true. `search_files` can return the matching
lines, and a pattern broad enough returns most of a file's content — so the material *can* reach
the context through search rather than through `read_file`.

What search cannot do is produce the answer: no search returns a count, a sum, a per-file maximum,
or a cross-file contribution. The agent still has to compute, and computing from a search dump is
worse than from a read: the dump is truncated by the tool's `limit`, so an agent that searches for
everything may silently hold part of the data and answer from it.

That is enough for the experiment, and it is the honest statement of why:

- **calls stay low** — 16 and 22 against a ceiling of 150, so a competent agent finishes;
- **context still grows past the budget** — 54,700 and 60,200 tokens whichever route the content
  takes, so the paged arm is exercised rather than idle;
- **the answer is still a computation** — the failure mode is a wrong number, which the checker
  catches, not an infinite loop.

A search-heavy route also burns iterations, which is what killed cells 1 and A. Both routes are
acceptable to the experiment; only the 686-search thrash was not.

## T-B, same rule

Same correction: search returns rows, not per-category counts, not sums, and not the per-file
contribution that `top_file` needs. The 20-file reconciliation is a computation over all rows, and
a truncated search dump is a wrong answer waiting to happen.