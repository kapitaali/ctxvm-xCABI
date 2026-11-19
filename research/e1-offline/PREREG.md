# PREREG-E1 — Fault availability and label quality (Route A, zero spend)

Status: **FROZEN before scoring**, 2026-11-18 (Europe/Helsinki). Owner clearance: chat "E1 is cleared"
(2026-11-18); this replaces the earlier Gate 0 / data-choice hold. No model call, no paid cell,
no commit, no wire or corpus change. Not M1/M2, not a Part III route result.

## 0. Question (Part III §9.1)

How many faults of each source exist in the frozen corpus, and do the fault labels name pages well
enough that removing the named pages beats removing the same number of random pages?

## 1. Data freeze

- **Held-out set:** all 17 JSONL traces under `<ctxvm>/corpus/m*/*/*.jsonl`, copied into `traces/`
  with distinct `mNN__<basename>` names (the m2/m8 basename collision is removed by the prefix).
  Full original path is the unit; never basename flattening.
- **Expected split (to confirm, not assume):** 62 `page.fault` events = 41 `identifier_scan` +
  21 `tool_recall`, on 15 fault-bearing paths. No live traces, no pooling with the wired run.
- `manifest.sha256` pins every copied trace, `view-v1.py` and this prereg; `fault-counts.json`
  records per-file counts by source. Traces are private fixtures; reports carry counts/ids only.

## 2. View v1 (pure, versioned)

- Source: `view-v1.py`, sha256 `150d24cad23cf1b8ff16a066f109fd54bc3605a88e04424677fd098a558d5568`.
- Version label: `v1:150d24ca…`. Pure deterministic fold of events to per-turn declared pages,
  rendered pages, faults (source), resident/evicted token totals; no model call, no I/O, no randomness.
- Intervention replay uses only this view; no new event type, no replay-engine change.

## 3. Arms (fixed before scoring)

| Arm | Definition |
|---|---|
| Control | Faults exactly as recorded, counted per turn by source. |
| A — fault-label drop | At each turn, after counting faults, add every page named by a fault at that turn to a removed set for **subsequent** turns. Count faults recorded at each turn on pages not yet removed. |
| B — random-page, fixed seed | Same removal size per turn as A, but remove `k` uniformly sampled declared pages not already removed, using a fixed per-trace seed derived from the trace path (SHA-256 first 8 bytes). Count faults on remaining pages. |

Both interventions are offline view manipulations of a recorded trace; they do **not** claim what a
new policy or model would do. Sample size per arm = the same 17 traces.

## 4. Metric, stop rule, falsifier

- **Metric:** faults per turn = counted faults / number of turns in the trace, pooled by source;
  report raw counts and rates per arm and stratum, never pooled across sources.
- **Stop rule:** label advantage = `(B_rate − A_rate) / control_rate`. With `tool_recall` n = 21
  (≥10): if advantage ≤ 10 % for a source, record a **negative result** for that source. If both
  sources ≤ 10 %, record overall negative. If `tool_recall` n < 10, Route A is Blocked before any
  comparison. No interval is a significance claim at this n.
- **Falsifier:** A fails to beat B by >10 % on `tool_recall`; corpus counts fail to reproduce;
  manifest mismatch; or the view is non-deterministic on a second pass.
- **Deviations:** any change after the freeze is recorded with time, reason and before/after hash;
  frozen-input changes require owner ratification before application.
- **No GO:** this prereg authorizes no model call, no spend, no E2, no paid ablation.

## 5. Owner sign-off

- Decision: **GO**, owner chat "E1 is cleared" (2026-11-18); Gate 0 closed by `RR-PART3REVIEW-CLOSE`.
- Cost bracket: zero; route: none (offline only).
- Capability uplift / human gate: not applicable to a pure offline view; no policy ships.
- Deviation authority: research lane records; frozen-input changes need owner ratification.
