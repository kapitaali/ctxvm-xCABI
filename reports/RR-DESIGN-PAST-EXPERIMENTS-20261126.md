# RR-DESIGN-PAST-EXPERIMENTS-20261126 — archive past experiments out of design/ root

Owner instruction 2026-11-26: move past experiments into a separate subdirectory so `design/` has room
for actual product-design documents.

## Moved

Created `design/past-experiments/` and moved **36 tracked files**:

- all root-level `W8*`, `w8*`, and `TB-*` experiment artifacts;
- `design/w8-tasks/` as a unit;
- one-off `G4-LANE-DEVELOPER-PROMPT.md`, `H16-H18-LANE-DEVELOPER-PROMPT.md`,
  `EXP-SURFACE-PROMPT.md`, and `exp-surface.md`.

Files keep their basenames. `design/past-experiments/README.md` records the exact old→new prefix map.
The root of `design/` now holds **27 product/workstream files** plus the `experiment-runs/`,
`past-experiments/`, `rfc-0.1/`, and `runtime-abi/` subdirectories.

## References

Updated active documentation, prompts, roadmaps, handoff law, code comments/docstrings, tests, tools,
and white-paper references to the archive paths. A locator check found **0 missing archive targets**.

Not rewritten:
- closed `reports/LOG.md`;
- append-only W8 spend ledgers;
- frozen `benchmarks/w8/**`;
- another lane's dirty `handoff/PROJECT-STATE.md`;
- untracked `design/DSH-LANE-DEVELOPER-PROMPT.md`.

Historical reports keep their original paths as evidence; the archive README supplies the mapping.

## Scope

Organizational/path-only change. No experiment was rerun, no model call or spend, no gateway/profile
change, no release, and no push. `design/experiment-runs/` remains for future authorized runs; product
designs remain at the root of `design/`.

## Verification

- `git diff --check` passes.
- `bash tools/check-handoff.sh` and `bash tools/git-hygiene.sh` pass.
- Full `bash tools/run-ci.sh` passes.
- Closed `reports/LOG.md` hash remains unchanged.

## Applied

This card, one four-pipe row in active `reports/LOG02.md`, a day-file section, the archive README, and
the moves/reference updates. No push.
