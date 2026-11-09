# Task T-A: Cross-file line-length census

## Task text (as pasted to the agent)

You are given a directory of text files. For every file, compute:

- `lines`: number of lines (a line is terminated by `\n`; a final line without trailing `\n` still counts as one line)
- `bytes`: total byte size of the file
- `long`: number of lines whose byte length (newline excluded) is **greater than 100**
- `short`: number of lines whose byte length (newline excluded) is **less than 10**

Then compute two cross-file values:

- `widest_file`: the filename (basename only) with the largest `long` value. Tie-break by filename ascending (lexicographic).
- `total_long`: sum of `long` across all files.

Write the result to `artefact.json` in the working directory. The artefact must be a single JSON object with this exact shape:

```json
{
  "files": {
    "<basename>": {"lines": N, "bytes": N, "long": N, "short": N},
    ...
  },
  "widest_file": "<basename>",
  "total_long": N
}
```

Keys in `files` must be sorted ascending. All numbers are integers. No extra keys. Write it with
2-space indentation and one trailing newline if you can; formatting is recorded but is not the gate
(see below).

**What the gate is** (ruled 2026-11-09, after a cell produced every value correctly with per-file
objects written inline): the checker compares the **parsed** artefact — same keys, same values, same
ordering — and reports canonical formatting separately as a non-gating observation. A byte-exact
requirement turns JSON style into an accuracy result, and two arms failing on style is a null about
indentation, not about context policy.

You may read any file in the fixture directory. You may write only `artefact.json`. Do not run shell commands or access the network.

**Why there is no `max_line` / `min_line`** (2026-11-09, measured): a naive cell produced the right
`lines`, `bytes`, `long` and `short` for all fourteen files and the wrong maximum line length in every
one of them — 119, then 116, then 115 against a ground truth of 120, across three artefacts. It is a
measurement this model cannot make reliably from a tool result, and a gate it cannot meet measures
arithmetic rather than context policy. The counts stay; the measurements go.

## Fixture specification

- Directory: `fixture/` (relative to working directory), containing 14 files named `part-01.txt` … `part-14.txt`.
- Each file has exactly 250 lines, each line 5–120 bytes excluding the terminating `\n`. The low
  tail exists so that `short` is a real measurement rather than a constant zero: a field that cannot
  vary cannot be wrong, and a checker that always sees 0 there tests nothing.
- Content: lowercase ASCII letters and spaces, no tabs, no other control characters.
- Generated deterministically from seed `42` with a documented generator (generator spec to be supplied with the fixture; the design does not ship code). The generator produces each line by drawing a length uniformly from [5,120] and filling with
lowercase letters and spaces (lengths 5–9 give the `short` tail; 101–120 give the `long` tail).
- No file is empty; no file is a prefix of another.

**Declared-token floor:** 14 files × 250 lines × ~62.5 bytes (the mean of a uniform 5–120 draw)
= 218,750 bytes ≈ **54,700 tokens** at 4 bytes/token. Above the 45,000 floor with margin; the
lane must confirm it against the generated fixture's real bytes before any paid cell.

## Expected artefact

The byte-exact artefact is determined by running the checker (below) against the generated fixture. The design does not ship the expected bytes; the checker is the authority.

## Checker rules

A Python script `check.py` (not shipped with this design; to be implemented by the lane) does:

1. Load `fixture/` and recompute every per-file statistic from the raw bytes.
2. Load `artefact.json`.
3. Compare: sorted file keys, exact integer match on every field, `widest_file` exact string, `total_long` exact integer.
4. Print `PASS` and exit 0 on full match; print `FAIL: <reason>` and exit 1 on any mismatch.

**Perturbation test:** change one digit in any number in `artefact.json` (e.g., `long` from 47 to 48) → checker prints `FAIL` and exits 1. Change a filename in `widest_file` → `FAIL`. Add an extra key → `FAIL`. Remove the trailing newline → `FAIL` (byte-exact comparison of serialized form).

## Call-count estimate

- 1 call: list the fixture directory (or `search_files` for `*.txt`) to discover the 14 files.
- 14 calls: `read_file` once per file.
- 1 call: `write_file` for `artefact.json`.
- Total: **16 calls** (estimate upper bound 20 with verification re-reads). Well within 150; margin ≈ 130 calls.

The agent is not expected to re-read files; each is read once and its stats extracted in-context.

## Anti-search argument

**Property a search cannot return:** the byte length of a line. `search_files` returns matching *lines* (content that matches a pattern), not the length of any line. To compute `long` (lines > 100 bytes) and `short` (lines < 10 bytes), the agent must read every line and measure its length. No grep pattern can express "lines longer than 100 bytes" because grep matches content, not length.

**Cross-file property:** `widest_file` requires comparing the `long` count across all 14 files. A search returns per-file hit lists but cannot aggregate counts across files into a single maximum. `total_long` requires summing across all files. Neither is derivable from search output without reading every file.

**Falsifier:** A search-based shortcut would have to return, for each file, the count of lines whose byte length exceeds 100 and the count below 10, plus the per-file max/min line lengths and byte totals. No single `search_files` invocation produces any of these aggregates; producing them from search would require one search per distinct line length (unbounded) or reading every line anyway. Therefore search cannot shortcut the task.

## Known weaknesses

- The task is a pure measurement exercise. It is not artificially tedious (no repeated similar steps beyond reading 14 files), but it does require reading every file. If the model decides to skip a file and guess, the checker catches it — but the failure mode is "wrong answer", not "infinite loop", so a weak model could submit a wrong artefact quickly. This is acceptable: the experiment measures accuracy, and a wrong artefact is a failure for both arms equally.
- The floor (≈56,000 tokens) is above 45,000 but not by a large margin. If the generator produces shorter lines, the floor drops. The lane should verify the floor with the actual generated fixture before running.