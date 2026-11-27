# RR-SHADOW-COLLECTOR-IMPL-20261127 — tracked shadow collector implemented; review acceptance owed

Lane: hermes/tools. Date: 2026-11-27. Authority: `RR-SHADOW-COLLECTOR-AUTH-20261127` and
`design/experiment-runs/SHADOW-COLLECTOR-HERMES-PROMPT.md`.

This card resumes and completes the interrupted, untracked collector draft exported in
`experiments/ctxvm-development-04-local-7d.json`. Implementation only: no model session, live batch,
profile/gateway/model-config edit, restart, candidate-pin activation, publish, or push.

## 1. What was done

- Completed `tools/collect-shadow.py` and `tools/test_collect_shadow.py`.
- Preflight fails closed on plugin-version disagreement, stale gateway, wrong profile/arm/budget/mode,
  non-private paths, missing gate files, fixture hash mismatch, and sync-runner errors.
- Added `--preflight-only`; it proves the live prerequisites and exits without running a model session.
- Every attempt now copies the SHA-256-pinned fixture files into a fresh private `0700` workspace under
  the run directory. A model cannot mutate the research-owned source fixture or a later attempt.
- Per-attempt private evidence includes stdout/stderr, rc, session id, requested/observed model/provider,
  trace and coverage snapshot, shadow delta, digests, four gate receipts, shape labels, and join receipt.
- Validity now requires sidecar `arm=control` and both `shadowWriteFailures=0` and
  `shadowWriteFailuresProcess=0`.
- Requested provider remains exact; an observed `unknown` provider is recorded, while known drift excludes
  the attempt.
- Sequential round-robin quotas enforce the owner caps: 12 informative target, 18 total attempts, six per
  shape. Auth/model failure stops the run. Candidate pins remain hashed, offline-only, and not authorized.
- Aggregate output has separate `all_valid` and `informative_only` denominator views and omits raw refs,
  bodies, prompts, answers, credentials, session ids, and host paths.
- Wired the no-model suite into `tools/run-ci.sh` and `.github/workflows/ci.yml` at the same point.

## 2. Verification

### Focused suite

```text
$ python3 -m pytest tools/test_collect_shadow.py -q
24 passed, 31 subtests passed in 1.01s

$ python3 -m py_compile tools/collect-shadow.py tools/test_collect_shadow.py
exit 0
```

Red-before witnesses recorded during this card:

- missing version files raised `FileNotFoundError` instead of `PreflightError`;
- `--preflight-only` was rejected by argparse;
- process-global shadow failures and `arm=paged` sidecars were accepted;
- repeated attempts reused and mutated the source fixture workspace;
- a sync-runner timeout escaped the preflight error contract.

Each regression failed before its fix and passed afterward.

### CI wiring anti-vacuity

An intentional failing test was temporarily added, the gate was run, and the exact named step failed:

```text
FAILED: shadow collector no-model suite
intentional collector gate wiring probe
GATE rc=1
```

The test file was restored byte-identically: SHA-256
`2cab9fde4f7772b471a05b5ce3ddebea66ffd4201e64b558eb862e0b5d088000`, mode `664`.

### Full local gate

```text
$ bash tools/run-ci.sh
ALL GATES GREEN
```

The 2026-11-27 final run printed `ts 30 + 62 + 46 + 35`, `py 264 + 8 + 66`, and schema `682` checks.
The collector suite is deliberately a separate `run_step`, not part of the counted pytest summary,
because pytest-subtests prints a second `N passed` count.

Evidence: `~/.local/state/ctxvm/ci/collector-post-books-20261127.log`.

### Workflow rehearsal

```text
$ python3 tools/ci-rehearsal.py
rehearsal OK — 4 job(s), every run step green in a pristine clone
```

The `ts` job executed step 17, `shadow collector no-model suite`, successfully. Evidence:
`~/.local/state/ctxvm/ci/collector-rehearsal-20261127.log`.

### Bookkeeping and sweeps

- `bash tools/check-handoff.sh` → `ALL HANDOFF CHECKS PASS`.
- `bash tools/git-hygiene.sh` → shared index agrees with HEAD.
- `git diff --check` → clean.
- AST duplicate-name probe → clean for both Python files.
- CJK sweep → zero hits in the four implementation/CI files.
- Secret/home-path sweep → zero hits in production collector, CI, report, ledger, and day files. The only
  hits are two intentional lines in `tools/test_collect_shadow.py` carrying fake credential, fake home-path,
  and fake private-ref fixtures used to prove aggregate privacy.

## 3. Deviations from the work order

- Added `--preflight-only` so review can prove the live boundary without a model call.
- Added per-attempt fixture snapshots; the minimum draft reused the source workspace.
- Used `run_step` for the collector suite instead of `run_counted` to avoid counting pytest-subtests as
  additional tests.

No scope outside the collector, its tests, the two CI surfaces, and the required report records.

## 4. Discoveries

- The inherited draft checked only the per-session shadow failure counter. The process counter is the
  field that exposed the earlier global-failure defect, so both are now mandatory.
- The inherited draft did not check the sidecar arm. A paged sidecar could otherwise pass the control
  collector's remaining checks.
- Running a model in the research-owned fixture workspace permits mutation. Fresh private snapshots are
  required to keep the frozen-input claim true across attempts.
- Missing plugin files and sync-runner exceptions now produce the documented preflight exit contract.

## 5. Open questions and limitations

- Review acceptance is still required before any live attempt. A delegated reviewer failed before review
  with a provider model-availability error; this card does not claim independent review acceptance.
- Research/experiment still owns the real frozen fixture manifest and prompt freeze. No live fixture
  manifest was created by this lane.
- No live session, model call, spend, metric, pin, or causal/cost/paging/model/determinism/availability/
  redaction claim was produced.
- `position_band` and `later_dependency_use` remain UNVERIFIED. Dependency distance remains UNVERIFIED.
- The process failure counter is process-global by design; any observed process failure excludes the
  attempt rather than being hidden.

## 6. Repro commands

```bash
for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done
python3 -m pytest tools/test_collect_shadow.py -q
python3 -m py_compile tools/collect-shadow.py tools/test_collect_shadow.py
bash tools/run-ci.sh
python3 tools/ci-rehearsal.py
bash tools/check-handoff.sh
bash tools/git-hygiene.sh
git diff --check
```

## 7. Applied

This report, one four-pipe `reports/LOG02.md` row, and one `reports/RR-DAY-20261127.md` section.
`handoff/PROJECT-STATE.md` remains review-lane owned; its current next action already requires collector
review acceptance before the conditional live batch. No push.
