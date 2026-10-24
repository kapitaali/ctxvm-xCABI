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
    post_tool_call     → page.declare   (status == "completed" only; T6 §2)
    pre_llm_call       → scan(history) + render()   [turn boundary]
    on_session_end     → finish_all() flush

Env-gated: traces are only written when ``CTXVM_TRACE_DIR`` is set. Unlike the
T12 OpenCode adapter (which gates at setup time), Hermes loads plugins in a
long-running gateway process, so the gate is checked lazily at each hook call.
Without ``CTXVM_TRACE_DIR``, hooks are registered but no tracing occurs.

Trace output (on plugin unload / session end):
    $CTXVM_TRACE_DIR/<name>.jsonl        — RFC-0 xCABI JSONL trace
    $CTXVM_TRACE_DIR/<name>.meta.json    — session id, harness, hook counts, trace stats
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


def _traced() -> bool:
    """True when CTXVM_TRACE_DIR is set (checked lazily per hook call)."""
    return bool(os.environ.get("CTXVM_TRACE_DIR"))


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
    _plugin: Optional[Any] = None
    trace_name = os.environ.get("CTXVM_TRACE_NAME")
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
        nonlocal _plugin
        if _plugin is None and _traced():
            _plugin = _make_plugin()
        return _plugin

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
        # hooks.py demo payloads use "completed"/"error"; accept both for
        # demo/synthetic compatibility.
        if status in ("ok", "completed"):
            stats["completed"] += 1
        else:
            stats["errored"] += 1
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
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_session_end(kwargs)
            # Flush per-session traces at session end so captures are written
            # even when the gateway stays up (on_unload only fires at shutdown).
            _flush_traces()

    def _flush_traces() -> None:
        """Write all finished tracers to $CTXVM_TRACE_DIR."""
        vm = _ensure_plugin()
        if vm is None:
            return
        flushed = vm.finish_all()
        trace_dir = os.environ.get("CTXVM_TRACE_DIR")
        if not trace_dir:
            return
        Path(trace_dir).mkdir(parents=True, exist_ok=True)
        base = trace_name
        for record in flushed:
            session_id = record["sessionID"]
            trace = record["trace"]
            file = base or session_id
            jsonl_path = Path(trace_dir) / f"{file}.jsonl"
            meta_path = Path(trace_dir) / f"{file}.meta.json"
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

    def cleanup() -> None:
        """Flush any remaining tracers on plugin unload / gateway shutdown."""
        _flush_traces()

    # Register hooks (always; tracing gated lazily inside each handler)
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("on_session_end", on_session_end)

    # Register cleanup on plugin unload
    ctx.on_unload(cleanup)
