# RR-ACTIVESTUB-20261125 — active DSH stub engine staged and verified

Date: 2026-11-25. Lane: dsh/ctxvm. Workspace-staged; no checkout write, commit,
push, publish, release, default-on activation, or gateway restart.

## Summary

The canonical `packages/deepseek` copy now contains the opt-in active context
engine alongside the previously verified passive stub wire. Mirror mode remains
the default.

## Implementation

- Config adds active mode/protection/stub/selection controls.
- Pure context engine ports Hermes hard keeps, second-demand pinning,
  content-change release, apx4 code-point budget arithmetic, fresh/stable
  recency selection, duplicate-PageId fail-closed behavior, and exact stub text.
- Runtime uses `sessionQuery.readSurface()` and message-id projection mapping,
  measures through tokenMeter, appends validated single-node tool/result
  replacements at pre-step, flushes, and fails open.
- Pre-step delegates downstream first and preserves rejection/series decisions.
- Raw tool arguments are retained for read-only stub excerpts.
- `ci-deepseek.sh` now requires 35 adapter passes and still installs the tracer as
  an external tarball.

## Verification

- Adapter: **35 passed**, 1 named replay skip; typecheck rc=0.
- `ci-deepseek.sh`: rc=0.
- Local forced-pressure mock: exact request stub, 8-event trace, live projection
  stub, schema/checker green, Rust replay zero divergences/violations.
- Real Nous `meituan/longcat-2.5:free`: rc=0, 15-event trace, two active stub
  pairs, schema/checker green, Rust replay zero divergences (one expected
  identifier-scan fault).

Evidence:
- `stub-live-harness/active-summary.json`
- `stub-live-harness/remote-active-summary.json`

## Limits

No pinned-block reordering; off mode plans without mutation; pre-step lacks the
new system prompt/tool schemas; stable mode is incremental; stub cost is not
reserved (Hermes parity). No cost/quality/determinism/availability/redaction
claim.

## Owner sequence

Publish/install `@ctxvm/node@0.1.1` if not already available, copy both manifests,
run the gates, then review before enabling active mode in a real profile.
