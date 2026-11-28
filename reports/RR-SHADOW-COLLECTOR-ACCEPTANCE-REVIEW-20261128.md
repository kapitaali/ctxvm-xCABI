# RR-SHADOW-COLLECTOR-ACCEPTANCE-REVIEW-20261128 — three blockers remain at 4ca6469

Review lane, verify-then-record. Subject: `4ca6469` (and route-consistency fix `5e8f637`). Date 2026-11-28.
No live session, model call, spend, gateway/profile change, or push.

## 1. What passed

- Collector: **51 passed, 82 subtests**.
- Join: **6 passed**.
- Hermes shadow: **17 passed**.
- Full CI and committed rehearsal: **4/4 green**.
- Kit/hygiene/compile/diff/privacy checks pass.
- Active-status query uses `command.dispatch` and checks plugin version.
- Session-store route consistency now rejects contradictory column/billing/runtime evidence in the tested cases.

## 2. Blocker A — status parser can hide a slash override

`_parse_trace_status()` (`tools/collect-shadow.py:125`) uses a non-greedy regex that stops at the first
` (source: …), name=` inside the directory text. Probe:

```text
enabled=True, dir=/safe (source: env CTXVM_TRACE_DIR), name=x (source: slash command), version=0.13.37
```

returned `trace_dir=/safe`, `source=env CTXVM_TRACE_DIR`. The actual directory is the full slash-override path.
The allowlist therefore does not reliably prove “no slash override.” Parse the status fields structurally or
anchor the source/name fields at the end; reject ambiguous/multiple source markers.

## 3. Blocker B — relative defaults resolve against the collector cwd

`_gateway_trace_dir()` (`:100–103,118,132`) and active-status normalization (`:1090–1095`) call `.resolve()`
in the collector process. The plugin default resolver can return a relative path unchanged. With
`XDG_STATE_HOME=relative-state`, the collector produced
`/home/theb/Documents/ctxvm/relative-state/ctxvm/traces`; a gateway with another cwd would write elsewhere.
Reject non-absolute raw gateway paths or resolve them using the gateway process's cwd.

## 4. Blocker C — simultaneous auth and route failure loses route-stop classification

At `:938–943` the auth branch breaks before `route_failure` is set; `:951–960` emits `STOPPED_AUTH_MODEL`.
No-model probe with a route contradiction plus rc=401 produced:

```text
status=STOPPED_AUTH_MODEL
auth_model_failure=true
model_provider_failure=true
```

It stops and exits 4, but the design requires every route contradiction to write `STOPPED_MODEL_PROVIDER`.
Evaluate both flags before branching and define a deterministic combined status/receipt that preserves the
route-stop classification.

## 5. Required fix

1. Make status parsing unambiguous and fail closed on embedded/duplicate source markers.
2. Reject relative gateway defaults or resolve with gateway cwd proof.
3. Preserve route-stop status when auth/model and route failures occur together.
4. Add no-model regressions for all three, including slash text introduced through `$VAR` expansion.
5. Rerun focused suite, full CI, rehearsal, kit/hygiene, and hand back for acceptance.

Nice-to-haves: preserve original sidecar bytes, persist preflight facts, normalize attach errors, re-query active
status before attempts, and assert non-null per-shape rates.

## 6. Verdict

**NOT ACCEPTED for live collection.** The conditional live batch remains blocked. No rates, pins, causal, cost,
paging, model, determinism, availability, or redaction claim.

## 7. Applied

This card, one four-pipe LOG02 row, a day-file section, a focused fix prompt, and a PROJECT-STATE precision update.
No collector code changed by review; no push.
