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
