# RR-TBBREACH-20261116 — owner ruling: the 582-vs-579 overrun is a breach; next work is the wired experiment

The review lane routed the CEILING breach from `RR-TBOPEN2FULL-REVIEW` for an owner decision. The owner ruled in
chat, verbatim:

> lets call it a breach. we were supposed to plan for the wired experiment anyway

## What this ruling decides

1. **The overrun is a breach, not a passed run with a footnote.** 193 prompts, 582 model requests against the
   frozen 579 ceiling (P193 needed 5). The ceiling is **not** raised retroactively and the run is not re-scored
   as a clean cell. The completeness figures (192/192 file-exact, 1536/1536 both coverages, artefact PASS,
   lookups 3/3) remain observations from a CEILING run, with the breach attached.
2. **No GO for a Hermes paged cell came from this run.** The original plan's decision point ("a GO means
   preregister a Hermes paged cell") is not triggered. Any paged cell needs its own preregistration.
3. **The next planned work is the wired experiment**, i.e. `design/TB-OPENCODE-RUN.md` with `@ctxvm/opencode`
   wired, per the wiring checklist in `reports/RR-OPENWIRE-20261116.md`. The owner's sentence says to plan it;
   it does **not** authorize a model call for the wiring smoke or the wired run.

## What is still not authorized

- No paid cell, no Hermes paged cell, no ceiling change, no fixture/prompt change.
- No model call for the wired smoke test or the wired run — a smoke capture is the first check for the UNVERIFIED
  v2.3.0 compatibility and needs its own owner go.
- No cost or saving claim; `cost: 0` in the full run was harness-reported, not a receipt.
- No trace claim for the unwired run (no plugin, no validator).

## Handoff

The prompt for the other agents is in §"Prompt to pass on" below and is reproduced verbatim in the day file. It
asks for a **plan**, not an execution, and stops before any model call.

Mechanism note: no signature artifact; the owner ruled in chat and the review lane records the ruling with the
date and exact decision (precedent `RR-W8CSEQ-20261111`). Written by the review lane. No code change, no model
call, no spend.

## Prompt to pass on

```
T-B next step: plan the WIRED OpenCode experiment. Analysis and planning only — no model call, no run, no spend.

Owner ruling 2026-11-16 (verbatim): "lets call it a breach. we were supposed to plan for the wired experiment anyway"

WHAT IS SETTLED
- The full unwired run is CEILING: 193 prompts completed with exact replies (192/192 file-exact, 1536/1536
  tuple coverage both denominators, artefact PASS canonical, lookups 3/3), but P193 took 5 requests and the
  session ended at 582 against the frozen 579 ceiling. The owner calls this a BREACH.
- Do NOT raise 579 retroactively, do NOT re-score that run as a clean cell, and do NOT treat it as a GO for a
  Hermes paged cell. Its completeness numbers stay observations with the breach attached.
- The two harness defects in RR-TBOPEN2FULL-20261116 (P13 auth regex matched 401 inside 8401; lexicographic
  ledger mapping corrected) are settled and disclosed. Do not re-litigate them.

YOUR TASK: produce a plan for the wired run; stop before any model call.
1. Read: AGENTS.md; handoff/LANES.md; design/TB-PLAN.md (what T-B measures); design/TB-OPENCODE-RUN.md
   (harness plan, status AUTHORIZED for the unwired run); reports/RR-OPENWIRE-20261116.md (wiring checklist);
   reports/RR-TBOPEN2FULL-20261116.md and reports/RR-TBOPEN2FULL-REVIEW.md (the breach).
2. The plan must say exactly:
   - how @ctxvm/opencode is wired: project-local <run-dir>/.opencode/plugins/ctxvm.ts re-exporting the adapter's
     default {id,setup}; no built dist needed; no config-key shortcut.
   - the env set: CTXVM_TRACE_DIR + a FRESH CTXVM_TRACE_NAME per run, CTXVM_MODEL, CTXVM_PROVIDER,
     CTXVM_AGENT_ID, CTXVM_BUDGET_TOKENS, CTXVM_OPENCODE_VERSION.
   - flush discipline: the capture flushes only on graceful shutdown; a hard kill loses the slice silently;
     check hooks-witness.log after the smoke; no hot-reload.
   - the FIRST gate: v2.3.0 compatibility is UNVERIFIED (adapter documents v2.1.x). A one-prompt smoke capture
     must prove an xCABI trace and .meta.json are written, then validate with
     spec/rfc-0.1/validate_schema_v0_1.py and rust/target/release/replay. This smoke is a MODEL CALL and is NOT
     authorized by this prompt — end your plan with an explicit request for that authorization.
   - the run shape: same 192x150 fixture and verbatim design prompt unless the owner rules otherwise; a NEW
     ceiling derived from a wired-run smoke, not from the unwired 582; do not reuse 579 or 451.
   - the claim ceiling: even wired, the adapter is MIRROR-ONLY (no engine, no eviction, no enginePlan). A wired
     run witnesses capture fidelity — valid, replayable traces over the prompts — NOT paging, H3/H4, cost, or
     model-output determinism.
   - privacy: traces stay in the private state dir (law 9), no trace bytes or credentials committed.
3. Record the plan as a proposal card in design/ and a report card in reports/, with a LOG row (exactly four
   pipes), a day-file section, explicit staged paths via a private index, git read-tree HEAD afterwards, and
   git-hygiene.sh OK. Never push — the owner pushes. Attribution: kapitaali <teppo@kapitaali.com>.
4. STOP. Do not run opencode with a model, do not create the shim in a live run dir, do not edit packages/** or
   tools/**. Return the plan's file paths and the single authorization sentence you need for the smoke.

Gates for a planning-only handoff: bash tools/check-handoff.sh -> ALL PASS; the repo gate is unchanged by a plan.
```
