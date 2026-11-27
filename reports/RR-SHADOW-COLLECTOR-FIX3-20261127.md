# RR-SHADOW-COLLECTOR-FIX3-20261127 — gateway path and route consistency corrected

Lane: hermes/tools. Date: 2026-11-27. Authority: `RR-SHADOW-COLLECTOR-FINAL-REVIEW-20261127`,
`design/experiment-runs/SHADOW-COLLECTOR-FIX3-PROMPT.md`, and the owner-supplied four-item final re-review.

Fix target: `5d43b18`. No model session, live batch, profile/gateway/model-config edit, restart, pin
activation, publish, or push. Live collection remains blocked pending independent re-acceptance.

## 1. What was done

1. **Gateway trace directory proven.** Preflight reads the gateway lock PID and `/proc/<pid>/environ`
   read-only. It resolves the gateway's effective `CTXVM_TRACE_DIR`, or the default
   `$XDG_STATE_HOME/ctxvm/traces` / `$HOME/.local/state/ctxvm/traces`, and rejects any different requested
   `--trace-dir`. The client subprocess environment remains bound, but is no longer treated as proof.
2. **Frozen stop semantics restored.** The latest final review supersedes fix2's stricter coverage-stop
   behavior. Digest, schema, checker, replay, missing/malformed/multiple/wrong-SID coverage failures now
   exclude the attempt, as the frozen prereg requires. The independent session-store route is still queried;
   only auth/model route failure stops the batch.
3. **Route evidence made consistent.** Session column `model`, non-empty `billing_provider`, present
   `gateway_runtime.model`, present `gateway_runtime.provider`, and `fallback_active` must agree exactly with
   the frozen route. Missing runtime model/provider proof fails closed. Contradictions stop after one attempt
   with `STOPPED_MODEL_PROVIDER` and a receipt.
4. **Auth/model normalization added.** Separator normalization now catches `missing_api_key`,
   `API key is missing`, `insufficient_quota`, `quota_exceeded`, `rate_limit_exceeded`, and
   `model_overloaded` alongside the existing signatures.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
46 passed, 73 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Each fix was first demonstrated red with a focused regression, then green.

### Real no-model probes

A temporary SHA-256-pinned manifest was used with `--preflight-only`; no model session ran.

```text
PREFLIGHT_RC=0
{"baseline_sessions":21,...,"fallbackDisabled":true,
 "gatewayTraceDir":"~/.local/state/ctxvm/traces",
 "plugin_version":"0.13.37","profile":"w8-shadow","provider":"nous",
 "sessionStoreReady":true,"target_informative":12}
PREFLIGHT_FACTS_OK
```

A direct read-only probe against one accepted live session returned matching column, billing, and runtime
route evidence with `consistent: true` and `fallback_active: false`.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-27 run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks. Evidence:
`~/.local/state/ctxvm/ci/collector-fix3-full-20261127.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

Evidence: `~/.local/state/ctxvm/ci/collector-fix3-rehearsal-20261127.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits; two intentional fake-fixture lines remain in the test file.

## 3. Deviations and discoveries

- The repo fix3 prompt listed two blockers. The owner-supplied final re-review listed four; all four are
  addressed here.
- The earlier coverage-stop requirement conflicted with the frozen prereg. The latest final review explicitly
  rejected that stricter behavior, so evidence failures again exclude attempts while route/auth failures stop.
- Gateway environment proof uses Linux `/proc`; this collector is already Linux-scoped.
- Route consistency details remain private receipt fields; aggregate output remains content-free.

## 4. Limitations and open questions

- Independent re-acceptance is still required. This card does not claim acceptance.
- Research/experiment still owns the real frozen fixture manifest and prompt freeze.
- No live session, metric, pin, causal, cost, paging, model, determinism, availability, or redaction claim was
  produced. `position_band`, `later_dependency_use`, and dependency distance remain UNVERIFIED.

## 5. Repro commands

```bash
for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done
python3 -m pytest tools/test_collect_shadow.py -q
python3 research/shadow-analysis/test_join.py -v
python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
python3 -m py_compile tools/collect-shadow.py tools/test_collect_shadow.py
bash tools/run-ci.sh
python3 tools/ci-rehearsal.py
bash tools/check-handoff.sh
bash tools/git-hygiene.sh
git diff --check
```

## 6. Applied

This report, one four-pipe `reports/LOG02.md` row, and one `reports/RR-DAY-20261127.md` section.
`handoff/PROJECT-STATE.md` remains review-lane owned and continues to record the live block. No push.
