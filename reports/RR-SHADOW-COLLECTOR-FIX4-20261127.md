# RR-SHADOW-COLLECTOR-FIX4-20261127 — active gateway trace status proven read-only

Lane: hermes/tools. Date: 2026-11-27. Authority: owner-supplied final re-review of `5e8f637`.

Fix target: the sole remaining blocker — `/proc/<pid>/environ` proves launch state, not the plugin's active
trace state after `/ctxvm-trace start` or `stop --hard`. No model session, live batch, profile/gateway/model-
config edit, restart, pin activation, publish, or push.

## 1. What was done

1. **Exact launch resolver mirror.** `_gateway_trace_dir()` now mirrors the plugin's `_resolve_trace_dir()`:
   `CTXVM_TRACE=0/off/false/no` disables; an empty `CTXVM_TRACE_DIR` disables; unset uses the default state
   directory; paths expand `~` and `$VAR` in the same order and resolve to absolute paths.
2. **Active gateway query.** Preflight now calls the running gateway's read-only `command.dispatch` RPC with
   `name=ctxvm-trace`, `arg=status`, and a baseline session ID. It uses a single-use attach ticket, never logs
   or returns the ticket, and ignores event frames until the matching JSON-RPC answer arrives.
3. **No active override.** The active status must report `enabled=True`, the exact requested directory, the
   same plugin version, and a non-override source. Slash-command overrides and process-disabled states fail
   closed.
4. **Launch and active state must agree.** The `/proc` launch environment and the live plugin status must
   resolve to the same validated trace directory. A client-only `CTXVM_TRACE_DIR` is no longer accepted as
   proof.
5. **No plugin change required.** The existing `/ctxvm-trace status` command is the transport. No plugin
   version bump, installed-copy sync, gateway restart, or configuration change was needed.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
51 passed, 82 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

New regressions cover disable values, empty directories, default paths, `~`/`$VAR` expansion, active-status
parsing, read-only RPC shape, ticket non-disclosure, matching state, path mismatch, slash override, disabled
state, and plugin-version mismatch. Each fix was demonstrated red before green.

### Real read-only gateway probe

A direct call to the active-status transport returned:

```text
{'enabled': True,
 'trace_dir': PosixPath('~/.local/state/ctxvm/traces'),
 'source': 'start (defaults)',
 'version': '0.13.37'}
ACTIVE_GATEWAY_STATUS_OK
```

A full `--preflight-only` run with a temporary SHA-256-pinned manifest returned rc=0 and:

```text
{"baseline_sessions":21,...,"fallbackDisabled":true,
 "gatewayTraceDir":"~/.local/state/ctxvm/traces",
 "gatewayTraceSource":"start (defaults)","plugin_version":"0.13.37",
 "profile":"w8-shadow","provider":"nous","sessionStoreReady":true,
 "target_informative":12}
PREFLIGHT_FACTS_OK
```

No model turn or session creation occurred; the query reused an existing baseline session ID.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-27 run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks. Evidence:
`~/.local/state/ctxvm/ci/collector-fix4-full-20261127.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

Evidence: `~/.local/state/ctxvm/ci/collector-fix4-rehearsal-20261127.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits; test-only fake paths and credential shapes remain
  intentional negative fixtures.

## 3. Deviations and discoveries

- The earlier `/proc` check is retained as launch-state proof, but it is no longer treated as active-state
  proof.
- The active query uses the plugin's existing slash-command dispatcher rather than adding a new plugin RPC
  method, so the running 0.13.37 gateway can prove status without restart.
- `websocket-client` is already present in the Hermes runtime. The collector fails closed if it is absent;
  CI uses an injected fake transport and makes no network call.

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
`handoff/PROJECT-STATE.md` remains review-lane owned. No push.
