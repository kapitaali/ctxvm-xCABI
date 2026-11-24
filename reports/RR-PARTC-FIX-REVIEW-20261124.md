# RR-PARTC-FIX-REVIEW-20261124 — verified: bounded stub-seam fix is sound; argument injection surface closed

Review lane, verify-then-record. Subject: `8d8286c` (fix) + `cfd174f` (PROJECT-STATE delta), card
`reports/RR-PARTC-FIX-20261124.md`. Authority: `RR-PARTC-FIX-ROUTE`. Date 2026-11-24. $0, no model call, no push.

## 1. Verified from disk

| claim | check | result |
|---|---|---|
| version bumped both places + installed | grep `__init__.py` | repo/installed **0.13.31** |
| sync | `sync-plugin.sh --check` | repo/installed/manifest 0.13.31, load check OK; gateway pid 19529 started 13:29 after files, holds build |
| arg cap/escape in code | `context_engine.py:296–307,1060–1065` | `_STUB_READ_ONLY_TOOLS={read_file,search_files}`, `_STUB_ARG_LIMIT=200`, `_stub_arg_excerpt()` strips control chars, escapes `[`/`]`, caps with `...[truncated]`; mutating tools get "see the call above" |
| suite | `pytest packages/hermes -q`, `CTXVM_*` cleared | **241 passed, 15 subtests** |
| gate | `run-ci.sh` unpiped, `CTXVM_*` cleared | **rc=0 ALL GATES GREEN** |
| checker rule | `coverage_check.py:451–459` | version-gated (`>=0.13.31`) + presence-gated: `stubDropped=recoverable` & `evictedTokens>0` → require `stubCount>0` |
| red-before laws | grep test names | 9 stub tests incl. body-leak, carrier-retention, default-off, env-channel, per-session attestation |

## 2. Decisive end-to-end probe (the reviewer's exact concern)

Built a stub argument from hostile text via the shipped `_stub_arg_excerpt()`:
- 10,050-char input (incl. newline + instruction + `]`/`[` + control char + planted code) → **214-char** excerpt;
  newline removed, control chars removed, `...[truncated]` marker present, **no planted code leaked**.
- Brackets early enough to survive truncation are escaped (`\]`, `\[`); no bare injected bracket remains after removing
  the tool's own marker. The "unescaped `]`" in a first quick read was the `[truncated]` marker, not injected text —
  corrected by a second probe with early brackets.

So check 2's injection/size defect is genuinely closed, not just tested on the template.

## 3. Per-session attestation limit — recorded

The card honestly states unit tests capture two engines in one process (observer is module-global, last wins) but
**no real sidecar with `stubDropped: recoverable` exists** (accepted gap, `RR-RETRY-BLOCKED`). So per-session
attestation is proven at the plan-payload/unit level, not by a live sidecar. I do not overstate it.

## 4. Scope / what's owed

No cost/paging/model-quality/determinism claim, no arm, no re-score of Part B, no pooling, no default-on, no D17, no
`page.evict` (separate owner-gated card). Hermes-lane implementation; I wrote none. **Owed:** operator gateway restart
(the card notes the fix is not live until then); a future stub-arm preflight must cite **0.13.31**, not the
reviewer's 0.13.30; the three reviewer data requests remain unsatisfiable (my prior review).

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
