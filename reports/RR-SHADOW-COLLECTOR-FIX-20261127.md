# RR-SHADOW-COLLECTOR-FIX-20261127 — review blockers fixed; re-acceptance owed

Lane: hermes/tools. Date: 2026-11-27. Authority: `RR-SHADOW-COLLECTOR-REVIEW-20261127` and
`design/experiment-runs/SHADOW-COLLECTOR-FIX-PROMPT.md`.

Fix target: `1ec95ae`. Implementation remains blocked from live use until independent review accepts the
new commit. No model session, live batch, profile/gateway/model-config edit, restart, pin activation,
publish, or push.

## 1. What was done

1. **Live target frozen.** Production preflight now requires exactly 12 informative sessions. Reduced
   targets use the internal `Config.test_mode` seam only; the CLI exposes no test-mode switch.
2. **Fallback disabled proof.** Preflight reads effective `fallback_providers` and legacy `fallback_model`
   through `hermes config get -p w8-shadow --json`. Unset/empty is accepted; any nonempty chain fails closed.
3. **No-drop validity corrected.** A schema-valid, zero-failure no-drop session remains in `all_valid` and
   is non-informative. This follows the later review clarification and supersedes the earlier test that
   treated no drop as an invalid attempt.
4. **Failure counter scope corrected.** Only per-session `shadowWriteFailures` gates validity. The
   process-global total is diagnostic and no longer contaminates unrelated sessions.
5. **Per-shape denominators added.** Both `all_valid` and `informative_only` now contain `pooled` and
   `by_shape` views with selections, opportunities, label counts, rates, and candidate-pin status.
6. **Subprocess environment bound.** Every sync/config/session/gate/join subprocess receives an environment
   with all `CTXVM_*` variables removed and `HERMES_HOME` set to the validated root. `profile_home` must be
   exactly `<HERMES_HOME>/profiles/w8-shadow`, so `-p w8-shadow` cannot target a different tree.
7. **Malformed evidence receipted.** Coverage, session, plugin, policy, page-list, and PageId parsing is
   type-safe. Malformed evidence excludes the attempt and still writes a receipt and aggregate.
8. **Auth/model signatures expanded.** Missing API keys, invalid/expired tokens, access denial, model-not-
   found/invalid/unknown/unsupported/no-longer-free errors, HTTP 402, and HTTP 429 quota failures stop the run.
9. **Route drift stops the batch.** Observed model/provider must match exactly. `unknown` or known drift sets
   `model_provider_failure`, writes a receipt, stops further attempts, and exits 4 as
   `STOPPED_MODEL_PROVIDER`.
10. **New-session uniqueness enforced.** Durable session IDs are deduplicated before quota credit. A repeated
    ID receives `duplicate_session` and cannot count toward the 12-session target.
11. **Session ID parsing hardened.** One unique ID is required across stdout and stderr. Stdout-only,
    stderr-only, matching-duplicate, conflicting, and missing cases are covered.

## 2. Verification

### Focused and adjacent suites

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
36 passed, 51 subtests passed

$ python3 research/shadow-analysis/test_join.py -v
Ran 6 tests
OK

$ python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed
```

Every review fix was first demonstrated red with a focused regression, then green after the fix.

### Real no-model preflight

A temporary SHA-256-pinned manifest was used with `--preflight-only`; no model session ran.

```text
PREFLIGHT_RC=0
{"budgetTokens":24000,"fallbackDisabled":true,...,"plugin_version":"0.13.37",
 "profile":"w8-shadow","provider":"nous","target_informative":12}
PREFLIGHT_FACTS_OK
```

This proved the live gateway/plugin, effective profile, frozen target, and empty fallback chain without
changing live configuration.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-27 run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks. Evidence:
`~/.local/state/ctxvm/ci/collector-fix-full-20261127.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

The collector step executed successfully in the `ts` job. Evidence:
`~/.local/state/ctxvm/ci/collector-fix-rehearsal-20261127.log`.

### Bookkeeping and sweeps

- `check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean for both Python files.
- CJK sweep → zero hits.
- Secret/home-path sweep → zero production hits. Two test lines contain intentional fake credential,
  home-path, and private-ref fixtures used to prove aggregate privacy.

## 3. Deviations and discoveries

- Added `STOPPED_MODEL_PROVIDER` as an explicit status while retaining exit code 4 for model/provider stops.
- The aggregate `denominator_views` shape is now `{view: {pooled, by_shape}}`; no external consumer existed.
- The earlier no-drop exclusion test encoded the behavior the review rejected. It was replaced, not relaxed.
- Effective fallback is read through Hermes' own config command rather than a second YAML parser.
- Profile override flags remain available but are bound: a profile outside the validated Hermes home is rejected.

## 4. Limitations and open questions

- Independent re-review is still required. This card does not claim acceptance.
- Research/experiment still owns the real frozen fixture manifest and prompt freeze.
- No live session, metric, pin, causal, cost, paging, model, determinism, availability, or redaction claim was
  produced. `position_band`, `later_dependency_use`, and dependency distance remain UNVERIFIED.
- The process-global failure total remains diagnostic; the per-session counter remains mandatory.

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
