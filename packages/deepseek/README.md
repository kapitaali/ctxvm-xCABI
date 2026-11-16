# @ctxvm/dsh — ctxvm adapter for DeepSeek Harness

W22 Phase 1: **mirror-mode xCABI v0 trace capture** from a live dsh session.

The plugin is a Cordis bundle that:

1. Listens to `session/event` for every committed dsh session event.
2. Maintains one `@ctxvm/node` tracer per session (keyed by `sessionId`).
3. Maps dsh events to xCABI verbs (see `src/event-map.ts`).
4. Registers a session projection for the page table (`src/page-table.ts`).
5. Writes the trace to `<traceDir>/<sessionId>-<ts>.jsonl` on session end.

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

Prerequisite: build the tracer first, because Node refuses TypeScript under
`node_modules` and `@ctxvm/node` exports point at `dist/`:

```
cd packages/node && npm run build
```

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
```

## Validate / replay a captured trace

```
venvs/odps/bin/python spec/rfc-0/validate_schema.py <trace.jsonl>   # exit 0 = pass
cargo run --release -p ctxvm-conformance --bin replay <trace.jsonl>  # exit 0 = no divergence
```

Note: the current `@ctxvm/node` build emits RFC-0.1 additive fields
(`schemaVersion: "0.1"`, `ts`, …); if the strict v0 schema rejects them, use
`spec/rfc-0.1/validate_schema_v0_1.py` (see open questions in the W22 doc).

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
  src/types.ts         # shared types
  test/                # node --test unit tests
```
