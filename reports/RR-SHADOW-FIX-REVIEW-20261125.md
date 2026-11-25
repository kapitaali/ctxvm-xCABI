# RR-SHADOW-FIX-REVIEW-20261125 — accepted: all three shadow data-integrity blockers are fixed

Review lane, verify-then-record. Subject: `1454007` + `024156b`, card `RR-SHADOW-FIX-20261125`.
Date 2026-11-25. $0, no model call, no profile activation, no push.

## 1. Independent re-probe of the three blockers

| blocker from `RR-SHADOW-IMPL-REVIEW` | independent probe | result |
|---|---|---|
| historical PageId used latest-by-ref hash | declare `file:same.md` v1 (`sha256:3bfc2695`) then v2 (`sha256:fb04dcb6`); write a v1 shadow row with exact `contentHash` | record hashes **v1**, expected `sha256:f11c1d31…` — **fixed** |
| control shadow planner missed demand/pin/reposition parity | duplicate PageId + ten unique pages under pressure; compare real ctxvm plan with control shadow | both now `droppedCount=0`, `repositionedCount=1`, `selectionHash=sha256:24c0f4ab4c9b2a2f` — **fixed** |
| no schema validation; invalid records writable | writer payload with `budget=-1`, `resident=1`, `dropped=2`, null hashes | no file written; `shadowWriteFailures` incremented — **fixed** |

`repositioned_pages` is now populated from exact plan payload entries and hashed with the same PageId scheme.

## 2. Code review

- `_PageUnit` carries an exact tracer-compatible `content_hash` computed from the tool-result body.
- Real and shadow plan payloads carry `contentHash` for dropped and repositioned pages.
- Writer hashes `logicalRef + payload.contentHash`; it no longer derives identity from the latest ref entry.
- Control shadow clone runs `_update_page_state()` and `_credit_demand()` on the short-lived clone before planning;
  live `_pages`, `_pin_order`, demand state, and request remain untouched.
- `shadow_schema.py` enforces exact key sets, non-negative counts, positive budget, `dropped <= resident`,
  `floor <= resident`, required hashes, page-id shape, trigger enum, `request_unchanged=true`, and boolean
  `policy_applied`.
- Writer validates before opening the file; invalid data is fail-closed and visible.
- Offline validator and valid fixture are wired into CI.

No new blocking defect was found in the authorized `w8-shadow` path.

## 3. Verification

| check | result |
|---|---|
| focused shadow tests | **12 passed** |
| full Hermes suite | **259 passed, 15 subtests** |
| offline shadow validator | **OK (1 record)** |
| full `run-ci.sh` | **rc=0 ALL GATES GREEN** |
| sync | repo/installed/manifest **0.13.35**, load OK |
| kit/hygiene | ALL PASS / OK |

Gateway pid 6930 started 11:28, before the 0.13.35 files were written at 13:55–14:04. Newest real sidecars are
still 0.13.33; no shadow record exists. The fix is synced but **not live**; operator restart remains owed.

## 4. Verdict / scope

**Accepted for shadow data collection after the operator restarts to 0.13.35, on `w8-shadow` only.**

- Mirror remains default; no other profile opts in.
- Candidate pins remain offline-only; any live stub-arm use needs a separate owner ruling.
- The proven control parity path is the authorized **fresh** profile. Stable control-profile parity is not claimed.
- No causal-importance, cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim.
  Later reuse is a proxy; `never_observed` is right-censored, not safe.
- No publish, registry action, model call, spend, profile activation, or push.

## 5. Applied

This card, an append-only LOG row (four pipes), a day-file section, and a one-line PROJECT-STATE verification
update.
