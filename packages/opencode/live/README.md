# `@ctxvm/opencode` — live wiring (T12)

Loads the T9 payload→tracer mapping from the **OpenCode v2 promise-plugin surface**.
No OpenCode source patch is required: the v2 runtime exposes the same trigger sites to
external plugins.

```ts
// <session-project>/.opencode/plugins/ctxvm.ts
export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts";
```

Content capture is opt-in:

```sh
CTXVM_TRACE_DIR=/tmp/ctxvm-capture \
CTXVM_TRACE_NAME=my-session \
CTXVM_MODEL=opencode/deepseek-v4.1-flash-free \
CTXVM_PROVIDER=opencode \
CTXVM_OPENCODE_VERSION="$(opencode --version | awk '{print $2}')" \
opencode run --standalone --auto -m opencode/deepseek-v4.1-flash-free "…"
```

On plugin unload (`location.shutdown` → cleanup) the adapter writes:

- `<name>.jsonl` — RFC-0 trace (`@ctxvm/node` `finish()` output)
- `<name>.meta.json` — session id, model/provider, hook counts, trace stats

Without `CTXVM_TRACE_DIR` the plugin is a no-op.

## Contract notes (v2.1.2, observed)

- `ctx.session.hook("context", cb)` fires once per **primary** model request
  (title/compaction/generate use their own hooks) — one fire = one xCABI turn.
- `ctx.tool.hook("execute.before", cb)` payload: `{ tool, sessionID, agent, messageID,
  id, input }` — identical to the T9 pin.
- `ctx.tool.hook("execute.after", cb)` payload: the same fields plus
  `{ status: "completed", result: { content: [{ type, text }] } } | { status: "error",
  error }` — identical to the T9 pin.
- `SessionContext.model` is `{ id, providerID, variant }` on v2.1.2 (the pinned v2.1.3
  contract copy says `{ providerID, modelID }`); only the session.open metadata uses it.
- The v1 documented `export const Plugin = async (ctx) => ({ "tool.execute.before": … })`
  form is **not** accepted by the v2.1.2 loader — modules must
  `export default { id, setup }` (see `packages/core/src/plugin/module.ts` in
  `anomalyco/opencode@e965774f`).
