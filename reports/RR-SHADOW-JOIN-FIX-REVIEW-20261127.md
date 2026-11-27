# RR-SHADOW-JOIN-FIX-REVIEW-20261127 — accepted: all three join corrections verified

Review lane, verify-then-record. Follow-up to `RR-SHADOW-JOIN-REVIEW-20261127`. Date 2026-11-27.
No model call, spend, gateway/profile change, or push.

## 1. Corrections independently verified

| review blocker | staged fix | probe/result |
|---|---|---|
| equal same-turn timestamps misclassified as not-later | `_is_later()` returns `None` when parsed timestamps are equal | equal-ts probe → **None/ambiguous** |
| insufficient-data output emitted per-session ratios | `run()` strips `pressure`, `floor_pressure`, `drop_share`, `selection_churn` from public session summaries until the three-session gate passes | live `result.json` session has **no ratio fields**; counts remain |
| candidate pins lacked offline-only marker | pin entries now include `offline_only: true`, `activation: "not_authorized"` | synthetic pin probe → **True / not_authorized** |

Regression coverage remains six tests and all pass.

## 2. Live result unchanged

Live join still exits **3** with `INSUFFICIENT_DATA`:

- 71 schema-valid records, 13 sessions, 12 excluded, 1 valid / 3 required;
- 6 selections, 1 persisted dropped page, 1 right-censored `never_observed`;
- 0 later tool_recall, 0 later identifier_scan;
- `metrics=null`, `candidate_pins=[]`;
- accepted trace digest/PageId and privacy checks remain clean.

No rate or pin claim is made.

## 3. Staging/copy state

The five intended artifacts are already present in the working tree and byte-identical to staging:

- `reports/RR-SHADOW-JOIN-20261126.md`
- `reports/RR-SHADOW-JOIN-RESULT-20261127.md`
- `research/shadow-analysis/join.py`
- `research/shadow-analysis/test_join.py`
- `research/shadow-analysis/out/result.json`

The two rejected white-paper staging files are gone from the dry-run set; repo HEAD remains `993138d`.
The copy dry-run reports zero because the working tree already matches staging.

## 4. Verdict

**Accepted for commit.** The join implementation is correct for the current `INSUFFICIENT_DATA` corpus and
ready for additional fresh 0.13.37 sessions. At least two more valid sessions with persisted drops are
required before descriptive pooled metrics or candidate-pin evaluation.

The five join artifacts remain uncommitted research/experiment WIP; this review commit records acceptance
only. No causal, cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim.

## 5. Verification

- `python3 research/shadow-analysis/test_join.py -v` → **6 passed**
- live join → exit 3, expected counts
- `bash tools/run-ci.sh` → **ALL GATES GREEN**
- `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK; `git diff --check` clean

## 6. Applied

This card, one four-pipe row in active `reports/LOG02.md`, and a day-file section. No join code or paper
source changed by review; no push.
