# TB-WIRED-BLOCK-20261118 — preregistration for today's fresh wired OpenCode run (ceiling 584)

**Status: FROZEN before any model call, 2026-11-18.** Owner authorization in chat this morning: "good morning. we
will do fresh new run now"; when asked which ceiling, the owner chose **"584 again (recommended)"** — meaning the
same derivation as the 17 Nov prereg, but as a **fresh** preregistration under today's date and a fresh run.

## 1. Frozen ceiling and derivation

| input | value | basis |
|---|---|---|
| `r` | **3.0** requests/prompt | measured on wired tool-using prompts: 201 requests ÷ 67 prompts (17 Nov CEILING run); the operator-stopped run confirmed 285 ÷ 95 = 3.0 |
| `A` | **5** requests | P193 allowance from the unwired 582-request run, stated as an **UNMEASURED ASSUMPTION** for the wired harness |
| **ceiling** | **584** = `ceil(193 × 3.0) + 5` | frozen here before prompt 1; arithmetic, not a carried-over integer from a voided prereg |

The prior preregs are void for this run: 198 (`TB-WIRED-BLOCK-20261117.md`, ended CEILING at P67), 579/451 from
earlier runs, and 582 from the unwired full run as an observation only. An overrun is the recorded CEILING
outcome; the integer is never raised after the fact.

## 2. Run shape (frozen)

- Same 192×150 seed-7 fixture, digest `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`;
  verbatim 193 prompts from the accepted bundle; lexicographic order (P100 asks for `data-181.csv`).
- One harness-managed server process (`opencode serve --hostname 127.0.0.1 --port <fixed>`) and one session for all
  193 prompts, with a **fresh run dir and trace name** for 18 Nov. Use the clean-flush driver; keep the process
  alive; flush gracefully. A hard kill loses the slice silently.
- `@ctxvm/opencode` project-local shim re-exporting the adapter; model/provider `opencode-go/hy4-flash-free`;
  seven `CTXVM_*` env keys set deliberately, including `CTXVM_BUDGET_TOKENS=60000` (metadata/headroom only).
- D1 fidelity criteria, D2 reply-ledger keying on each prompt's own `fixture/data-NN.csv` reference, D3 explicit
  auth/quota detector forms only, D4 the ceiling arithmetic above. Real wall time is ~5–6 h at observed pace;
  budget the day accordingly.

## 3. Hard stops and claim ceiling

Hard stops: calls past **584**; a prompt past the timeout; repeated "does not exist"; explicit auth/quota; any
billed token; tool refusal; a second session; an unparseable export; no flush in `hooks-witness.log`. Stop outcomes
(NO RECORD, CEILING, DATA-INVALID, INCOMPLETE) are recorded, never retried to green.

Capture fidelity only. No cost/saving, paging, H3/H4, eviction, `enginePlan`, determinism, or model-quality claim;
no GO for a Hermes paged cell. `cost: 0` is harness-reported, not a receipt. Traces and exports stay private
(law 9); no trace byte or credential committed; never pushed.

## 4. Evidence to return at the end

Final progress tail; witness chain including cleanup → flush → finishAll → cleanup exit; validator and replay exits
with full JSON; the three scoring denominators separately (file-exact, coverage over attempted files, whole
fixture); artefact and lookups if P193 ran; harness cost labelled as reported. Compare with prior wired runs only
on the axes in `RR-TBWIREDFULL2-REVIEW.md`; never as like-for-like session traces.

Written by the review lane. Kit/hygiene were green at setup; this card changes no gate input.
