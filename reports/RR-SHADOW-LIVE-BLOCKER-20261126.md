# RR-SHADOW-LIVE-BLOCKER-20261126 — live control-shadow collection does not run; join remains blocked

Review lane, verify-then-record. Date 2026-11-26. Owner authorized fresh `w8-shadow` collection. One successful
free-model session was run; no publish, profile edit, restart, or push.

## 1. Live state

- Installed plugin: **0.13.35**.
- Gateway pid **3913**, started 09:57, serves `w8-shadow`; `sync-plugin.sh --check` confirms it holds 0.13.35.
- No restart was needed.
- The profile's previous default `meituan/longcat-2.5:free` now returns 404. The successful collection run used
  the currently available Nous free model `tencent/hy4-flash:free`.

## 2. Successful session, missing shadow output

Workspace: `/tmp/opencode/shadow-live-workspace` with four 130,021-byte files. Prompt asked the model to read all
four and return their markers. DSH exited rc=0 and returned all four markers.

Capture:
`~/.local/state/ctxvm/traces/local-0b6b2f710b79a56f2f835c7ee96996ed1ea0e0a0d7f1b53d2de7a820d0144bee.jsonl`

Coverage facts:
- `plugin.version: 0.13.35`
- `plugin.profile: w8-shadow`
- `plugin.engineSetting: compressor`
- `plugin.budgetTokens: 24000/settings`
- `plugin.engineSelections: 0`
- `plugin.engineEntered: 0`
- `plugin.shadowSelection: false`
- `plugin.shadowWriteFailures: 0`
- trace: 4 pages, 102,076 resident tokens — well over the 24,000 budget

Yet `~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl` does not exist. No shadow plan ran.

## 3. Two live-integration defects

### 3.1 Control profiles never invoke the shadow planner

Shadow planning is currently inside `CtxvmFaultPinEngine.select_context()`. Hermes does not call that engine for
`context.engine: compressor`, so the authorized control profile never reaches `_emit_shadow_plan()`.
`engineSelections=0` is direct evidence.

The host's `pre_api_request` hook already receives `request_messages`, `conversation_history`, `session_id`, and
`system_prompt` for every model request (`hermes-agent/agent/turn_api_request.py::_fire_pre_api_request_hook`).
That is the available insertion point for a pure control-shadow planner that does not alter the request.

### 3.2 Configured shadow flag is not attested live

Direct offline resolution of the same profile returns:

```text
engine=compressor budget=24000/settings shadowSelection=true/settings
```

The live sidecar nevertheless says `shadowSelection=false`. The per-session policy stamp is therefore not carrying
the configured value into the capture, even though profile/budget are present. The follow-up must make the stamp and
the planner use the same file-resolved policy module and session id, and expose the source (`settings`) for diagnosis.

## 4. Route to Hermes

1. Add a control-safe shadow invocation at `pre_api_request` (or another hook proven to run for compressor profiles),
   using the pure clone planner and never changing `request_messages`/the model-visible request.
2. Fix per-session policy stamping so `shadowSelection=true/settings` reaches `policy_by_session` and the coverage
   sidecar.
3. Add a live integration gate: a shadow-enabled compressor session under pressure must produce at least one valid
   `selection.jsonl` record, `engineSelections` may remain zero but a new `shadowSelections` counter must advance, and
   the sidecar must attest `shadowSelection=true`.
4. Preserve exact PageId, control-plan parity, schema validation, privacy, per-session isolation, and fail-open
   behavior from 0.13.35.

## 5. Join card status

`reports/RR-SHADOW-JOIN-20261126.md` is copied into the repo as a **blocked draft**. Its stale “no gateway” state was
corrected to the live pid/version and this collection failure. Research/experiment implementation should wait for
valid records; no rates or candidate pins can be computed now.

## 6. Scope / claim ceiling

No causal, cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim. No live stub
arm or candidate-pin use. Raw traces stay private. No repo code, profile, gateway, or model configuration was changed
by review; no publish or push.

## 7. Applied

This card, an append-only LOG row (four pipes), a day-file section, the corrected join draft, and a PROJECT-STATE
blocker update.
