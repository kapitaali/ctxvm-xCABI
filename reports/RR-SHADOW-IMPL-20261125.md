# RR-SHADOW-IMPL-20261125 — shadow mode landed: one temp profile, hashed refs, offline-only candidates

Lane: hermes. Authority: owner ruling — "one named temporary opt-in profile, hashed refs only, and
candidate pins restricted to offline analysis unless a separate live-arm ruling is made." Design:
`RR-SHADOW-SPEC-20261124`. Version **0.13.33 → 0.13.34**, synced; gateway restart owed to operator.
No model call, spend, live arm, pin mutation, export, default-on, D17 action, or push.

## 1. Owner constraints, implemented

- **One named temporary profile:** `w8-shadow`, created as a full copy of the working control profile
  `w8cn-naive`, then patched only with `budgetTokens: 24000` + `shadowSelection: true`. Engine remains
  `compressor` (control), so the pure counterfactual planner is exercised. No other profile enables shadow.
- **Hashed refs only:** shadow `page_id` = `sha256(logicalRef|contentHash)`. No raw ref, body, stub text,
  arguments, prompt, answer, or absolute path enters the record.
- **Offline-only candidates:** shadow mode never mutates live `_pages`, `_pin_order`, demand state, or
  request. No candidate pin is applied. Any later live use needs a separate owner ruling.
- **Retention:** lifetime of `w8-shadow`. Records live under `<profile>/ctxvm-shadow/selection.jsonl`;
  deleting the temporary profile purges them. Directory 0700, file 0600.

## 2. Implementation

- `profile_policy.py`: `shadowSelection` boolean setting, default false, **no env channel**.
- `context_engine.py`: constructor/adoption support. Control profiles return early as before, but when
  shadow is on they call `_emit_shadow_plan()`: a fresh short-lived engine with a **local page table**
  initialized from the request, no live page/pin mutation, no request change. It emits a payload with
  `shadow=true`, `policyApplied=false`, `requestUnchanged=true`. Ctxvm sessions observe their real plan
  with `shadowSelection=true`, `policyApplied=true`.
- `live/__init__.py`: `_write_shadow_record()` writes the spec's content-free JSONL schema
  (`ctxvm-shadow-selection/v1`) with hashed dropped-page ids, per-session call index, policy hash,
  budget/resident/floor/dropped tokens, selection/prefix hashes, trigger, and `request_unchanged=true`.
  Control shadow payloads never overwrite the real `enginePlan`/tally. Write failure is fail-open for the
  request and increments visible `shadowWriteFailures`; coverage sidecar attests `shadowSelection` and
  the counter.

## 3. Tests + red-before (7 new, suite 254)

- profile setting/default/no-env;
- control shadow plan leaves request, live page table and pin order unchanged;
- shadow off/on return the same control result;
- record is hashed, private (0700/0600), content-free;
- two sessions produce disjoint records / call indexes;
- write failure increments the visible counter.

Red-before: returning the control request when shadow is on fails the no-perturbation test (rc=1);
restored → pass. Emitting a raw ref as `page_id` fails the privacy test (rc=1); restored → pass. A first
no-perturbation mutation targeted the helper's return path and did not exercise the control branch;
discarded, not counted. A backup-path typo during the privacy probe required direct line restoration;
the final suite proves the hashed expression is restored.

## 4. Verification

- `python3 -m pytest packages/hermes -q` → **254 passed, 15 subtests**.
- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 254+8+66; ts
  30+62+46+35 after the node/DSH lane's parallel updates).
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.34**, load check OK.
- Gateway-interpreter policy probe on `w8-shadow`: `engine compressor`, `budget 24000`,
  `shadowSelection true/settings`.
- Kit ALL PASS; hygiene OK; CJK/secret/home sweeps clean at close.

## 5. Limits / owed

No causal-importance, cost-saving, paging-quality, model-quality, or determinism claim. Later reuse is
a proxy, not truth; `never_observed` is right-censored, not safe. No live stub arm or candidate-pin
activation is authorized. Operator restart owed; review verification owed. The temporary profile and
its records remain until the owner deletes them.
