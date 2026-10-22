# `@ctxvm/opencode` — T9 spike

OpenCode plugin adapter wiring `@ctxvm/node` into OpenCode's native hook domains —
the T7 design "Adapter A", implemented. **Mirror-only**: every handler is read-only
(never mutates payloads, never raises `Tool.Error`); the identifier-scan channel uses
the *history fallback* rather than the mutable `aisdk.language` tap, so all surfaces
stay read-only (the tap remains an explicit enablement for later).

Payload contracts are pinned at `anomalyco/opencode` dev @
`e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b` (v2.1.3). `src/opencode-contract.ts`
holds verbatim-field local snapshots so the spike runs without an npm workspace;
replace with `@opencode/plugin` imports at dev-build wiring time.

## Dev-build wiring (one line per hook)

```ts
import { createCtxvmPlugin } from "@ctxvm/opencode"

const vm = createCtxvmPlugin({
  agentId: "opencode", model: "<model.ref>", provider: "<providerID>", budgetTokens: <window>,
})

hooks.register("session", "context", (payload) => vm.onSessionContext(payload)) // model-request.ts:399–404, primary only
hooks.register("tool", "execute.before", (payload) => vm.onToolExecuteBefore(payload))
hooks.register("tool", "execute.after", (payload) => vm.onToolExecuteAfter(payload))
// session end / process exit: vm.finishAll() → RFC-0 JSONL per session
```

## Mapping (verified)

| OpenCode hook | xCABI | Rule |
|---|---|---|
| `session.context` | `vm.render()` + scan | one fire = one turn; scan runs BEFORE render so faults attribute to the turn whose output produced the texts (RFC-0 §5); the tracer's per-page·source dedupe absorbs the window re-walk |
| `tool.execute.before` | `vm.recall()` | Pichay key `(tool, canonical(input))` (arXiv 2603.09023); only pre-existing pages mark |
| `tool.execute.after` (`status:"completed"`) | `vm.page()` | body = `result.content` texts; `status:"error"` → no page (T6 §2); `result.metadata` is call.meta material (parked) |

## Resolved RR-T7 open questions (source-verified at the pinned SHA)

1. **`toolOutput.truncate` reach-through** — CONFIRMED: the hook fires on the FULL
   result; truncation applies afterwards in the step loop
   (`executeTool → toolOutput.truncate → publisher.toolExecution`, `runner/step.ts`),
   capped at `MAX_LINES=2000` / `MAX_BYTES=50 KiB` with a
   `[showing … full output saved to …]` marker + `metadata.truncated/outputPath`.
   Consequence: page content overstates transcript bytes for oversized tool results
   (page identity is unaffected — the full-content hash is deterministic). v0 posture:
   documented approximation (same as T3); truncation-variant pages or render-window
   re-derivation are RFC-1 items.
2. **Provider-executed tools** — CONFIRMED: `step.ts` skips `executeTool` for
   `event.providerExecuted`, so no hooks fire and no pages declare for those calls.
   Documented gap; render-window declaration is the RFC-1 mitigation.

## Fixture provenance

`fixtures/hook-payloads/echo-session.json` — 13 chronological hook payloads
reconstructed from the pinned payload types (ToolHooks / SessionContext) for one
echo session: first fetch → double fetch (resident re-call) → fresh fetch (resource
changed, never scored as waste) → errored call → end. Not live-captured (a live
dev-build echo session needs an orchestrator-approved provider spend); the shapes
are the contract (`packages/plugin/src/effect/*` at the pinned SHA).

`fixtures/opencode-echo.jsonl` — the generated xCABI trace (17 events). Gates:
schema-validated (repo gate, PASS) and replay-divergence-free (`cargo replay` exit 0;
violation ledger = 2 × `FaultOfResidentPage`: the scan touch + the double fetch).

```sh
npm test    # 6 glue tests over the recorded payloads
npm run gen # regenerate fixtures/opencode-echo.jsonl
```
