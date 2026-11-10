# Packet P5: D-U1 calibration transfer — is n=180 enough?
STATUS: answered 2026-11-10 (verdict in handoff/QUESTIONS.md; full record reports/RR-P5CAL-20261110.md:
publish per-corpus calibration WITH the caveat, no transfer claim until a preregistered held-out
corpus of new label sets passes equivalence (±2 pt margin, Brier/log-loss primary, ≥5 sets,
cluster bootstrap); point estimates worsened (A1 +4.7, A2 +1.9). The reviewer's UNKNOWN arm
definitions RESOLVED from the books: A0/A1/A2 = design/W9-TRANSFER.md:36-38's exact table.

Date: 2026-11-09. Requester: A6. Related decision: D-U1.

## Question (one specific question)

W9 transfer at n=180 returns "no detectable degradation" (CIs include zero). Is that sufficient to publish per-(pin,seed,label) calibration, or is a larger held-out corpus required first?

## Excerpt or diff (only the relevant lines, with file path and line range)

umpire `reports/RR-W9TRANSFER-20261101.md` (and `design/W9-TRANSFER.md`): A1 7.5→12.2%, A2 4.9→6.8% ECE, paired 95% includes zero.

## Constraints (what must not change)

No spec edit without 5 touchpoints + D-number. No umpire edit. Calibration is sidecar-only; raw identity unchanged.

## Evidence (numbers with the command that produced them; UNVERIFIED marked)

`python3 spec/transfer_eval.py report` → A1/A2 vs A0 on 90 rows, extended to n=180 (Amendment 1). Paired CIs include zero (W9 §234-244).

## Output wanted (numbered verdicts, one line each; rewrites only if asked)

1. Ship per-scope / wait for larger corpus / publish with caveat?
2. What corpus size closes the 2-point effect?
3. One sentence on what to tell a caller with a new label set.
