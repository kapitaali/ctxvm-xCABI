# TB-WIRED-BLOCK2-20261117 — preregistration for the fresh wired OpenCode run (ceiling 584)

**Status: FROZEN before any model call.** Owner authorization 2026-11-17, confirmed in chat after I drafted the
re-run prompt:

> I authorize a fresh full 193-prompt wired OpenCode run with the @ctxvm/opencode shim and opencode-go/hy4-flash-free, under a newly preregistered ceiling of 584 derived from the measured rate of 3.0 requests per prompt plus a stated P193 allowance of 5, with the D1–D4 fidelity and detector rules applied and any overrun recorded rather than repaired.

This replaces the earlier preregistration in `reports/TB-WIRED-BLOCK-20261117.md` (ceiling 198). That run ended
CEILING at P67 with 201 requests; its record is `RR-TBWIREDFULL2-20261117.md`. 198, 579 and 451 are void for this
run; 582 remains an observation from the unwired run.

## 1. Frozen ceiling and derivation

| input | value | basis |
|---|---|---|
| `r` | **3.0** requests/prompt | measured on the wired run's tool-using prompts: 201 requests ÷ 67 prompts = 3.0 |
| `A` | **5** requests | P193 allowance measured on the **unwired** run (577 → 582). Applied here as an **UNMEASURED ASSUMPTION** for the wired harness; stated, not asserted as wired-measured |
| **ceiling** | **584** = `ceil(193 × 3.0) + 5` | frozen here before prompt 1; arithmetic, not a reused integer |

The no-tool smoke's rate of 1.0 from `RR-TBOPENSMOKE-20261116` is explicitly rejected as a basis: it did not
survive either full run. An overrun is the recorded **CEILING** outcome, never a repaired ceiling.

## 2. Run shape (frozen)

- Same 192×150 seed-7 fixture, digest `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`;
  verbatim 193 prompts from the accepted bundle; lexicographic order (P100 asks for `data-181.csv`).
- One server process and one session for all prompts, using the driver that produced the earlier **complete flush
  chain**. Keep the process alive; flush gracefully. A hard kill loses the slice silently and yields NO RECORD.
- `@ctxvm/opencode` project-local shim re-exporting the adapter; model/provider `opencode-go/hy4-flash-free`;
  seven `CTXVM_*` env keys set deliberately with a fresh trace name.
- Timeout cap per prompt as in the plan. D1 fidelity criteria, D2 reply-ledger keying on each prompt's own
  `fixture/data-NN.csv` reference, D3 explicit auth/quota detector forms only, D4 the ceiling above.

## 3. Hard stops and claim ceiling

Hard stops: calls past **584**; a prompt past the timeout; repeated "does not exist"; explicit auth/quota; any
billed token; tool refusal; a second session; an unparseable export; no flush in `hooks-witness.log`. A stop is a
recorded outcome — NO RECORD, CEILING or DATA-INVALID — never a retry until green.

Capture fidelity only. No cost or saving, no paging, H3/H4, eviction, `enginePlan`, model-output determinism, or
model-quality claim, and no GO for a Hermes paged cell. `cost: 0` is harness-reported, not a receipt. Traces and
exports stay private (law 9); nothing committed; never pushed.

## 4. What the run must report

Final progress tail and witness chain (cleanup → flush → finishAll → cleanup exit), validator and replay exits
with full JSON, three scoring denominators separately (file-exact, coverage over attempted files, whole fixture),
artefact and lookups if P193 runs, harness cost labelled as reported. Compare with earlier runs only on the axes
in `RR-TBWIREDFULL2-REVIEW.md` — never as a like-for-like session trace.

Gate/kit were green at the last check; this card changes no gate input. Written by the review lane.

## 5. Erratum — duplicate preregistration collision (opencode lane)

Another lane had already committed this same preregistration at `2242220` with the same frozen
ceiling **584** and the same derivation (`ceil(193 × 3.0) + 5`, allowance A = 5 as an UNMEASURED
ASSUMPTION). My subsequent commit `6d5f36d` overwrote this card and appended a second LOG row with
the same id. That commit was unpublished; I reset the local HEAD to `2242220` and restored this
card, the LOG and the day file to the other lane's committed bytes. This block records the collision
instead of rewriting committed history. The authoritative preregistration is the version above; the
ceiling **584** and all run rules are unchanged. No model call had been made when the collision was
found and corrected.
