# RR-SHADOW-BATCH-RESULT-20261128 — 18-attempt ratified shadow batch is underpowered

Experiment/review lane. Date: 2026-11-28.
Authority: `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md`,
`reports/RR-SHADOW-COLLECTOR-FINAL-ACCEPTANCE-20261128.md`, and
`design/experiment-runs/SHADOW-BATCH-FIXTURE-FREEZE-20261128.md`.

No profile/gateway/model-config change, restart, paid fallback, silent model/provider switch, candidate-pin
activation, publish, or push occurred.

**Concurrency addendum:** this run overlapped another authorized collector for 836.003 seconds. Its frozen
per-attempt snapshots remain admissible for the within-run counts below, but it is not a clean sequential
replicate and must not be pooled or compared with the overlapping run as model variance. See
`RR-SHADOW-BATCH-CONCURRENCY-REVIEW-20261128`.

## 1. Execution

The ratified batch ran on Hermes plugin 0.13.37, profile `w8-shadow`, fresh control mode, budget 24,000,
model `tencent/hy4-flash:free` / `nous`. All 18 attempts were anonymous one-shot sessions with
`--max-turns 20`.

- Frozen manifest SHA-256: `202b9468ffa53301e7b56e29a2df92a3074c47ecb1a5f4164c50f820acdbc735`
- Preflight: rc=0; 21 baseline sessions; fallback disabled; gateway trace source `start (defaults)`
- Attempts: 18, exactly six per shape
- Exit code: 3 (`UNDERPOWERED`), the expected cap outcome
- Auth/model failure flags: 0
- Model/provider route failure flags: 0
- Requested route: 18/18 `tencent/hy4-flash:free` / `nous`
- Session-store route proof: 18/18 exact model/provider, `fallback_active=false`

## 2. Outcome by shape

| shape | attempts | collector-valid | informative | target | status |
|---|---:|---:|---:|---:|---|
| read-once pressure | 6 | 3 | 2 | 4 | UNDERPOWERED |
| deliberate later re-read | 6 | 3 | 0 | 4 | UNDERPOWERED |
| dependency chain | 6 | 1 | 0 | 4 | UNDERPOWERED |
| **total** | **18** | **7** | **2** | **12** | **UNDERPOWERED** |

Five collector-valid sessions had no shape label. No prompt or fixture was broadened, and no attempts
continued beyond the per-shape cap.

## 3. Dual denominator views

### All collector-valid sessions (n=7)

| count | value |
|---|---:|
| selections | 36 |
| dropped records | 4 |
| dropped pages / opportunities | 4 / 4 |
| later tool_recall opportunities | 0 |
| later identifier_scan opportunities | 0 |
| never-observed opportunities | 4 |
| ambiguous same-turn events | 0 |
| unmatched PageIds | 0 |

Descriptive rates:

- `would_drop_rate = 4/36 = 0.1111111111`;
- `later_tool_recall_rate = 0/4 = 0.0`;
- `later_identifier_scan_rate = 0/4 = 0.0`;
- `never_observed_rate = 4/4 = 1.0` — right-censored, not a safety result.

Per-shape all-valid counts:

| shape | sessions | selections | dropped records | dropped pages | later recall | later scan |
|---|---:|---:|---:|---:|---:|---:|
| read-once pressure | 3 | 19 | 2 | 2 | 0 | 0 |
| deliberate later re-read | 3 | 13 | 2 | 2 | 0 | 0 |
| dependency chain | 1 | 4 | 0 | 0 | 0 | 0 |

The dependency per-shape metrics are suppressed at n=1. The re-read shape had two dropped-page
opportunities but no later `tool_recall`; the dependency shape had no valid dropped-page opportunity.

### Informative-only sessions (n=2)

Both informative sessions were read-once-pressure attempts 1 and 16. Each persisted one dropped page
with `floor 17,702 < budget 24,000 < resident 32,870`.

