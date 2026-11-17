# TB-DSH-CAPTURE — proposal: a capture-fidelity run on the full T-B shape in the dsh lane

Status: **PROPOSAL / plan only.** Author: review lane, 2026-11-17, at the owner's request ("plan for a similar
run in the dsh lane"). The dsh lane was parked after Phase 1 (`RR-DSHPARK-20261117`); this card is a new
proposal, not a resumption. **No model call, no shim, no run, no ceiling freeze is authorized by this card.**
The first gate is a 3-prompt smoke that needs its own owner authorization.

## 1. What "similar" means, and the limit that changes it

The OpenCode wired run asked one harness to carry 193 prompts in **one session** and flush **one** xCABI trace.
The dsh adapter (`packages/deepseek/`) has a different lifecycle, measured from its source and the Plan C evidence:

- `src/index.ts:63-90` flushes on `session/disposed` and on effect cleanup; `src/tracer.ts:94-104` writes
  `<sessionId>-<Date.now()>.jsonl` per flush.
- The headless app is **one task per process** (`dsh --profile <p> headless "<task>"`), with optional
  `--session-id` to resume a persisted session. Each process mounts the plugin anew; its in-memory `sessions`
  map is new. So 193 headless prompts produce **193 short traces**, not one long trace. `--session-id` carries
  the model's context across prompts but does not make the adapter reuse one tracer across processes.

**Consequence:** this run can witness *per-prompt capture fidelity over the full fixture* — every prompt's
tool work becomes a valid, replayable trace — but **not** whole-session residency, paging, H3/H4, eviction, or
one-trace-with-193-turns. Anyone comparing it to the OpenCode run must compare like for like. If a single
193-turn dsh trace is required, that is a different harness problem (one long-lived process driving many turns)
and needs its own plan; do not assume it from `--session-id`.

## 2. Prerequisites already in place (verify once, do not re-derive)

- Fixture: 192 files × 150 rows, seed 7, digest `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`;
  193 prompts from the accepted phase-0 bundle; lookups key. Live prompt order is **lexicographic**
  (P100 asks for `data-181.csv`), so a reply ledger must key on each prompt's own `data-NN.csv` reference
  (delta D2 from `RR-TBWIRED-20261116.md`).
- Adapter: Plans A and B landed (`a2669c9`, `b701cc2`), both trees byte-identical, suite 15/14/0/1.
- Profile: `ctxvm-plana` boots `dsh-headless`, links the ctxvm adapter copy, and uses the OpenCode free route
  with the `x-opencode-session` header (verified in the profile patch, value not reproduced here). `ctxvm-dsh-local`
  links the DSH-checkout copy; either is acceptable, name the one used.
- Credential: `OPENCODE_API_KEY` is in the dsh store; export it into the process without printing it.
- Detector: match only explicit auth/quota forms (`HTTP 401/429`, `insufficient_credits`,
  `FreeUsageLimitError`, `authentication_error`), never bare digits — `401` once matched inside `8401` and
  stopped the unwired run (D3).

## 3. Phase 1 — smoke (MODEL CALL, NOT AUTHORIZED HERE)

Three prompts with a file read on `data-01.csv`…`data-03.csv` (not the no-tool "OK" prompt), on one profile,
each in its own headless process. For each prompt:
1. exit 0 with a reply;
2. a new `[ctxvm] trace written:` line in stderr and a new private `<sessionId>-<ts>.jsonl` under the trace dir;
3. `session.open` carries real provider/model from the header (`opencode` / `hy4-flash-free`) — Plan A's buffered
   identity path;
4. at least one `page.declare` from the tool result;
5. `validate_schema_v0_1.py` exit 0 and `replay` exit 0 with `divergences: []`;
6. no `400 MissingSessionID`, no auth/quota, no billed token.

The smoke also measures the rate this plan needs: assistant messages (model requests) per prompt for a
**tool-using** prompt, and how many traces one prompt writes. Record both. A no-tool smoke is not sufficient
(the OpenCode wired smoke used one and its rate of 1.0 did not survive the full run).

## 4. Ceiling — preregister from the smoke, before the full run

`ceiling = ceil(193 × r_smoke)` where `r_smoke` is the measured model requests per tool-using prompt, plus a
separately stated allowance for P193 (artefact write plus three lookups). The 5-request allowance from the
unwired run is an **assumption** when applied here; either measure a reconciliation-shaped prompt in the smoke
or state the allowance explicitly. No ceiling from any other run (198, 579, 451) is reused. Freeze one integer in
a new preregistration card before prompt 1; an overrun is a recorded result, never repaired by raising it.

## 5. Phase 2 — the full run (not authorized here)

- 193 prompts, same profile, one headless process per prompt, same `CTXVM_*` set with a **fresh trace name
  prefix per prompt** (or rely on the adapter's `<sessionId>-<ts>` naming and record every path).
- Snap the trace directory before and after; expect exactly one new private trace per prompt, 193 total.
  A missing trace is `NO RECORD` for that prompt and stops the run; no retry until green.
- Hard stops: calls past the frozen ceiling; prompt past 180 s; repeated "does not exist"; explicit auth/quota;
  any billed token; tool refusal; a second profile/session serving the run; an unparseable export; a `[ctxvm]
  flushTracer FAILED` line.
- Reply ledger keyed on each prompt's own file reference (D2), with auth detector as in §2 (D3).

## 6. Phase 3 — offline verification and fidelity criteria (D1, adapted for 193 traces)

- Count: 193 new traces, one per prompt; each validates under `validate_schema_v0_1.py` and replays with exit 0.
- Every trace's `session.open` carries real identity; every prompt with a tool result has ≥1 `page.declare`.
- `page.declare` refs across the run cover all 192 fixture files (distinct logicalRefs), one per per-file prompt;
  P193's artefact and three lookups scored by `tb-check`.
- Score the three denominators separately: file-exact (192/192), tuple coverage over attempted files
  (1536/1536 if all replies present), whole-fixture (1536/1536). Keep a wrong-labelled first ledger as an audit
  trail if the mapping defect recurs; correct it from the prompt text.
- Record every `[ctxvm]` flush line count and any `faultOfResidentPage` violation rows (the Plan C trace had
  none; the wired OpenCode partial had 20). They are observations, not paging evidence.

## 7. Claim ceiling and boundaries

This witnesses capture fidelity only: the dsh adapter turns each of the 193 prompts' tool work into a valid,
replayable v0.1 trace with correct identity. It does **not** witness paging, H3/H4, eviction, `enginePlan`, a
single 193-turn trace, cost, model-output determinism, or model quality. `cost: 0` is harness-reported, not a
receipt. Traces and exports stay private (law 9); no trace byte, credential, or unredacted prompt is committed.
No RECORD/CEILING/DATA-INVALID outcome is retried until green. Never push.

## 8. Authorization requested (STOP)

 authorized: planning only. To proceed, the owner must authorize the **3-prompt tool-using smoke** in §3.
After it passes, a fresh ceiling must be preregistered from its measured rate before any full run. This card
may be filed as a proposal; implementation belongs to the dsh lane (`packages/deepseek/**`, `reports/RR-W22*`).
