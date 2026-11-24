# RR-STUB-RENDER-REVIEW-20261124 — verified: 0.13.33 emits the full stub wire; prior A3/A4 caveat resolved

Review lane, verify-then-record. Subject: hermes commits `046cc2b` (implementation) + `140c540` (PROJECT-STATE
delta), card `reports/RR-STUB-RENDER-20261124.md`; live record `RR-STUB-RENDER-LIVE-20261124.md` (`41669be`,
`2945bc2`). Date 2026-11-24. $0, no model call, no push.

## 1. The prior caveat is resolved

My prior explanation said the current implementation emitted `page.evict` but not `page.render(mode=stub)`, so
the paper could not use the full design wording. That was accurate for 0.13.32, but the repo has since moved:
`046cc2b` adds the companion event and corrects the visibility-turn off-by-one. **As of 0.13.33, the full stub wire
is implemented and live.** The paper may now use the design's full A3/A4 wording.

## 2. Verified from disk

| claim | check | result |
|---|---|---|
| version 0.13.32 → 0.13.33 repo + installed | grep `__init__.py` | both **0.13.33** |
| sync | `sync-plugin.sh --check` | repo/installed/manifest 0.13.33, load check OK |
| gateway holds new build | `sync-plugin.sh --check` gateway line | pid **100399**, started 17:05:46 after the files |
| suite | `pytest packages/hermes -q`, `CTXVM_*` cleared | **247 passed, 15 subtests** |
| gate | `run-ci.sh` unpiped, `CTXVM_*` cleared | **rc=0 ALL GATES GREEN** |
| real capture under new build | two coverage sidecars | both mtime 17:14:52, `pluginVersion 0.13.33`, arm control, `stubDropped off`, `stubbedRefs []` — default-off attested live |
| kit/hygiene | `check-handoff.sh`, `git-hygiene.sh` | ALL PASS / OK |

## 3. Implementation verified against the design

- **Companion emitter** `Tracer.emit_stub_render(ref, turn)` (`packages/hermes/src/plugin.py:426`): sealed-v0
  `page.render` with `mode: "stub"`, same declared `PageId`, same visibility turn, `ts` last via `_push`.
  Unknown ref → False (fail-open).
- **One pair, one turn:** bridge observer (`packages/hermes/live/__init__.py:1563–1578`) emits, per unique matched
  ref, `page.evict` then `page.render(mode=stub)` at `_visible = tracer._turn` (the current turn). The old `_turn + 1`
  was an off-by-one: host source shows `pre_llm_call` calls `render()` **before** request assembly/`select_context`,
  so `_turn` is already current when the stub enters the request.
- **Per-session sidecar:** `stubbedRefs` entries are `{ref, stubText, turn}`; drop mode writes `[]`.
- **Checker** (`tools/coverage_check.py:461–505`): version-gated (`>= 0.13.32` base rule, with the render requirement
  applied to the 0.13.33 sidecar shape) + presence-gated — recoverable sidecar with `evictedTokens > 0` requires, per
  stubbed ref, a `page.evict` with byte-identical `stubText` **and** a `page.render(mode=stub)` at the recorded
  visibility turn. Missing or wrong-turn render fails; old/off fixtures exempt.
- **Hostile-arg protection carried:** the same `_stub_arg_excerpt`-sanitized stub dict feeds both events.
- **Tests:** 6 `PageEvictStubTests`, including evict→stub-render pair at the same current turn and host-order
  visibility law; red-before mutation suppressing `emit_stub_render._push` made the new test fail (rc=1), restored
  green. A first mutation targeting the wrong path was discarded, not counted.
- **Sealed v0 untouched:** no `spec/**` change; v0.1 validator accepts `page.render(mode=stub)` with `ts`; live
  traces carry `ts`, sealed v0 vectors do not. Law 1 intact.

## 4. A3/A4 consequence — full wording now valid

The exact old paper sentences are in the tracked canonical files (not only the gitignored working copies):
- `research/white-paper/white-paper.md:265`, mirrored `research/white-paper/index.md:271` — says shipped adapters
  emit `full` only and no adapter emits `stub`.
- `research/white-paper/white-paper.md:583`, mirrored `research/white-paper/index.md:589` — says stub renders
  are not emitted, so a turn's omissions are not recorded.

With 0.13.33 those statements are stale. The honest full wording is: **stub mode emits `page.render(mode=stub)` +
`page.evict` per dropped result, same PageId and visibility turn, `stubText` byte-identical to the placeholder
actually sent; drop mode emits neither. Drop-mode omissions remain outside the trace (P12).** The paper still does
not reconstruct the request's raw bytes. This wording must land with the emitter; research owns the edit.

## 5. Limits

No live stub-mode capture exists, so the accepted Part C arm attestation/re-read gap remains unchanged. No
cost-saving, paging-quality, model-quality, determinism, or `stubText`-redaction claim. No arm, model call, spend,
default-on, D17, Part B re-score, or push. Future stub-arm preflight cites **0.13.33**.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
