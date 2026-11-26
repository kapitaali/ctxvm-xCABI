# RR-EXPERIMENT-RUNS-DIR-20261126 — create design/experiment-runs/

Owner instruction 2026-11-26: **“create a separate subdirectory for experiment runs in design/.”**

## Created

- `design/experiment-runs/README.md` — scope and rules for future authorized run plans/preregistrations.
- `design/experiment-runs/TEMPLATE.md` — run-plan skeleton covering authorization, frozen inputs, arms,
  commands, metrics/denominators, stop rules, claim ceiling, and receipts.

`AGENTS.md` now names the subdirectory in the repository layout. Existing historical run plans at the root
of `design/` were not moved, preserving all existing links.

## Scope

This is an organizational change only. It authorizes no model call, spend, active paging, gateway restart,
default-on change, release, or push. Results remain in `reports/RR-*`; raw traces and secrets never belong in
`design/experiment-runs/`.

## Verification

- `git diff --check` passes.
- `bash tools/check-handoff.sh` and `bash tools/git-hygiene.sh` pass.
- Full `bash tools/run-ci.sh` passes.

## Applied

This card, one four-pipe row in active `reports/LOG02.md`, a day-file section, and the new directory files.
No change to closed `reports/LOG.md`; no push.