| count | value |
|---|---:|
| sessions | 2 |
| selections | 15 |
| dropped records | 2 |
| dropped pages / opportunities | 2 / 2 |
| later tool_recall opportunities | 0 |
| later identifier_scan opportunities | 0 |
| never-observed opportunities | 2 |

Informative-only metrics are suppressed at n=2 under the existing minimum-three-session rule. No
informative-only rate is reported.

## 4. Exclusions and frozen-join reconciliation

All 18 attempts exited rc=0. Eleven were excluded by collector evidence gates:

- 10 had `sidecar_failures`;
- 11 had `sidecar_selections`;
- attempt 10 had only `sidecar_selections`: the sidecar reported 3 selections while the frozen shadow
  delta contained 4 records;
- the other 10 excluded attempts had both sidecar failures and selection-count mismatch.

The independent receipt validator found no quota, stop-rule, route-proof, digest, public/raw projection,
privacy, or file-mode errors.

A stable offline join was run over frozen per-attempt trace, coverage, and shadow-delta snapshots:

- shadow schema: OK, 103 records;
- join status: OK;
- join-valid sessions: 8;
- selections: 40;
- dropped records/pages: 4/4;
- later recall/scan: 0/0;
- candidate pins: 0.

The join's eighth valid session is attempt 10, which the join accepts but the collector excludes for the
stricter sidecar selection-count gate. It contributes four selections and no drops. The seven
collector-valid sessions match the collector aggregate exactly: 36 selections, 4 dropped records/pages,
4 opportunities, and no later recall/scan.

A global live join was attempted but is not used as batch evidence: the global shadow file changed during
review, and one collector-accepted session's live sidecar later reported a write failure after its frozen
snapshot. No global corpus count is claimed from that mutable view.

## 5. Interpretation

The ratified batch reached its authorized cap without meeting the 12-informative target. Read-once
pressure produced two informative sessions; the later-re-read and dependency shapes produced no
informative session. No later `tool_recall` or `identifier_scan` was observed in collector-valid sessions.

This is an underpowered descriptive result, not evidence that the prompts, model, or paging policy are
good or bad. The cause of the missing later events is UNVERIFIED. Candidate pins remain empty and
offline-only.

## 6. Claim ceiling

No causal, cost-saving, paging-quality, model-quality, determinism, availability, redaction, or safety
claim. `position_band`, `later_dependency_use`, and dependency distance remain UNVERIFIED. More sessions
or amended inputs would require a new ruling and freeze; this batch does not authorize broadening.

## 7. Evidence and repro

Committed aggregate-only artifacts:

- `reports/shadow-batch-20261128-aggregate.json`
- `reports/shadow-batch-20261128-aggregate.md`
- `reports/shadow-batch-20261128-frozen-join.json`

Private receipts and raw snapshots remain under
`~/.local/state/ctxvm/w8-runs/shadow-batch-20261128-ratified-v1/` and are not committed.

```bash
RUN=~/.local/state/ctxvm/w8-runs/shadow-batch-20261128-ratified-v1
python3 tools/shadow-selection-validate.py "$RUN/frozen-join-input/batch-shadow.jsonl"
python3 research/shadow-analysis/join.py \
  --shadow "$RUN/frozen-join-input/batch-shadow.jsonl" \
  --trace-dir "$RUN/frozen-join-input/traces" \
  --out "$RUN/frozen-join-repro" --repo .
python3 -m pytest tools/test_collect_shadow.py -q
python3 research/shadow-analysis/test_join.py -q
python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
```

The collector's committed no-model suite remains 59 tests + 107 subtests; join 6/6; Hermes shadow 17/17.

## 8. Applied

This result card, three aggregate-only artifacts, one four-pipe `reports/LOG02.md` row, one
`reports/RR-DAY-20261128.md` section, and a separate PROJECT-STATE delta. Raw traces, shadow records,
session ids, prompt bodies, and private host paths remain outside git. No push.
