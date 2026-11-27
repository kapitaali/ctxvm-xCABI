# RR-SHADOW-COLLECTOR-FIX2-20261127 — route proof and stop semantics corrected

Lane: hermes/tools. Date: 2026-11-27. Authority: `RR-SHADOW-COLLECTOR-REREVIEW-20261127`,
`design/experiment-runs/SHADOW-COLLECTOR-FIX2-PROMPT.md`, and the owner-supplied five-item re-review.

Fix target: `7c54041`. No model session, live batch, profile/gateway/model-config edit, restart, pin
activation, publish, or push. Live collection remains blocked pending independent re-acceptance.

## 1. What was done

1. **Trace directory bound.** The subprocess environment now removes ambient `CTXVM_*` values but sets
   `CTXVM_TRACE_DIR` to the exact validated `cfg.trace_dir`. The plugin cannot write to a different directory.
2. **Missing SID corrected.** A missing/empty parsed SID excludes the attempt without setting the route-stop
   flag. A nonempty SID with unbound coverage does stop the batch.
3. **Baseline uniqueness.** Preflight parses the shadow baseline, fails closed on unreadable/malformed JSON or
   missing session IDs, and seeds the seen-session set. A pre-existing SID cannot receive quota credit.
4. **Auth/model signatures expanded.** Added missing API key, API key not provided, quota exceeded, rate limit
   exceeded, and model overloaded.
5. **Independent route proof.** Real 0.13.37 traces stamp `provider: unknown`, so exact provider cannot be
   proven from coverage alone. The collector now reads the bound profile's `state.db` session row and requires
   exact model/provider plus `gateway_runtime.fallback_active == false`. Only those route fields enter the
   private receipt; raw `model_config` is never emitted.
6. **Coverage stop.** Missing, malformed, duplicated, or SID-unbound coverage sets
   `model_provider_failure=true`, writes the normal receipt and aggregate with `STOPPED_MODEL_PROVIDER`, stops
   before another attempt, and exits 4. Known model/provider drift still stops even when the store row matches.
7. **Session-store preflight.** The profile store must exist, be readable, and expose the required `sessions`
   columns before any model call.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
43 passed, 63 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Each new fix was first demonstrated red with a focused regression, then green.

### Real no-model probes

A temporary SHA-256-pinned manifest was used with `--preflight-only`; no model session ran.

```text
PREFLIGHT_RC=0
{"baseline_sessions":21,...,"fallbackDisabled":true,"sessionStoreReady":true,
 "plugin_version":"0.13.37","profile":"w8-shadow","provider":"nous","target_informative":12}
PREFLIGHT_FACTS_OK
```

A direct read-only probe against one accepted live session returned:

```text
{'model': 'tencent/hy4-flash:free', 'provider': 'nous',
 'fallback_active': False, 'source': 'session_store'}
REAL_SESSION_STORE_ROUTE_OK
```

This resolves the real 0.13.37 `provider: unknown` conflict without changing the plugin or weakening the
frozen provider contract.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-27 run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks. Evidence:
`~/.local/state/ctxvm/ci/collector-fix2-full-20261127.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

Evidence: `~/.local/state/ctxvm/ci/collector-fix2-rehearsal-20261127.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits; two intentional fake-fixture lines remain in the test file.

## 3. Deviations and discoveries

- The repo's narrow fix prompt covered unbound coverage. The owner-supplied re-review added five related
  live-path issues; all six are addressed here.
- Exact provider proof uses the profile session store rather than plugin instrumentation. The store records
  `model`, `billing_provider`, and `model_config.gateway_runtime`; the collector reads only the route facts.
- Missing SID is an excluded attempt, while a present SID with unbound coverage is a route-stop. This keeps
  the two failure classes distinct.
- Aggregate output remains content-free; session-store route details are private receipt fields only.

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
