# RR-LOG02-ROTATION-20261126 — open LOG02 as the active append-only ledger

Owner instruction 2026-11-26: **“we should move on to next LOG file, LOG02.md.”**

## Decision

- `reports/LOG.md` is closed unchanged at **637 lines / 1,043,777 bytes**, SHA-256
  `0f538307c8ac2dd683eb36c4411ad4ec25775ee203d99fa52a4e04fbd2bd0eac`.
- Its final row is `RR-SHADOW-DATA-FIX-20261126`.
- `reports/LOG02.md` is the new active append-only ledger. No historical rows were moved or copied.
- New report rows go to `LOG02.md`; `LOG.md` remains immutable history.
- The four-pipe rule, append-only rule, no-CJK rule, and private-index commit rule are unchanged.

## Canonical references updated

- `AGENTS.md`
- `00-README.md`
- `08-HANDOFF.md`
- `handoff/AGENT-PROMPT.md`
- `handoff/LANES.md`
- `handoff/CONTEXT-PACK.md`

Historical reports and design notes retain their original `LOG.md` references as evidence of what was true
when written. `handoff/PROJECT-STATE.md` was not staged because it carries another lane's uncommitted delta.

## Verification

- `reports/LOG.md` hash is unchanged after rotation.
- `reports/LOG02.md` has the same table header and this rotation row.
- `bash tools/check-handoff.sh` and `bash tools/git-hygiene.sh` pass.
- Full `bash tools/run-ci.sh` passes.

## Applied

This card, the first `LOG02.md` row, a day-file section, and the canonical reference updates. No push.
