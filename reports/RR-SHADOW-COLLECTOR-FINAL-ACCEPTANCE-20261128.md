# RR-SHADOW-COLLECTOR-FINAL-ACCEPTANCE-20261128 — collector accepted at 7c53889

Review lane, verify-then-record. Subject: `7c53889`. Date: 2026-11-28.
No live model call, session creation, profile/gateway/config change, restart, pin activation, publish, or push.

## 1. Verdict

**ACCEPTED for the authorized conditional live batch.** Independent re-review found no residual
implementation defect, and local verification reproduced the acceptance evidence.

Acceptance does not start collection. Execution still requires:

1. the research-owned frozen fixture manifest and prompts;
2. a fresh successful preflight against the active 0.13.37+ gateway immediately before the batch.

The authorized limits remain unchanged: at most 18 anonymous one-shot attempts on
`tencent/hy4-flash:free` / `nous`, at most six per shape, stopping at 12 new informative sessions or 18
attempts. Candidate pins remain offline-only.

## 2. Accepted behavior

Independent re-review and local no-model probes confirm:

- raw `HOME`, `XDG_STATE_HOME`, and explicit `CTXVM_TRACE_DIR` surrounding whitespace fails closed;
- clean absolute, `~/`, and `$VAR` paths remain accepted;
- active-status path whitespace fails closed before resolution;
- catalog provenance validates every plugin-command entry, category, and pair;
- malformed discovery evidence and discovery failures reject before `command.dispatch`;
- benign non-discovery warnings remain allowed;
- prior status-parser, command-shadowing, gateway route-proof, missing-coverage, and combined
  auth/route-stop fixes remain intact;
- a route contradiction retains `STOPPED_MODEL_PROVIDER` when auth/model failure is also present.

## 3. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
59 passed, 107 subtests passed

$ python3 research/shadow-analysis/test_join.py -q
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Additional local probes rejected whitespace in default and explicit path branches, accepted clean
absolute/tilde/`$VAR` controls, rejected malformed categories/pairs/plugin entries, and proved malformed
catalog evidence sends only `commands.catalog` with no `command.dispatch`.

### Full gate and committed rehearsal

```text
$ bash tools/run-ci.sh
ALL GATES GREEN

$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

The CI run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks.
`check-handoff.sh`, `git-hygiene.sh`, compile, diff, AST-duplicate, CJK, and production secret/home-path
sweeps also pass.

### Fresh read-only preflight

The active gateway returned enabled status at the expected trace directory on plugin 0.13.37. A full
`--preflight-only` run with a temporary synthetic SHA-256-pinned manifest returned rc=0 with:

```text
plugin_version=0.13.37
model=tencent/hy4-flash:free
provider=nous
profile=w8-shadow
budgetTokens=24000
shadowSelection=true
selectionMode=fresh
stubDropped=off
fallbackDisabled=true
gatewayTraceSource=start (defaults)
baseline_sessions=21
target_informative=12
max_attempts=18
max_attempts_per_shape=6
```

No model turn or session creation occurred. The session-store count stayed 58→58 and the temporary
output directory contained no entries. The synthetic manifest proves preflight mechanics only; it is
not the research-owned fixture freeze and does not authorize collection.

## 4. Non-blocking nit

Discovery-warning matching uses broad substrings. A hypothetical benign warning such as “no discovery
error” would be rejected. This is fail-closed, does not affect current Hermes warning formats, and does
not block acceptance. Anchoring to Hermes's authoritative failure prefixes can be handled separately.

## 5. Limitations and claim ceiling

This acceptance covers collector implementation and preflight behavior only. It does not establish
fixture validity, workload informativeness, metric values, causal importance, cost saving, paging quality,
model quality, determinism, availability, or redaction. `position_band`, `later_dependency_use`, and
dependency distance remain UNVERIFIED. No candidate pin is authorized for activation.

## 6. Repro commands

```bash
for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done
python3 -m pytest tools/test_collect_shadow.py -q
python3 research/shadow-analysis/test_join.py -q
python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
python3 -m py_compile tools/collect-shadow.py tools/test_collect_shadow.py
bash tools/run-ci.sh
python3 tools/ci-rehearsal.py
bash tools/check-handoff.sh
bash tools/git-hygiene.sh
git diff --check
```

The fresh preflight uses the same temporary three-shape synthetic manifest pattern as the no-model
preflight probes and calls `tools/collect-shadow.py --preflight-only`; it does not call `Collector.run()`.

## 7. Applied

This report, one four-pipe `reports/LOG02.md` row, one `reports/RR-DAY-20261128.md` section, and a separate
PROJECT-STATE delta. No collector code changed in the review lane. No push.
