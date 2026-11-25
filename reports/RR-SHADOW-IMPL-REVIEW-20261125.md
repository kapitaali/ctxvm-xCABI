# RR-SHADOW-IMPL-REVIEW-20261125 — core safety gates pass; three data-integrity gaps block acceptance

Review lane, verify-then-record. Subject: `7d58032` + `867b16e`, card `RR-SHADOW-IMPL-20261125`.
Date 2026-11-25. $0, no model call, no profile activation, no push.

## 1. Verified claims

| claim | check | result |
|---|---|---|
| version 0.13.34 repo + installed | grep `__init__.py` | both **0.13.34** |
| sync | `sync-plugin.sh --check` | repo/installed/manifest 0.13.34, load OK; gateway restart still owed |
| focused shadow tests | `pytest packages/hermes/test/test_shadow_mode.py -q` | **7 passed** |
| full Hermes suite | `pytest packages/hermes -q`, `CTXVM_*` cleared | **254 passed, 15 subtests** |
| full gate | `run-ci.sh` unpiped, `CTXVM_*` cleared | **rc=0 ALL GATES GREEN** |
| kit/hygiene | `check-handoff.sh`, `git-hygiene.sh` | ALL PASS / OK |
| one temp profile | `~/.hermes/profiles/w8-shadow` | mode 0700; `engine: compressor`, budget 24000, `shadowSelection: true`; no other profile opts in |
| privacy/permissions | code + tests | hashed page ids; directory 0700; file 0600; no body/ref/args in record |
| no-perturbation | code + tests + red-before record | control return stays `None`; live `_pages`/`_pin_order` unchanged; off/on results equal |
| per-session records | tests | disjoint session ids and per-session call indexes |
| write failure | tests | fail-open; visible `shadowWriteFailures` increment |

Gateway pid 6930 started 11:28, before the 0.13.34 files were written at 12:04–12:06. Newest real sidecars are
still 0.13.33; no shadow record exists yet. The implementation is synced but **not live**.

## 2. Blocking finding 1 — historical PageId is hashed as the latest version

`_write_shadow_record()` resolves identity tokens to a logical ref, then reads `tracer._declared[ref]`. That map
holds only the latest content hash for a ref. If the would-drop unit is an older version, the shadow record hashes
the wrong PageId.

Repro: declare `file:same.md` with content `v1` (hash `sha256:3bfc2695`), then the same ref with `v2`
(`sha256:fb04dcb6`); submit a shadow payload whose ids match the older page. The record contains
`sha256:977acee…`, which is `sha256(file:same.md|sha256:fb04dcb6)` — the latest version — not the expected
`sha256:f11c1d31…` for v1.

Impact: later-event joins by page id can attach labels to the wrong content version. This violates the spec's
exact PageId requirement.

## 3. Blocking finding 2 — control shadow planner does not reproduce demand pinning

`_emit_shadow_plan()` creates a fresh engine and initializes every local page with `demand_count: 1`. It never
replays repeated sightings from the current transcript or any persistent page/pin history. Second-demand pinning
and content-change release therefore cannot match the real keep law on control sessions.

Repro: a request containing the same `read_file("dup.md")` PageId twice plus ten unique pages under a tiny budget
produces:

```text
real ctxvm plan:  droppedCount=0, repositionedCount=1, selectionHash=sha256:24c0f4ab4c9b2a2f
control shadow:   droppedCount=0, repositionedCount=0, selectionHash=sha256:e30da4f85d377abb
```

The plans differ. The authorized `w8-shadow` profile is a control profile, so this is the primary production path,
not an edge case. The shadow corpus would not be a faithful counterfactual of the current keep law.

## 4. Blocking finding 3 — no schema validation; invalid records are writable

The spec requires every record to validate, token counts to be non-negative, `dropped_tokens <= resident_tokens`,
and hashes to be present. No shadow schema/validator exists, and `_write_shadow_record()` casts values without
checking those invariants.

Repro: call the writer with `budget_tokens=-1`, `resident_tokens=1`, `dropped_tokens=2`, and null hashes. It writes
the record successfully with all invalid values intact.

Also, `repositioned_pages` is hard-coded to `[]`; neither the real plan payload nor the control shadow payload
carries the page details needed to populate it. The field is therefore incomplete for any plan with repositioning.

Impact: the acceptance “schema gate” is not implemented; malformed data can enter the private corpus silently.

## 5. Verdict / route

**Core safety behavior is sound, but shadow mode is NOT accepted for data collection yet.** Route a Hermes
follow-up to:

1. preserve exact historical `(logicalRef, contentHash)` through the engine→observer→writer join;
2. make the control shadow planner reproduce demand/pin/reposition state from the request (or explicitly scope
   shadow to ctxvm sessions until it can);
3. add a versioned shadow schema/validator and enforce non-negative counts, `dropped <= resident`, required hashes,
   and exact record shape; populate `repositioned_pages` or remove it by a recorded spec erratum.

Mirror remains default and no real profile was activated. No causal, cost, paging-quality, model-quality,
determinism, availability, or redaction claim. Gateway restart remains owed; no live shadow data exists.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261125.md`.
