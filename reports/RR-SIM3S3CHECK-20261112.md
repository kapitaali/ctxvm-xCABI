# RR-SIM3S3CHECK-20261112 — verification of `d491912` (plugin `0.13.14`, `sim(S3)` interval scorer, `CALL_LOG` uncensored, sidecar mends, and deletion of `upstream/hermes-context-engine-hook.md`)

Card: verification of `d491912` and direct append of the §8 retraction block onto our review card
`reports/RR-W8CTRANSPORT-20261112.md`.

## 1. Verified in `d491912`

1. **`upstream/hermes-context-engine-hook.md` deleted (`git rm`)**: confirmed removed from the tree;
   `reports/RR-W8CTRANSPORT-20261112.md` now carries an explicit §8 Erratum / Retraction block in the
   file itself.
2. **Plugin `0.13.14` (`packages/hermes/live/context_engine.py:494-505`)**: `CALL_LOG.append({"before":
   _before, "after": _after, "dropped": len(dropped), "budget": self._v_budget})` now runs **before**
   `if not dropped and not repositioned: return None`, so future captures record all selections (dropping
   and non-dropping) with unit drop counts.
3. **Sidecar fixes in `0.13.14` (code-verified; next live capture confirms in sidecar bytes)**:
   - `packages/hermes/live/__init__.py:579`: `_engine_activated_for` now gates on `_selections_total() > 0`
     (`ACTIVATIONS['select']`) rather than the per-instance `_engine_selections_for(profile)`.
   - `packages/hermes/src/plugin.py:385-398`: `refs_for_identity_tokens` now joins by lowercased basename
     stem (`_stem`), verified in-process (`['tool:read_file({"path":".../part-01.txt"})']` returned for
     `_value_tokens` output `[['.../part-01', 'txt']]`).
   - Hermetic `pytest packages/hermes/test -q`: **201 passed, 15 subtests passed**.
4. **Scorer `sim(S3)` (`tools/w8-sim-score.py:65-111`)**:
   - Replaces the 5% point tolerance with the quantization interval `(budget - 2*page_est, budget]`,
     where `page_est = min(before - after) = 4,424` → `(51,152, 60,000]`, reporting `median |after -
     budget| / budget = 1.15%` as a diagnostic. All 16 dropping calls (`after = 55,449..59,834`) lie
     inside the interval.
   - **Minor wording/bound note in `tools/w8-sim-score.py`**: the docstring (`:72`) writes `budget -
     page_max < after_k <= budget` and the verdict print (`:110`) says `"inside one page of the budget"`,
     whereas line 97 sets `lo = budget - 2 * page_est` (two minimum-pages of slack = `8,848` tokens)
     because call 10's single dropped page was `4,473` tokens (`after = 55,449`, slack `4,551 = 1.029 ×
     page_est`, 127 tokens wider than `page_est = 4,424`). Once a `0.13.14` capture provides `dropped`
     per call, `page_max = max((before - after) / dropped)` can bound single-page slack directly.
