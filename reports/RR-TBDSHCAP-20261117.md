# RR-TBDSHCAP-20261117 — plan proposed for a dsh-lane T-B capture run

Owner request 2026-11-17: "plan for a similar run in the dsh lane". Proposal filed at
`design/TB-DSH-CAPTURE.md`. **No model call, no shim, no run, no ceiling freeze, no spend.** The dsh lane remains
parked (`RR-DSHPARK-20261117`); this is a proposal for a new assignment.

## The finding that shaped the plan

"Similar" cannot mean a one-trace copy of the OpenCode wired run. The dsh adapter flushes on `session/disposed`
and effect cleanup, writing `<sessionId>-<Date.now()>.jsonl` (`src/index.ts:63-90`, `src/tracer.ts:94-104`), and
the headless app is one task per process. So 193 prompts produce **193 short traces**, not one long trace;
`--session-id` carries model context but not a tracer across processes. The plan states that limit up front and
requires like-for-like comparison.

## Measured inputs to the plan

| item | source | value |
|---|---|---|
| fixture / prompts / lookups | accepted phase-0 bundle | 192 × 150, seed 7, digest `36561425…`, 193 prompts, lexicographic order |
| adapter | this repo | Plans A+B landed, both trees byte-identical, suite 15/14/0/1 |
| profile | `~/.dsh/profiles/ctxvm-plana/cordis.patch.yml` | `dsh-headless`, OpenCode free route with `x-opencode-session`, provider opencode / hy4-flash-free |
| credential | dsh store | `OPENCODE_API_KEY` present; export without printing |
| detector rule | unwired run defect | explicit auth/quota forms only; bare `401` matched inside `8401` once |
| ledger rule | unwired run defect | key each reply on its prompt's own `data-NN.csv`, never turn index |

## What the plan asks

1. **First gate: a 3-prompt tool-using smoke** (not the no-tool "OK" prompt), measuring requests per prompt and
   traces per prompt. `session.open` identity, a `page.declare`, validator and replay exits, and no auth/quota.
   **This is a model call and is NOT authorized by this card.**
2. Preregister a fresh ceiling from that measured rate — `ceil(193 × r_smoke)` plus a stated P193 allowance.
   No reuse of 198, 579, or 451; overrun recorded, never repaired.
3. Full run: 193 headless prompts, expect 193 private traces, hard stops as listed in the plan card.
4. Offline: per-trace validator/replay, 192 distinct refs, artefact and three lookups, three scoring denominators.

**Claim ceiling:** capture fidelity only — no paging, H3/H4, eviction, `enginePlan`, cost, determinism, or model
quality, and no claim of one 193-turn trace.

Owner authorization for the smoke is the next decision; this card does not request a full-run go yet.

Kit: `bash tools/run-ci.sh` rc=0 **ALL GATES GREEN** (2026-11-17, `/tmp/opencode/20261117-dshplan-ci.log`, ambient `CTXVM_*` cleared); `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.

## Revision after the dsh lane's handoff 15 (same day)

The lane's read-only comment was accepted in full, and `design/TB-DSH-CAPTURE.md` was revised before any
authorization. Changes:

1. **Session mode fixed:** one persisted DSH session via `--session-id` for every prompt, required because P193
   says "You have read every file in fixture/ in this session". Smoke and full run use the same mode; the exact
   command shape and session ids are recorded. Without this, `r_smoke` is undefined.
2. **Ceiling arithmetic:** `ceil(193 × r_smoke) + A`, using the **per-prompt maximum** from the smoke (not the
   mean), with A measured by a fourth P193-shaped smoke prompt or explicitly frozen as `5, UNMEASURED
   ASSUMPTION`. Overrun remains CEILING, never a repaired ceiling.
3. **Page-ref criterion:** set inclusion of the expected per-file tool refs, not a distinct-ref count; the adapter
   also declares `tool:unknown(null)` and summary/file pages (verified in the Plan A trace: 3 declares, 2 of them
   `tool:unknown(null)`). Extra refs recorded as observations; the smoke asserts data-01/02/03 filenames.
4. **Trace naming:** the trace-name-prefix option removed — grep finds no `CTXVM_TRACE_NAME` in the dsh adapter.
   Track captures via trace-dir snapshot, session ids, and `<sessionId>-<ts>` paths.
5. **No hardcoded scores:** the plan states the three denominators and lets `tb-check` print numbers with its
   command and date (law 5).
6. **Comparison axes table added** (§6b): one process/one trace-intended OpenCode wired run vs 193 processes/193
   traces here, with the route difference; no like-for-like claim. The unwired CEILING run is a separate reference.
7. **Wording:** "no billed token" replaced with harness-reported `cost: 0`, not a provider receipt.

Verified before revising: the absent `CTXVM_TRACE_NAME`, the extra page refs in the Plan A trace, the headless
`--session-id` option, and P193's own wording. The smoke remains **unauthorized**; this is a plan revision.
