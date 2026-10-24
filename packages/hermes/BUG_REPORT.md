# BUG REPORT — ctxvm-tracer plugin

Date: 2026-10-24
Card: T17 (ctxvm UC1 v0 — Hermes plugin for within-harness session capture)
Plugin version: 0.2.0
Status: ROOT CAUSE CONFIRMED AND FIXED (code verified end-to-end); deployment restart pending

## Symptom

Trace files contained only `session.open`, `turn.render`, and `call.meta` —
**zero `page.declare` events** — while `hookStats` reported hundreds of
`post_tool_calls` and `completed` calls. `traceStats.pages` was always 0.

Representative meta from a live capture:

```json
"hookStats": {
  "session_starts": 12, "pre_tool_calls": 259, "post_tool_calls": 258,
  "completed": 235, "errored": 50, "pre_llm_calls": 47, "session_ends": 46
},
"traceStats": { "turns": 1, "pages": 0, "faults": 0, "residentTokens": 0 }
```

## Root cause (confirmed, not hypothesised)

The hook handlers increment `stats` **unconditionally**, then call the tracer
only if `_ensure_plugin()` returns a non-None plugin:

```python
def on_post_tool_call(**kwargs):
    stats["post_tool_calls"] += 1        # always counted
    vm = _ensure_plugin()                # None while tracing is disabled
    if vm is not None:
        vm.on_post_tool_call(kwargs)     # page.declare would happen here
```

So `hookStats` counts **hook fires**, not **recorded events**. A session whose
tool calls happen while `_traced()` is False records nothing, and the later
flush writes a tracer that has only seen `session.open`. That matches the
observed files exactly: full hook counters, `pages: 0`, `turns: 1`.

Two contributing conditions made this look like a tracer bug:

1. **Tracing was enabled after the work, not before.** `/ctxvm-trace start` only
   affects hooks that fire *after* it runs. It does not retroactively record
   calls already made in that process.
2. **The installed plugin was stale.** `~/.hermes/plugins/ctxvm-tracer/` held an
   older build (no `_state()`, no `pluginVersion`, module-level `_trace_dir`)
   while the repo had the fixed code. A long-running Hermes process keeps the
   module it imported at startup; on-disk edits do nothing until restart.

## Fixes applied (all verified)

### 1. `tool_name` vs `tool` — packages/hermes/src/plugin.py

Hermes passes `tool_name=function_name`. The plugin read `payload.get("tool")`,
which is `None` live. Now:

```python
tool = payload.get("tool") or payload.get("tool_name")
```

Applied in `on_pre_tool_call` and `on_post_tool_call`.

### 2. Tool result shape — `extract_page_body()`

Hermes tool results are usually plain strings. `result.get("content")` raised
`AttributeError`, silently swallowed by the fail-open dispatcher, producing zero
pages. `extract_page_body()` now handles `str`, `dict` with a `content` list,
`dict` with `text`, `list`, `None`, and other types.

### 3. Process-global state survives re-import — live/__init__.py

Hermes re-registers plugins between sessions, which creates a new module object
and resets module-level variables — losing both the trace dir and every declared
page. State now lives on `sys._ctxvm_tracer_state`:

```python
def _state():
    state = getattr(sys, "_ctxvm_tracer_state", None)
    if state is None:
        state = {...}
        setattr(sys, "_ctxvm_tracer_state", state)
    return state
```

`sys` is never reloaded, so tracing config and the tracer survive any number of
`register()` calls.

### 4. Flush-all, not flush-by-session — `_flush_traces()`

`on_session_end` no longer looks up a tracer by `session_id` (the id in the end
hook does not reliably match the id used during tool calls). It calls
`finish_all()` and writes one file per tracer.

### 5. Idempotent `finish()` — packages/hermes/src/plugin.py

`finish()` used to append `turn.render` / `call.meta` to `_events` on every
call, so multiple flushes (session end, unload, atexit) duplicated records. The
tail is now computed per call and never appended.

### 6. Diagnostic: `skipped_untraced`

New counter in `hookStats`. Non-zero together with `pages: 0` means tracing was
switched on **after** the calls — the tracer did not miss events, it did not
exist yet. This removes the main false-alarm signal.

`/ctxvm-trace status` now also reports `version`, `register_calls`, and
per-tracer `events`/`pages`:

```
ctxvm-trace: enabled=True, dir=/tmp/cap, name=x, version=0.2.0,
  register_calls=1, tracers=[ses-1:events=7,pages=3]
```

## Verification

End-to-end through the installed plugin path with Hermes-shaped payloads
(`tool_name`, `status="ok"`, plain-string `result`).

Case B — tracing enabled before any call:

```
event types: ['session.open', 'page.declare', 'page.declare', 'page.declare',
              'page.render', 'page.render', 'page.render', 'turn.render', 'call.meta']
traceStats: {'turns': 1, 'pages': 3, 'faults': 0, 'residentTokens': 45}
skipped_untraced: 0
```

Case A — two tool calls made while tracing was off, then enabled:

```
skipped_untraced: 5
traceStats: {'turns': 0, 'pages': 1, ...}   # only the call made after start
```

Case A reproduces the reported failure exactly and shows the counter naming the
cause.

CI: rust 44/44, ts 12+8, python 21/21, schema 412, hub byte-identity — all green.

## Deployment requirement

The fix is live only after Hermes reloads the plugin module. A running process
keeps the code it imported at startup, so editing files is not enough:

```bash
# from a shell OUTSIDE the running Hermes process
systemctl --user restart hermes-gateway.service   # gateway-backed sessions
# standalone `hermes` CLI process: exit and start it again
```

Cross-check that the new build is live:

```
/ctxvm-trace status      # must report version=0.2.0
```

## Operating rule

Start tracing **before** the tool calls that must be recorded:

```
/ctxvm-trace start /tmp/ctxvm-capture
... do the work ...
/ctxvm-trace stop
```

Files are written as `<session-id>.jsonl`. Hermes session ids begin with
`local-`, so a healthy capture shows `local-*.jsonl` in the directory.

## Files changed

- `packages/hermes/src/plugin.py` — `extract_page_body`, `tool_name` fallback,
  idempotent `finish()`
- `packages/hermes/live/__init__.py` — `sys`-backed state, `_active_trace_dir`,
  flush-all, `skipped_untraced`, richer `status`, guarded `atexit`
- `packages/hermes/live/plugin.yaml` — version 0.2.0
- `packages/hermes/test/test_plugin.py` — 21 tests including live-shape cases
- `~/.hermes/plugins/ctxvm-tracer/` — installed copies synced, `__pycache__` cleared
