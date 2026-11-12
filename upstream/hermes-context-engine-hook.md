# Upstream issue draft — a plugin context engine is attached but its per-turn hook is never called

File-ready. Strip this preamble; the block below is a standalone issue. Host tree read at
`~/.hermes/hermes-agent` HEAD `3b421578` (2026-11-09); plugin under test is a third-party context
engine registered through `ctx.register_context_engine`.

---

## Summary

A plugin context engine is registered, selected at agent build, and attached to the agent
(`agent.context_compressor` is the plugin's class), the override gate that guards the hook returns
`True`, no hook failure is logged — and `select_context()` is **never entered** on the transport the
CLI one-shot path uses. The per-turn selection hook appears to be unreachable there.

## Environment

```
Hermes host   HEAD 3b421578 (2026-11-09)
transport     `hermes chat -q <prompt> --oneshot -c <title> --create-if-missing`
plugin        third-party context engine, registered via ctx.register_context_engine(engine)
config        context.engine: "ctxvm" in both the root and the profile config
safe_worker   False
```

## Reproduction

1. Register a context engine whose `select_context()` appends one line to a file and increments a
   module-global counter, and returns `None` (byte-identical request).
2. Run `hermes chat -q "…" --oneshot -c <title> --create-if-missing` under a profile whose config
   says `context.engine: "<engine name>"`.
3. Read three witnesses from that one run:
   - the engine's append-only log — **empty**;
   - the engine's module-global entry counter — **0**, after a six-prompt session;
   - the host's own build state — the engine **is** attached.

## Evidence, all from the same sessions

```
attached before=NoneType selected='<engine>'
attached after=CtxvmFaultPinEngine        ← agent.context_compressor is the plugin engine
_engine_overrides_hook(engine, "select_context")  → True   (also True for its deepcopy)
no "Context engine select_context hook failed" warning in any log
plugin entry log: absent after 1-prompt and 6-prompt sessions (clean flushes)
```

## The code path, as read

```
agent/turn_request_assembly.py:145   api_messages = _apply_context_engine_selection(...)
                                     ← the only production call site of select_context
agent/conversation_loop.py:1342      _engine_overrides_hook(engine, name)
agent/conversation_loop.py:1757      _run_phase(assemble_api_request, agent, s)
hermes_cli/main.py:2903              _run_oneshot_from_args → launch_gateway_chat
```

`_apply_context_engine_selection` is reached only through `assemble_api_request`. With the engine
attached and the gate passing, an empty entry log means the one-shot request is not assembled through
`assemble_api_request`.

## Expected

`select_context()` is called once per assembled API request when the engine overrides the hook.

## Actual

It is never called on the one-shot transport; the request goes out unselected, and the plugin's
selection counters stay at zero for the whole session.

## Why it matters beyond one plugin

The hook is the documented seam for request-only context selection. A transport that skips it makes
every such engine a silent no-op — and silent is the problem: the request is valid, the session
succeeds, and the only symptom is a counter at zero.

## Suggested minimal fix

Route the one-shot request through `assemble_api_request` (or call
`_apply_context_engine_selection` wherever the one-shot path builds `api_messages`), so the single
documented call site is the only one and no transport bypasses it. A regression test that asserts the
hook is entered on the one-shot transport would keep it fixed.

## Notes

Nothing here is specific to the engine under test: it overrides the ABC method, returns `None` by
default, and needs no host capability beyond the hook.
