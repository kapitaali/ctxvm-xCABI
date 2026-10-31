# RR — CI-1 — 20261031

**Card executed:** CI↔mirror alignment + a way to test the workflow before a push.
**Date:** 2026-10-31. **Trigger:** the owner asked "how do we test the ci" — the answer
turned out to include "it has drifted from the mirror it claims to be".

## The question

`tools/run-ci.sh` is documented as the *byte-equivalent local mirror* of
`.github/workflows/ci.yml`, and the repo has no other way to witness the workflow: the
Actions run happens only after an owner push. So "testing the CI" has three levels, and only
the first two are available here:

1. **Parse it** — `yaml.safe_load`, count steps, check each step has `run` or `uses`. Cheap,
   catches syntax and structural mistakes, proves nothing about behaviour.
2. **Rehearse it** — run the workflow's own `run` steps, in order, in a pristine clone.
   Catches steps that quietly depend on `venvs/`, `node_modules/`, `dist/` or on a
   developer's local state. This is what `run-ci.sh` cannot do: it runs *its own* text, so a
   step that exists only in the workflow, or is missing from it, stays invisible.
3. **Run it** — the Actions run after a push. The only real verdict; the owner's act.

## What was built

- **NEW `tools/ci-rehearsal.py`** — clones the repo, overlays the working tree (tracked diff
  + untracked non-ignored files, committed inside the clone so the hub job's
  `git diff --exit-code hub/` compares against the right baseline), then executes each job's
  `run` steps in order with a throwaway virtualenv per job, stopping a job at its first
  failure the way Actions does. It skips `uses:` steps and prints the host's node/python/cargo
  versions so the record says what was actually exercised. `--job`, `--keep`.
- **NEW `tools/export-roundtrip.sh`** — the T21 chain (`export m3 @2 --odps` → zstd slice →
  `replay --turn 2` → `diff` → m4 replay → per-dir checksums) extracted from `run-ci.sh`, so
  the mirror and the workflow run one text instead of two copies.
- **`ci.yml` aligned** with the mirror. Three real drifts were found by diffing the two:
  1. **Six fixtures were never validated in CI** — `corpus/m6` (UC1 pause/resume pair),
     `corpus/m7` (Hermes pause/resume pair), `corpus/m8` (Vercel AI SDK echo/thrash). The
     mirror validates 24 fixtures; the workflow validated 18.
  2. **Three drop checksum steps were missing** — CI verified m1–m5 only, while the mirror
     verifies m1–m8. Every drop after M5 (the whole UC1/UC3/M8 era) had no integrity check
     in CI.
  3. **The export round-trip chain was absent from CI entirely** — the gate that proves a
     handoff snapshot is a faithful slice ran only locally.
- **`00-README.md`** tools row lists the new scripts; the workflow now runs the shared export
  script in the `ts` job (where `cargo build --release` has already produced the binaries, so
  no second Rust build is paid).

## Verification

```
$ python3 tools/ci-rehearsal.py
  rust   ✔ cargo test · ✔ tiktoken feature
  ts     ✔ 14 steps (source tests → npm ci → export round-trip → parity → opencode →
           hermes → py binding → metrics)
  schema ✔ 13 steps (jsonschema → rfc-0 v0 over 24 fixtures → rfc-0.1 → m1..m8 checksums)
  hub    ✔ 6 steps (SDK install → manifest validate → regen → byte-identity)
  rehearsal OK — 4 job(s), every run step green in a pristine clone

$ bash tools/run-ci.sh
  export-roundtrip: OK — slice @2 replays, diff a_extends_b, m4 replay clean, checksums verified
  ALL GATES GREEN
```

**Red-before for the rehearsal itself.** Injecting `run: exit 7` as a schema-job step makes
the rehearsal print `✖ [14] RED-BEFORE PROBE → exit 7`, report `FAIL schema`, and exit 1;
removing it returns a green run. So the tool fails when the workflow fails — it is not a
printer.

## Semantics recorded

- A green rehearsal means "the step text is self-sufficient on this host", not "GitHub ran
  it". Runner-provided tooling (`uses:` steps) is whatever the host has; the script prints it.
- The rehearsal deliberately runs the **working tree**, not `HEAD`. A workflow edit is
  therefore testable before it is committed — which is the whole point — and the overlay is
  committed inside the throwaway clone so repository-level steps (`git diff --exit-code`)
  behave as they would on the runner.
- Drift is now checkable mechanically: extract the `run:` commands from the workflow and
  compare against `run-ci.sh`. That is how all three gaps above were found, and it is the
  check to run whenever either file changes.

## Explicitly not done

- **No `act`.** Docker is present, but the rehearsal answers the question without pulling
  action images, and `act` would still not be the real runner. Recorded as an option, not
  taken.
- **No push.** The Actions run remains the owner's act; this card makes it a confirmation
  rather than an experiment.
- No change to what the gates assert — only to where they run and how they are tested.

## Open questions

- Should the rehearsal run in CI itself (a job that checks the other jobs)? It would catch
  drift automatically, at the cost of a nested runner and doubled wall time.
- Should `run-ci.sh` gain a `--verify-mirror` mode that diffs the workflow's `run:` commands
  against its own, so the two cannot silently diverge again?

## Addendum (same day) — portability fix found by reusing the tool

The rehearsal tool was carried to umpire, which has no `venvs/` at all. It assumed a python
with PyYAML existed (`venvs/odps` here, `sys.executable` as fallback), and neither repo's
default python imports `yaml`. The tool now bootstraps its own parser venv when both
candidates fail, so it works in any repo that has a workflow:

```
$ python3 -c "import yaml"        # ModuleNotFoundError on the default interpreter
$ python3 tools/ci-rehearsal.py   # creates a throwaway venv, pip install pyyaml, parses, deletes it
```

Same lesson as the drift itself: a tool that depends on a developer's local state is not a
check. The rehearsal is only worth its red-before if it runs where the workflow runs — from a
clean clone, with no assumptions about what the host already has.

## Addendum 2 (same day) — the first real run

The workflow ran on GitHub: **run 41240870951** on `31bd84f`, four jobs, all success, 34 s
(20:51:46Z → 20:52:20Z). The steps this card added executed for the first time there, not
merely appeared:

```
ts     ✓ 07 @ctxvm/node install + build (W10: the publishable artifact)
       ✓ 08 T21 export round-trip (slice → replay → diff → checksums)
       ✓ 09 src-vs-dist parity (a behaviour-changing build fails here)
schema ✓ 12 corpus drop checksums (M6 UC1 pause/resume)
       ✓ 13 corpus drop checksums (M7 Hermes pause/resume)
       ✓ 14 corpus drop checksums (M8 Vercel AI SDK)
       ✓ 05 rfc-0 schema validator (24 fixtures)
```

Limit of that evidence, stated plainly: step conclusions say each step RAN and returned 0.
They do not show the numbers inside it. The job-log endpoint returns 403 unauthenticated and
`gh` is not installed on the workstation, so the runner's `16 events byte-identical` line
could not be read from outside — the numbers come from the local rehearsal, which produced the
same ones. The rehearsal also proved (red-before) that the parity step fails when the build
breaks, so a green step is not a vacuous one.
