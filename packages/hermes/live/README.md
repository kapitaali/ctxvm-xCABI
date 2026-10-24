# `@ctxvm/hermes` — live wiring (T17)

Loads the tracer core (`packages/hermes/src/plugin.py`) into the **Hermes Agent plugin surface**.
Hermes plugins are Python packages with `register(ctx)`; the adapter is mirror-only
(v0 observes, never mutates).

```ts
// <hermes-home>/plugins/ctxvm-tracer/__init__.py  (adopted via `hermes plugins adopt`)
// or copy packages/hermes/live/ to ~/.hermes/plugins/ctxvm-tracer/ then:
hermes plugins enable ctxvm-tracer
```

Content capture is opt-in. Two ways to enable:

## Method 1 — Env-gating (gateway restart required)

```sh
export CTXVM_TRACE_DIR=/tmp/ctxvm-capture
export CTXVM_TRACE_NAME=my-session
export CTXVM_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
export CTXVM_PROVIDER=nvidia
export CTXVM_AGENT_ID=hermes
export CTXVM_BUDGET_TOKENS=120000

systemctl --user import-environment CTXVM_TRACE_DIR CTXVM_TRACE_NAME CTXVM_MODEL CTXVM_PROVIDER CTXVM_AGENT_ID CTXVM_BUDGET_TOKENS
hermes gateway restart   # from a separate shell outside the gateway process

hermes -z "…"   # CLI mode; plugin registers hooks, flushes traces on session end
```

## Method 2 — Slash command (no gateway restart, works from inside Hermes)

```sh
hermes -z "…"

# Inside Hermes, issue slash commands:
/ctxvm-trace start /tmp/ctxvm-capture my-session
hermes -z "Read notes/alpha.md."
/ctxvm-trace stop
```

`/ctxvm-trace start <dir> [name]` begins tracing and writes `<dir>/<name>.jsonl`
plus `<dir>/<name>.meta.json`. `/ctxvm-trace stop` flushes and stops.
`/ctxvm-trace status` shows whether tracing is active.

The slash command sets the trace dir at runtime, so no `systemctl --user
import-environment` or gateway restart is needed.

## Output

On `on_session_end` (and `on_unload`), the adapter writes:

- `<name>.jsonl` — RFC-0 trace (`@ctxvm/node`-equivalent `finish()` output)
- `<name>.meta.json` — session id, model/provider, hook counts, trace stats

Without either env-gating or the slash command, the plugin registers hooks but no
tracing occurs (mirror-only v0: never mutates messages, never evicts).

## Contract notes (Hermes Agent v0.22.5, observed)

- Hook contracts pinned from source (`hermes_cli/plugins.py` `VALID_HOOKS`, `plugins_dispatch.py`, `hooks.py` synthetic payloads, bundled `disk-cleanup` plugin). See `packages/hermes/HOOKS.md` for the full pin.
- `pre_tool_call` payload: `{tool_name, args, session_id, task_id, tool_call_id}` — matches T9 pin.
- `post_tool_call` payload: same fields plus `{status, result|error}` — `status` is `"ok"` on success, `"error"` on failure per `model_tools.py:_tool_result_observer_fields` (line 656-671); the adapter also accepts `"completed"` for demo/synthetic compatibility.
- `pre_llm_call` payload: `{session_id, user_message, conversation_history, is_first_turn, model, platform}` — `conversation_history` is scanned for `identifier_scan` faults, then `render()` marks the turn boundary.
- `on_session_start` payload: `{session_id}` only — `model`/`provider`/`agentId`/`budgetTokens`/`tokenizerId` come from `CTXVM_*` env vars.
- `on_unload` callback flushes all tracers; `on_session_end` also flushes (gateway stays up between CLI invocations).
- Plugin isolation: runs in the Hermes process (plugin host). The slash command sets
  the trace dir in-process, so `CTXVM_TRACE_DIR` need not be in the gateway env when
  using Method 2.
