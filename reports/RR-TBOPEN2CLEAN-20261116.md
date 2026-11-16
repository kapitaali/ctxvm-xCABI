# RR-TBOPEN2CLEAN-20261116 — clean re-do of T-B phase 1, ceiling frozen at 579

**Lane:** opencode. **Date:** 2026-11-16. **Verdict:** phase 1 checkpoint passed on a session that
used **only** the authorized model; this supersedes the phase-1 ceiling in
`RR-TBOPEN2-20261116.md` (commit `7abc537`). No phase-2 call was made.

## 1. Why this card exists

In the first phase-1 attempt the provider had to be corrected mid-sequence: `explabs` attempts and a
non-Go `opencode/hy4-flash-free` attempt failed before any reply, then the measured three prompts ran
on a new session with `opencode-go/hy4-flash-free`. Those failures were disclosed in
`RR-TBOPEN2-20261116`, and that session itself used only the Go route. The owner asked for phase 1 to
be redone so the checkpoint has a session with **no other provider in its history at all**. This card
is that re-do; it does not rewrite the committed card or its LOG row (errata by new record, per the
book law).

## 2. What ran

Same fixture, prompts and lookups under `~/.local/state/ctxvm/w8-runs/tb-open2-20261116/`. Fresh
session `ses_tbopen2_20261116_p1clean`, from the first prompt to the last on one model:

```sh
cd ~/.local/state/ctxvm/w8-runs/tb-open2-20261116
SID=ses_tbopen2_20261116_p1clean
for n in 1 2 3; do
  timeout 180 opencode run --session "$SID" --model opencode-go/hy4-flash-free \
    --auto "$(cat p$n.txt)" > p${n}c.out 2> p${n}c.err
done
opencode session export "$SID" --sanitize > export-clean-sanitized.json
opencode session export "$SID"             > export-clean-full.json
python3 <repo>/tools/tb-check.py fixture --per-reply replies-clean.jsonl > per-reply-clean.txt
```

All three prompts exited 0 inside the 180 s cap; no tool refusal, no `does not exist` error, no auth
error, no billed token. `--auto` made execution tools available. The exported ledger's assistant
messages name exactly one model: `hy4-flash-free`. `info.cost` is 0 — a harness-reported field, not a
receipt, so no cost claim.

As before, `--sanitize` redacts reply text, so the reply ledger was built from the private
unsanitized export; both exports remain in the state dir and neither is committed.

## 3. Measurements

| quantity | value |
|---|---|
| file-exact replies | **3 / 3** (data-01, data-02, data-03 each `PASS — tuples 8/8`) |
| tuple coverage over files attempted | **24 / 24 = 100 %** |
| tuple precision | **24 / 24 = 100 %** |
| whole-fixture tuple coverage | 24 / 1536 = 1.6 % (only 3 of 192 files run) |
| assistant messages per prompt | **3, 3, 3 → 9 total** |
| tool calls | 6 |
| measured rate | **3.000 calls/prompt** |
| **frozen ceiling** | **ceil(193 × 9/3) = 579 calls** |

**The 451 ceiling from the earlier phase-1 card is void for this run.** The mechanical rule is the
same as before — ceiling = ceil(193 × measured calls/prompt) — applied to the clean session. P193
(artefact write plus three lookups) may need more calls; an overrun is a recorded result, not a
reason to raise the ceiling after the fact.

## 4. Claim ceiling

This witnesses only that three hand-countable per-file prompts on the authorized Go route produced
complete, exact replies with tools available, at 3.0 model requests per prompt (n = 1 session). It
does **not** witness paging, H3/H4, any eviction, any full-run completeness verdict, any cost
saving, or any trace (the OpenCode harness is unwired; no validator applies).

## 5. Files

- Repo: this card, one LOG row, one appended section in `reports/RR-DAY-20261116.md`. No tool,
  package, spec, corpus or research byte changed.
- Private artefacts under `~/.local/state/ctxvm/w8-runs/tb-open2-20261116/`: `session-clean.id`,
  `p1c.out`–`p3c.out`, `p1c.err`–`p3c.err`, `export-clean-sanitized.json`, `export-clean-full.json`,
  `replies-clean.jsonl`, `per-reply-clean.txt`.

Phase 2 has not started.
