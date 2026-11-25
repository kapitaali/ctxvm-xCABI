# RR-DSHSTUB-PASSIVE-20261124 — external tracer stub API and DSH checker gate

Date: 2026-11-24. Lane: dsh/ctxvm. Workspace-staged; no checkout write, commit,
push, publish, release, gateway restart, active paging, or model call.

## Changes

### `@ctxvm/node` 0.1.1

- Adds `StubInput` and `Tracer.stub()`.
- Emits one atomic `page.evict` + `page.render(mode="stub")` pair for the exact
  original PageId and visibility turn; `stubText` is byte-preserved and `ts` is
  last.
- Accepts optional `contentHash` for historical PageId selection; ref-only calls
  select the first declared PageId.
- Retires a superseded same-turn full render before the stub pair so Rust's final
  mode schedule does not contradict an earlier fact.
- Tracks effective full/stub schedules and derives per-turn resident/evicted
  token facts; mirror-only output is unchanged.
- Version/package-lock bumped to 0.1.1; public `publishConfig` added.

### DSH adapter

Canonical `packages/deepseek` copy is synchronized with the open-dsh staging
copy: durable replacement provenance, exact stub mapping, page-table v3,
per-session state, full W17 coverage sidecar, exact external dependency 0.1.1.

### Coverage checker

- Adds a DSH-only `plugin.adapter == "dsh"` branch gated by
  `plugin.capabilities.stubWire >= 1`.
- Requires exact declared PageId, eviction turn/text, matching stub-render turn,
  integer counts, and one event pair per sidecar record (duplicates cannot reuse
  a pair).
- Keeps legacy DSH without the capability and off/empty captures exempt.
- Leaves Hermes version gates unchanged and explicitly excludes DSH from them.

### Gates

- `tools/ci-deepseek.sh` now builds/packs `@ctxvm/node` and installs the tarball as
  an external package; it no longer creates a repo-relative source symlink. It
  also runs the new checker unittest suite and requires 22 adapter passes.
- `tools/check-node-build.sh` exercises `stub()` in source/dist parity.

## Verification

```
node tracer: 30/30 tests; build rc=0; source/dist parity OK
adapter: 22/22 pass + 1 named replay skip; tsc rc=0
checker: 13/13 synthetic DSH tests
committed Hermes W8B sidecars: 4/4 consistent
ci-deepseek.sh: rc=0
stub trace: v0.1 validator OK; checker OK; Rust replay divergences=[] violations=[]
mirror trace: v0.1 validator OK; checker OK; Rust replay divergences=[] violations=[]
```

## Owner sequence

Publish `@ctxvm/node@0.1.1` first, then copy both staging manifests and run the
listed gates. Active DSH mode remains a separate owner-approved checkpoint.

## Claim ceiling

Passive stub wire and checker parity only. No active paging, cost, quality,
determinism, availability, or redaction claim.

## Packaging correction (2026-11-25)

The owner ruled that `@ctxvm/node@0.1.1` stays in the ctxvm repository and is not published to npm. The canonical adapter now uses `file:../node`; the open-dsh copy points to the same ctxvm package with a repository-relative path. The earlier publish/install sequence in this report is superseded; see `RR-W22-LOCAL-NODE-20261125.md`.
