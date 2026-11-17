# TB-WIRED-BLOCK-20261117 — preregistration for the full wired OpenCode run

**Status: FROZEN before the full run.** Owner authorization 2026-11-17: "I authorize the full
193-prompt wired OpenCode run with the @ctxvm/opencode shim and opencode-go/hy4-flash-free, under a
freshly preregistered ceiling derived from r_smoke = 1.0 by the plan rule ceil(193 × r_smoke) plus a
stated P193 allowance, with the D1–D4 fidelity and detector rules applied and any overrun recorded
rather than repaired."

This block freezes the single integer the run is held to. It is written and committed **before**
any full-run model call. No ceiling from the unwired run (579, 451) or its breach observation (582)
is reused.

## 1. Frozen ceiling

| input | value | derivation |
|---|---|---|
| `r_smoke` | **1.000** requests/prompt | wired smoke, 1 assistant message for 1 no-tool prompt (`RR-TBOPENSMOKE-20261116`) |
| base | `ceil(193 × 1.000)` = **193** | plan rule `design/TB-OPENCODE-WIRED.md` §6 |
| P193 allowance | **5** requests | measured on the unwired run (P193 took 577 → 582). Applying it to a wired run is an **assumption**, stated here, not a wired measurement |
| **FROZEN CEILING** | **198 model requests** | 193 + 5 |

The delta card's `ceil(193 × r_smoke × 1.10) + 5 = 218` is recorded as a proposal, not used. The
owner's authorization names the plan rule, not the delta formula.

**Stated risk before the run:** `r_smoke` came from a no-tool prompt. The full prompts require a file
read and an arithmetic tool call, so their per-prompt request count may exceed 1.0. That is not a
reason to change the number after seeing the data: if the session crosses **198**, the run stops and
the overrun is recorded (CEILING/BREACH), never repaired by raising the ceiling.

## 2. Run shape (frozen)

- Fixture: 192 files × 150 rows, seed 7, digest
  `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`.
- Prompts: the same 193 from the accepted phase-0 bundle, verbatim `design/TB-PLAN.md` §3 wording;
  lexicographic order (P100 asks for `data-181.csv`).
- Harness: one OpenCode v2.3.0 process with the project-local `@ctxvm/opencode` shim in the run
  dir, one session for all 193 prompts, `opencode-go/hy4-flash-free`, seven `CTXVM_*` env keys with
  a fresh trace name, `CTXVM_BUDGET_TOKENS=60000` (metadata/`headroom` only, not an engine budget).
- One long-running server process is used so a single tracer accumulates the whole session and
  flushes once on graceful shutdown; per-prompt `opencode run` processes would each overwrite the
  same trace name and lose the earlier events.

## 3. D1–D4, applied as authorized

- **D2 ledger keying:** every reply keyed on its prompt's own `fixture/data-NN.csv` reference, never
  the turn index.
- **D3 auth detector:** explicit forms only (`HTTP 401/429`, `insufficient_credits`,
  `FreeUsageLimitError`, `authentication_error`); no bare digits.
- **D1 full-run fidelity pass criteria (to evaluate after the run, not now):** ≥192 distinct page
  refs in `page.declare`; one `session.open` with the real model/provider; `pluginVersion` and
  `harnessVersion` populated; `hooks-witness.log` showing both hook domains across the run;
  completeness scores re-derived from the same replies, unchanged or the difference explained.
- **D4 ceiling:** §1 above; 198 frozen, overrun recorded.

## 4. Hard stops and claim ceiling

Hard stops: calls past 198; prompt past 180 s; repeated `does not exist`; explicit auth/quota error;
any nonzero harness cost; tool refusal; a second session; an unparseable export; no flush in the
witness log. A stop is a result to record, never a retry until green.

Mirror-only adapter: the run can witness capture fidelity only — valid, replayable xCABI traces over
the prompts. No paging, H3/H4, eviction, `enginePlan`, cost, or model-output determinism claim.
Traces stay in the private state dir; no trace byte or credential is committed.

## 5. Verification

`bash tools/check-handoff.sh` → ALL PASS; repo gate re-run unpiped with ambient `CTXVM*` cleared
after this tracked card is added. Explicit staged paths via private index, `git read-tree HEAD`
afterwards, `bash tools/git-hygiene.sh` OK. Never pushed.
