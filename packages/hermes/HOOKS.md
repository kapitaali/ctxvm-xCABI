# Hermes Hook-Terrain Spike — Phase 0 Findings

**Card:** T17 (ctxvm UC1 v0 — Hermes plugin for within-harness session capture)
**Date:** 2026-10-24
**Method:** Source-level pin from Hermes Agent v0.22.5 runtime contracts (`/home/theb/.hermes/hermes-agent/`), not docs. Read `hermes_cli/plugins.py` (`VALID_HOOKS`, `PluginContext.register_hook`), `hermes_cli/plugins_dispatch.py` (hook invocation), `hermes_cli/hooks.py` (synthetic payload shapes matching real `invoke_hook()` call sites), and bundled plugin `plugins/disk-cleanup/__init__.py` (real `register(ctx)` callback signatures).

## 1. Hook domains available to a v0 plugin

| Hook | Fires when | Payload kwargs (observed) | xCABI mapping |
|------|-----------|--------------------------|---------------|
| `on_session_start` | New session created | `session_id` (str) | `session.open` (model/provider from env vars) |
| `pre_tool_call` | Before tool execution | `tool_name`, `args`, `session_id`, `task_id`, `tool_call_id` | `recall({tool, args})` — pre-execution re-call mark |
| `post_tool_call` | After tool completes | `tool_name`, `args`, `session_id`, `task_id`, `tool_call_id`, `status` ("ok"\|"error"), `result`/`error` | `page.declare` only when `status in {"ok", "completed"}` (T6 §2) |
| `pre_llm_call` | Before model request | `session_id`, `user_message`, `conversation_history`, `is_first_turn`, `model`, `platform` | Turn boundary: `scan(history)` then `render()` |
| `post_llm_call` | After model response | `session_id`, `model`, `platform` (no output text) | — |
| `transform_llm_output` | LLM output produced | returns replacement str or None | — (transform, not observe) |
| `on_session_end` | Session ends | `session_id`, `task_id`, `turn_id`, `completed`, `failed`, `interrupted`, `turn_exit_reason`, `model`, `platform` | Flush all tracers via `finish()` |
| `pre_api_request` | Before provider API call | `session_id`, `task_id`, `platform`, `model`, `provider`, `base_url`, `api_mode`, `api_call_count`, `message_count`, `tool_count`, `approx_input_tokens`, `request_char_count`, `max_tokens` | `call.meta` latency source |
| `post_api_request` | After provider API response | `session_id`, `task_id`, `platform`, `model`, `base_url`, `api_mode`, `api_call_count`, `api_duration`, `started_at`, `ended_at`, `first_chunk_at`, `finish_reason`, `message_count`, `response_model`, `usage` `{input_tokens, output_tokens}`, `context_length`, `assistant_content_chars`, `assistant_tool_call_count`, `moa_references` | `call.meta` (providerReported possible in v1) |

**Full VALID_HOOKS set** (from `plugins.py:108-157`): `pre_tool_call`, `post_tool_call`, `transform_terminal_output`, `transform_tool_result`, `transform_llm_output`, `pre_llm_call`, `post_llm_call`, `on_stream_start`, `on_stream_delta`, `on_stream_end`, `on_interim_message`, `pre_verify`, `pre_api_request`, `post_api_request`, `api_request_error`, `pre_auxiliary_call`, `post_auxiliary_call`, `transform_api_error_classification`, `on_session_start`, `on_session_end`, `on_session_finalize`, `on_session_reset`, `on_session_delete`, `on_skill_lifecycle`, `subagent_start`, `subagent_stop`, `pre_gateway_dispatch`, `post_gateway_admission`, `agent_loop_stopped`, `pre_approval_request`, `post_approval_response`, `on_human_input_request`, `on_human_input_resolved`, `on_room_member_activity`, `pre_transcription`.

Hooks run all-callbacks (run-all). `pre_tool_call` is fail-closed (timeout blocks the tool). `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end` are bounded-timeout fail-open. Unknown hook names warn but are stored.

## 2. Plugin structure contract

A Hermes plugin is a Python package directory with:
- `__init__.py` containing `register(ctx)` where `ctx` is `PluginContext`
- `plugin.yaml` with `name`, `version`, `description`, `author`, `provides_hooks`

`ctx.register_hook(hook_name, callback)` stores the callback under the hook name. Callback receives the hook's kwargs as keyword arguments (with `**_: Any` to absorb extra fields). Callbacks must never raise (fail-closed hooks block on raise; fail-open hooks skip on raise).

`ctx.register_command(name, handler, description)` registers a slash command.

## 3. Timing model (one fire = one turn, per T7/T9 fact)

```
pre_llm_call(turn=t)   → vm.scan(conversation_history) → vm.render()   [turn boundary, turn becomes t]
pre_tool_call          → vm.recall({tool, args})                       [during turn t]
post_tool_call(ok)     → vm.page({tool, args, content})               [during turn t]
pre_llm_call(turn=t+1) → vm.scan(conversation_history) → vm.render()   [turn boundary, turn becomes t+1]
```

`conversation_history` at `pre_llm_call` includes all messages up to now, including prior assistant outputs. Scanning it there catches identifiers from previous model output — equivalent to T9's `session.context` scan of `payload.messages`.

`post_tool_call` result content: `result.content` is a list of `{type, text, ...}` items; text items joined by `\n` form the page body (same as T9's `contentToPageBody`). Non-text items become `<type>` markers. Errored calls (`status not in {"ok", "completed"}`) produce no page.

**Status taxonomy errata:** `hooks.py` demo payloads use `status="completed"|"error"`, but the real Hermes taxonomy from `model_tools.py:_tool_result_observer_fields` (line 656-671) returns `status="ok"` on success and `status="error"` on failure. The adapter accepts both `{"ok", "completed"}` for demo/synthetic compatibility.

## 4. Resume-from-files: CAN a v0 plugin seed a new session's context?

**No.** There is no Hermes hook that fires before a session's context is assembled. `on_session_start` fires after session creation (payload: only `{session_id}`). No hook provides access to pre-populate the conversation history or message array before the first `pre_llm_call`. The `--resume-from snapshot` flow from UC1 §3 Step 3 is **not implementable** at the v0 plugin layer. It requires core Hermes support (a session-seeding API or a pre-session hook) and is explicitly out of scope for this card (recorded as a Phase-0 spike finding, not built).

## 5. Honest adapter mapping for Hermes

| xCABI event | Hermes hook | Source of truth |
|-------------|-------------|-----------------|
| `session.open` | `on_session_start` + env vars | `session_id` from hook; `model`/`provider`/`agentId`/`budgetTokens`/`tokenizerId` from `CTXVM_*` env (T9 convention) |
| `page.declare` | `post_tool_call` (status in {"ok", "completed"}) | `tool_name`, `args`, `result.content` text items |
| `page.fault(tool_recall)` | `pre_tool_call` | `tool_name`, `args` matched against declared pages |
| `page.fault(identifier_scan)` | `pre_llm_call` | `conversation_history` text scanned for page identity tokens |
| `turn.render` + `call.meta` | `pre_llm_call` | Turn boundary; `providerReported=false` (estimated only) |
| flush | `on_session_end` | `vm.finishAll()` writes traces |

**Env-gating:** Inert unless `CTXVM_TRACE_DIR` is set (same as T12). Without it, `setup()` returns immediately and registers no hooks.
