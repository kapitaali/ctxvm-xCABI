# RR-NODE-0.1.1-LIVE-STUB-REVIEW-20261124 — independently re-run: live DSH replacement/stub path passes on local mock

Review lane, verify-then-record. Subject: DSH handoff 34 and the self-contained harness
`~/Documents/deepseek-harness/default-workspace/ctxvm-dsh-scaffold/stub-live-harness/run.mjs`. Date 2026-11-24.
No remote model call, no publish, no push.

## 1. Independent re-run

Executed the documented command unchanged:

```sh
node /home/theb/Documents/deepseek-harness/default-workspace/ctxvm-dsh-scaffold/stub-live-harness/run.mjs
```

Result: **rc=0**. New isolated run directory:
`~/Documents/deepseek-harness/default-workspace/ctxvm-dsh-scaffold/stub-live-run-2NXEqg`.

The harness builds/packs the staged 0.1.1 tracer, installs it as an external dependency into a temp adapter copy,
creates an isolated `DSH_HOME`/XDG state, starts the in-process mock, runs the real headless DSH CLI, appends a
durable replacement through a test-only plugin, and asserts the wire, projection, sidecar, schema, checker, and
replay. It stops the mock in `finally`.

## 2. Verified receipts from the new run

| check | observed result |
|---|---|
| mock requests | **2**: `tool_call_success`, `success` |
| request #2 tool-result bytes | exactly `[ctxvm: live replacement stub]\n  exact bytes  ` |
| trace | **8 events** |
| tool-result declarations | **1** |
| `page.evict` | **1**, original PageId, turn 0, exact stub text |
| `page.render(mode=stub)` | **1**, same PageId and turn 0 |
| live projection cache | version **3**, original page `status: "stub"`, hash `sha256:0af21cac`, tokens 4, seq 17 |
| sidecar | `stubWire: 1`, `stubDropped: "recoverable"`, `stubCount: 1`, exact `stubbedRefs` record, `evictedTokens: 4` |
| durable DSH log | replacement event found (`replacementSeen: true`) |
| v0.1 schema | **OK: all checks passed** |
| coverage checker | **consistent**, digest OK |
| Rust replay | **events=8, divergences=[], violations=[]** |

The trace itself contains the exact original bash PageId on the declaration, eviction, and stub render; the
replacement body is not declared as a second page. `turn.render` records `evictedTokens: 4`.

## 3. What this closes

The previously unproven **live DSH `tool/result` replacement path** is now proven in the real CLI/plugin runtime on
a local mock. This is stronger than the earlier file-level synthetic test: the replacement was appended through
`session.append()`, persisted in the durable session log, observed by the live adapter, reflected in the live
projection cache, sent in mock request #2, and emitted into the trace/sidecar.

## 4. Cleanup / scope

- No checkout file in ctxvm or `~/Apps/deepseek-harness` was modified by the harness; pre-existing WIP remains.
- No existing DSH profile or web process was changed. The staging `node_modules` symlink was removed; no mock
  server remains; no `ctxvm-node011-*` temp profile remains in the real DSH home.
- No remote-provider model/tool run, active paging, cost/quality/determinism/availability/redaction claim.
- The only remaining unproven item named by the DSH lane is a successful remote-provider run; the earlier attempt
  returned `401 User not found` before model output.
- No publish, registry action, default-on change, or push.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
