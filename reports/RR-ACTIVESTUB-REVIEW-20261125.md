# RR-ACTIVESTUB-REVIEW-20261125 — verified: opt-in DSH active stub mode is sound; mirror remains default

Review lane, verify-then-record. Subject: DSH handoff 36, staged active implementation, local forced-pressure
receipt, and real Nous receipt. Date 2026-11-25. No real profile activation, publish, or push.

## 1. Landing / copy

Dry-ran both manifests (21 open-dsh files, 31 ctxvm files), then copied every manifest entry except the
append-only `reports/LOG.md` files. Only the missing active ledger row was appended to each LOG; existing rows
were preserved. Adapter copies in ctxvm and open-dsh are byte-identical across all 19 package files.

All copied changes remain **unstaged** in both repos.

## 2. Default-off / mirror safety verified

- `config.ts`: `mode` defaults to **`mirror`**; `stubDropped` defaults to **`off`**; `enabled` remains false by
  default.
- `index.ts`: the `agent/pre-step` active listener is registered only when `config.mode === 'stub'`.
- Mirror mode still performs passive tracing/projection only; the earlier live mirror harness remains green.
- No real DSH profile was changed or enabled. The existing DSH web process was not restarted.

## 3. Code review

Verified the active path against the design:

- Hermes-derived hard keeps: system, head, tail, last user, open tool-call floor.
- Second-demand pinning and content-hash release.
- Fresh/stable recency selection; duplicate current PageIds fail closed.
- Code-point `apx4` estimate with Hermes message overhead.
- Exact stub template; read-only argument excerpt is bounded/escaped; mutating tools use `see the call above`.
- `sessionQuery.readSurface()` freshness check against `session.seq`; message-id projection mapping.
- Pre-step delegates downstream first, preserves reject/abort decisions, checks cancellation before and during
  replacement, and fails open with bounded diagnostics.
- Replacements are durable single-node `tool/result` events; flush is attempted after append.
- Per-SessionId active state; mirror mode never creates it.

No defect was found in the reviewed path. The deliberate parity limits are recorded in handoff 36 and remain
claim ceilings, not hidden assumptions.

## 4. Verification

| check | result |
|---|---|
| ctxvm adapter suite | **35 passed, 0 failed, 1 named skip** |
| ctxvm `ci-deepseek.sh` | **rc=0**, minimum 35 passes |
| ctxvm full `run-ci.sh` | **rc=0 ALL GATES GREEN** |
| open-dsh adapter suite | **35 passed, 0 failed, 1 named skip** |
| open-dsh typecheck | **rc=0** after temporary workspace peer links; links removed afterward |
| local active harness against **repo copies** | **rc=0**: exact request stub bytes, 8 events, 1 declare/1 evict/1 stub render, projection v3 stub, recoverable sidecar, schema/checker pass, replay `divergences=[]`, `violations=[]` |
| real Nous artifact re-check | 15 events, 2 eviction/stub pairs, `stubCount=2`, schema/checker pass, replay `divergences=[]`, one expected identifier-scan `faultOfResidentPage` |

The first open-dsh typecheck attempt failed only because this checkout's `packages/deepseek/node_modules/@deepseek-ai`
peer links were absent. Adding temporary links to the existing workspace packages made it pass; no source or
manifest change was needed, and the links were removed.

## 5. Claim ceiling / owed

- Active mode is opt-in; mirror remains default. No real profile has been switched to `mode: stub`.
- No cost-saving, paging-quality, model-quality, determinism, availability, or `stubText`-redaction claim.
- Documented limits remain: no pinned-block reordering; `stubDropped: off` plans without replacement; pre-step
  lacks newly assembled system/tool-schema bytes; stable mode is incremental; stub-text token cost is not
  reserved; duplicate PageIds fail closed.
- No publish, registry action, remote model call by review, or push. The real-provider receipt was revalidated
  from disk, not rerun.

## 6. Applied

This card, an append-only LOG row (four pipes), and `reports/RR-DAY-20261125.md`. Copied implementation and
review records are unstaged pending owner commit.
