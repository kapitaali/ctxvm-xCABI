# RR-PARTA-INVALID-20261123 — Part A first run INVALID: harness never set the engine's budget; no exposure table, no Gate E

Owner authorized Part A (`RR-E3REVISED-REVIEW`). I hash-stamped bank-36 into the manifest and added a model-free
`--exposure-only` mode to `stage1-policy-damage.py` (final harness sha `6cccefd0…`), then ran Part A on the frozen
bank-36 twice. **The output is INVALID — I am recording the defect, not a result.** $0, no model call, no push.

## 1. What I did correctly (conditions of the authorization)

- `manifest.sha256` now lists both `bank-pilot9.json` (`dbfaba69…`) and `bank-36.json` (`bfc6ce39…`, 36 items
  12/12/12); `sha256sum -c` → both OK; manifest sha `a3a882f0…`.
- `--exposure-only` mode contains **no model call** (no `/completion`, no `logp_gold`), needs no server, and is not
  gated on the failed Stage 0 (the exposure branch runs before the Stage 0 guard, which now applies only to the
  model-based Stage 1 path). Compiled; harness sha `6cccefd0…`.

## 2. The defect (why Part A is invalid)

`trim_by_policy` passes `budget_tokens=int(full_tokens*frac)` to `engine.select_context(..., budget_tokens=...)`.
But inspection of `CtxvmFaultPinEngine.select_context` shows **`budget_tokens` is never referenced in its body** —
the engine plans against `self._v_budget`, resolved at construction from `CTXVM_VBUDGET` or the pinned policy's
`budget`, default **24,000** (`context_engine.py:341–343, 494–496`). So all 6 policies × 3 budgets ran at the same
24k budget against ~4.7k-token tasks: `keep-law` returned None (no eviction) at every cell, producing a fake
"all needles survive" table. Two runs were byte-identical (sha `97331344…`) — deterministic but vacuous.

**Consequence:** the "Gate E fails / middle needle survives at all budgets" finding is an **artifact of the harness
bug**, not a property of the keep law. I did **not** report it as a NO-OP. The output was preserved as
`experiments/needle-revisit/partA-exposure-INVALID.json` (evidence, sha `97331344…`), not deleted.

## 3. Another mismatch worth recording

The bank-36 task is ~4,729 tokens (24 pages × 26 lines), not the ~8,331 tokens of bank-pilot9 (the probe measured
pilot9). So even with a correct budget, the 80/60/40% cells would be ~3,783/2,837/1,892 tokens — all below the
engine's 24k default, which is why nothing evicted. A real Part A needs the engine constructed with an **explicit
`v_budget` per cell** (the constructor's `v_budget` arg, or `CTXVM_VBUDGET` env with the engine rebuilt per cell),
and tasks large enough that the floor fits under the budgets. The revised dev prompt's "budgets 80/60/40% of full
tokens" is not the engine's budget semantics.

## 4. What is not claimed

No exposure table, no Gate E verdict, no NO-OP, no damage result, no hypothesis claim. The stub/shadow plugin work
(Part C) stays unrouted. I did not patch the harness further or re-run — that is a new harness correction needing
your ruling, given Part A already consumed an authorization and produced invalid data once.

## 5. Recommendation (owner's decision)

Authorize a **corrected Part A**: construct the engine with an explicit `v_budget` per budget cell (not the
`budget_tokens` kwarg), use tasks whose floor fits under the smallest budget, and freeze the corrected harness with
a new hash before running. Then Gate E can be computed from a real exposure table. No Part B/C until then.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.
