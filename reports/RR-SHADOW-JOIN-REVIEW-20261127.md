# RR-SHADOW-JOIN-REVIEW-20261127 — core join verified; three corrections required before landing

Review lane, verify-then-record. Subject: staged offline shadow join under `research/shadow-analysis/`,
updated `RR-SHADOW-JOIN-20261126`, and `RR-SHADOW-JOIN-RESULT-20261127`. Date 2026-11-27.
No model call, spend, gateway/profile change, or push.

## 1. Verified

- Six synthetic regression tests pass.
- Live rerun exits **3** as specified: `INSUFFICIENT_DATA`, 1 valid session / 3 required.
- Counts match the staged result: 71 records, 13 sessions, 12 excluded, 6 selections, 1 dropped page,
  0 later tool_recall, 0 later identifier_scan, 1 never_observed.
- Accepted trace digest and PageId match the live acceptance card.
- Output privacy scan finds no `/home/`, raw tool ref, secret filename, CTXVM variable, bearer token,
  or provider key shape.
- `metrics=null` and `candidate_pins=[]` at insufficient data.

The core session mapping, digest, PageId, exclusion, and privacy path works.

## 2. Required correction 1 — equal timestamps are misclassified as not-later

`_is_later()` returns `ets > rts`. For same-turn events with **equal parseable timestamps**, it returns
`False`, which can count the page as `never_observed`. Equal timestamps cannot establish order and must
return `None` (ambiguous), like missing/unparseable timestamps.

Probe:

```text
record ts = 2026-11-26T19:00:00.000Z
 event ts = 2026-11-26T19:00:00.000Z
_is_later -> False   # must be None/ambiguous
```

Add a regression; no current accepted record depends on equal timestamps, so the fix should be
behavior-preserving for the present corpus.

## 3. Required correction 2 — insufficient-data output still emits ratios

The result card says no pressure/churn/drop-share rate is reported when fewer than three sessions are
valid. `result.json` nevertheless includes per-session `pressure`, `floor_pressure`, `drop_share`, and
`selection_churn` summaries. `metrics=null` only suppresses the pooled block.

Choose one and record it:
- suppress those per-session summaries until the sufficiency gate passes; or
- explicitly label them `descriptive_only` and correct the card to say “no pooled metrics/rates.”

The current card/output mismatch should not ship.

## 4. Required correction 3 — candidate pins lack an offline-only marker

When enough sessions exist, `candidate_pins` entries contain `page_id`, event count, sessions, and kind,
but no machine-readable offline-only/not-authorized status. The spec says candidate pins remain offline-only
and live use needs a separate ruling.

Add e.g. `"offline_only": true` and `"activation": "not_authorized"` to every pin entry, plus a regression.
This prevents a downstream consumer from treating nomination as permission to mutate a live profile.

## 5. White-paper updates rejected separately

The two staged white-paper changes only removed `/past-experiments/` from W8/W8B/W8C links, reverting them
to old `design/W8*` paths that no longer exist after `2ff9724`. They contained no semantic paper update.

They were snapshotted to `/tmp/opencode/whitepaper-stale-backup/` and restored to HEAD. Do not copy those
two staged versions. The archive README mapping remains the correct historical locator guide.

## 6. Status / route

The five join artifacts are already present in the working tree and byte-identical to staging, but remain
uncommitted. Research/experiment lane should apply the three corrections and rerun the six-plus regressions
and live join. Review then verifies equal-timestamp ambiguity, insufficient-data output shape, pin markers,
and privacy before commit.

Current corpus remains **INSUFFICIENT_DATA**; no rates or pins are claimed. No causal, cost-saving,
paging-quality, model-quality, determinism, availability, or redaction claim.

## 7. Applied

This card, one four-pipe row in active `reports/LOG02.md`, and a day-file section. No join code or paper
source was changed by review; no push.
