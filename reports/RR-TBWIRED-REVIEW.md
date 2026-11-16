# RR-TBWIRED-REVIEW — reviewed: the wired plan is single, the delta card is an honest record, and one item needs your ruling

Review lane, verify-then-record. Subject: `d06cf06` (`design/TB-OPENCODE-WIRED.md`,
`reports/RR-TBOPENWIRE-PLAN-20261116.md`), `5f7c0b3` (LOG-collision erratum), `159d0ec`
(`reports/RR-TBWIRED-20261116.md`, the withdrawn duplicate). No model call, no code change, no spend.

## 1. Verdict

**Two lanes produced two cards; one is the plan of record and the other is a delta, not a duplicate plan.** The
outcome is honest and correctly recorded: `design/TB-OPENCODE-WIRED.md` is the plan of record; the other lane
withdrew its own `design/TB-WIRED-PLAN.md` and kept its independent verification plus four offered deltas in
`RR-TBWIRED-20261116.md`. I verified both cards and the erratum chain. **One substantive question remains open and
is yours:** the `CTXVM_BUDGET_TOKENS` value (200000 vs 60000). The smoke authorization request stands as the
plan's §9 states it and is not granted by this review.

## 2. Verified

| claim | how | result |
|---|---|---|
| plan of record | `git show --stat d06cf06` | `design/TB-OPENCODE-WIRED.md` + its report + LOG row + day section; 134-line plan |
| plan mechanics | read §2–§4 | project-local shim `<run-dir>/.opencode/plugins/ctxvm.ts` re-exporting the adapter; no built dist; seven env vars with reasons; graceful-shutdown flush with `hooks-witness.log` |
| smoke gate | read §5 | v2.3.0 UNVERIFIED; five explicit pass conditions (exit 0 + reply, `.jsonl` + `.meta.json` written, witness chain, validator, replay); **"smoke is a model call and is NOT authorized"** |
| breach handling | read §6 | 579 and 451 explicitly not reused; 582 not used as a ceiling; new ceiling from `r_smoke`, integer frozen before the run, overrun recorded |
| claim ceiling | read §7 | mirror-only: capture fidelity, not paging/H3/H4/cost |
| stop | read §9 | stops before model call, shim creation, or run; asks for one authorization |
| independent verification | `RR-TBWIRED-20261116` §1 | adapter `export default {id,setup}`, shim surface, inert-without-env, all env reads, v2.1.x-vs-v2.3.0 gap — checked from files; I re-checked the key ones earlier in `RR-OPENWIRE-20261116` and they agree |
| duplicate withdrawn | `ls design/TB-WIRED-PLAN.md`, `git show --stat 159d0ec` | file absent; the erratum card records the withdrawal and keeps the verification/deltas |
| shared-LOG collision | `5f7c0b3` + report §6 | the misattribution is named as an erratum by new record; committed rows not rewritten — correct book law |
| index state | `git-hygiene.sh` | **was STALE** from the previous lane's private-index commit (staged deletion of a file present in HEAD). Fixed with `git read-tree HEAD` — index-only, no worktree bytes changed; now OK |

## 3. The four deltas, and my read

The delta card offers them to the plan's owner rather than applying them — correct lane behavior.

- **D1 (full-run fidelity pass criteria):** sound. The plan gates the smoke but does not say what makes the
  full run's traces adequate (≥192 distinct file refs, real model/provider in `session.open`, populated meta
  fields, witness across hook domains, scores re-derived). Worth adding before the full run is authorized.
- **D2 (lexicographic ledger keying):** must. The measured defect from the unwired run (P100 → `data-181.csv`)
  would recur. Key each reply on the prompt's own file reference, never the turn index.
- **D3 (explicit auth forms):** must. Bare digits matched `401` inside `8401`.
- **D4 (ceiling arithmetic `ceil(193 × r_smoke × 1.10) + 5`):** reasonable, but it is a *proposal*. The plan's
  own rule (`ceil(193 × r_smoke)` + a stated P193 allowance) is authoritative until you rule. The 5 is measured
  from P193's 577→582 on the unwired run; applying it to a wired run is an assumption, not a measurement.

## 4. Open ruling — `CTXVM_BUDGET_TOKENS`

- Plan: **200000** — the adapter's `headroom` field only, not an engine budget.
- Delta card: **60000** — T-B's declared budget, so a later reader of `.meta.json` is not misled by a number no
  arm ever had.

Both are defensible; the field is metadata in a mirror-only run, so no paging fact turns on it. My recommendation:
**use 60000 and state in the plan that it is the declared design budget and drives `headroom` only** — it keeps
the capture's metadata consistent with `design/TB-PLAN.md`. Your call.

## 5. Not authorized by this review

The one-prompt wired smoke remains **unauthorized**. No model call, no shim creation, no full wired run, no
ceiling freeze, no GO for a Hermes paged cell, no cost claim.

Kit: `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK after the index resync. This card changes no gate input.
