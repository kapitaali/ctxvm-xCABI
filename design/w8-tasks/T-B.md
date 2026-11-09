# Task T-B: Cross-file category histogram and reconciliation

## Task text (as pasted to the agent)

You are given a directory of CSV files. Each file has a header row exactly `id,category,value` followed by data rows. The format is
plain: no quoting, no embedded commas, no whitespace padding, LF line endings. For every file, the rows record (id, category, value) triples where `value` is an integer.

Produce two things:

**1. Per-category global statistics** across all files:

- `count`: total number of rows with that category
- `sum`: total of `value` across all rows with that category
- `min_id`: the smallest `id` (as integer) among rows with that category
- `max_id`: the largest `id` among rows with that category

**2. Cross-file reconciliation:**

- `top_category`: the category with the largest `sum`. Tie-break by category name ascending.
- `top_file`: the filename (basename) that contributes the most rows to `top_category`. Tie-break by filename ascending.
- `grand_total`: sum of `value` across all rows in all files.

Write the result to `artefact.json` in the working directory. Exact shape:

```json
{
  "categories": {
    "<category>": {"count": N, "sum": N, "min_id": N, "max_id": N},
    ...
  },
  "top_category": "<category>",
  "top_file": "<basename>",
  "grand_total": N
}
```

Keys in `categories` must be sorted ascending. All numbers are integers. No extra keys, no extra whitespace beyond 2-space indentation and a single trailing newline.

You may read any file in the fixture directory. You may write only `artefact.json`. Do not run shell commands or access the network.

## Fixture specification

- Directory: `fixture/` (relative to working directory), containing 20 files named `data-01.csv` … `data-20.csv`.
- Each file: header `id,category,value\n` plus 150 data rows.
- `id`: integer 1–9999, unique within a file but may repeat across files.
- `category`: one of 8 fixed categories: `alpha`, `beta`, `gamma`, `delta`, `epsilon`, `zeta`, `eta`, `theta`.
- `value`: integer in [-500, 500].
- Generated deterministically from seed `7` with a documented generator. Each row draws category uniformly from the 8, id uniformly from [1,9999], value uniformly from [-500,500].
- No empty files; no file is a prefix of another.

**Declared-token floor:** 20 files × 151 lines × ~25 bytes ≈ 76,000 bytes ≈ **19,000 tokens** at 4 bytes/token. Hmm — below 45,000. Recompute with larger rows: make each row ~40 bytes (wider id range, category names) → 20 × 151 × 40 = 120,800 bytes ≈ **30,000 tokens**. Still below 45,000.

Adjust: 20 files × 300 rows × ~40 bytes = 240,000 bytes ≈ **60,000 tokens**. Use 300 rows per file. Floor comfortably above 45,000.

Revised: each file has header + **300** data rows.

**Declared-token floor:** 20 × 301 × 40 ≈ 240,800 bytes ≈ **60,200 tokens**. Above 45,000.

## Expected artefact

Determined by the checker. The design does not ship expected bytes.

## Checker rules

A Python script `check.py` (to be implemented by the lane) does:

1. Load `fixture/`, parse every CSV, recompute per-category `count`, `sum`, `min_id`, `max_id`, `top_category`, `top_file`, `grand_total`.
2. Load `artefact.json`.
3. Compare exact.
4. Print `PASS` and exit 0 on full match; `FAIL: <reason>` and exit 1 on any mismatch.

**Perturbation test:** change one `count` → `FAIL`. Change `top_category` → `FAIL`. Swap two category keys → `FAIL` (sorted-order check). Remove trailing newline → `FAIL`.

## Call-count estimate

- 1 call: list the fixture directory.
- 20 calls: `read_file` once per file.
- 1 call: `write_file` for `artefact.json`.
- Total: **22 calls** (upper bound 26 with verification re-reads). Within 150; margin ≈ 124.

## Anti-search argument

**Property a search cannot return:** a count or sum over lines that match a *category value*, combined across all files. `search_files` with a pattern like `alpha` returns the matching lines but not their count or the sum of their `value` column. To get `count` and `sum` per category, the agent must parse every row and aggregate — search returns raw lines, not aggregates.

More precisely: `grand_total` requires summing the `value` column across all 6,000 rows. A search for any numeric pattern returns matching lines but cannot sum a column. `top_category` requires comparing 8 sums. `top_file` requires, for the top category, counting which file contributed the most rows — a cross-file, per-category, per-file count that no single search can produce.

**Falsifier:** A search-based shortcut would have to return, for each of 8 categories, the total count and sum across 20 files, plus per-file row counts for the top category. No `search_files` invocation produces any aggregate; producing them from search would require reading every matching line and summing manually, which is reading every file. Therefore search cannot shortcut the task.

**Additional search hostility:** the 8 categories share no common prefix and are all real words, so a single broad pattern (e.g., `.`) matches everything and returns 6,000 lines — useless. A narrow pattern (one category) misses the other 7. Either way, search does not reduce the work.

## Known weaknesses

- The task is a standard aggregation exercise. It is not artificially tedious: 20 reads + one aggregation pass is the natural way to compute a histogram. The search-hostility comes from the aggregate nature of the answer, not from repetition.
- `id` uniqueness is per-file, so `min_id`/`max_id` are per-category global extrema, not per-file. This adds a small cross-file dimension.
- If the model guesses categories or skips files, the checker catches it. As with T-A, the failure mode is "wrong answer", not "infinite loop".