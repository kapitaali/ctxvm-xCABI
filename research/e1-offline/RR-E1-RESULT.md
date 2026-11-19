# RR-E1-RESULT — offline E1 replay: mixed outcome, no answer claim

Date: 2026-11-18 (Europe/Helsinki). Prereg: `PREREG.md` (frozen before scoring).
Owner clearance: chat "E1 is cleared". No model call, no spend, no commit, no
wire/corpus change. Run executed in the writable workspace copy of `e1-offline`;
the frozen inputs are byte-identical to `~/research/e1-offline` (manifest verified).

## Commands

```
sha256sum -c manifest.sha256        -> 19/19 OK
python3 replay1.py --list           -> 17 traces, expected 41/21, no scoring
python3 replay1.py | tee logs-e1.txt
```

## Freeze and reproduction

- View `v1:150d24ca…`; 17 traces copied with distinct prefixed names (m2/m8
  basename collision removed); full original path preserved in `path-map.json`.
- `SOURCE_REPRODUCE true`: control counts **41 identifier_scan / 21 tool_recall**
  on **15** fault-bearing paths, matching the prereg and `fault-counts.json`.
- All 17 items printed `OK`; no `FAIL`; view deterministic on second pass;
  bounded input (max 20,000 events/file) never approached.
- Total turns scored: **96**.

## Counts and rates (control / A fault-label drop / B random fixed seed)

| Source | Control | A | B | Control rate | A rate | B rate |
|---|---|---|---|---|---|---|
| identifier_scan | 41 | 40 | 41 | 0.4271 | 0.4167 | 0.4271 |
| tool_recall | 21 | 12 | 21 | 0.2188 | 0.1250 | 0.2188 |

Verbatim runner output:

```
COUNTS {"A":{"identifier_scan":40,"tool_recall":12},"B":{"identifier_scan":41,"tool_recall":21},"control":{"identifier_scan":41,"tool_recall":21},"turns":96}
ADVANTAGE {"identifier_scan":0.02439024390243894,"tool_recall":0.42857142857142855}
PER_SOURCE {"identifier_scan":true,"tool_recall":false}
VERDICT LABEL-QUALITY SIGNAL ONLY: no answer/model claim; E2 still owner-gated
```

## Interpretation under the prereg stop rule

- `tool_recall` n = 21 ≥ 10, so the comparison is valid. Its label advantage is
  **42.9 % > 10 %**: the fault-named pages are much better at predicting later
  faults than same-size random removals. That is a **label-quality signal only**.
- `identifier_scan` advantage is **2.4 % ≤ 10 %**: on this source the labels are
  indistinguishable from random at this scale — a **negative result** for that source,
  reported with equal prominence. It matches Part I §17's "close to definitional"
  warning for rendered-page identifier scans.
- Overall verdict is **mixed**, not a GO. Per the prereg: no answer, model-quality,
  paging, cost/saving or E2 claim. No cost-saving claim (law 7); no model-output
  determinism claim — only the view fold is deterministic.
- Arm B equals control exactly; random removals avoided no recorded faults. Arm A's
  reduction is confined to faults on pages that fault again later in the same trace.
  This measures label quality on recorded traces, not the behaviour of a new policy.

## Limitations and deviations

- n = 21 `tool_recall` events across 15 fault-bearing paths; intervals are not
  significance claims. No development/train split: all frozen corpus traces were
  scored, as preregistered.
- The runner was executed from the writable workspace copy because the original
  `~/research` tree is read-only under this session; no frozen input was changed.
- No deviation from the prereg was applied. `result.json` and `logs-e1.txt` are
  outputs, not frozen inputs; their hashes are not in the freeze manifest.
- Earlier toolkit errors (variant glob, JS draft, route-format fix in M2) are not
  part of this experiment and are not reconciled here.

## Consequence

E1 is now **recorded**, not merely cleared. Route A has one positive label-quality
signal (`tool_recall`) and one negative source (`identifier_scan`). Any paid
ablation (E2) still needs a fresh owner decision and cost bracket. M1 is closed
no-go, M2 closed invalid/inconclusive, and this result is not pooled with either.
