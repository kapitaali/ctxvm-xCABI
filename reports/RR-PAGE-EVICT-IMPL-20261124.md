# RR-PAGE-EVICT-IMPL-20261124 — page.evict emitted at the stub seam (hermes lane, 0.13.32)

Lane: hermes. Work order: `design/PAGE-EVICT-HERMES-PROMPT.md`, design of record
`design/page-evict-stub-mode.md`. Scope: emitter + checker only. **Research owns the paper wording,
review owns the Rust replay cross-check and conformance vectors — not touched here.** Version
**0.13.31 → 0.13.32**, synced; gateway restart owed to operator. No arm, model call, spend, default-on,
D17 action, re-score of Part B, or push.

## 1. What landed

- **One assembly, one object.** `select_context` now computes `assembled` **before** the plan
  observer and reuses it at all four sites (before: four separate `_assemble` calls). The observer
  fires with the stub rows from that exact assembly.
- **Stub seam carries the text.** `_stub_message()` builds the stub; `_emit_transcript_slot()`
  records `{ids, stubText}` in `self._stub_rows` from the **same stub dict inserted into the request**;
  the plan payload carries `stubRows` only in recoverable mode. No reformat, no re-derivation from `_plan`.
- **Tracer emitter** `Tracer.emit_evict(ref, stub_text, turn)`: sealed-v0 `page.evict` with
  `page = (logicalRef, contentHash)` from the tracer's declared page, `stubText` byte-identical,
  `ts` last via `_push`. Refuses unknown refs / non-string text; fail-open (never raises into a turn).
- **Bridge observer** emits via `refs_for_identity_tokens([ids])` (the existing identity join), only
  when exactly one ref matches, at `turn = tracer._turn + 1` — the stub is sent in the request *after*
  `render()` increments, so RFC-0 `page.evict@t → visible@t` holds. Per-session state
  (`stubbed_refs_by_session`), never process-global.
- **Coverage sidecar** stamps `plugin.stubbedRefs` (ref + exact text) per session; drop mode stamps `[]`.
- **Checker** `tools/coverage_check.py`: version-gated (`>= 0.13.32`) + presence-gated rule — a
  recoverable sidecar with `evictedTokens > 0` must have a `page.evict` row for each stubbed ref with
  byte-identical `stubText`. Old/off fixtures exempt. The earlier `stubCount > 0` rule stays.

## 2. Tests (5 new, suite 246) + red-before

Laws: stub rows byte-identical to the request body; drop mode emits zero rows; `emit_evict` byte-
identity + `ts` last; unknown ref / non-string refusal; visibility turn = next after completed turn.
All 5 pass; suite **246 passed, 15 subtests**. Checker rule proven independently: mismatched
`stubText` → violation line, matching → clean, old version → exempt (rc=1 in the minimal fixture came
from unrelated fields; only rule-specific lines cited).

## 3. Verification

- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 246+8+66).
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.32**, installed load check OK.
- **Sealed v0 untouched**: `git diff --stat -- spec/ rust/` empty; v0 conformance vectors pass
  unchanged. A standalone `page.evict` with `ts` is v0.1-valid (`validate_schema_v0_1.py` rc=0) and
  v0-invalid — expected: live traces carry `ts`; sealed v0 vectors do not. No schema change.
- Kit ALL PASS; hygiene OK; CJK/secret/home sweeps clean at close.

## 4. Not claimed / owed

- Does **not** retroactively fill the Part C re-read/attestation gap (`RR-PARTC-ARM-RESULT`).
- No cost-saving, paging-quality, model-quality, or determinism claim. `stubText` is a raw-text
  channel; G4 models only `logicalRef` — no redaction claim.
- **Owner/other lanes:** gateway restart; paper A3/A4 wording (research); Rust replay cross-check +
  conformance vector (review); review verification of this card. Future stub-arm preflight cites 0.13.32.
