# TB-DSH-CAPTURE — proposal: a capture-fidelity run on the full T-B shape in the dsh lane

Status: **PROPOSAL / plan only (revised 2026-11-17 after the dsh lane's handoff 15).** Author: review lane, 2026-11-17, at the owner's request ("plan for a similar
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

**Session mode is fixed, not a choice.** The full run uses one persisted DSH session via
`--session-id <id>` for every prompt, because P193 says *"You have read every file in fixture/ in this
session"* and needs the accumulated artefact. One headless **process** per prompt still gives one trace per
process (the adapter's in-memory `sessions` map is per process), but the model's context is carried by the
resumed session. The smoke **must use the same mode** — same `--session-id` shape, same profile — or its
measured rate is not comparable to the full run. Record the exact command shape and the session id(s).

The smoke has **four** prompts: P1–P3 with a file read on `data-01.csv`…`data-03.csv` (not the no-tool "OK"
prompt), and P193-shaped reconciliation (artefact write + the three lookups) as the fourth. For each:
1. exit 0 with a reply;
2. a new `[ctxvm] trace written:` line in stderr and a new private `<sessionId>-<ts>.jsonl` under the trace dir;
3. `session.open` carries real provider/model from the header (`opencode` / `hy4-flash-free`) — Plan A's buffered
   identity path;
4. for P1–P3, a `page.declare` whose `logicalRef` contains the prompt's own filename (`data-01` etc.); for the
   reconciliation prompt, the artefact and the three lookup answers;
5. `validate_schema_v0_1.py` exit 0 and `replay` exit 0 with `divergences: []`;
6. no `400 MissingSessionID`, no explicit auth/quota form, harness-reported `cost: 0` (**not a provider receipt**).

The smoke measures two quantities for the ceiling: model requests (assistant messages) per tool-using prompt
and requests for the reconciliation-shaped prompt. Record the **per-prompt maximum**, not the mean — the OpenCode
wired smoke used a no-tool prompt and measured 1.0, while the unwired full run's real rate was 582/193 ≈ 3.015.
Also record how many traces one prompt writes.

## 4. Ceiling — preregister from the smoke, before the full run

```
r_smoke     = max(model requests per tool-using smoke prompt)   # the maximum, not the mean
A           = measured reconciliation requests, if the P193-shaped smoke prompt ran;
              otherwise A = 5, explicitly labelled UNMEASURED ASSUMPTION
ceiling     = ceil(193 × r_smoke) + A
```

State `r_smoke`, A, and whether A was measured or assumed in the prereg card, together with the exact command
that produced them. No ceiling from any other run (198, 579, 451) is reused. Freeze one integer before prompt 1;
an overrun is the recorded outcome **CEILING**, never a repaired ceiling.

## 5. Phase 2 — the full run (not authorized here)

- 193 prompts, same profile and same `--session-id` mode as the smoke, one headless process per prompt, with the
  same `CTXVM_*` set. The adapter exposes **no** `CTXVM_TRACE_NAME` option (verified by grep over
  `packages/deepseek/**`); identify captures by a trace-directory snapshot plus recorded session ids and the
  adapter's `<sessionId>-<ts>.jsonl` paths. Do not promise a name-prefix feature that does not exist.
- Snap the trace directory before and after; expect exactly one new private trace per prompt, 193 total.
  A missing trace is `NO RECORD` for that prompt and stops the run; no retry until green.
- Hard stops: calls past the frozen ceiling; prompt past 180 s; repeated "does not exist"; explicit auth/quota;
  harness-reported nonzero cost; tool refusal; a second profile/session serving the run; an unparseable export; a
  `[ctxvm] flushTracer FAILED` line.
- Reply ledger keyed on each prompt's own file reference (D2), with auth detector as in §2 (D3).

## 6. Phase 3 — offline verification and fidelity criteria (D1, adapted for 193 traces)

- Count: 193 new traces, one per prompt; each validates under `validate_schema_v0_1.py` and replays with exit 0.
- Every trace's `session.open` carries real identity; every P1–P192 trace has ≥1 `page.declare` whose
  `logicalRef` contains the expected filename. **Score page refs by set inclusion**, not by distinct-ref count:
  the adapter also declares `summary`/`file` pages and `tool:unknown(null)` refs from message-less `tool/result`
  rows (seen in the Plan A/C traces), so the distinct total will exceed 192. Extra refs are observations, not
  failures. The smoke must assert that `data-01/02/03` appear in their traces' refs.
- P193's artefact and three lookups are scored by `tb-check`. Do not hardcode expected scores in this plan:
  state the three denominators — file-exact, coverage over files attempted, coverage over the whole fixture —
  and let `tb-check` print the numbers with its command and date (AGENTS law 5). Target values belong in the run
  card, not in the plan's result language.
- Record every `[ctxvm]` flush line and any `faultOfResidentPage` violation rows (the Plan C trace had none; the
  wired OpenCode partial had 20). They are observations, not paging evidence.

## 6b. Comparison axes — no like-for-like claim

| axis | OpenCode wired full | dsh capture run |
|---|---|---|
| processes / session | one server process, one session | 193 headless processes, one resumed DSH session via `--session-id` |
| traces | one final trace intended; **never produced** (NO RECORD at P22) | 193 short traces intended, one per process |
| route | `opencode-go/hy4-flash-free` direct | `opencode/hy4-flash-free` through DSH with `x-opencode-session` |
| context | carried in the single session | carried by the resumed DSH session, not by a tracer across processes |
| ending | NO RECORD (no flush) | to be measured; CEILING on overrun |

Any later comparison is **per-prompt capture fidelity**, never a like-for-like session trace. The unwired
OpenCode run (CEILING at 582 vs 579, 193/193 correct replies, no trace) is a separate reference, not a result
this run can inherit.

## 7. Claim ceiling and boundaries

This witnesses capture fidelity only: the dsh adapter turns each of the 193 prompts' tool work into a valid,
replayable v0.1 trace with correct identity. It does **not** witness paging, H3/H4, eviction, `enginePlan`, a
single 193-turn trace, cost, model-output determinism, or model quality. `cost: 0` is harness-reported, not a
receipt. Traces and exports stay private (law 9); no trace byte, credential, or unredacted prompt is committed.
No RECORD/CEILING/DATA-INVALID outcome is retried until green. Comparison with the OpenCode runs uses only the axes in §6b. Never push.

## 8. Authorization requested (STOP)

 authorized: planning only. To proceed, the owner must authorize the **3-prompt tool-using smoke** in §3.
After it passes, a fresh ceiling must be preregistered from its measured rate before any full run. This card
may be filed as a proposal; implementation belongs to the dsh lane (`packages/deepseek/**`, `reports/RR-W22*`).
