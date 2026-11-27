# RR-SHADOW-COLLECTOR-FINAL-REVIEW-20261127 — two live-path blockers remain

Review lane, verify-then-record. Subject: `5d43b18`. Date 2026-11-27. No live session, model call, spend,
gateway/profile change, or push.

## 1. Prior blocker fixed

Missing, malformed, multiple, and wrong-SID coverage now writes a receipt, sets the route-stop flag, stops after
one attempt, writes `STOPPED_MODEL_PROVIDER`, and exits 4. The original re-review blocker is closed.

Verification remains green: collector 43 + 63 subtests, join 6, Hermes shadow 17, full CI, rehearsal 4/4, kit,
hygiene, compile/diff/privacy checks, and live no-model preflight.

## 2. Blocker A — client trace-dir binding does not reach the gateway

`tools/collect-shadow.py:77–81,924` sets `CTXVM_TRACE_DIR` in the Hermes CLI subprocess environment. Installed
Hermes executes `chat` turns in the already-running gateway (`hermes_cli/main.py:2642–2647`). The client-env
allowlist drops `CTXVM_TRACE_DIR` (`agent/session_client_env.py:22–29,67–76`), and `client_env_scope()` only binds
a ContextVar; it does not change gateway `os.environ` (`:112–136`). The plugin reads `os.environ` directly
(`packages/hermes/live/__init__.py:974–1022`).

No-model host probe:

```json
{
  "cli_env_trace_dir": "/bound/traces",
  "gateway_client_env_keeps_trace_dir": false,
  "gateway_os_environ_inside_client_env_scope": "/gateway/traces"
}
```

The claim that the plugin “cannot write to a different directory” is therefore false for an arbitrary
`--trace-dir`. Preflight must prove the gateway's effective trace directory and reject a different requested path,
or use a supported per-session transport. No gateway restart/config edit is authorized.

## 3. Blocker B — session-store route proof accepts contradictory evidence

`_session_store_route()` (`tools/collect-shadow.py:379–392`) combines the session column `model` with
`gateway_runtime.provider`, falling back to `billing_provider` only when runtime provider is absent. It ignores
`gateway_runtime.model` and any non-empty `billing_provider` disagreement. `store_ok` (`:609–614`) approves the
mixed record.

No-model probes:

```text
billing_provider=other, runtime provider=nous
  -> attempt valid=true, all_valid_sessions=1

column model=frozen, gateway_runtime.model=other/model
  -> attempt valid=true, all_valid_sessions=1
```

Both should fail closed. Hermes can rewrite billing route columns after accounted usage without changing
`model_config`, and model/provider must be taken from matching records. Require every present route source to
agree exactly; any contradiction stops the batch.

## 4. Required fixes

1. Bind collection to the gateway's actual trace directory. Reject arbitrary client-only overrides unless a
   supported gateway/session transport proves delivery.
2. Treat `model`, `billing_provider`, `gateway_runtime.model`, and `gateway_runtime.provider` as a consistency
   set: all present values must match the frozen route; missing required runtime proof fails closed.
3. Add no-model regressions for client/gateway trace-dir mismatch, billing-provider contradiction, runtime-model
   contradiction, and matching-route success.
4. Rerun focused suite, full CI, rehearsal, kit/hygiene, and hand back for final acceptance.

Nice-to-haves remain non-blocking: preserve original sidecar bytes, persist preflight facts, normalize remaining
preflight I/O errors, and assert non-null four-per-shape rate fields.

## 5. Verdict

**NOT ACCEPTED for live collection.** The conditional live batch remains blocked. No rates, pins, causal, cost,
paging, model, determinism, availability, or redaction claim.

## 6. Applied

This card, one four-pipe LOG02 row, a day-file section, a focused fix prompt, and a PROJECT-STATE precision update.
No collector code changed by review; no push.
