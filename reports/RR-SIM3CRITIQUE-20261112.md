# RR-SIM3CRITIQUE-20261112 — critical audit of `RR-W8SIM3-20261112` (`78cc6e9`), the `CALL_LOG` scorer, and `upstream/hermes-context-engine-hook.md` (`e430322`)

Card: critical verification of (1) what `sim(S2)` actually scored in `local-b7d235587eef…coverage.json`,
(2) why the residual is whole-page quantization rather than "the protected-set/scaffold gap", (3) why
`upstream/hermes-context-engine-hook.md` must be **deleted** rather than edited, and (4) an explicit
erratum on `reports/RR-W8CTRANSPORT-20261112.md`.

---

## 1. What holds up in `RR-W8SIM3-20261112` — and the three things its narrative gets wrong or overstates

### A. What holds up (and holds up even without switching the denominator)
The central diagnosis — that `sim(S)` failed at turn granularity (33.3% median error) because each turn
makes **two** API requests while `turn.render.evictedTokens` sums both — is **true**, and we verified it
on the same `drop_k` denominator that `sim(S)` used:
- Scoring **`drop_k`** (`abs(pred_drop - obs_drop) / obs_drop`) across the 16 dropping calls in `callSizes`
  yields **median relative error 8.63%** (mean 8.71%, max 17.44%), which **passes `sim(S)`'s original
  ≤ 10% tolerance**.
- So the turn-vs-call aggregation diagnosis does not depend on switching the denominator from `drop_k`
  to `after_k`.

### B. Three analytical defects in `RR-W8SIM3-20261112` and the chat summary

1. **The physical explanation of the residual ("the protected-set/scaffold gap") is wrong — the residual
   is whole-page quantization (knapsack slack), and 7 of the 16 calls exceed 5% (`6.01%–8.21%`)**:
   - `RR-W8SIM3-20261112` writes: *"the engine fits the request under the budget including the protected
     set and scaffold, so `after` lands a few hundred tokens under the clamp. 1.2 % is that gap."*
   - In `packages/hermes/live/context_engine.py:495-496`, both `before` and `after` are
     `sum(_tokens_for(m) for m in ...)` over the full request (`request_messages` and `assembled`).
     Both already include the protected set and scaffold.
   - `after` lands below `60,000` because the engine drops **whole pages** (~4,400 apx4 tokens each ≈
     7.3% of the 60,000 budget) until the request fits. The slack `60,000 - after` is therefore bounded
     by the marginal dropped page's size (`0` to `~4,550` tokens), not by the scaffold.
   - Across the 16 calls in `local-b7d235587eef…coverage.json`:
     - Calls 1–9 (`before = 63,765..81,448`) land at `after = 59,283..59,834` → relative errors
       **`0.28%–1.21%`** (9 calls).
     - Calls 10–16 (`before = 81,539..100,026`) cross a page boundary by 91 tokens at call 10, forcing
       an extra ~4.4k page drop, and land at `after = 55,449..56,599` → relative errors
       **`6.01%–8.21%`** (7 calls, **all 7 above the 5% threshold**; overall mean `3.66%`, max `8.21%`).
     - Because 9 calls sit in the first regime and 7 in the second, the 16-sample median (average of the
       8th and 9th sorted errors, `1.06%` and `1.11%`) is **`1.16%` (`1.2%`)**, whereas the 10th sorted
       error jumps to **`6.01%`**. Two additional prompts (18 dropping calls instead of 16) would push
       the median above 6% and flip `sim(S2)` from PASS to FAIL — because a 5% clamp tolerance is tighter
       than one discrete page (`~4,400 / 56,000 ≈ 7.8%`).

2. **`CALL_LOG` censors all non-dropping calls, making `score_calls()`'s sign test one-sided**:
   - In `packages/hermes/live/context_engine.py:492-496`, `CALL_LOG.append(...)` sits **after**
     `if not dropped and not repositioned: return None`.
   - Consequently, `callSizes` contains **only the 16 dropping calls**, not the 25 non-dropping calls.
   - In `tools/w8-sim-score.py:76-81`, `dropped_obs = after < before` is therefore `True` on every entry
     in `callSizes` by construction. The 25 calls where the engine did not drop (`dropped_obs == False`)
     are never passed to `score_calls()`, and if a call ever had `before > budget` while failing to drop
     (e.g., if `_hard_keep` exceeded `budget`), it would return `None` at line 493, never enter
     `CALL_LOG`, and leave `sign_ok = True`.
   - Also note: the chat block `sim(S2): 41 selections, 16 that dropped, budget 60,000` was paraphrased;
     the actual stdout of `python3 tools/w8-sim-score.py --calls … --budget 60000` is
     `sim(S2): 16 selections, budget 60,000` / `sim(S2): selections with a predicted drop 16; median |error| 1.2%`.

3. **Two sidecar fields in `0.13.13` are still reading the old path** (`reports/RR-SIM3CHECK-20261112.md` §2):
   - `plugin.engine` is still `null` in `local-b7d235587eef…coverage.json` (`_engine_activated_for` in
     `packages/hermes/live/__init__.py:576-581` still checks instance `_engine_selections_for(profile)`).
   - `plugin.evictedPagesCount` is still `0` (`context_engine._value_tokens` splits on `.` while
     `plugin.identity_tokens` keeps `.txt`).

---

## 2. Verdict on `upstream/hermes-context-engine-hook.md` (`e430322`) — **delete, do not "correct"**

- `upstream/hermes-context-engine-hook.md` (committed in `e430322`, marked `"File-ready"`) claims that
  Hermes's `--oneshot` transport never enters `select_context()` because it bypasses
  `assemble_api_request`.
- That claim is **completely false**:
  - In `f1879a3` (plugin `0.13.7`), `select_context` wrote `ENTERED["n"] += 1` and `_d = Path(...)` inside
    `try: ... except Exception: pass` blocks **without defining `ENTERED` or importing `Path`** (fixed in
    `22404cd`, plugin `0.13.9`). Every call into `select_context` raised `NameError`, was swallowed
    silently, and left `_entered.log` absent and `engineEntered = 0`.
  - Once `Path` and `ENTERED` were defined (`22404cd`), `--oneshot` recorded `engineEntered = 57`
    (`w8b-20261112-161822`) and `engineEntered = 47` (`w8b-20261112-201127`).
- **Erratum on `reports/RR-W8CTRANSPORT-20261112.md` (`769c86e`)**: our earlier review card verified that
  `_prune_traces` only globs `*.jsonl` and inferred from the absent `_entered.log` that
  `assemble_api_request` was not reached on `--oneshot`. Because we read `context_engine.py` at HEAD
  after `22404cd` had already added `from pathlib import Path` and `ENTERED`, we missed that the runs
  being diagnosed had run under `f1879a3` (`0.13.7`), where both names raised `NameError` inside
  `except Exception: pass`. That inference in `RR-W8CTRANSPORT-20261112.md` §1–§2 is retracted.
- **Recommendation**: **Delete `upstream/hermes-context-engine-hook.md`** (`git rm`). Do not leave a
  falsified `"File-ready"` issue draft in `upstream/`. (If any upstream note is ever filed about
  `ContextEngine` ergonomics, it would be about documenting per-agent `deepcopy` of registered engines
  and multi-profile config scoping in a single gateway, not about an unreachable hook.)
