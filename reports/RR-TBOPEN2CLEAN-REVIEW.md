# RR-TBOPEN2CLEAN-REVIEW — verified: the clean phase-1 session, and the 579-call ceiling

Review lane, verify-then-record. Subject: `7e3d977` / `RR-TBOPEN2CLEAN-20261116.md`. **No model call, no run,
no code change.** The artefacts stay private under `~/.local/state/ctxvm/w8-runs/tb-open2-20261116/`.

## 1. Verdict

**All claims re-derived from the artefacts.** The clean session is a valid basis for the new ceiling: one model
for all three prompts, 3/3 exact replies, 9 assistant messages (3 per prompt), 6 tool parts. The ceiling
`ceil(193 × 9/3) = 579` replaces 451 **for this run**. Phase 2 has not started, and none of this witnesses a
paged effect, a cost, or a trace.

## 2. Evidence

| claim | command / source | result |
|---|---|---|
| commit and card | `git log --oneline -3`, read card | `7e3d977` present, card + LOG row + day section; earlier cards intact (errata by new record) |
| clean session id | `export-clean-full.json → info.id` | `ses_tbopen2_20261116_p1clean` |
| exactly one model in the ledger | parsed 9 assistant `model` fields | `{('opencode-go','hy4-flash-free'): 9}`; `info.model` matches. No explabs or non-Go entry in the history |
| 3 prompts | user messages in the export | **3** |
| replies | `python3 tools/tb-check.py <fixture> --per-reply replies-clean.jsonl` | data-01/02/03 each `PASS — tuples 8/8`; file-exact 3/192; attempted coverage 24/24 = 100 %; precision 24/24 = 100 %; whole-fixture 24/1536 = 1.6 % |
| assistant messages | export, `type == "assistant"` | **9**, i.e. 3, 3, 3 per prompt |
| tool parts | assistant `content` part types | 6 `tool`, 2 `reasoning`, 3 `text` — matches the card's "tool calls 6" |
| rate / ceiling | arithmetic from 9/3 | **3.000 calls/prompt**, `ceil(193 × 3) = 579` |
| cost | `info.cost` and per-message cost | all `0` — harness-reported, not a receipt; no cost claim, as the card says |
| no trace | harness unwired; card states it | no validator run; correct |
| phase 2 not started | card's own statement + no new artefacts beyond phase 1 | accepted as reported; no call from this lane |

## 3. Carry-forward for phase 2

- Ceiling **579**, frozen; P193 may need more calls. An overrun is a recorded result, not a reason to raise it
  after the fact.
- Keep the unsanitized export private: `--sanitize` redacts reply text, so it cannot be the reply source. Both
  exports stay in the state dir; nothing is committed.
- The restart/new-session discipline matters: this ceiling was measured on the clean Go route. A session with
  another provider in its history is not comparable, and the earlier 451 must not be revived.
- Hard stops from the plan still apply: a prompt past the timeout, repeated "does not exist" errors, 401/429,
  any billed token, calls past 579, a second session, or an unparseable export.
- When reporting, keep the three denominators distinct: file-exact (3/192), attempted coverage (24/24), and
  whole-fixture coverage (24/1536). They answer different questions.

Kit/gate: last re-run green (`ALL GATES GREEN`, rc=0; `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK). This
card adds no gate input.
