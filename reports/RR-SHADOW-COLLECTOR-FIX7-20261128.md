# RR-SHADOW-COLLECTOR-FIX7-20261128 — unconditional raw-path validation and fail-closed catalog structure

Lane: hermes/tools. Date: 2026-11-28. Authority: owner-supplied re-review of `49be10f` and
`SHADOW-COLLECTOR-FIX6-PROMPT.md`.

Fix target: `49be10f`. No model session, live batch, profile/gateway/model-config edit, restart, pin
activation, publish, or push.

## 1. What was done

1. **Raw HOME validated unconditionally.** Surrounding whitespace in `HOME` is rejected before either the
   default or explicit `CTXVM_TRACE_DIR` branch, before any `.strip()`, expansion, or `.resolve()`.
2. **Raw explicit path validated.** An explicit `CTXVM_TRACE_DIR` with surrounding whitespace now fails
   closed before normalization. This is deliberately stricter than Hermes's explicit-path stripping.
3. **Catalog structure fully validated.** `_plugin_status_proven()` now requires:
   - every category is a dict with a non-empty string name and list `pairs`;
   - every pair is a two-string list/tuple;
   - every plugin-command key and value is a string;
   - no malformed entry is skipped or ignored.
4. **Malformed catalog cannot reach dispatch.** Any structural defect rejects provenance before
   `command.dispatch`; a later `type="exec"` result is therefore never accepted on incomplete catalog
   evidence.
5. **Clean explicit-path controls retained.** Absolute paths, `~/...`, and `$VAR` expansions still pass
   when all raw inputs are whitespace-clean.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
59 passed, 107 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Each fix was first demonstrated red with focused regressions, then green. New cases cover whitespace
around explicit `CTXVM_TRACE_DIR`, whitespace `HOME` with `~/traces`, clean explicit controls, malformed
category objects, non-list/oversized/malformed pairs, non-string names, and malformed plugin-command
entries.

### Real read-only gateway probes

The live catalog remains complete; `/ctxvm-trace` is listed only under `Plugin commands`. Active status
remains:

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
`~/.local/state/ctxvm/ci/collector-fix7-full-20261128.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

Evidence: `~/.local/state/ctxvm/ci/collector-fix7-rehearsal-20261128.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits; test-only fake paths and credential shapes remain
  intentional negative fixtures.

## 3. Deviations and discoveries

- The explicit `CTXVM_TRACE_DIR` whitespace rejection is stricter than Hermes's resolver, which strips the
  value. It is retained as the collector's fail-closed boundary, as required.
- Catalog validation is now total rather than selective: an unrelated malformed category rejects the whole
  provenance proof instead of being skipped while a later valid row permits acceptance.

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
