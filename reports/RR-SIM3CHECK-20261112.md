# RR-SIM3CHECK-20261112 — review verification of `0.13.11–0.13.13` (`49a7f53`, `1af40e7`, `bf6fcb1`) and `RR-W8SIM3-20261112` (`78cc6e9`)

Card: independent verification from the capture (`local-b7d235587eef918aa747c31e1dc4302fc2afad3bc6c2b39106ce46ed0734ce75.jsonl` + `.coverage.json`, run `w8b-20261112-201127`) and source check of `packages/hermes/live/__init__.py` and `packages/hermes/live/context_engine.py`.

## 1. Independent repro of the call-granularity scorer (`RR-W8SIM3-20261112`)

Command run against the capture:

```
python3 tools/w8-sim-score.py --calls \
  ~/.local/state/ctxvm/traces/local-b7d235587eef918aa747c31e1dc4302fc2afad3bc6c2b39106ce46ed0734ce75.jsonl \
  --budget 60000
```

Output matches `reports/RR-W8SIM3-20261112.md` byte-for-byte:
- `16 selections, budget 60,000` (out of `engineSelections: 41`, `engineEntered: 47`)
- `selections with a predicted drop 16; median |error| 1.2%`
- `every prediction's sign matches: True`
- `VERDICT PASS (sign exact, median error <= 5 %)`
- Trace `turn.render.evictedTokens` sum: **227,963** across 7 dropping turns (`$0.00`, longcat free tier).

What this settles:
1. The engine was engaging once residency crossed the 60,000 apx4-char budget (`_decision.log` confirmed `units=18…22 kept=10 dropped=6…9`), and the earlier `engineSelections: 0` / `callSizes: []` readings were **instance-identity splits** between `engine_obj._meter` and the instance invoked by the host, now fixed by module-global `OBSERVER`, `ACTIVATIONS['select']`, and `CALL_LOG` (`1af40e7`, `bf6fcb1`).
2. Default home `~/.hermes` is now forced to `compressor` in `profile_policy` (`1af40e7`), stopping the experiment engine from trimming the operator's own session.
3. The turn-granularity scorer failure (`RR-W8SIM2-20261112`, 33.3% median error) was the 2-calls-per-turn aggregation mismatch, whereas the preregistered call-granularity clamp rule (`2b6c950`) passes at **1.2% median relative error** (`78cc6e9`). As `RR-W8SIM3-20261112` notes, this validates that the keep law clamps each request under budget (`after_k = min(before_k, budget)`), not general multi-turn policy prediction.

## 2. Two minor sidecar residuals located in the same capture (non-blocking for `RR-W8SIM3`)

In `local-b7d235587eef…coverage.json`, `plugin.engineSelections` is `41` and `len(plugin.callSizes)` is `16`, while two sidecar fields still read empty:
- **`plugin.engine: null`**: `packages/hermes/live/__init__.py:779` calls `_engine_activated_for(_session_profile)` (`:576-581`), which still checks `_engine_selections_for(profile) > 0` (the per-instance `engine_obj._meter["by_profile"]`) instead of `_selections_total()` (`ACTIVATIONS['select']`).
- **`plugin.evictedPagesCount: 0`**: `packages/hermes/src/plugin.py:345` builds page `identities` via `identity_tokens(ref)`, which preserves the file extension (`.../part-01.txt`), whereas `packages/hermes/live/context_engine.py:187` (`_value_tokens`) splits on `.` and yields `{'.../part-01', 'txt'}`. Because `refs_for_identity_tokens` (`packages/hermes/src/plugin.py:376-393`) joins by exact set intersection (`want & set(page["identities"])`), the dot-split prevents the join from matching.

Neither affects the trace events (`turn.render.evictedTokens = 227,963`) or `CALL_LOG` / `w8-sim-score.py --calls`.
