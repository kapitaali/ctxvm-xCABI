# RR-SHADOW-LIVE-FIX-20261126 — control shadow collection wired through pre_api_request

Lane: hermes. Authority: `RR-SHADOW-LIVE-BLOCKER-20261126` route. Version **0.13.35 → 0.13.36**,
synced; gateway restart owed to operator. No profile/gateway/model-config edit, live model call, spend,
pin activation, export, default-on, D17 action, or push.

## 1. Live-integration defects fixed

- **Control profiles never called `select_context`.** `on_pre_api_request` now invokes the pure
  `_emit_shadow_plan()` clone planner when the per-session policy says `shadowSelection` and the
  engine is not ctxvm. It uses the host-provided `request_messages`, never mutates them, and leaves
  live page/pin/demand state untouched.
- **Configured shadow flag was not attested.** `_stamp_environment` now uses a **live-local by-path
  loader** for the sibling `profile_policy.py` — the same file the engine resolves, independent of
  stale profile-local bare imports and test-global patches. The per-session stamp carries
  `shadowSelection` and `shadowSelectionSource`; coverage attests both.

## 2. Counter + live gate

- `shadowSelectionsBySession` increments in `_record_plan` whenever a shadow record is emitted;
  coverage sidecar exposes `shadowSelections` and `shadowSelectionSource`.
- `ShadowLiveIntegrationTests` drives a compressor profile through the real hooks
  (`on_session_start` → page declarations → `pre_llm_call` → `pre_api_request` → flush) with a
  pressured request. It asserts: request bytes unchanged, a schema-valid `selection.jsonl` exists,
  `policy_applied=false`, `shadowSelection=true/settings`, `shadowSelections>0`, `engineSelections=0`,
  and `shadowWriteFailures=0`. No model call.

## 3. Verification

- Focused shadow tests **13 passed**; full Hermes suite **260 passed, 15 subtests**.
- Red-before: suppressing the pre-api shadow call fails the live integration test; dropping
  `shadowSelection` from the stamp fails it again; restored → 13 pass.
- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 260+8+66;
  ts 30+62+46+35).
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.36**, load check OK.
- Kit ALL PASS; hygiene OK; CJK/secret/home sweeps clean at close.

## 4. Limits / owed

No live shadow record is created by this card; collection still needs the operator restart to
0.13.36 and a real `w8-shadow` session. Fresh control parity only; stable control parity is not
claimed. Candidate pins remain offline-only. Exact PageId, schema validation, privacy, per-session
isolation and fail-open behavior from 0.13.35 are preserved. No causal, cost, paging-quality,
model-quality, determinism, availability, or redaction claim.
