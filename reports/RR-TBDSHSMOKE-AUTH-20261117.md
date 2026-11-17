# RR-TBDSHSMOKE-AUTH-20261117 — owner authorizes the dsh capture smoke, sequenced after the OpenCode wired run

Owner decision 2026-11-17, verbatim:

> the smoke run is authorized. we will run after the full wired run finishes

## What this authorizes

The **four-prompt tool-using smoke** in `design/TB-DSH-CAPTURE.md` §3 as revised in `ac5d932`: P1–P3 with file
reads on `data-01.csv`…`data-03.csv` plus one P193-shaped reconciliation prompt, on the fixed
`--session-id` mode, with the auth detector and ledger keying from the plan. The purpose is measurement —
`r_smoke` (per-prompt maximum) and the reconciliation allowance — not a result.

## The sequencing condition

The smoke is **not to start until the OpenCode full wired run has finished**. That run was still ongoing when
this authorization was given; its two precedents are CEILING (unwired, 582 vs 579, no trace) and NO RECORD
(wired, server exited without flush at P22). Neither is a result the dsh run inherits. Because the owner attached
the condition to the authorization, starting the smoke before the OpenCode run ends would exceed it.

## Not authorized by this ruling

- The full 193-prompt dsh run: that still needs a fresh ceiling preregistered from the smoke's measured rate
  (`ceil(193 × r_smoke) + A`) before prompt 1.
- A retry of the OpenCode wired run, a ceiling change (198 stands), any reuse of 579/451/582, a GO for a Hermes
  paged cell, or any cost/paging/determinism claim.
- Any edit to `packages/**`, `tools/**`, or another lane's uncommitted work. The dsh lane owns
  `packages/deepseek/**` and `reports/RR-W22*`.

Mechanism note: no signature artifact; the owner rules in chat and the review lane records the ruling with the
date and exact decision (precedent `RR-W8CSEQ-20261111`). Written by the review lane. No code change, no model
call, no spend, no push.
