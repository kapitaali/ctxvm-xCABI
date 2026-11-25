# RR-SHADOW-FIX-20261125 — shadow data-integrity blockers fixed (historical PageId, parity, schema)

Lane: hermes. Authority: review blockers in `RR-SHADOW-IMPL-REVIEW-20261125`. Version
**0.13.34 → 0.13.35**, synced; gateway restart owed to operator. No live data collection, model call,
spend, pin activation, export, default-on, D17 action, or push.

## 1. Historical PageId — exact, never latest-by-ref

- `_PageUnit` now carries `content_hash`, computed from the exact tool-result body with the tracer's
  `sha256:<8 hex>` algorithm at classification time.
- Real and shadow plan payloads carry `contentHash` on every dropped/repositioned page.
- `_write_shadow_record()` hashes `logicalRef + payload.contentHash`; it never reads
  `tracer._declared[ref]["contentHash"]` (latest version). Missing exact hash fails closed.

Regression: declare `file:same.md` v1 then v2; a shadow row for v1 hashes v1, not v2. Red-before:
restoring the latest-by-ref lookup fails the test; fixed → pass.

## 2. Control shadow-plan parity — real demand/pin/reposition replay

The control shadow clone now runs the same `_update_page_state(units)` and `_credit_demand(messages)`
passes as the live engine before `_plan`, on the short-lived clone only. This reproduces second-demand
pinning, identity release and reposition state without touching live `_pages`/`_pin_order`/request.

Regression: duplicate PageId + ten unique pages under pressure now yields the **same**
`droppedCount`, `repositionedCount` and `selectionHash` as the real ctxvm plan (repositionedCount=1).
Red-before: the old demand_count=1 initialization fails the parity test; fixed → pass.

## 3. Versioned schema validator — fail-closed before disk

- New `packages/hermes/live/shadow_schema.py`: exact record/policy/page key sets; non-negative token
  counts; positive budget; `dropped_tokens <= resident_tokens`; `floor_tokens <= resident_tokens`;
  required `sha256:` selection/prefix hashes; `sha256:<64 hex>` page ids; frozen trigger enum;
  `request_unchanged=true`; boolean `policy_applied`.
- Writer calls the validator **before opening the file**. Invalid records increment
  `shadowWriteFailures` and write nothing.
- `repositioned_pages` is now populated from the plan payload (hashed ids + tokens + kind), not
  hard-coded empty.
- Offline CLI `tools/shadow-selection-validate.py` + valid fixture; new gate step in run-ci gate 3
  and ci.yml schema job.

Regression: negative budget, dropped>resident, null hashes, extra keys and raw page ids are rejected;
missing validation fails the writer test; fixed → pass. Valid fixture validates (rc=0).

## 4. Verification

- Focused shadow tests **12 passed**; full Hermes suite **259 passed, 15 subtests**.
- Three red-before proofs (historical hash, control parity, schema suppression) each fail then restore.
- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (py 259+8+66;
  ts 30+62+46+35); new schema gate step green.
- `bash tools/sync-plugin.sh` → repo/installed/manifest all **0.13.35**, load check OK.
- Kit ALL PASS; hygiene OK; CJK/secret/home sweeps clean at close.

## 5. Limits / owed

Shadow mode remains opt-in on `w8-shadow` only; no live record exists and none may be collected until
the operator restarts to 0.13.35 and review accepts this fix. Candidate pins remain offline-only. No
causal, cost, paging-quality, model-quality, determinism, availability, or redaction claim.
