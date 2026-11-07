# Task T4 — report-index audit

The workspace holds `reports/LOG.md` — the repository's append-only report index — split into
line-aligned parts. `MANIFEST.tsv` maps every `*.partNN` file to its logical path and line
range; concatenating a file's parts in manifest order reproduces it exactly.

Audit the index and write the result as **`release.md` in the workspace root**.

## Rules — these are the whole specification

1. **Rows.** A row is a line of `LOG.md` whose first field starts with `| RR-`. The **id** is
   that first field, stripped of the leading pipe and spaces.
2. **Date.** The **last** run of exactly eight digits inside the id, rendered `YYYY-MM-DD`.
   Some ids carry a suffix after their date (`-FIX`, `-CI`, `(RESOLUTION)`, `(T17.1)`) — the
   last run is the one that means a date.
3. **Track.** The id with the `RR-` prefix and that date run removed, with surrounding
   hyphens and spaces trimmed. An id that has non-space text after the date run is
   **irregular**, and that trailing text is recorded with it.
4. **Order.** A row whose date is earlier than the date of the row before it is an order
   violation, reported as the id and the date it followed.
5. **Duplicates.** Ids appearing more than once, with counts.
6. **Last 60.** The final 60 rows of the file, in file order.

## Deliverable — exact shape

```
# LOG audit

## Last 60 rows

| n | id | date | track |
|---|----|------|-------|
| 1 | RR-… | YYYY-MM-DD | TRACK |

## Irregular ids

- RR-… → `SUFFIX`

## Date order violations

- RR-… (YYYY-MM-DD after YYYY-MM-DD)

## Summary

rows=<n> last60=<n> duplicates=<n> orderViolations=<n> irregular=<n>
- RR-… ×<count>
```

A section with no findings contains the single line `none` (the summary counts stay 0).
The duplicates list appears after the summary line, one `- <id> ×<count>` per id, sorted.

**Hard rule (DQ).** The artefact carries ids, dates, tracks and counts — never prose copied
out of a row. A checker rejects an artefact containing row text, because quoting a row
verbatim is how the earlier release-note attempt failed its own redaction scan.

`release.md` must be the only file you create.
