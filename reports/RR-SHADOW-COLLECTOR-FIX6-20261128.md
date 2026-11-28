# RR-SHADOW-COLLECTOR-FIX6-20261128 — whitespace-safe paths and complete catalog provenance

Lane: hermes/tools. Date: 2026-11-28. Authority: owner-supplied whitespace re-review and
`RR-SHADOW-COLLECTOR-CATALOG-REVIEW-20261128` / `SHADOW-COLLECTOR-FIX5-PROMPT.md`.

Fix target: `a51ea8d`. No model session, live batch, profile/gateway/model-config edit, restart, pin
activation, publish, or push.

## 1. What was done

1. **Raw default validation.** `XDG_STATE_HOME` and `HOME` are validated before normalization. Leading or
   trailing whitespace is rejected instead of being stripped into a false absolute path.
2. **Raw active-path validation.** The active status parser no longer strips the directory before checking
   it. Surrounding whitespace fails closed; only then is absoluteness checked and the path resolved.
3. **Complete command discovery required.** Catalog provenance now requires string `warning` and
   `plugin_discovery_error` fields. Non-empty plugin discovery errors, malformed fields, and warnings that
   report quick/plugin/skill discovery failure reject preflight before `command.dispatch`.
4. **Benign warnings remain allowed.** A non-discovery warning does not block provenance when the plugin
   command is complete and collision-free.
5. **Expanded-path regression hardened.** The adversarial `$VAR` parser case now starts from a real
   `os.path.expandvars()` result rather than literal variable text.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
57 passed, 98 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Each fix was first demonstrated red with a focused regression, then green. New cases cover leading and
trailing whitespace in `XDG_STATE_HOME`, `HOME`, and active paths; quick/plugin/skill discovery warnings;
plugin discovery errors; malformed discovery fields; benign warnings; and proof that failed provenance
sends no `command.dispatch` request.

### Real read-only gateway probes

The live catalog remains complete (`warning=""`, `plugin_discovery_error=""`), `/ctxvm-trace` is listed
only under `Plugin commands`, and active status remains:

```text
{'enabled': True,
 'trace_dir': PosixPath('~/.local/state/ctxvm/traces'),
 'source': 'start (defaults)',
 'version': '0.13.37'}
ACTIVE_GATEWAY_STATUS_OK
```

A full `--preflight-only` run returned rc=0 with 21 baseline sessions. No model turn or session creation
occurred.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-28 run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks. Evidence:
`~/.local/state/ctxvm/ci/collector-fix6-full-20261128.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

Evidence: `~/.local/state/ctxvm/ci/collector-fix6-rehearsal-20261128.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits; test-only fake paths and credential shapes remain
  intentional negative fixtures.

## 3. Deviations and discoveries

- The whitespace defect and the catalog-completeness defect were both open at the start of this card. Both
  are fixed here so the next review sees one coherent provenance/path boundary.
- Hermes can emit benign catalog warnings for non-discovery collisions. The collector rejects only malformed
  fields and discovery-failure warnings, preserving those benign warnings.

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

This report, one four-pipe `reports/LOG02.md` row, and one `reports/RR-DAY-20261128.md` section.
`handoff/PROJECT-STATE.md` remains review-lane owned. No push.
