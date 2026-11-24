# RR-STUB-RENDER-20261124 — page.render(mode=stub) added; visibility turn corrected

Lane: hermes. Authority: owner "implement stub render". Completes `design/page-evict-stub-mode.md`
§3 and the design erratum (`RR-PAGE-EVICT-DESIGN-ERRATUM`). Version **0.13.32 → 0.13.33**, synced;
gateway restart owed to operator. No arm, model call, spend, default-on, D17 action, Part B re-score,
paper edit, Rust edit, or push.

## 1. The two defects this closes

1. **Missing companion event.** The previous implementation emitted `page.evict` but no
   `page.render(mode=stub)`; `_reveal()` still emitted `full` only. The design requires both at the
   same seam. Replay's presence gate could not catch this because no stub-mode hermes trace existed.
2. **Off-by-one visibility turn.** The previous bridge used `_turn + 1`, assuming selection ran before
   `render()`. Host source proves the opposite: `pre_llm_call` (which calls tracer `render()`) runs in
   `turn_context.py` **before** request assembly (`turn_request_assembly.py::assemble_api_request` →
   `select_context`). At stub-emit time `_turn` is already the current turn. Tagging `_turn + 1` put
   both the eviction and the stub render one turn late.

## 2. The fix

- `Tracer.emit_stub_render(ref, turn)`: sealed-v0 `page.render` with `mode: "stub"`, same declared
  `PageId`, same visibility turn, `ts` last via `_push`. Pure event emission — the page was already
  revealed at the pre-LLM boundary; this records the mode the selected request actually sent.
- Bridge observer now emits, per unique matched ref, **`page.evict` then `page.render(mode=stub)`**
  at `_visible = tracer._turn` (current turn). `stubbedRefs` entries carry `{ref, stubText, turn}`.
- `tools/coverage_check.py`: version-gated (`>= 0.13.33`) rule now requires **both** a matching
  `page.evict` (byte-identical `stubText`) **and** a `page.render(mode=stub)` at that same turn for
  every stubbed ref. Missing or wrong-turn render fails. Old/off fixtures exempt.

## 3. Tests + red-before

6 `PageEvictStubTests` (one added): stub rows byte-identical; drop mode zero; evict byte-identity +
`ts` last; refusal; **evict→stub-render pair at the same current turn**; host-order visibility law.
Suite **247 passed, 15 subtests**.

Red-before: suppressing `emit_stub_render`'s `_push` makes
`test_stub_mode_emits_evict_then_stub_render_at_same_turn` fail (rc=1); restored → 6 pass. (A first
mutation targeted the bridge instead of the emitter and did not exercise the unit path — discarded,
not counted as proof.) Checker: missing render and wrong-turn render both print violations; matching
turn is clean; old version exempt.

## 4. Verification

- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 247+8+66).
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.33**, installed load check OK.
- v0.1 validator accepts `page.render(mode=stub)` with `ts` last (rc=0). Sealed v0/spec/rust untouched.
- Kit ALL PASS; hygiene OK; CJK/secret/home sweeps clean at close.

## 5. Consequence / owed

The research paper may now use the **full design wording**: stub mode emits
`page.render(mode=stub)` + `page.evict` per dropped result; drop mode emits neither. Paper wording is
research lane's file — not touched here. Operator restart owed; future stub-arm preflight cites
**0.13.33**. Review lane verifies. This does not retroactively fill the accepted Part C attestation
gap. No cost/paging/model-quality/determinism or `stubText`-redaction claim.
