# RR-LOG02-PROMPTS-20261126 — lane prompts now target the active LOG02 ledger

Owner instruction 2026-11-26: **“update prompts too.”**

Updated active work-order/lane prompts from `reports/LOG.md` to `reports/LOG02.md`:

- `design/H16-H18-LANE-DEVELOPER-PROMPT.md`
- `design/HERMES-PLUGIN-DEVELOPER-PROMPT.md`
- `design/OPENCODE-LANE-DEVELOPER-PROMPT.md`
- `design/TB-OPENCODE-PROMPT.md`
- `design/W8B-LANE-PROMPT.md`
- `design/W8-EXECUTOR-PROMPT.md`

The OpenCode prompt's historical P11 count is explicitly preserved as a closed-`LOG.md` fact; its active
count command now uses `LOG02.md`. `handoff/AGENT-PROMPT.md` already carried the correct closed-history
wording from the rotation commit.

Historical plans/reports were not rewritten. The untracked `design/DSH-LANE-DEVELOPER-PROMPT.md` belongs to
another lane and was not touched.

## Verification

- No active prompt instructs new rows to `reports/LOG.md`.
- `git diff --check` passes.
- `bash tools/check-handoff.sh` and `bash tools/git-hygiene.sh` pass.
- Full `bash tools/run-ci.sh` passes.

## Applied

This card, one four-pipe row in active `reports/LOG02.md`, a day-file section, and the six prompt updates.
No change to closed `reports/LOG.md`; no push.
