MASTER PROMPT — hermes/tools lane: fix gateway trace-dir binding and route consistency

Authority: `reports/RR-SHADOW-COLLECTOR-FINAL-REVIEW-20261127.md`. The prior coverage-stop blocker is fixed.
Two live-path blockers remain. No live sessions or gateway/profile/config changes.

## 1. Gateway trace directory

`CTXVM_TRACE_DIR` in the Hermes CLI subprocess does not reach the already-running gateway's `os.environ`; the
client-env allowlist drops it and `client_env_scope()` is only a ContextVar. Preflight must prove the gateway's
effective trace directory and reject any requested `--trace-dir` that differs, unless a supported per-session
transport is implemented and tested. Do not restart or reconfigure the gateway.

## 2. Route evidence consistency

`_session_store_route()` currently accepts mixed evidence. Require exact agreement among every present source:

- session column `model`;
- `billing_provider` when non-empty;
- `gateway_runtime.model` when present;
- `gateway_runtime.provider` when present;
- `fallback_active is False`.

Missing required runtime proof or any contradiction must set the route-stop flag, write a receipt, stop before
another attempt, write `STOPPED_MODEL_PROVIDER`, and exit 4.

## 3. Tests

Add no-model regressions for:

1. requested trace dir differs from effective gateway trace dir;
2. matching gateway trace dir passes;
3. billing provider contradicts runtime provider;
4. runtime model contradicts column model;
5. all route sources matching passes;
6. each contradiction stops after one attempt with exit-4 semantics.

Run collector suite, full CI, rehearsal, kit, hygiene, diff, privacy checks. Append one four-pipe LOG02 row and day
section. Private index; no push. Live batch remains blocked until final review acceptance.
