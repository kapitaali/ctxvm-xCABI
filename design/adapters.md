# T7 — Harness adapter survey: OpenCode + Vercel AI SDK

**Status:** design only (v0 mirror mode per `03`/`design/mcp-shim.md`) · **Pinned commits:**
OpenCode `anomalyco/opencode` branch `dev` @ [`e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b`](https://github.com/anomalyco/opencode/commit/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b) (v2.1.3) ·
Vercel AI SDK `vercel/ai` branch `main` @ [`36e4ce7c7f4c2a51676167634adb8c4eb3b18e77`](https://github.com/vercel/ai/commit/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77).

Both adapters implement the **`mcp-shim.md` recording contract verbatim** (§2 identity
minting, §3 Pichay matching (arXiv 2603.09023), §4 recording matrix) through read-only hooks — neither
touches protocol code, messages, or tool arguments. Shared helpers (canonicalArgs,
sha256, token counting) live in `@ctxvm/node` (library, not counted as glue).

Common assumptions carried from T6: `vm.page_raw {tool, input, content}` mints
`logicalRef = tool:<name>(<canonicalArgs>)`, declares, and records renders;
`vm.observe_recall` is the `tool_recall` fault channel; `vm.render` emits turn facts;
mirror mode never mutates anything it receives.

---

## Adapter A — OpenCode (plugin, native hook domains)

OpenCode loads JS plugins whose hooks settle in the registry of
[`packages/core/src/plugin/hooks.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/core/src/plugin/hooks.ts)
— domains `aisdk / session / permission / shell / tool`; **only `tool.execute.before`
may fail** (`Tool.Error`); every other hook is a mirror by construction. Plugin
activation machinery: [`packages/core/src/plugin.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/core/src/plugin.ts)
(host: `packages/core/src/plugin/host.ts`).

### Exact hook points (file/function at pinned commit)

| xCABI | Hook | Trigger site | Payload |
|---|---|---|---|
| `vm.page` | `tool.execute.after` | [`packages/core/src/tool.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/core/src/tool.ts) `executeTool` (`Effect.fn("Tool.execute")`, lines ~110–149): on success triggers `{ status:"completed", result:{ output?, content, metadata? } }` | type [`packages/plugin/src/effect/tool.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/plugin/src/effect/tool.ts) `ToolHooks["execute.after"]` (`tool, sessionID, agent, messageID, id: Tool.CallID, input, status, result/error`) |
| `vm.render` | `session.context` | [`packages/core/src/session/model-request.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/core/src/session/model-request.ts) `agentHook` (lines 399–402) wired at Service `primary` (line 404): `prepare("primary", …) → hooks.trigger("session","context",{ ...draft, agent, tools })` | [`packages/plugin/src/effect/session.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/plugin/src/effect/session.ts) `SessionContext extends SessionRequest` (system, **mutable `messages`**, options, tools, agent) |
| observe: recall (`tool_recall`) | `tool.execute.before` | `packages/core/src/tool.ts` `beforeExecute` (lines ~101–113) | `ToolHooks["execute.before"]` (`tool, …, id, input` — input is mutable; mirrors read only) |
| observe: scan (`identifier_scan`) | no message-text hook exists in v2.1.x — verified: `Domain` has none, and [`packages/schema/src/plugin.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/schema/src/plugin.ts) exports only the `plugin.updated` lifecycle event | fallback: [`packages/plugin/src/effect/aisdk.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/plugin/src/effect/aisdk.ts) `aisdk.language` hook (receives `{ model, sdk, options }`, may return a `LanguageModelV3` replacement or `undefined`) | return a pass-through `LanguageModelV3` whose stream taps text deltas → `vm.scan_text` (mirror-identical stream) |

Two timing facts confirmed in the source:

- **One `session.context` fire = one model request = one xCABI turn.** The runner's
  primary loop is [`packages/core/src/session/runner/llm.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/core/src/session/runner/llm.ts)
  (`drain → advanceToStep → runStep`, `context.request.primary(...)` at line 228) and the
  step loop is [`packages/core/src/session/runner/step.ts`](https://github.com/anomalyco/opencode/blob/e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b/packages/core/src/session/runner/step.ts)
  (`attempt()` ingests `tool-call` events → `executeTool` → `toolOutput.truncate` →
  `publisher.toolExecution` at line 128; `SessionEvent.Step.Ended` at line 251).
- **No kind-filtering needed:** compaction/generate/title prepares trigger the separate
  hooks `session.compaction` / `session.generate` / `session.title` (`model-request.ts`
  lines 405–407) — `session.context` is primary-only *by construction*.

### What `vm.page()` wraps

`tool.execute.after` with `status === "completed"`: the page body is `result.content`
(what OpenCode will feed the transcript; `output` is structured side-data, metadata is
`call.meta` material per `design/mcp-shim.md` §6). `status === "error"` → **no page**
(T6 §2). Identity minting per T6 §2: `logicalRef = tool:<server?>.<tool>(<canonical(input)>)`,
`contentHash = sha256(serialized result)` — the repeat-call rows of T6 §4 (evicted →
fault-in; resident → `FaultOfResidentPage` ledger row; new hash → new page) all fall out
of matcher state keyed on `(sessionID, logicalRef)`.

### What `vm.observe()` needs

- **`tool_recall`**: `tool.execute.before` fires pre-execution with the *full canonical
  input* — the Pichay key is exactly `(tool, canonical(input))`; no history re-walk.
- **`identifier_scan`**: no direct text hook (table above). Primary choice: the
  `aisdk.language` pass-through tap (captures text deltas per model call → scan attributed
  to the correct turn). Fallback (zero extra machinery): scan the **incoming message
  history** at each `session.context` fire for assistant texts, with the T3 touch-proxy
  dedupe (one fault per page per source) absorbing the one-turn lag it introduces.

### Test strategy

1. **Replay/conformance:** capture one live OpenCode session's hook payloads as fixtures
   (recordable — all hooks are plain JSON-in / JSON-out), feed the generated xCABI events
   to `spec/rfc-0/validate_schema.py` (108-check baseline) and the divergence re-player.
2. **Glue units:** `canonicalArgs` truncation + hashing, identity minting, and the
   `status:"error"`/`isError` matrix rows against recorded payload fixtures from the
   pinned commit (payload types are the contract — they *are* the fixture schema).
3. **Live:** MCP echo/demo server + deliberately repeated calls; assert ledger contains
   exactly one `FaultOfResidentPage` row per repeated resident call and zero mis-scored
   fresh fetches.

### Risks

1. **Post-hook normalization/truncation:** core applies image normalization *after* the
   hook (`normalizeImages(normalizeContent(...))` in `tool.ts`, immediately post-trigger)
   and the step loop applies `toolOutput.truncate(outcome)` (`step.ts`) — the mirrored
   content can exceed what the model finally sees for image-heavy/truncated results.
   v0: flag as approximation baseline (same posture as T3); v0.1: prefer re-deriving
   page content from the next `session.context` window (ground truth) where available.
2. **Provider-executed tools** bypass `executeTool` (step loop forks execution only for
   non-provider-executed calls) → no hook → no page. Mitigation: render-window
   declaration as in (1); tracked as known gap until verified.
3. **Subagent/multi-session:** hooks carry `sessionID` (both domains, verified) — vm
   state (turn counter, pages, matcher) must key per session or a shared session pool
   will cross-contaminate matches.
4. **Built-in compaction** (`packages/core/src/session/compaction.ts`, ~44 kB): the
   compaction flow is non-primary, so `session.context` stays clean, but post-compaction
   transcripts drop pages wholesale — conflicts with the RFC-0 slot-stability invariant.
   v0: record compaction-output pages as `kind:"summary"`; stable mapping of removed
   pages to evict/stub cycles is deferred to RFC-1 (not invented here).
5. **`aisdk.language` tap is the only mutable-object surface** (returns a replacement
   model object). It is optional-return, so shipping the adapter with identifier_scan
   OFF keeps every surface read-only; the tap is an explicit enablement.
6. **API drift:** hook names/payloads are typed in `@opencode/plugin/effect/*` — anchor
   the adapter's TS types to those packages (source-of-truth, not our copies).

### Glue sketch (~45 LoC; helpers live in `@ctxvm/node`)

```ts
// opencode-ctxvm-plugin.ts — register-only; mirrors; no Tool.Error raised
import { trace } from "@ctxvm/node"
export const CtxvmPlugin = (hooks: PluginRegistry) => {
  const vm = trace({ agent: "opencode" })                     // mirror mode (mcp-shim.md §5)
  hooks.register("session", "context", ({ sessionID, agent, messages }) =>   // primary only
    void vm.render({ session: sessionID, agent, out: messages }))
  hooks.register("tool", "execute.before", ({ tool, input, sessionID }) =>   // Pichay key
    void vm.observe_recall({ session: sessionID, tool, input }))
  hooks.register("tool", "execute.after", ({ tool, input, status, result, sessionID }) => {
    if (status === "completed")                               // errors are not pages (T6 §2)
      vm.page_raw({ session: sessionID, tool, input, content: result.content })
  })
  hooks.register("aisdk", "language", ({ language }) =>
    language && withScanTap(language, vm))                    // identifier_scan enablement (risk 5)
}
```

---

## Adapter B — Vercel AI SDK (middleware + fullStream tap)

`streamText` apps see everything through `result.fullStream` (`TextStreamPart` union,
defined in
[`packages/ai/src/generate-text/stream-text-result.ts`](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/generate-text/stream-text-result.ts):
`text-delta` L448, `reasoning-delta` L480, `tool-call` L533 (`& TypedToolCall`),
`tool-result` L537 (`& TypedToolResult`), `start-step` L555, `finish-step` L561; the
step loop lives in
[`packages/ai/src/generate-text/stream-text.ts`](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/generate-text/stream-text.ts)).
The sanctioned model-level injection point is language-model middleware:
[`packages/ai/src/middleware/wrap-language-model.ts`](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/middleware/wrap-language-model.ts)
(`transformParams` at L69–70, `wrapStream` at L103–104).

### Exact hook points (file/function at pinned commit)

| xCABI | Hook | Trigger site | Notes |
|---|---|---|---|
| `vm.render` | middleware `transformParams` | `wrap-language-model.ts` L69–70 (`await transformParams({ params, type, model })`) | `params.prompt` is the **exact outbound request** per model call; final call params assembled in [`packages/ai/src/generate-text/stream-language-model-call.ts`](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/generate-text/stream-language-model-call.ts); one fire = one xCABI turn |
| `vm.page` | fullStream `tool-result` part | results are produced inside the generate-text layer: [`packages/ai/src/generate-text/execute-tools-from-stream.ts`](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/generate-text/execute-tools-from-stream.ts) (`executeToolsFromStream`, `transform` at L97) + [`execute-tool-call.ts`](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/generate-text/execute-tool-call.ts) (`executeToolCall`) | body = part.output (`TypedToolResult`); `tool-error` / `tool-output-denied` parts → **no pages** (matches T6 `isError` rule) |
| observe: recall (`tool_recall`) | fullStream `tool-call` part | `stream-text-result.ts` L533 (`toolName` + final aggregated `input`; streamed input chunks arrive earlier as language-layer deltas) | Pichay key = `(toolName, canonical(input))` per T6 §3 |
| observe: scan (`identifier_scan`) | fullStream `text-delta` parts, scanned at `finish-step` (L561) | boundaries `start-step`/`finish-step` L555/L561 | no extra machinery — the tap already owns the stream |

Per-step folding into the next step's prompt happens in
[to-response-messages.ts](https://github.com/vercel/ai/blob/36e4ce7c7f4c2a51676167634adb8c4eb3b18e77/packages/ai/src/generate-text/to-response-messages.ts)
(imported by `stream-text.ts` as `import { toResponseMessages } from './to-response-messages'`)
— it carries tool results into the *next* step's `transformParams` view, so the render
anchor sees each step's full outbound window, matching the one-request-per-turn model
exactly.

### What `vm.page()` wraps / what `vm.observe()` needs

Same contract as Adapter A (T6 §2–§4), fed from different streams: the tap consumes the
stitched `fullStream` (single ordered view over all steps —
`stream-text.ts` uses `createStitchableStream` internally), so page/observe ordering is
wire-order-safe. `tool-call` (recall) always precedes its `tool-result` (page) in stream
order, so matcher state sees the missing-page case *before* the fresh declaration — the
T6 recording matrix applies without extra buffering.

### Test strategy

1. **Replay:** drive `streamText` with the SDK's mock language model (deterministic
   streams with `tool-call` + result + `finish-step` parts, a pattern already used
   throughout the SDK's own test suites); record the resulting fullStream orderings as
   fixtures; run the xCABI validator (`validate_schema.py`) on generated events.
2. **Glue units:** middleware `transformParams` (assert params unchanged — mirror),
   part-mapping switch, `tool-error`/denied exclusion, per-step text scan attribution.
3. **Live:** MCP echo server via the `@ai-sdk/mcp` client (first-party MCP package
   exists upstream) + repeated identical calls → same ledger assertions as Adapter A.

### Risks

1. **Two-layer correlation:** render fires inside middleware (per model call), pages/
   observable parts arrive on the app-level tap (per step) — the adapter increments one
   turn counter per `transformParams` + `finish-step` and *asserts the counts agree*;
   divergence ⇒ warn and skip (never mis-score).
2. **Stream nesting (`streamSegments`):** nested child streams (foreach/continue with
   tools of their own) replay through the same stitched iterator — the keyed matcher
   must be per `{ session, stepIndex }` like A's per-`sessionID` keying to avoid
   cross-contamination.
3. **Approval/permission flows:** `tool-output-denied` / approval-request parts yield no
   content pages; the denied outcome never enters `params.prompt` identically to a
   result — render association of pages on approval-gated turns is approximate in v0.
4. **Provider-executed tools:** same hook gap as Adapter A risk 2 (execution delegated
   to the provider; the SDK still surfaces the `tool-result` part, which the tap *does*
   see — verify per-provider at implementation time).
5. **`transformParams` mutability temptation** (`type: "generate" | "stream"` discard
   both branches): tempting to mutate `params` for control later — mirror contract
   explicitly forbids it; middleware is recorded `read-only` in adapter TS types.

### Glue sketch (~40 LoC)

```ts
// ai-sdk-ctxvm.ts — middleware (render) + fullStream tap (page/observe); mirror only
import { trace } from "@ctxvm/node"
const vm = trace({ agent: "ai-sdk" })

export const ctxvmMiddleware = {                               // wrapLanguageModel target
  transformParams: async ({ params }) => {                     // wrap-language-model.ts:69
    vm.render({ out: params.prompt })                          // 1 fire = 1 xCABI turn
    return params                                              // unchanged (mirror)
  },
}

export async function* ctxvmTap(stream: AsyncIterable<TextStreamPart>) {
  for await (const part of stream) {
    switch (part.type) {
      case "tool-call":                                        // stream-text-result.ts:533
        vm.observe_recall({ tool: part.toolName, input: part.input }); break
      case "tool-result":                                      // :537
        vm.page_raw({ tool: part.toolName, input: part.input, content: part.output }); break
      case "text-delta":                                       // :448
        vm.scan_text(part.delta); break
      case "tool-error": case "tool-output-denied":            // not pages (T6 §2)
        break
      case "finish-step":                                      // :561
        vm.render_facts(); break                               // renders pages visible this step
    }
    yield part                                                  // pass-through, untouched
  }
}
```

---

## Adapter B ERRATUM — re-pin survey (2026-10-27, T15 B0 at `ai` 7.0.154)

No hook-point drift: all five surfaces survive into the latest stable tag.
Formal deltas vs the pinned-commit text above:

1. **Middleware typing is V4-based.** `LanguageModelMiddleware` is now
   `Omit<LanguageModelV4Middleware, 'specificationVersion'> & { specificationVersion?: string }`
   (`ai` dist/index.d.ts:158–168), with `transformParams({ type: 'generate' |
   'stream', params: LanguageModelV4CallOptions, model })`, `wrapGenerate`, and
   `wrapStream` all present (`@ai-sdk/provider` dist/index.d.ts:3536–3573).
   V3 middleware payloads remain accepted.
2. **NEW: `tool-result.preliminary?: boolean`.** Partial/promise-tool results
   stream as `preliminary` parts before the final result. The tap pages only
   `preliminary !== true` results; preliminary parts pass through unmapped.
   Recorded as T15 implementation risk 6 (glue unit pins it).
3. **Part union intact** at 7.0.154: `text-delta`, `reasoning-delta`,
   `tool-call`, `tool-result`, `tool-error`, `tool-output-denied`,
   `start-step`, `finish-step` (union shape as tabulated; line refs moved).
   Unknown part kinds pass through unmapped by contract (mirror law).
   App-layer field rename inside `text-delta`: `TextStreamPart`'s text-delta
   carries **`text`** (the provider-layer `LanguageModelV4StreamPart` keeps
   `delta`) — fixtures and the tap bind to the app-layer name.
4. **T15 pins `ai@7.0.154`** (latest stable tag per B0 ruling) — package
   devDependency, exact version.

---

## Cross-adapter notes

- **Ecosystem fact:** the AI SDK organization already ships first-party harness
  adapters in the same tree (`@ai-sdk/harness-opencode` et al. — packages listing at the
  pinned commit) — OpenCode ↔ AI SDK interconnection is upstream reality, which makes
  both adapters' coupling points *moving targets by design*: anchor TS types to the
  harnesses' own exported payload interfaces (as done above) rather than ad-hoc shapes.
- **T6 continuity:** T6 named the direct wrapper `vm.call` (shim over `callTool`).
  These adapters replace the wrapper with ingestion hookups but keep the *recording
  contract identical* — one matrix (T6 §4), two front doors. The MCP shim remains the
  right tool when no harness hooks exist.
- **Everything here is v0 mirror.** No `page`-mode control path is opened by these
  adapters; eviction policies arrive later on top of the same ledger.
