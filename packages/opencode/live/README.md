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

## Flush semantics for interactive sessions (v2.1.4, 2026-10-25 erratum)

The m5 self-capture (`corpus/m5`) pinned how the interactive path actually behaves:

- **Capture lives in the CLI/TUI process.** A TUI boot carries the `CTXVM_*` capture
  env; the background server (`opencode serve --service`) carries none and can never
  flush anything.
- **The flush fires only on graceful TUI exit** (SIGTERM) → plugin cleanup →
  `vm.finishAll()` → files written. There is *no plugin hot-reload*: an edit to
  `ctxvm.ts` is picked up by the next boot, not the running process.
- **A hard kill loses the slice, silently.** An unsignaled process death skips cleanup;
  nothing is written and nothing warns (a 2026-10-25 interactive quit lost its window
  exactly this way before the diagnosis). The instrumented adapter now appends every
  hook fire and every flush attempt to `hooks-witness.log` inside `CTXVM_TRACE_DIR`
  (best-effort; witness failures are swallowed by design), so the *next* failure names
  its cause. The m5 flush chain was witnessed end-to-end.
- **One `CTXVM_TRACE_NAME` accumulates.** Each flush overwrites `<name>.jsonl` —
  snapshot the file immediately after a successful flush if older eras matter.

Interactive (TUI) recipe — the exports are the same as the `opencode run` block above,
and `CTXVM_OPENCODE_VERSION` matters here too: the adapter reads it from the process env
at flush time, and the m5 boot omitted it, so its `.meta.json` honestly carries
`"opencodeVersion": null`:

```sh
export CTXVM_TRACE_DIR=/tmp/opencode/self-capture
export CTXVM_TRACE_NAME=my-session
export CTXVM_MODEL=<provider/model-id>
export CTXVM_PROVIDER=opencode
export CTXVM_AGENT_ID=ctxvm-self
export CTXVM_BUDGET_TOKENS=200000
export CTXVM_OPENCODE_VERSION="$(opencode --version)"
opencode --continue
```

End the capture by terminating the TUI first (the flush owner), then the background
service; verify the flushed file with the replay/profile binaries and
`benchmarks/metrics/metrics.py`.

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
