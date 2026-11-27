# RR-SHADOW-JOIN-RESULT2-20261127 — offline shadow join reaches OK with three valid sessions

Review/experiment lane, verify-then-record. Date 2026-11-27. Authority: owner-authorized collection after
`RR-SHADOW-JOIN-RESULT-20261127`; join implementation accepted in `RR-SHADOW-JOIN-FIX-REVIEW-20261127`.
No model-config, gateway, or profile change; no publish or push.

## 1. Two fresh sessions collected

Workspace: `/tmp/opencode/shadow-join-sessions` with two 57,620-byte files and three 25-byte files.
Prompt required sequential reads of `L1.md`, `L2.md`, `T1.md`, `T2.md`, `T3.md` and marker recall.

Model/provider: `tencent/hy4-flash:free` / `nous`. Host: Linux x86_64. Anonymous one-shot path; no named
`--create-if-missing` session. Hosted output is non-deterministic; no seed/interval applies.

| session | exit | shadow selections | persisted dropped pages | session failures | process failures |
|---|---:|---:|---:|---:|---:|
| `local-9d702745be8c6532813007785ff498fa7dcfff10d3ef8e9a842e02a61d3b9220` | 0 | 6 | 1 | 0 | 0 |
| `local-71891829af8efe13c6171e7c66274cf17b9b924f6503641166af05d988cb4f30` | 0 | 6 | 1 | 0 | 0 |

Both new traces pass coverage checker, v0.1 schema, and Rust replay: 8 events, 0 divergences, 0 violations.

## 2. Corpus gates

- Shadow schema: **OK (83 records)**.
- Sessions seen: **15**.
- Excluded: **12** old 0.13.36 sessions with the former process-global `shadowWriteFailures=2`.
- Valid: **3** 0.13.37 `w8-shadow` fresh-control sessions; minimum required is 3.
- Join status: **OK**.

Accepted session keys: `sha256:06b63f34cf135248`, `sha256:0a3f29a2791d6f73`,
`sha256:01ea04761ab34652`.

## 3. Counts and denominators

| count | value |
|---|---:|
| selections | 18 |
| dropped selections | 3 |
| dropped pages / page opportunities | 3 |
| unmatched PageIds | 0 |
| later tool_recall opportunities | 0 |
| later identifier_scan opportunities | 0 |
| never_observed opportunities | 3 |
| ambiguous same-turn events | 0 |

Every valid session contributed six selections and one persisted dropped page. No dropped PageId was
unmatched. No later matching fault, stub render, or eviction was observed for the three dropped pages.

## 4. Descriptive metrics

These are descriptive only, with n=3 sessions and n=3 page opportunities:

- `would_drop_rate = 3/18 = 0.1666666667`
- `later_tool_recall_rate = 0/3 = 0.0`
- `later_identifier_scan_rate = 0/3 = 0.0`
- `never_observed_rate = 3/3 = 1.0` — **right-censored, not evidence of safety**
- pressure (`resident/budget`): min 0.0425, mean 1.0756388889, max 1.429625
- floor pressure (`floor/budget`): min 0.0425, mean 0.964625, max 1.427
- drop share (`dropped/resident`): min 0.0, mean 0.0784799153, max 0.4814502275
- selection churn (Jaccard): min 0.0, mean 0.8, max 1.0

`candidate_pins=[]`: the offline nomination rule requires at least two sessions and three unique later
tool_recall events; this corpus has zero later tool_recall events. No pin is nominated or activated.

## 5. Interpretation and limits

The join now executes end to end and passes its preregistered three-session sufficiency gate. The result
shows only that, on this small forced-pressure corpus, the keep law would drop one page per session and no
later reuse was observed before session end.

It does **not** establish causal importance, safety, cost saving, paging quality, model quality,
determinism, availability, or redaction. `never_observed` is right-censored. `position_band` and
`later_dependency_use` remain UNVERIFIED because the sidecar/trace lack request order and a dependency graph.
More sessions and varied workloads are needed before interpreting rates; candidate pins remain offline-only
and any live use needs a separate owner ruling.

## 6. Repro

```bash
cd "$CTXVM_REPO"
python3 research/shadow-analysis/test_join.py -v
python3 tools/shadow-selection-validate.py \
  ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl
python3 research/shadow-analysis/join.py \
  --shadow ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl \
  --trace-dir ~/.local/state/ctxvm/traces \
  --out research/shadow-analysis/out
```

Expected current result: `OK`, valid sessions 3/3, 83 records, 3 dropped pages, no candidate pins, exit 0.

## 7. Applied

Updated `research/shadow-analysis/out/result.json`, this result card, the living join spec's current-state
section, LOG02/day, and PROJECT-STATE. Raw traces remain private. No publish or push.
