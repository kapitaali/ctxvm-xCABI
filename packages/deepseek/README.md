# @ctxvm/dsh — ctxvm adapter for DeepSeek Harness

W22: **mirror-mode xCABI v0.1 trace capture** plus passive stub facts from a live dsh session.

The plugin is a Cordis bundle that:

1. Listens to `session/event` for every committed dsh session event.
2. Maintains one `@ctxvm/node` tracer per session (keyed by `sessionId`).
3. Maps dsh events to xCABI verbs (see `src/event-map.ts`).
4. Registers a session projection for the page table (`src/page-table.ts`).
5. Writes the trace and exact-byte coverage sidecar to `<traceDir>/<sessionId>-<ts>.jsonl{,.coverage.json}` on session end.
6. Maps single-node `tool/result` replacements to `page.evict` + `page.render(mode="stub")` without declaring the stub body as a page.

Mirror mode guarantees: the plugin never mutates a dsh message, tool argument,
surface node, or config; it never raises from an event handler; it writes only
to its own trace file and its own projection state; it appends nothing to the
session log (acceptance: session log identical with/without the plugin).

## Install (local path)

```
dsh plugin install /home/theb/Documents/ctxvm/packages/deepseek
# or via the agent tool: plugin_manager action=install_bundle,
# target=/home/theb/Documents/ctxvm/packages/deepseek
```

`@ctxvm/node` is an exact external dependency (`0.1.1`) containing the passive
`stub()` API. No repository-relative `file:` dependency or workspace symlink is
used. Publish/install that package before installing this adapter.

## Config

Set on the `ctxvm-tracer` row in the profile's `cordis.patch.yml`
(`$DSH_HOME/profiles/<profile>/cordis.patch.yml`):

```yaml
- id: ctxvm-tracer
  name: '@ctxvm/dsh'
  config:
    enabled: true
    traceDir: ~/.local/state/ctxvm/traces   # default; dir mode 0700, files 0600
    tokenizerId: apx4-char
    budgetTokens: 200000
    mode: mirror                 # default; stub enables active selection
    protectFirstN: 3
    protectLastN: 6
    stubDropped: off             # off = no mutation; recoverable = exact stubs
    selectionMode: fresh         # fresh | stable
    stableEvery: 4
```

Active `mode: stub` runs at `agent/pre-step`, measures the current surface through
`ctx.tokenMeter`, applies Hermes-derived system/head/tail/last-user/open-call
protection, second-demand pinning, content-change release, and newest-first
recency selection. Selected append-origin tool results are replaced through the
durable DSH surface with the exact Hermes stub template. Mirror mode never
registers the active listener. `stubDropped: off` still plans but emits no
replacement.

## Validate / replay a captured trace

```
venvs/odps/bin/python spec/rfc-0.1/validate_schema_v0_1.py <trace.jsonl>   # exit 0 = pass
cargo run --release -p ctxvm-conformance --bin replay <trace.jsonl>  # exit 0 = no divergence
python3 tools/coverage_check.py <trace.jsonl> <trace.jsonl>.coverage.json
```

Traces negotiate `schemaVersion: "0.1"` and use the v0.1 validator. Passive
stub captures also require the adapter-aware DSH coverage gate.

## Layout

```
packages/deepseek/
  package.json         # @ctxvm/dsh, dsh.bundle.patch
  cordis.patch.yml     # bundle patch inserting the ctxvm-tracer row
  src/index.ts         # Cordis plugin entry (apply)
  src/config.ts        # schemastery Config schema
  src/tracer.ts        # per-session @ctxvm/node tracer lifecycle
  src/event-map.ts     # dsh SessionEvent → xCABI tracer calls
  src/page-table.ts    # page table fold + ProjectionDefinition
  src/context-engine.ts # pure active selection/protection/stub helpers
  src/active-runtime.ts # sessionQuery + pre-step surface replacement
  src/types.ts         # shared types
  test/                # node --test unit tests
```
