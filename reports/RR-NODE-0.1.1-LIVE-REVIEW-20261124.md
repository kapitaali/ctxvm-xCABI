# RR-NODE-0.1.1-LIVE-REVIEW-20261124 — live DSH plugin run succeeds on local mock; external provider auth blocks real-model run

Review lane, verify-then-record. Subject: staged `@ctxvm/node@0.1.1` + staged DSH adapter, run through the actual
DeepSeek Harness CLI/plugin runtime. Date 2026-11-24. No publish, no push. One external provider auth attempt was
made at the owner's request; it returned 401 before any model output. The completed run used the repo's local mock
LLM server and made no external model call or spend.

## 1. Setup (reversible, temp-only)

- Packed/installed the staged 0.1.1 tracer into a temp adapter copy at
  `/tmp/opencode/ctxvm-node-0.1.1-stage/packages/deepseek`.
- Created two temporary DSH profiles under `~/.dsh/profiles/`:
  - `ctxvm-node011-live` — OpenRouter free model attempt;
  - `ctxvm-node011-mock` — local `llm-mock-server`, `anthropic-messages`, model `mock-model`.
- Redirected `XDG_STATE_HOME` to `/tmp/opencode/dsh-live-*` so normal trace storage was untouched.
- Removed both temp profiles after the run. The existing DSH web process (pid 5800) was not restarted or modified.

## 2. External provider attempt — instrument/provider failure, not adapter failure

Profile loaded the adapter (`[ctxvm] apply called`, projection registered), created a session, received DSH events,
and flushed a trace + sidecar. The model request then failed:

```text
dsh: AUTH: 401: {"message":"User not found.","code":401}
```

The resulting 5-event trace passed v0.1 schema, Rust replay (`divergences=[]`, `violations=[]`), and the coverage
checker. Sidecar carried `adapter=dsh`, `capabilities.stubWire=1`, `stubDropped=off`. This verifies live plugin load
and flush even on the error path, but it is **not** a successful real-model run.

## 3. Local mock live run — success

Ran the real headless DSH app with the temp mock profile and the staged adapter. Scripted model behavior:
`tool_call_success` → `success`; tool call:

```json
{"command":"echo CTXVM_NODE_011_LIVE","description":"Print the live marker"}
```

Observed:
- DSH exited **rc=0**;
- bash tool executed and returned `CTXVM_NODE_011_LIVE\n` with `status=completed`;
- adapter logged `session/created`, `session/event`, `session/disposed`, and `trace written`;
- wrote a **7-event** v0.1 trace + exact-byte coverage sidecar;
- trace contains the bash `page.declare` with the exact tool identity and content hash;
- v0.1 validator: **all checks passed**;
- Rust replay: **divergences=[]**; one `faultOfResidentPage` from the adapter's identifier scan seeing the just-
  returned marker in the model text — expected mirror behavior;
- coverage checker: **consistent**, digest OK;
- sidecar: `adapter=dsh`, `stubWire=1`, `stubDropped=off`, `stubbedRefs=[]`, 3 pages, 1 turn.

Artifacts:
- `/tmp/opencode/dsh-live-mock-state-2/ctxvm/traces/session-5d62aaba-73fc-4381-8abb-79731a890476-1795551796383.jsonl`
- matching `.coverage.json`

## 4. What this proves / does not prove

**Proves:** the staged 0.1.1 package loads as an external dependency in the real DSH plugin runtime; the adapter
receives live session events, maps a successful tool result, flushes trace + sidecar, and produces artifacts that
pass schema, replay, and checker.

**Does not prove:** a live DSH `tool/result` replacement event (the passive stub path), active paging, model quality,
cost, determinism, availability, or redaction. The live stub path remains file-level/synthetic only; the accepted
Part C live stub-arm gap is unchanged.

## 5. Scope / cleanup

No package publish, registry action, default-on change, active paging, or push. No existing DSH profile or source
file was modified. Temp profiles removed; mock server stopped; existing web process untouched. No cost-saving or
paging-quality claim.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
