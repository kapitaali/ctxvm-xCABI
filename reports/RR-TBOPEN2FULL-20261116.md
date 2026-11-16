# RR-TBOPEN2FULL-20261116 — full T-B OpenCode run: complete replies, but CEILING

**Lane:** opencode. **Date:** 2026-11-16. **Verdict:** **CEILING** — all 193 prompts produced usable
replies, but the run ended at **582 model requests against the frozen 579 ceiling**. Per the
owner's ruling the breach is a recorded result, not a reason to raise the ceiling afterwards.
**n = 1** session. No phase-4 cell was run.

## 1. Authority and setup

Preregistration signed (`RR-TBAUTH-20261116`); phase 0 accepted (`RR-TBPHASE0-20261116`); clean
phase 1 verified and ceiling frozen at 579 (`RR-TBOPEN2CLEAN-20261116` and its review
`RR-TBOPEN2CLEAN-REVIEW`, commit `6bc6357`). Model: `opencode-go/hy4-flash-free` throughout, one
session `ses_tbopen2_20261116_full`, one process per prompt, `--auto` so tools were available.

```sh
cd ~/.local/state/ctxvm/w8-runs/tb-open2-20261116
# driver: for i in 1..193:
#   timeout 180 opencode run --session ses_tbopen2_20261116_full \
#     --model opencode-go/hy4-flash-free --auto "$prompt_i"
# after every prompt: local session export --sanitize, count assistant messages,
# stop on rc!=0 / calls>579 / cost!=0 / auth-quota / tool refusal / repeated
# "does not exist" / timeout. No model call in the checks.
```

## 2. Two driver/ledger defects, disclosed (neither is a model result)

1. **P13 false positive.** The first driver's auth regex matched the bare digits `401` inside the
   data value `8401`. Prompt 13 had exited 0 with a correct reply; the run resumed **in the same
   session** from P14 with a corrected detector (explicit `HTTP 401/429`, status/code forms,
   `insufficient_credits`, `FreeUsageLimitError`, `authentication_error`). Prompts 1–13 were not
   re-run; no second session was used.
2. **Reply-ledger filename mapping.** The first offline ledger labeled turn *i* as
   `data-XX.csv` sequentially. The prompt list is **lexicographic** (`data-01`…`09`, `10`,
   `100`…`109`, `11`…), so P100 actually asks for `data-181.csv`. Rebuilding the ledger from each
   prompt's own `fixture/data-NN.csv` reference turned an apparent 10/192 file-exact score into the
   real one below. No model call was repeated; the underlying replies and tool traces show the
   model read the correct file (P100 read `data-181.csv`, then computed it).

Both defects are in the harness-side driver/ledger, not in the measured work. They are recorded so
the raw progress files and the corrected scores can be reconciled.

## 3. Measurements

| measure | result |
|---|---|
| prompts run | **193 / 193**, all rc 0, all within 180 s |
| files answered | **192 / 192** |
| **file-exact accuracy** | **192 / 192 = 100 %** |
| **tuple coverage, files attempted** | **1536 / 1536 = 100 %** |
| **tuple precision (implied)** | **1536 / 1536 = 100 %** |
| **tuple coverage, whole fixture** | **1536 / 1536 = 100 %** |
| artefact | `tb-check fixture artefact.json` → **PASS**, parsed equality, bytes canonical |
| three exact-row lookups | **3 / 3 PASS** (data-02/5686/zeta/−264; data-07/8606/delta/−268; data-11/5329/zeta/487) |
| calls (assistant messages) | **582** (final prompt took the count from 577 to 582) |
| tool calls | 389 |
| harness session cost | `0` — a harness-reported field, **not a provider receipt** |
| harness tokens (observation) | input 1,548,955; output 62,969; cache read 115,840,768 |

The three denominators are independent: file-exact (192/192), coverage over files attempted
(1536/1536), and coverage over the whole fixture (1536/1536). All three are printed by the checker
in `per-reply-phase2-corrected.txt`; the first, wrong-labelled ledger is kept as
`per-reply-phase2.txt` for the audit trail.

**The ceiling.** The frozen ceiling was `ceil(193 × 3.000) = 579`. P193 (artefact write plus three
lookups) needed 5 requests, taking the session to 582. That is a **CEILING** result. The
completeness numbers above are observations from that run; they are not a clean cell, and no
ceiling was raised to accommodate the overrun.

## 4. Claim ceiling

No cost or saving claim (`cost: 0` is local/harness-reported, not a receipt); no model-output
determinism claim; no safety or evaluation claim; no paging, H3, H4, eviction or `enginePlan`
result — this harness has no engine. No xCABI trace exists (`@ctxvm/opencode` is not wired), so no
validator was run and no trace claim is made. The verdict is CEILING, not a GO for a Hermes paged
cell; any preregistration decision is the owner's.

## 5. Files

- Repo: this card, one LOG row, one appended section in `reports/RR-DAY-20261116.md`. No tool,
  package, spec, corpus or research byte changed.
- Private artefacts under `~/.local/state/ctxvm/w8-runs/tb-open2-20261116/`: `phase2-driver.py`,
  `phase2-resume.py`, `phase2-progress.jsonl`, `phase2-driver.log`, `phase2-resume.log`,
  `f001.out`–`f193.out`, `f001.err`–`f193.err`, `phase2-export-sanitized.json`,
  `phase2-export-full.json`, `replies-phase2.jsonl`, `replies-phase2-corrected.jsonl`,
  `per-reply-phase2.txt`, `per-reply-phase2-corrected.txt`, `artefact.json`, `artefact-check.txt`,
  `p193-reply.txt`, `lookups-phase2.txt`. Both exports stay private; the sanitized one redacts
  reply text.
