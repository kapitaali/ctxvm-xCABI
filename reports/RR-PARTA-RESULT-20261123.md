# RR-PARTA-RESULT-20261123 — Part A corrected: real exposure table, Gate E PASSES at the 40% budget

Owner authorized corrected Part A under five hard conditions (`RR-PARTA-CORRECT-AUTH`). Executed model-free, $0, no
provider call, no server. Two byte-identical runs. Kit ALL PASS, hygiene OK, no other lane's WIP touched, no push.

## 1. The five conditions — satisfied

1. **Engine per cell with explicit `v_budget`:** `CtxvmFaultPinEngine(v_budget=int(full×frac))`; asserted
   `eng._v_budget == budget and not refused` per cell — no clamp (all budgets ≥24,271).
2. **Tasks fit the smallest budget:** regenerated the fixture at 365 lines → `bank-60k.json` (36 items, 12/12/12),
   min task 60,679 tokens, floor ≈10,050, so `floor < 24,271 (40%) < resident` — H11FLOOR rule met. Fresh hash in
   manifest (`f919446e…` at run, final `10da4fe5…`), all three banks verify.
3. **Budget bit asserted at runtime:** captured each `select_context` plan via `set_observer(None, plan_callback)`;
   108/108 cells report `reason=evicted` / `droppedCount>0` (keep-law 108/108). Fail-closed guard would refuse a table
   if no cell bit (it fired correctly on the two earlier broken attempts).
4. **Corrected harness frozen:** `stage1-policy-damage.py` sha `1b32f980…` (per-cell engine, plan-bit assert, and
   pinning the engine's own by-path policy module to the paged arm — the third fix needed, see §4). The invalid
   output stays preserved as `partA-exposure-INVALID.json`.
5. **Gate E from the corrected table; Part B/C gated.** $0, model-free, no re-score.

## 2. Exposure table (needle survived / total, by band × policy × budget)

| policy | 80% (early/mid/late) | 60% | 40% |
|---|---|---|---|
| **keep-law (real engine)** | 12/12 · **11/12** · 12/12 | 12/12 · **7/12** · 12/12 | 12/12 · **1/12** · 12/12 |
| random-middle | 12/12 · 0/12 · 12/12 | same | same |
| recency-only | 1/12 · 0/12 · 12/12 | same | same |
| oracle (keep needle) | 12/12 · 12/12 · 12/12 | same | same |
| anti-oracle (drop needle) | 1/12 · 0/12 · 0/12 | same | same |
| touch-aware | 12/12 · 12/12 · 12/12 | same | same |

Reading: the real keep law protects head/tail perfectly and loses middle pages increasingly as the budget tightens —
1/12 at 80%, 5/12 at 60%, **11/12 at 40%**. Controls behave as designed (oracle keeps, anti-oracle drops,
random-middle drops all middle). This is a coherent silent-loss curve.

## 3. Gate E

Middle-needle drop fraction under keep-law: **0.083 @80% (FAIL), 0.417 @60% (FAIL), 0.917 @40% (PASS ≥0.75)**.
→ **Gate E PASSES at the 40% budget** (`budget ≈ 24,271` tokens). Per the dev prompt, Part B's budget is taken from
this table (40%), not by trial.

## 4. Two harness corrections needed beyond the ruling (recorded, not hidden)

- **Policy module pinning:** the engine resolves `pol = _policy_module().policy()` from its own by-path module
  `ctxvm_profile_policy`; my earlier `profile_policy` stub never reached it, so `select_context` read the operator's
  real `~/.hermes` (`engine: compressor`) and skipped every cell as a control arm. Fixed by pinning
  `ce._policy_module().policy` to the paged arm — the same mechanism the plugin test suite uses to keep laws
  non-inert.
- **Fixture size:** bank-36 (~4.7k tokens) and a first 110-line bank (~18.7k) could not exercise budgets ≥24k; the
  365-line bank was required. Both superseded banks remain in the gitignored workspace and manifest.

## 5. What this is / is not

This is a **structural result** — where the needle dies under the product's own keep law — even if Part B never runs.
No model call, no accuracy/causal/paging/cost/model-quality claim, nothing pooled. Part B (live recovery) still needs
its capability gate C, a free-route preflight, and a **separate owner ruling**; Part C (stub) is a hermes-lane plugin
card, owner-routed. The mandatory `tool_recall` dry check from the dev prompt remains owed before any Part B arm.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.
