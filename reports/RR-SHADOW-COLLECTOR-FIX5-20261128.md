# RR-SHADOW-COLLECTOR-FIX5-20261128 — status provenance, absolute paths, and combined-stop classification

Lane: hermes/tools. Date: 2026-11-28. Authority: `RR-SHADOW-COLLECTOR-ACCEPTANCE-REVIEW-20261128` and
`design/experiment-runs/SHADOW-COLLECTOR-FIX4-PROMPT.md`.

Fix target: `4ca6469`. No model session, live batch, profile/gateway/model-config edit, restart, pin
activation, publish, or push.

## 1. What was done

1. **Unambiguous status parsing.** The parser now requires one complete status line, exactly one source,
   name, version, and register-count marker, and an anchored full match. Embedded or duplicate
   ` (source: …), name=` text fails closed, including text introduced through `$VAR` expansion.
2. **Command provenance proven before dispatch.** The collector queries `commands.catalog` and requires
   `/ctxvm-trace` to appear exactly once under `Plugin commands` and in `plugin_commands`. A same-named
   quick/built-in command shadows the plugin and fails preflight.
3. **Runtime result type handled truthfully.** The running Hermes 0.13.37 gateway returns `type="exec"` for
   plugin slash-command output, not `type="plugin"`. The collector accepts only `exec`/`plugin` after the
   catalog provenance proof; an `exec` result without that proof is rejected.
4. **Absolute paths required.** Relative `CTXVM_TRACE_DIR`, relative `XDG_STATE_HOME`, relative `HOME`
   defaults, relative `$VAR` expansion, and relative active-status paths now fail closed. No path is
   resolved against the collector's cwd.
5. **Combined-stop classification preserved.** Auth/model and route flags are evaluated before branching.
   A route contradiction wins the aggregate status: `STOPPED_MODEL_PROVIDER`, with both failure flags and
   reasons retained in the receipt and exit code 4.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
55 passed, 87 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Each fix was first demonstrated red with a focused regression, then green. New cases cover embedded and
duplicate source markers, `$VAR`-introduced slash text, quick-command shadowing, actual `exec` plugin
output, relative defaults/paths, and simultaneous auth plus route failure.

### Real read-only gateway probe

The active-status transport returned:

```text
{'enabled': True,
 'trace_dir': PosixPath('~/.local/state/ctxvm/traces'),
 'source': 'start (defaults)',
 'version': '0.13.37'}
ACTIVE_GATEWAY_STATUS_OK
```

The catalog reported `/ctxvm-trace` only under `Plugin commands`. A full `--preflight-only` run returned
rc=0 with `gatewayTraceSource=start (defaults)` and 21 baseline sessions. No model turn or session creation
occurred.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-28 run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks. Evidence:
`~/.local/state/ctxvm/ci/collector-fix5-full-20261128.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

Evidence: `~/.local/state/ctxvm/ci/collector-fix5-rehearsal-20261128.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits; test-only fake paths and credential shapes remain
  intentional negative fixtures.

## 3. Deviations and discoveries

- The review requested `result.type == "plugin"`, but the real gateway returns `type="exec"` for the plugin
  handler. Requiring `plugin` would block every live preflight. The implemented alternative follows the
  review's allowed path: explicitly prove no quick-command override through `commands.catalog`, then accept
  the runtime's `exec` result.
- Status parsing no longer relies on a non-greedy regex that can stop inside adversarial directory text.
- Relative paths are rejected rather than resolved with an unproven gateway cwd.

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
