"""
T17 live adapter — Hermes plugin surface → tracer core
(`packages/hermes/src/plugin.py`).

Hermes plugins are Python packages loaded from ``$HERMES_HOME/plugins/`` or
adopted via ``hermes plugins adopt``. The plugin module must expose
``register(ctx)`` where ``ctx`` is a ``PluginContext`` with
``register_hook`` / ``register_command`` / ``on_unload``.

Hooks wired (see packages/hermes/HOOKS.md for the full pin):

    on_session_start   → session.open   (model/provider/budget from CTXVM_* env)
    pre_tool_call      → recall({tool, args})
    post_tool_call     → page.declare   (status in {"ok", "completed"} only; T6 §2)
    pre_llm_call       → scan(history) + render()   [turn boundary]
    on_session_end     → finish_all() flush

Trace output (flushes on session end and plugin unload):
    <trace-dir>/<session-id>.jsonl        — RFC-0 xCABI JSONL trace
    <trace-dir>/<session-id>.meta.json    — session id, harness, hook counts, trace stats

Two ways to enable tracing:

1. Env-gating (plugin loads with tracing already active):
   CTXVM_TRACE_DIR=<dir> CTXVM_TRACE_NAME=<name> hermes ...  (gateway must be
   restarted with these in its environment — see HOOKS.md §Live capture)

2. Slash command from inside Hermes (no gateway restart needed):
   /ctxvm-trace start <dir> [name]   — start tracing, writes to <dir>
   /ctxvm-trace stop                 — flush traces and stop
   /ctxvm-trace status               — show whether tracing is active

Without either, hooks are registered but no tracing occurs (mirror-only v0:
never mutates messages, never evicts, never throws on semantic conditions).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import sys

# Locate packages/hermes/src/ (the committed adapter) by walking up from this
# file's directory. Works in-repo; when installed at $HERMES_HOME/plugins/,
# fall back to a plugin-local copy of plugin.py.
_plugin_dir = Path(__file__).resolve().parent
_hermes_src = None
for _candidate in [_plugin_dir] + list(_plugin_dir.parents):
    _maybe = _candidate / "src" / "plugin.py"
    if _maybe.is_file():
        _hermes_src = str(_candidate / "src")
        break
# Fallback: plugin-local plugin.py (installed copy alongside __init__.py)
if _hermes_src is None and (_plugin_dir / "plugin.py").is_file():
    _hermes_src = str(_plugin_dir)
if _hermes_src and _hermes_src not in sys.path:
    sys.path.insert(0, _hermes_src)

from plugin import create_ctxvm_plugin  # noqa: E402

ENV_KEYS = [
    "CTXVM_TRACE_DIR",
    "CTXVM_TRACE_NAME",
    "CTXVM_MODEL",
    "CTXVM_PROVIDER",
    "CTXVM_AGENT_ID",
    "CTXVM_BUDGET_TOKENS",
]


def _clear_env_for_tests() -> None:
    for key in ENV_KEYS:
        os.environ.pop(key, None)
    # Reset module-level trace state set by slash-command tests.
    global _trace_dir, _trace_name
    _trace_dir = os.environ.get("CTXVM_TRACE_DIR")  # None after pop above
    _trace_name = os.environ.get("CTXVM_TRACE_NAME")


def _budget_from_env() -> int:
    raw = os.environ.get("CTXVM_BUDGET_TOKENS", "200000")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 200000
    return value if value > 0 else 200000


def _transcript_texts(history: Optional[list[dict[str, Any]]]) -> str:
    """All text entering the compose window this turn (user + assistant + tool summaries)."""
    parts: list[str] = []
    if not history:
        return ""
    for message in history:
        zone = message.get("parts") or message.get("content")
        if zone:
            for part in zone:
                if isinstance(part, dict) and part.get("text"):
                    parts.append(part["text"])
        elif message.get("text"):
            parts.append(message["text"])
    return "\n".join(parts)


def _content_to_page_body(content_items: Optional[list[dict[str, Any]]]) -> str:
    """Text items verbatim joined by \\n; non-text items as type markers."""
    if not content_items:
        return ""
    kept: list[str] = []
    for item in content_items:
        item_type = item.get("type") or "text"
        if item_type == "text":
            kept.append(item.get("text", ""))
        else:
            name = item.get("name")
            kept.append(f"<{item_type}{f':{name}' if isinstance(name, str) else ''}>")
    return "\n".join(kept)


# ---------------------------------------------------------------------------
# Module-level trace state. Initialized from env at import so the existing
# CTXVM_TRACE_DIR workflow keeps working; overridable at runtime via the
# /ctxvm-trace slash command (no gateway restart needed).
# ---------------------------------------------------------------------------
_trace_dir: Optional[str] = os.environ.get("CTXVM_TRACE_DIR")
_trace_name: Optional[str] = os.environ.get("CTXVM_TRACE_NAME")
_plugin: Optional[Any] = None


def _traced() -> bool:
    """True when a trace dir is active (env or slash-command set)."""
    return bool(_trace_dir)


def _make_plugin() -> Optional[Any]:
    """Create a tracer plugin if tracing is enabled; None otherwise."""
    if not _traced():
        return None
    return create_ctxvm_plugin({
        "agentId": os.environ.get("CTXVM_AGENT_ID", "hermes"),
        "model": os.environ.get("CTXVM_MODEL", "unknown/unknown"),
        "provider": os.environ.get("CTXVM_PROVIDER", "unknown"),
        "budgetTokens": _budget_from_env(),
    })


def register(ctx) -> None:
    """Hermes plugin entry point. Hooks always registered; tracing gated lazily."""
    trace_name = _trace_name  # initial value, may be overridden by slash command
    sessions: list[str] = []

    stats: Dict[str, Any] = {
        "session_starts": 0,
        "pre_tool_calls": 0,
        "post_tool_calls": 0,
        "completed": 0,
        "errored": 0,
        "pre_llm_calls": 0,
        "session_ends": 0,
    }

    def _ensure_plugin() -> Optional[Any]:
        global _plugin
        if _plugin is None and _traced():
            _plugin = _make_plugin()
        return _plugin

    def _write_trace(session_id: str, tracer: Any) -> None:
        """Write a single session's tracer to {session_id}.jsonl/.meta.json."""
        trace_dir = _trace_dir
        if not trace_dir:
            return
        Path(trace_dir).mkdir(parents=True, exist_ok=True)
        trace = tracer.finish()
        jsonl_path = Path(trace_dir) / f"{session_id}.jsonl"
        meta_path = Path(trace_dir) / f"{session_id}.meta.json"
        jsonl_path.write_text(trace.jsonl, encoding="utf-8")
        meta_path.write_text(
            json.dumps(
                {
                    "sessionID": session_id,
                    "harness": "hermes-python-plugin",
                    "model": os.environ.get("CTXVM_MODEL"),
                    "provider": os.environ.get("CTXVM_PROVIDER"),
                    "budgetTokens": _budget_from_env(),
                    "capturedAt": datetime.now(timezone.utc).isoformat(),
                    "hookStats": {**stats, "sessions": [session_id]},
                    "traceStats": trace.stats,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _flush_traces() -> None:
        """Write all finished tracers to the active trace dir, one file per session."""
        vm = _ensure_plugin()
        if vm is None:
            return
        flushed = vm.finish_all()
        trace_dir = _trace_dir
        if not trace_dir:
            return
        Path(trace_dir).mkdir(parents=True, exist_ok=True)
        for record in flushed:
            session_id = record["sessionID"]
            trace = record["trace"]
            jsonl_path = Path(trace_dir) / f"{session_id}.jsonl"
            meta_path = Path(trace_dir) / f"{session_id}.meta.json"
            jsonl_path.write_text(trace.jsonl, encoding="utf-8")
            meta_path.write_text(
                json.dumps(
                    {
                        "sessionID": session_id,
                        "harness": "hermes-python-plugin",
                        "model": os.environ.get("CTXVM_MODEL"),
                        "provider": os.environ.get("CTXVM_PROVIDER"),
                        "budgetTokens": _budget_from_env(),
                        "capturedAt": datetime.now(timezone.utc).isoformat(),
                        "hookStats": {**stats, "sessions": [session_id]},
                        "traceStats": trace.stats,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    # --- Hook handlers ------------------------------------------------------

    def on_session_start(**kwargs: Any) -> None:
        stats["session_starts"] += 1
        session_id = kwargs.get("session_id", "")
        if session_id and session_id not in sessions:
            sessions.append(session_id)
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_session_start(kwargs)

    def on_pre_tool_call(**kwargs: Any) -> None:
        stats["pre_tool_calls"] += 1
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_tool_call(kwargs)

    def on_post_tool_call(**kwargs: Any) -> None:
        stats["post_tool_calls"] += 1
        status = kwargs.get("status")
        # Real Hermes taxonomy (model_tools.py:_tool_result_observer_fields,
        # line 656-671): status is "ok" on success, "error" on failure.
        # hooks.py demo payloads use "completed"/"error"; accept both.
        if status not in ("ok", "completed"):
            stats["errored"] += 1
        else:
            stats["completed"] += 1
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_post_tool_call(kwargs)

    def on_pre_llm_call(**kwargs: Any) -> None:
        stats["pre_llm_calls"] += 1
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_llm_call(kwargs)

    def on_session_end(**kwargs: Any) -> None:
        stats["session_ends"] += 1
        session_id = kwargs.get("session_id", "")
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_session_end(kwargs)
            # Flush this session's tracer to its own file, so multiple sessions
            # don't overwrite each other.
            tracer = vm._tracers.get(session_id) if session_id else None
            if tracer is not None:
                _write_trace(session_id, tracer)

    # --- Slash command: /ctxvm-trace ---------------------------------------

    def _handle_trace_cmd(raw_args: str) -> str:
        """Handle /ctxvm-trace start <dir> [name] | stop | status."""
        global _plugin, trace_name
        global _trace_dir
        argv = raw_args.strip().split()
        if not argv:
            return (
                "Usage: /ctxvm-trace start <dir> [name] | stop | status\n"
                "  start <dir> [name]  — begin tracing, writes <dir>/<name>.jsonl\n"
                "  stop                — flush traces and stop tracing\n"
                "  status              — show whether tracing is active"
            )

        sub = argv[0].lower()

        if sub == "start":
            if len(argv) < 2:
                return "Usage: /ctxvm-trace start <dir> [name]"
            new_dir = argv[1]
            new_name = argv[2] if len(argv) > 2 else None
            _trace_dir = new_dir
            if new_name:
                trace_name = new_name
            # Force plugin (re)creation on next hook so it picks up the new dir.
            _plugin = None
            return (
                f"ctxvm-trace: tracing enabled, dir={_trace_dir}, "
                f"name={trace_name or '<session-id>'}"
            )

        if sub == "stop":
            _flush_traces()
            _trace_dir = None
            _plugin = None
            return "ctxvm-trace: tracing stopped, traces flushed."

        if sub == "status":
            plugin_active = _plugin is not None
            return (
                f"ctxvm-trace: enabled={_traced()}, "
                f"dir={_trace_dir or '<none>'}, "
                f"name={trace_name or '<session-id>'}, "
                f"plugin={plugin_active}"
            )

        return (
            f"Unknown subcommand '{sub}'. "
            "Usage: /ctxvm-trace start <dir> [name] | stop | status"
        )

    # Register hooks (always; tracing gated lazily inside each handler)
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("on_session_end", on_session_end)

    # Register slash command for runtime start/stop/status
    ctx.register_command(
        "ctxvm-trace",
        _handle_trace_cmd,
        description="Start/stop/show ctxvm trace capture.",
    )

    # Register cleanup on plugin unload
    ctx.on_unload(lambda: _flush_traces())