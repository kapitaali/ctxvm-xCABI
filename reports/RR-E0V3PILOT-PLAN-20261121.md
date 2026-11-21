# RR-E0V3PILOT-PLAN-20261121 — pre-registered pass criterion for the bank-v3 gradability pilot

Written **before** the pilot runs (owner "I copied the files. do your proposal" authorized the ratification,
landing, runner update, and v3 pilot on 2026-11-21). Anti-fishing guard: the decision rules below are frozen now,
not chosen after seeing the pilot outcome. Review lane, zero spend at authoring time.

## 1. What the pilot tests

`research/fixture-bank/` v3 (landed, `ctxvm-content-bearing-fixture-bank/v3`, 442/442 BANK_PHASE0_OK, traces
byte-identical to v2) changes the **prompt** (drops the fixation/echo triggers) and the **identifier rule**
(`T(p) = value_present + tag_present`, value counts `doc<j>_value` OR the bare distinctive number `100+7j`).
The pilot measures whether the v3 prompt makes a 1.7B baseline answer gradable on real generations — the part
that offline re-scoring cannot establish (12/20 on recorded answers under every rule variant).

## 2. Frozen decision rules

- **Sample:** 5 items (fb01–fb05), the same items as Gate 2 and chunk 1, pinned CPU llama.cpp 0.7.0-dev @
  620d222 / Qwen3-1.7B-Q8_0 `66a17017…`, $0 local ceiling, `temperature 0`, `seed 7`.
- **Gradability test per item:** `Var(T(p)) > 0` under the **v3** rule applied to the model's actual a(τ).
- **PASS criterion: ≥4 of 5 items gradable.** On PASS, a full 20-item v3 re-run is authorized to proceed
  (still a separate owner go-ahead for the ~7 h run, consistent with the prior chunking decision).
- **FAIL criterion: ≤3 of 5 gradable.** On FAIL, **stop** — do not loosen the identifier rule further, do not
  re-score by a new ruler, and do not proceed to the full run. Escalation is the fresh owner ruling for a larger
  model / GPU ceiling (option b), not a rule tweak.
- **No post-hoc changes:** the v3 rule and prompt are frozen at the landed `bank.json` sha. Any later rule change
  after seeing the pilot is a new deviation requiring its own owner-ratified card, and the pilot result may not be
  re-scored under it. This closes the c3 fishing path identified earlier.

## 3. What the pilot does not decide

No answer-quality, causal-influence, ρ, paging, cost, or model-quality claim. The pilot decides only whether the
gradability precondition is met for a valid E0 re-run. The invalid run's ρ observation (+0.518 among 12 gradable)
stays subordinated and is not pooled with any v3 result.

## 4. Applied

This plan card precedes the pilot run; the pilot result will be recorded in a separate card (`RR-E0V3PILOT`).
