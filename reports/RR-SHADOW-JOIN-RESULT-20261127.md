# RR-SHADOW-JOIN-RESULT-20261127 — offline join implemented; current corpus INSUFFICIENT_DATA

Lane: experiment/research. Date: 2026-11-27. Authority: `RR-SHADOW-JOIN-20261126`, live
acceptance `RR-SHADOW-LIVE-ACCEPT-20261126` (`7b4b0cd`, `5641c82`), and review corrections
`RR-SHADOW-JOIN-REVIEW-20261127` (`993138d`). Scope: offline join over private `w8-shadow`
records only. No model call, spend, gateway/profile change, live stub arm, candidate-pin use,
publish, commit, or push.

## 1. Implementation

Staged under `research/shadow-analysis/`:

- `join.py` — schema/profile/version/session/trace/PageId/order gates; descriptive counts;
  three-session sufficiency threshold; offline candidate-pin rule with machine-readable
  `offline_only=true` / `activation=not_authorized` markers.
- `test_join.py` — six synthetic regressions.
- `out/result.json` — aggregate result from the current private sidecar.

The script reads raw refs only in memory to recompute
`sha256(logicalRef|contentHash)`. Output contains hashed session/page ids, counts, denominators,
trace digest, and exclusion reason codes only. No raw ref, body, arguments, prompt, answer,
credential, or host path is emitted.

## 2. Verification

```text
python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK
```

Review corrections applied:

- equal same-turn timestamps now return ambiguous (`None`), never false/not-later;
- per-session `pressure`, `floor_pressure`, `drop_share`, and `selection_churn` summaries are
  suppressed until the three-session gate passes;
- every candidate-pin entry carries `offline_only=true` and `activation=not_authorized`.

Covered:

1. historical PageId v1 remains distinct from later v2 of the same ref;
2. same-turn ordering requires parseable, strictly later timestamps; equal timestamps are ambiguous;
3. ambiguous same-turn events are not labeled `never_observed`;
4. 0.13.36/global-failure sessions are excluded and insufficient output suppresses ratio summaries;
5. candidate pins require ≥2 sessions and ≥3 unique tool_recall events and carry offline-only markers;
6. output contains no raw ref or host path.

Independent live-artifact rechecks:

```text
shadow schema: OK (71 records)
coverage_check: consistent (...jsonl, 8 events, digest ok)
rust replay: {"events":8,"divergences":[],"violations":[]}
v0.1 schema: OK: all checks passed
```

## 3. Current corpus and gates

| item | result |
|---|---:|
| shadow records | 71 |
| schema-invalid records | 0 |
| sessions seen | 13 |
| excluded sessions | 12 |
| valid sessions | 1 |
| required valid sessions | 3 |
| status | **INSUFFICIENT_DATA** |

All 12 excluded sessions are 0.13.36 captures carrying the old process-global
`shadowWriteFailures=2`. Their reason codes are `version_too_old` and
`session_write_failures`. The accepted 0.13.37 session has per-session failures 0 and passes
all mapping/digest/PageId gates.

## 4. Valid-session counts (not rates)

Accepted session key: `sha256:06b63f34cf135248`.

| count | value |
|---|---:|
| selections | 6 |
| dropped selections | 1 |
| dropped pages | 1 |
| matched page opportunities | 1 |
| unmatched PageIds | 0 |
| later tool_recall opportunities | 0 |
| later identifier_scan opportunities | 0 |
| never_observed opportunities | 1 |
| ambiguous same-turn events | 0 |

The one `never_observed` opportunity is **right-censored**, not evidence that the page was safe
to drop. The accepted trace contains no later fault/stub/evict event for that PageId.

Because only one session is valid:

- `metrics = null`;
- per-session pressure/floor/drop-share/churn summaries are absent;
- `candidate_pins = []`;
- no would-drop, reuse, churn, pressure, or pin rate is reported;
- no stable-control parity is claimed.

The join command correctly exits **3** for `INSUFFICIENT_DATA` after writing the result JSON.

## 5. Interpretation

This run verifies that the offline join executes end to end on the accepted 0.13.37 live
artefact: exact session mapping, trace digest, historical PageId equality, ordering, and
aggregate output all work. It does **not** estimate rates or nominate pins. One acceptance
session is enough to test the join, not enough to characterize the keep law.

## 6. Next data requirement

Collect at least **two more fresh 0.13.37 `w8-shadow` sessions** with persisted drops to reach
the preregistered three-session minimum. More sessions are preferable before interpreting
rates. Candidate pins remain offline-only and still require the separate ≥2-session/≥3-event
rule plus a separate live-arm ruling.

No causal-importance, cost-saving, paging-quality, model-quality, determinism, availability, or
redaction claim follows. `position_band` and `later_dependency_use` remain UNVERIFIED because
the current sidecar/trace do not contain request order or a dependency graph.

## 7. Repro

```bash
cd "$CTXVM_REPO"
python3 research/shadow-analysis/test_join.py -v
python3 research/shadow-analysis/join.py \
  --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
  --trace-dir ~/.local/state/ctxvm/traces \
  --out research/shadow-analysis/out
```

Expected current result: `INSUFFICIENT_DATA`, valid sessions 1/3, exit 3.
