# RR-TBOPENWIRE-PLAN-20261116 — plan-only handoff for the wired OpenCode T-B run

**Lane:** opencode. **Date:** 2026-11-16. **Type:** proposal / planning handoff. **No model call, no
shim created, no run, no spend, no code change to `packages/**` or `tools/**`.**

## 1. What was done

Read the required sources before writing: `AGENTS.md`, `handoff/LANES.md`, `design/TB-PLAN.md`,
`design/TB-OPENCODE-RUN.md` (AUTHORIZED for the unwired run),
`reports/RR-OPENWIRE-20261116.md` (wiring checklist and the v2.3.0 unknown),
`reports/RR-TBOPEN2FULL-20261116.md` and `reports/RR-TBOPEN2FULL-REVIEW.md` (the breach and its
verification). Wrote one proposal card, `design/TB-OPENCODE-WIRED.md`, which is the plan of record
for the wired run. Wrote this report, one LOG row and one day-file section.

## 2. The owner's ruling, and what it settles

Verbatim: "lets call it a breach. we were supposed to plan for the wired experiment anyway".

- The unwired full run is **CEILING/BREACH** (582 against 579). 579 is not raised retroactively; the
  run is not re-scored as a clean cell; it is not a GO for a Hermes paged cell. Its completeness
  numbers (192/192 file-exact, 1536/1536 tuple coverage on both denominators, artefact PASS
  canonical, lookups 3/3) stay observations with the breach attached.
- The two settled harness defects (P13 `401`-inside-`8401` false positive; lexicographic ledger
  mapping) are not re-litigated.

## 3. Plan summary

The full plan is in `design/TB-OPENCODE-WIRED.md`. Its load-bearing points:

1. **Wiring** is a project-local `<run-dir>/.opencode/plugins/ctxvm.ts` re-exporting the adapter's
   default `{ id, setup }`; the three hook domains are already implemented. No built `dist` is
   needed and no `opencode.jsonc` `plugin` key is used.
2. **Env**: `CTXVM_TRACE_DIR` + fresh `CTXVM_TRACE_NAME` per run, `CTXVM_MODEL`, `CTXVM_PROVIDER`,
   `CTXVM_AGENT_ID`, `CTXVM_BUDGET_TOKENS`, `CTXVM_OPENCODE_VERSION`; ambient Hermes `CTXVM*`
   variables cleared.
3. **Flush**: only on graceful shutdown; a hard kill loses the slice silently; verify
   `hooks-witness.log` after the smoke; no hot-reload.
4. **First gate**: v2.3.0 compatibility is UNVERIFIED (adapter documents v2.1.x). A one-prompt
   smoke must write `.jsonl` + `.meta.json`, show a complete witness chain, and pass the v0.1
   validator and the Rust replayer.
5. **Run shape**: same 192×150, seed 7 fixture and verbatim design prompt unless the owner rules
   otherwise; a **new** ceiling from the wired smoke's measured request rate, never 579/451/582.
6. **Claim ceiling**: mirror-only adapter — capture fidelity only, no paging/H3/H4, no cost, no
   model-output determinism.
7. **Privacy**: traces stay in the private state dir; no trace bytes or credentials committed.

## 4. Stop and authorization needed

This handoff stops before any model call, shim creation or run. The single authorization sentence
needed is the one at the end of the design card: authorize the **one-prompt wired compatibility
smoke** that proves whether the v2.3.0 plugin surface loads and flushes a valid xCABI trace. The
full wired run is a separate, later authorization after that smoke and a fresh preregistration.

## 5. Gates and files

- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS. The repo gate is unchanged by a plan; no
  `run-ci.sh` claim is made here.
- Staged explicitly via a private index: `design/TB-OPENCODE-WIRED.md`, this card, `reports/LOG.md`,
  `reports/RR-DAY-20261116.md`. Shared index resynced with `git read-tree HEAD`; `git-hygiene.sh`
  OK. Never pushed.
- Dirty files elsewhere (`design/W8-EXECUTOR-PROMPT.md`, `reports/RR-W8B-20261110.md`,
  `tools/w8-run-env.sh`, `research/**`, plus untracked design/W8C drafts) belong to other lanes and
  were not staged or changed.

## 6. Erratum — shared LOG collision (same day)

When this card was committed (`d06cf06`), another lane's uncommitted LOG row
`| RR-TBWIRED-20261116 | tb-wired | … |` was already present in the working-tree `reports/LOG.md`
and was therefore captured by my explicit `git add` of that shared file. That lane then landed its
own commit `a39f617` with `design/TB-WIRED-PLAN.md` and `reports/RR-TBWIRED-20261116.md`, so its row
is now committed but carried in **my** commit rather than its own. Committed rows are never
rewritten; this erratum names the misattribution. §5's "one LOG row" claim is corrected: my commit
carried two rows, one of which belonged to the other lane. No file of theirs was edited by this
lane, and the two plan cards remain separate proposals for the owner to reconcile.
