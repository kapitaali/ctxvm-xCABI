# RR-CTXVMENV-20261111 — the local gate was red only because the shell's `CTXVM_*` variables leaked
## into it; the gate is now hermetic, and the test that assumed an unset environment is the other
## lane's to isolate

Card: a kit-integrity finding of this lane's own, found while witnessing the gate at a tree that
carries the other lane's plugin 0.11.0.

## 1. What was observed

```
env -u CTXVM_TRACE_TS -u CTXVM_HERMES_VERSION bash tools/run-ci.sh
...
FAILED test/test_context_engine.py::ArmPolicyTests::test_control_profile_is_control_and_carries_no_budget
1 failed, 192 passed, 15 subtests passed in 1.49s
```

The gate was red at a tree whose only new code was the other lane's 0.11.0 arm policy. The failing
assertion is one line:

```python
# packages/hermes/test/test_context_engine.py:760-766
home = self._home("naive", "compressor")
pol = _REAL_POLICY(home)
self.assertEqual(pol["arm"], "control")
self.assertEqual(pol["engine"], "compressor")
self.assertEqual(pol["budgetSource"], "default")      # <-- fails: got 'env'
```

## 2. Root cause, verified by reading the committed code (not guessed)

`profile_policy.policy()` resolves the budget in this order (`packages/hermes/live/profile_policy.py:114-127`):

```python
engine = cfg.get("engine") or "compressor"
budget = cfg.get("budgetTokens")
source = "settings" if isinstance(budget, int) and budget > 0 else "default"
if source == "default":
    env = os.environ.get("CTXVM_BUDGET_TOKENS", "").strip()   # <-- the ambient environment
    if env: budget, source = int(env), "env"
if not isinstance(budget, int) or budget <= 0:
    budget, source = 200000, "default"
```

So with `CTXVM_BUDGET_TOKENS` exported, a profile that declares **no** budget still resolves to
`budgetSource == "env"`, and the test's expectation of `"default"` fails. The variable is exported by
the owner's interactive shell:

```
~/.bashrc:28:export CTXVM_BUDGET_TOKENS="200000"                     # default 200000; integer > 0
```

so it is present in **every** bash invocation — while `.github/workflows/ci.yml` sets **no**
`CTXVM_*` variable at all (`grep -n 'CTXVM_' .github/workflows/ci.yml` → no match). In other words the
suite is green in CI and red in the owner's shell: the test asserts about a value it did not set.

Verified by isolating the variable (`env -u CTXVM_BUDGET_TOKENS … python -m pytest
test/test_context_engine.py -q` → **34 passed**), and by re-running the same file in a detached
worktree at `HEAD` (`4566c4b`), where it fails **identically** — so the failure arrived with the other
lane's committed 0.11.0/4566c4b code (exposed by the leak), not with their uncommitted work in progress
and not with this lane's commits, which are documentation only.

## 3. What this lane changed — the gate is now hermetic

`tools/run-ci.sh` now unsets the nine `CTXVM_*` variables an interactive shell may export, before any
step runs, with a comment naming both incidents:

```
for _v in CTXVM_TRACE_TS CTXVM_HERMES_VERSION CTXVM_BUDGET_TOKENS CTXVM_TRACE_DIR \
          CTXVM_TRACE_NAME CTXVM_FEATURES CTXVM_AGENT_ID CTXVM_MODEL CTXVM_PROVIDER; do
  unset "$_v" || true
done
```

The **steps are unchanged**, so the script stays the mirror of `ci.yml` it claims to be — and now it
is a mirror of ci.yml's *environment* too, instead of of whichever shell happened to run it. The
documented invocation `env -u CTXVM_TRACE_TS -u CTXVM_HERMES_VERSION bash tools/run-ci.sh` remains
valid and is now redundant (the first leak it worked around, `CTXVM_TRACE_TS`, is one of the nine).

## 4. The half that is the other lane's

The test still depends on an ambient variable it does not control. Run directly (not through the gate),
`pytest packages/hermes` fails for anyone whose shell exports `CTXVM_BUDGET_TOKENS` — i.e. for the
owner, in every session. The test should isolate the environment for the duration of the assertion
(delete `CTXVM_BUDGET_TOKENS`, or inject an empty environment), or assert the pair
`budgetSource in ("default", "env")` with the budget value it expects. **That file is the other lane's**
(`packages/hermes/**` is outside this lane's remit) and this lane writes no test byte.

## 5. Class of finding

This is the **second instance** of the environment-leak class recorded in `reports/RR-ENVLEAK-20261110.md`:
a `CTXVM_*` variable inherited from the shell changes what a test observes. First instance:
`CTXVM_TRACE_TS=0` broke `node --test`. Second: `CTXVM_BUDGET_TOKENS=200000` broke the arm-policy
test. The general fix is now in the gate, so the class no longer turns the local gate red — but a test
that reads the ambient environment remains fragile for anyone running the suite directly, which is why
item 4 is on the other lane's plate.

## 6. Executed agent-doings

- The red gate was diagnosed, not assumed: the failing assertion was read, the resolution order in
  `profile_policy.policy()` was read at the committed bytes, the shell export was located
  (`~/.bashrc:28`), the CI workflow was checked for the same variables (none), the isolation was tested
  (34 passed), and the failure was reproduced in a detached worktree at `HEAD` to place it in the other
  lane's commits rather than in anyone's working tree.
- The gate was made hermetic in this lane's own tooling; the other lane's test was left untouched.
- Kit: this card + LOG row + a day-file line + the gate's own comment. No spec, schema, corpus, vector
  or umpire byte changed; nothing pushed.
