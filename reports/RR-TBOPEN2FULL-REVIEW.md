# RR-TBOPEN2FULL-REVIEW — verified: the full run is complete and exact, and the verdict is CEILING

Review lane, verify-then-record. Subject: `31901eb` / `RR-TBOPEN2FULL-20261116.md`. No model call, no code
change, no spend by this lane. Private artefacts stay under `~/.local/state/ctxvm/w8-runs/tb-open2-20261116/`.

## 1. Verdict

**All reported figures re-derived from the artefacts.** The run produced complete, exact replies on all 192
files and the artefact and lookups pass, but it ended at **582 model requests against the frozen 579 ceiling**,
so **CEILING is the correct verdict**. Per the plan's hard-stop rule and the owner's prior ruling, the ceiling
was not raised. The completeness figures are observations from a CEILING run, not a clean cell, and no GO for a
Hermes paged cell has been issued. The decision on the breach is the owner's.

## 2. Evidence

| claim | command / source | result |
|---|---|---|
| commit and card | `git log --oneline -3`, card read | `31901eb` present; card + LOG row + day section; earlier cards intact |
| session / model | `phase2-export-full.json → info.id / info.model` | `ses_tbopen2_20261116_full`, `opencode-go / hy4-flash-free` |
| single model throughout | count assistant `model` fields | **582/582** assistant messages on that one model/provider |
| prompts | `user` messages in export | **193** |
| calls | assistant messages in export | **582**, matching the last progress row (`prompt 193 … calls 582`) |
| ceiling breach | `phase2-progress.jsonl` last row | `STOP CEILING prompt 193: 582 > 579`; card's P193 needed 5 requests (577→582). No ceiling was raised |
| file-exact | `python3 tools/tb-check.py fixture --per-reply replies-phase2-corrected.jsonl` | **192/192 = 100 %**; verified by my own re-run |
| tuple coverage, attempted and whole fixture | same | **1536/1536 = 100 %** for both; precision 1536/1536 |
| artefact | `artefact-check.txt` | `PASS … parsed equality, bytes canonical` |
| lookups | `lookups-phase2.txt` | **3/3 PASS** with the expected values |
| tool calls | assistant `content` part types | **389** `tool` parts, matching the card |
| cost | `info.cost` and progress rows | all `0` — harness-reported, not a receipt; no cost claim |
| no trace | harness unwired | none produced; no validator run; correct |
| P13 defect | driver/resume logs and story | first driver stopped on `401` matched inside `8401`; resumed in the **same** session from P14; no re-run. The card discloses it |
| ledger defect | prompt 100 + corrected ledger | P100 names `data-181.csv` (lexicographic order), and the corrected ledger contains that file; first ledger kept as audit trail. No re-run of model calls |

## 3. What this means, and what it does not

- The shape works: a hand-countable 150-row workload on this free Go route yields complete, exact replies and a
  correct artefact with three correct refetch lookups. That is a capability/completeness result.
- The run is **CEILING**: predeclared hard stop, recorded, not retried. A GO for a Hermes paged cell requires the
  owner's decision on the breach and a fresh preregistration; neither happened here.
- The two harness-side defects are disclosed in the card and I confirmed their effects, but they are driver and
  ledger bugs, not model results. Neither produced a second session or a re-run: the exported ledger carries one
  session id and 193 user messages.
- `cost: 0`, harness tokens, and the completeness figures do not support any cost, saving, determinism, safety,
  paging, H3/H4, or `enginePlan` claim.

## 4. Owner decision routed

Does the CEILING breach (582 vs 579, caused by P193 needing 5 requests) block preregistering a Hermes paged
cell on this shape, or does the owner accept it as a recorded, non-fatal overrun and order a new prereg with a
revised ceiling? The review lane's recommendation: **do not treat the breach as evidence about the shape** — the
completeness result stands on its own, and a new prereg can set a ceiling from the measured 582 without changing
the fixture or prompt list. That is the owner's call.

Kit/gate: last re-run green (`ALL GATES GREEN`, rc=0; `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK); this card
adds no gate input.
