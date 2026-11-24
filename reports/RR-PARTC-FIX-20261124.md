# RR-PARTC-FIX-20261124 — bounded stub-seam fix: arguments capped/escaped, four red-before laws, per-session attestation

Lane: hermes. Authority: `RR-PARTC-FIX-ROUTE-20261124` (owner forwarded `PARTC-FIX-LANE-PROMPT.md`).
Scope: reviewer checks **2, 4, 5** only. No arm, no model call, no spend, no push, no default-on,
no `page.evict` (separate owner-gated card), no re-score of Part B. Version **0.13.30 → 0.13.31**,
synced; gateway restart owed to operator.

## 1. The defect (measured before fixing)

With a hostile call in the dropped window of a synthetic transcript:
- 10k-char argument → **10,059-char stub** (no cap);
- newline+instruction argument → **101 chars of verbatim instruction text** in the stub;
- `]` in arguments → frame break; control chars passed through.

The earlier dq scan covered the literal template only — exactly the gap the reviewer predicted.
Budget (check 1) and message shape (check 3) already passed: `off` after 27,600 / 30,000;
`recoverable` after 27,717 / 30,000 with 3 stubs = 78 tokens; stub keys = `content`/`role`/
`tool_call_id`, matching the real tool-result shape.

## 2. The fix (`context_engine.py`)

- `_STUB_READ_ONLY_TOOLS` = `{read_file, search_files}` — the product's own read-only table;
  `_STUB_ARG_LIMIT = 200`.
- `_stub_arg_excerpt()`: control chars → spaces, `[`/`]` escaped, length capped with
  `...[truncated]` marker.
- `_stub_message()`: read-only tools get the bounded excerpt; **every other tool** (the MUTATING
  fail-safe class — write/execute, where arguments can carry bodies) gets **no excerpt**, just
  "see the call above". The producing call is still kept in the carrier, so the model can re-run it.

## 3. Tests + red-before (4 mutations, all red then green)

New laws: bounded/frame-safe hostile args (10k, instruction, `]`, control chars); body-carrying tool
omits arguments; per-session attestation. **Red-before**, each with its own mutation and rc:
- body leaked into stub → `test_stub_never_carries_the_page_body_or_planted_code` FAIL (rc=1);
- carrier call removed → `test_stubbed_call_stays_in_its_carrier_for_rerun` FAIL (rc=1);
- default changed to `recoverable` → `test_stub_is_off_by_default` FAIL (rc=1);
- env channel enabled → `test_ambient_env_cannot_enable_the_stub` FAIL (rc=1) — the first version of
  that test was **too weak** (checked only the default value); strengthened to assert
  `_stub_explicit is False`, then it correctly went red. No vacuous negatives.

The env test's weakness and its repair are recorded because a reviewer caught it.

## 4. Per-session attestation + checker rule

- Test captures two engines in one process (`recoverable`, `off`) and asserts each plan payload's
  `stubDropped`/`stubCount` — the engine's observer is module-global (last set wins), so plans are
  captured immediately after each selection. **This is the limit of what unit tests can prove:**
  no real sidecar with `stubDropped: recoverable` exists (accepted gap, `RR-RETRY-BLOCKED`).
- `stubCount` is **per call** in the plan payload; the sidecar's last plan is the latest call, not a
  session cumulative. Documented in the test and the checker comment.
- `tools/coverage_check.py`: version-gated (`>= 0.13.31`) and presence-gated rule — if
  `stubDropped == recoverable` and `evictedTokens > 0`, require `stubCount > 0`. Red case prints the
  violation; green/old-version/off cases do not. Minimal synthetic pair had unrelated violations, so
  only the rule-specific line is cited.

## 5. Verification

- Suite **241 passed, 15 subtests** (229 + 3 earlier + 3 new + 2 policy = 12 stub laws total).
- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 241+8+66).
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.31**, load check OK.
- `python3 -m py_compile tools/coverage_check.py` OK; checker rule red/green as above.
- kit + hygiene + sweeps at close.

## 6. Not claimed / owed

No cost saving, paging/model-quality, or determinism claim. No arm; a future stub-arm preflight must
cite **0.13.31**, not the reviewer's 0.13.30. Operator: gateway restart owed. Review lane: verify.
`page.evict` in stub mode stays a separate owner-gated card.
