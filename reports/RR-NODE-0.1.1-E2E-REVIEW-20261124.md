# RR-NODE-0.1.1-E2E-REVIEW-20261124 — file-level DSH capture → trace → sidecar → checker/replay verified

Review lane, verify-then-record. Follow-up to `RR-NODE-0.1.1-STAGE-REVIEW-20261124`. Subject: staged
`@ctxvm/node@0.1.1` + staged DSH adapter, exercised offline against a real DSH session log and a synthetic
single-node replacement session. Date 2026-11-24. $0, no model call, no plugin install, no publish, no push.

## 1. Real DSH session log (mirror path)

Source: `~/Documents/deepseek-harness/session-jsons/w22-plana-session.jsonl` (28 committed session events).
Fed each event through the staged adapter's real `ensureTracer` / `mapEvent` / `flushTracer` path in a temp copy.

Result:
- **7-event** v0.1 trace + exact-byte coverage sidecar written;
- v0.1 validator: **all checks passed**;
- coverage checker: **consistent**, digest OK;
- Rust replay: **divergences=[]**; one `faultOfResidentPage` violation from the session's identifier scan on a
  resident page — expected mirror behavior, not a stub or adapter failure;
- sidecar: `adapter=dsh`, `capabilities.stubWire=1`, `stubDropped=off`, `stubbedRefs=[]`, 3 pages, 1 turn.

This verifies the adapter can ingest a real DSH event stream and emit a schema-valid, checker-consistent capture
without a live plugin runtime.

## 2. Synthetic DSH replacement session (stub path)

Built a 7-event DSH session envelope with `request/header`, `turn/start`, `tool/call`, append-origin `tool/result`,
single-node replacement `tool/result`, and assistant usage. Ran the same offline adapter path.

Result:
- **6-event** v0.1 trace + sidecar;
- exactly **1** `page.declare`, **1** `page.evict`, **1** `page.render(mode=stub)`;
- evict and stub render share the exact original PageId and turn 0; `stubText` byte-preserved;
- sidecar: `stubDropped=recoverable`, `evictedTokens=4`, `stubCount=1`, one exact `stubbedRefs` record;
- v0.1 validator: **all checks passed**;
- Rust replay: **divergences=[]**, **violations=[]**;
- coverage checker: **consistent**, digest OK.

This is the file-level end-to-end proof that the DSH replacement path produces the wire and sidecar the checker
expects, using the external packed 0.1.1 tracer.

## 3. What remains unproven

- No live DSH plugin install or live replacement event was performed; the plugin runtime wiring itself was not
  exercised.
- No live model call, active paging, cost/quality/determinism/availability/redaction claim.
- The accepted Part C live stub-arm attestation/re-read gap is unchanged.
- Public npm remains unpublished; this evidence is pre-publication verification only.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
