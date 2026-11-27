# RR-SHADOW-VARIED-RESULT-20261127 — six varied sessions complete; only mixed-2 persisted drops

Review/experiment lane. Date 2026-11-27. Authority: owner-approved
`design/experiment-runs/SHADOW-VARIED-20261127.md`. No profile/gateway/model-config change, publish, or push.

## 1. Execution

Six anonymous one-shot sessions ran on Hermes 0.13.37, profile `w8-shadow`, fresh control mode, budget 24,000,
model `tencent/hy4-flash:free` / `nous`. A per-session `--max-turns 20` override allowed the approved multi-file
prompts without editing the profile. All six exited rc=0.

| shape | session | selections | dropped records | dropped pages | max resident | outcome |
|---|---|---:|---:|---:|---:|---|
| many-small | `local-bfab…` | 2 | 0 | 0 | 15,353 | below budget; no pressure |
| many-small | `local-fe08…` | 2 | 0 | 0 | 15,353 | below budget; no pressure |
| medium-middle | `local-2aa5…` | 7 | 0 | 0 | 53,419 | final floor 27,807 > budget; floor-bust no-op |
| medium-middle | `local-43dc…` | 2 | 0 | 0 | 28,883 | floor 28,883 > budget; floor-bust no-op |
| mixed | `local-2707…` | 2 | 0 | 0 | 40,089 | floor 39,010 > budget; floor-bust no-op |
| mixed | `local-f8a8…` | 9 | 2 | 6 | 57,133 | **informative**: two persisted drop records |

The informative session's drop shapes were:

- `floor 20,907 < budget 24,000 < resident 57,071`, 3 dropped pages;
- `floor 3,434 < budget 24,000 < resident 57,133`, 3 dropped pages.

Per the frozen stop rule, no prompt was broadened and no third attempt was run for a no-drop shape.

## 2. Trace and sidecar checks

All six traces pass:

- coverage checker: consistent, digest OK;
- v0.1 schema: OK;
- Rust replay: 0 divergences, 0 violations.

All six sidecars are 0.13.37, `shadowSelection=true`, with zero session and process write failures.

## 3. Updated aggregate join

- Shadow schema: **OK (107 records)**.
- Sessions seen: **21**; valid: **9**; excluded: **12** old 0.13.36 global-failure captures.
- Join status: **OK**.

| count | value |
|---|---:|
| selections | 42 |
| dropped selections | 5 |
| dropped pages / opportunities | 9 |
| unmatched PageIds | 0 |
| later tool_recall opportunities | 0 |
| later identifier_scan opportunities | 0 |
| never_observed opportunities | 9 |
| ambiguous same-turn events | 0 |

Descriptive metrics:

- `would_drop_rate = 5/42 = 0.1190476190`
- `later_tool_recall_rate = 0/9 = 0.0`
- `later_identifier_scan_rate = 0/9 = 0.0`
- `never_observed_rate = 9/9 = 1.0` — right-censored, not safety
- pressure: min 0.0425, mean 1.1590277778, max 2.3805416667
- floor pressure: min 0.0425, mean 0.9338670635, max 2.3272083333
- drop share: min 0.0, mean 0.0637649684, max 0.6330886089
- selection churn: min 0.0, mean 0.8787878788, max 1.0

`candidate_pins=[]`: no later tool_recall events occurred.

## 4. Interpretation

The varied batch confirms that workload shape matters:

- many-small pages stayed below budget and produced no drops;
- medium/mixed workloads often hit a protected floor above budget, producing no-op plans;
- one mixed session reached an evictable middle and produced six dropped pages.

The pooled rates describe these nine sessions only. They do not establish causal importance, safety, cost saving,
paging quality, model quality, determinism, availability, or redaction. `position_band` and `later_dependency_use`
remain UNVERIFIED. More varied informative sessions are needed before treating the rates as stable; candidate
pins remain offline-only and inactive.

## 5. Repro

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

Expected: OK, 9 valid sessions, 107 records, 42 selections, 9 dropped pages, no candidate pins, exit 0.

## 6. Applied

Updated `research/shadow-analysis/out/result.json`, this result card, the living join spec, LOG02/day, and
PROJECT-STATE. Raw traces remain private. No publish or push.
