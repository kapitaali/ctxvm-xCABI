# RR-SHADOW-BATCH-CONCURRENCY-REVIEW-20261128 — frozen snapshots admissible, sequential inference barred

Review lane. Date: 2026-11-28. Subject: `RR-SHADOW-BATCH-CONCURRENCY-20261128` and the two private
shadow-batch runs. No live model call, session creation, profile/gateway/config change, restart, pin
activation, publish, or push.

## 1. Ruling

1. **The ratified run's frozen per-attempt snapshots remain admissible** for the committed within-run
   descriptive counts in `RR-SHADOW-BATCH-RESULT-20261128` and its three aggregate artifacts.
2. **The ratified run is not a clean sequential replicate.** It overlapped another authorized collector
   for 836.003 seconds and must be labeled as a concurrent bounded run.
3. **The overlapping `shadow-batch-20261128-1840` run is contaminated for sequential-batch inference**
   and remains quarantined. Do not pool, average, or compare the two runs' validity counts, informative
   counts, or rates as model variance.
4. Mutable global `selection.jsonl`, live sidecars, and whole-directory joins are not batch evidence.
   The frozen per-attempt trace, coverage, and shadow-delta snapshots are the evidence boundary.
5. Any new batch requires a single-run lock or equivalent exclusivity check before the first model call.

## 2. Verified overlap

| run | first attempt start | last attempt end | attempts | collector-valid | informative |
|---|---|---|---:|---:|---:|
| `shadow-batch-20261128-ratified-v1` | 16:45:47.983 UTC | 17:03:46.541 UTC | 18 | 7 | 2 |
| `shadow-batch-20261128-1840` | 16:49:50.538 UTC | 17:08:18.810 UTC | 18 | 12 | 1 |

- Overlap: **836.003 seconds** (13m56s).
- Overlapping attempt pairs: **28**.
- Each run has 18 unique session IDs; the intersection is empty.
- No collector process remains.

The ratified run's whole-shadow digest chain breaks at attempts 7→8, 11→12, and 14→15. This confirms that
the shared append-only shadow file was modified between ratified attempts. It does not contaminate the
frozen per-session deltas, because those files were filtered and snapshotted by session ID.

## 3. Why the frozen evidence survives

- Every ratified `shadow-delta.jsonl` contains only its own attempt's session ID; no cross-run rows were
  found.
- The frozen join input contains exactly the 18 ratified session IDs and none from the overlapping run.
- All 18 current trace files still match the frozen trace digests byte-for-byte.
- The collector gates and join use per-session `shadowSelections` and `shadowWriteFailures`, not the
  process-global counters, for attempt validity.
- The independent receipt validator reports zero errors for quotas, stop rules, route proof, digests,
  public/raw projections, privacy, and file modes.
- The frozen join comparison reports zero errors and reproduces the collector-valid counts exactly.

Live coverage sidecars did change after the snapshots. In particular, attempts 10 and 16 later showed
`shadowWriteFailures` 0→1, and all snapshots retain the collector's rewritten `traceFile` name. Those
mutations disqualify mutable whole-sidecar joins, not the immutable attempt-time evidence. This is the
same boundary already used by the committed result card.

## 4. Impact on the committed result

The committed counts stand with a concurrency caveat:

- status remains `UNDERPOWERED`;
- 18 attempts, 7 collector-valid, 2 informative;
- 4 dropped records/pages, no later recall/scan, no candidate pins;
- frozen join remains 8 join-valid / 40 selections, with attempt 10 explaining the one-session difference.

The result card receives a targeted addendum linking this ruling. The aggregate JSON/Markdown artifacts
are unchanged because they accurately describe the frozen snapshots.

No causal, cost-saving, paging-quality, model-quality, determinism, availability, redaction, or safety
claim is permitted. Shared model/provider scheduling and rate limits remain an unmeasured concurrency
effect. `never_observed` remains right-censored; candidate pins remain offline-only.

## 5. BUG_REPORT status

`packages/hermes/BUG_REPORT.md` contains the appended defect section and remains unstaged. No explicit
"commit BUG_REPORT" authorization has been given, so this review does not stage or commit it.

## 6. Applied

This review report, a targeted concurrency addendum in `RR-SHADOW-BATCH-RESULT-20261128.md`, one
four-pipe `reports/LOG02.md` row, one `reports/RR-DAY-20261128.md` section, and a separate PROJECT-STATE
delta. No push.
