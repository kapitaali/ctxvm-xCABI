# Task T2 — corpus forensics digest

You are auditing the frozen trace corpus of this repository. The workspace holds the corpus
split into line-aligned parts: `MANIFEST.tsv` maps every `*.partNN` file to its logical path
and line range, and concatenating a file's parts in manifest order reproduces it exactly.

Write the digest as **`drops.json` in the workspace root**. Nothing else is part of the
answer.

## Deliverable schema

```json
{
  "drops": [
    {
      "drop": "m1",
      "files": [{"name": "session-healthy.jsonl", "sha256": "<64 hex>", "checksumStatus": "verified"}],
      "eventsByType": {"call.meta": 3, "page.declare": 5},
      "totalEvents": 105,
      "pages": 13,
      "faultsBySource": {"identifier_scan": 5, "tool_recall": 4},
      "sessions": null,
      "sessionsSource": "no .meta.json sidecar (checked: README.md, checksums.sha256, …)"
    }
  ]
}
```

## Rules — these are the whole specification

1. **Drops.** One entry per directory `corpus/m1` … `corpus/m8`, in name order. The drop id
   is the directory name.
2. **Files.** Every `*.jsonl` trace in that directory, in name order. `sha256` is the full
   lowercase hex digest of the file's bytes. `checksumStatus` compares it with that
   directory's `checksums.sha256` row for the same file name:
   `verified` = the row exists and matches · `mismatch` = the row exists and differs ·
   `unlisted` = the file has no row.
3. **Events.** `eventsByType` counts the `type` field over every non-empty line of every
   trace in the drop, keys sorted. `totalEvents` is their sum. `pages` is the number of
   `page.declare` events. `faultsBySource` counts the `source` field over every `page.fault`
   event, keys sorted.
4. **Sessions.** `sessions` is the number of distinct `sessionID` values across the drop's
   `*.meta.json` sidecars, or `null` when the drop has no sidecar. A session identity is
   never derivable from event rows — do not infer one. When the value is `null`,
   `sessionsSource` names the files you checked in that directory; when it is a number,
   `sessionsSource` names the sidecar files, sorted and joined by ", ".

Do the hashing and counting from the bytes you read. `drops.json` must be the only file you
create.
