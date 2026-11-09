# RR-FRICTION-20261109 — A2: umpire friction vs RFC-0.1

**Date:** 2026-11-09. **Workstream:** A2. **Condition:** ctxvm `HEAD cd43555` read-only, umpire read-only. No spec file edited.

## What was done

Reconciled R0-R5 (`spec/rfc-0.1/RFC-0.1-xCABI.md`) and umpire's `00-SPEC.md` §2 + `spec/ledger_tools.py:40-54`. Wrote the design card `design/umpire-friction-vs-rfc01.md` (full friction table F1-F9 with statuses) and packet `handoff/packets/P4-ts-umpire.md` for the top residual (F8: umpire omits `ts`).

## Result

F1-F3, F5-F7 resolved by R1, R2, R3, R5, R0 respectively (locators in card). Residuals: F8 `ts` adoption gap (options: consumer rule recommended), F9 canonical order (accept + document). No spec change proposed or applied.

## Repro

`cat spec/rfc-0.1/RFC-0.1-xCABI.md` (R0-R5 §), `grep -rn "intentional_rerun" umpire/` (version branch `validate_ledger.py:47-54`), `grep -c '"ts"' umpire/fixtures/*.ledger.jsonl` → 0, `cat design/umpire-friction-vs-rfc01.md`.

## Limitations / open questions

- UNKNOWN: GitHub issues/TODOs in umpire not read (no remote fetch). Friction list is repo-local.
- F8/F9 need owner/umpire D-U decisions (A6 register), not this card.

## Conflicts

None beyond A1 notes (docs/drafts dirs for A3/A5). `PACKET P4` < 3 KB (1,550 bytes).
