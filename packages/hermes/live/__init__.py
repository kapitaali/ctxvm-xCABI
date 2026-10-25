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
from typing import Any, Callable, Dict, List, Optional, Set

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
from uc_registry import (
    TRACE_FEATURE,
    UC1_FEATURE,
    UC2_FEATURE,
    UC3_FEATURE,
    HANDOFF_FEATURE,
    UCModule,
    is_enabled,
    parse_features,
)
from uc1_handoff import UC1Handoff
from uc2_forensics import UC2Forensics
from uc3_planner import UC3Planner

# Bumped whenever the adapter's wire behaviour changes. Written into every
# .meta.json so a stale in-process copy is identifiable from its output alone.
PLUGIN_VERSION = "0.2.0"

# --- KIT-1 sidecar + witness canonicalization (09-plugin-parity.md §3, §5) ----
# Both flush paths build .meta.json through _canon_meta so the harnesses emit
# identical sidecar SHAPES (packages/opencode/live/ctxvm.ts is the GO mirror).


def _rfc3339_z(dt: datetime) -> str:
    """RFC-3339 with the mandated Z suffix (canonical capturedAt form)."""
    return dt.isoformat().replace("+00:00", "Z")


def _witness(msg: str) -> None:
    """Best-effort diagnostic witness (09-plugin-parity.md §5): append one
    timestamped line to hooks-witness.log in the active trace dir so a missing
    flush is diagnosable. Failures are swallowed by design — a broken witness
    must never break capture."""
    try:
        trace_dir = _active_trace_dir()
        if not trace_dir:
            return
        Path(trace_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(trace_dir, "hooks-witness.log"), "a", encoding="utf-8") as fh:
            fh.write(f"{_rfc3339_z(datetime.now(timezone.utc))} {msg}\n")
    except Exception:
        pass


def _flush_base() -> Optional[str]:
    """Preferred filename root for flushed captures — parity with opencode's
    `base || sessionID`: slash-command name first, env second, else None."""
    state = _state()
    return state.get("trace_name") or os.environ.get("CTXVM_TRACE_NAME")


def _canon_meta(session_id: str, hook_stats: Dict[str, int], trace_stats: Any) -> Dict[str, Any]:
    """Canonical .meta.json sidecar (09-plugin-parity.md §3). Both writers route
    through this; the package parity tests assert the exact key sets."""
    return {
        "sessionID": session_id,
        "harness": "hermes-python-plugin",
        "harnessVersion": os.environ.get("CTXVM_HERMES_VERSION"),
        "pluginVersion": PLUGIN_VERSION,
        "model": os.environ.get("CTXVM_MODEL"),
        "provider": os.environ.get("CTXVM_PROVIDER"),
        "budgetTokens": _budget_from_env(),
        "capturedAt": _rfc3339_z(datetime.now(timezone.utc)),
        "hookStats": {
            "contexts": hook_stats["pre_llm_calls"],
            "before": hook_stats["pre_tool_calls"],
            "after": hook_stats["post_tool_calls"],
            "completed": hook_stats["completed"],
            "errored": hook_stats["errored"],
            "extraHookStats": {
                "session_starts": hook_stats["session_starts"],
                "session_ends": hook_stats["session_ends"],
                "skipped_untraced": hook_stats["skipped_untraced"],
            },
            "sessions": [session_id],
        },
        "traceStats": trace_stats,
    }


ENV_KEYS = [
    "CTXVM_TRACE_DIR",
    "CTXVM_TRACE_NAME",
    "CTXVM_MODEL",
    "CTXVM_PROVIDER",
    "CTXVM_AGENT_ID",
    "CTXVM_BUDGET_TOKENS",
]


def _clear_env_for_tests() -> None:
    """Drop CTXVM_* env and reset the process-global state (tests only)."""
    for key in ENV_KEYS:
        os.environ.pop(key, None)
    os.environ.pop("CTXVM_FEATURES", None)
    if hasattr(sys, _STATE_ATTR):
        delattr(sys, _STATE_ATTR)


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
# Process-global trace state.
#
# WHY sys, not module globals: Hermes re-imports/re-registers plugins between
# sessions (and a fresh import creates a NEW module object). Module-level
# variables therefore reset to their import-time values, silently discarding
# both the trace dir set by /ctxvm-trace and every page declared so far.
# ``sys`` is imported exactly once per process and is never reloaded, so an
# attribute hung off it survives any re-import of this plugin.
# ---------------------------------------------------------------------------
_STATE_ATTR = "_ctxvm_tracer_state"


def _state() -> Dict[str, Any]:
    """Return the process-global tracer state, creating it on first use."""
    state = getattr(sys, _STATE_ATTR, None)
    if state is None:
        state = {
            "trace_dir": os.environ.get("CTXVM_TRACE_DIR"),
            "trace_name": os.environ.get("CTXVM_TRACE_NAME"),
            "features": parse_features(os.environ.get("CTXVM_FEATURES")),
            "plugin": None,
            "stats": {
                "session_starts": 0,
                "pre_tool_calls": 0,
                "post_tool_calls": 0,
                "completed": 0,
                "errored": 0,
                "pre_llm_calls": 0,
                "session_ends": 0,
                # Hooks that fired while tracing was disabled. Non-zero here
                # with pages=0 means tracing was switched on AFTER the calls
                # happened — nothing was missed by the tracer, it simply was
                # not created yet. This is the #1 false-alarm signal.
                "skipped_untraced": 0,
            },
            "register_calls": 0,
        }
        setattr(sys, _STATE_ATTR, state)
    return state


def _traced() -> bool:
    """True when a trace dir is active (env or slash-command set)."""
    state = _state()
    return bool(state["trace_dir"] or os.environ.get("CTXVM_TRACE_DIR"))


def _active_trace_dir() -> Optional[str]:
    """Active trace dir: slash-command value wins, env is the fallback."""
    state = _state()
    return state["trace_dir"] or os.environ.get("CTXVM_TRACE_DIR")


def _features() -> Set[str]:
    """Active CTXVM_FEATURES set (default {trace})."""
    return _state()["features"]


def _enabled_stubs(features: Set[str]) -> list[UCModule]:
    """UC modules whose feature is enabled, in declaration order.

    Reuses the instances stored in state["ucs"] (created once at register()
    time) so hook dispatch never allocates new UC objects.
    """
    stubs: list[UCModule] = []
    ucs = _state().get("ucs", {})
    for name in ("uc1-handoff", "uc2-forensics", "uc3-planner"):
        uc = ucs.get(name)
        if uc is not None and uc.enabled(features):
            stubs.append(uc)
    return stubs


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
    state = _state()
    state["register_calls"] += 1
    _witness(f"init name={state.get('trace_name') or os.environ.get('CTXVM_TRACE_NAME') or '<session-id>'}")
    stats = state["stats"]
    features = _features()  # parsed once; UC modules read it via _enabled_stubs()
    state["ucs"] = {
        "uc1-handoff": UC1Handoff(),
        "uc2-forensics": UC2Forensics(),
        "uc3-planner": UC3Planner(),
    }
    
    def _ensure_plugin() -> Optional[Any]:
        """Create the tracer plugin on first traced hook call; reuse thereafter.

        The tracer is only created when the ``trace`` feature is active
        (default) AND a trace dir is set. Other features drive their own UC
        modules, which are stubs until their logic lands.
        """
        if TRACE_FEATURE not in _features():
            return None
        if state["plugin"] is None and _traced():
            state["plugin"] = _make_plugin()
        return state["plugin"]

    def _write_trace(session_id: str, tracer: Any) -> None:
        """Write a single session's tracer to {file}.jsonl/.meta.json."""
        trace_dir = _active_trace_dir()
        if not trace_dir:
            return
        Path(trace_dir).mkdir(parents=True, exist_ok=True)
        trace = tracer.finish()
        file = _flush_base() or session_id
        jsonl_path = Path(trace_dir) / f"{file}.jsonl"
        meta_path = Path(trace_dir) / f"{file}.meta.json"
        jsonl_path.write_text(trace.jsonl, encoding="utf-8")
        _witness(f"flush {file}.jsonl bytes={len(trace.jsonl)} session={session_id}")
        meta_path.write_text(
            json.dumps(_canon_meta(session_id, stats, trace.stats), indent=2)
            + "\n",
            encoding="utf-8",
        )

    def _flush_traces() -> None:
        """Write all finished tracers to the active trace dir, one file per session."""
        features = _features()
        vm = _ensure_plugin()
        trace_dir = _active_trace_dir()
        if vm is not None and trace_dir:
            Path(trace_dir).mkdir(parents=True, exist_ok=True)
            base = _flush_base()
            for record in vm.finish_all():
                session_id = record["sessionID"]
                trace = record["trace"]
                file = base or session_id
                Path(trace_dir, f"{file}.jsonl").write_text(
                    trace.jsonl, encoding="utf-8"
                )
                _witness(f"flush {file}.jsonl bytes={len(trace.jsonl)} session={session_id}")
                Path(trace_dir, f"{file}.meta.json").write_text(
                    json.dumps(_canon_meta(session_id, stats, trace.stats), indent=2)
                    + "\n",
                    encoding="utf-8",
                )
        # UC stubs flush (no-op for current stubs; real UCs write artefacts)
        for uc in _enabled_stubs(features):
            uc.flush()

    # --- Hook handlers ------------------------------------------------------

    def on_session_start(**kwargs: Any) -> None:
        stats["session_starts"] += 1
        _witness("session_start")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_session_start(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_session_start(kwargs)

    def on_pre_tool_call(**kwargs: Any) -> None:
        stats["pre_tool_calls"] += 1
        _witness(f"before tool={kwargs.get('tool')}")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_tool_call(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_pre_tool_call(kwargs)

    def on_post_tool_call(**kwargs: Any) -> None:
        stats["post_tool_calls"] += 1
        status = kwargs.get("status")
        _witness(f"after tool={kwargs.get('tool')} status={status}")
        if status not in ("ok", "completed"):
            stats["errored"] += 1
        else:
            stats["completed"] += 1
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_post_tool_call(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_post_tool_call(kwargs)

    def on_pre_llm_call(**kwargs: Any) -> None:
        stats["pre_llm_calls"] += 1
        _witness("pre_llm (context)")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_llm_call(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_pre_llm_call(kwargs)

    def on_session_end(**kwargs: Any) -> None:
        stats["session_ends"] += 1
        _witness("session_end -> flush all tracers")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_session_end(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        _flush_traces()
        for uc in _enabled_stubs(features):
            uc.on_session_end(kwargs)

    # --- Slash command: /ctxvm-trace ---------------------------------------

    def _handle_trace_cmd(raw_args: str) -> str:
        """Handle /ctxvm-trace start <dir> [name] | stop | status."""
        argv = raw_args.strip().split()
        if not argv:
            return (
                "Usage: /ctxvm-trace start <dir> [name] | stop | status\n"
                "  start <dir> [name]  — begin tracing, writes <dir>/<session-id>.jsonl\n"
                "  stop                — flush traces and stop tracing\n"
                "  status              — show whether tracing is active"
            )

        sub = argv[0].lower()

        if sub == "start":
            if len(argv) < 2:
                return "Usage: /ctxvm-trace start <dir> [name]"
            state["trace_dir"] = argv[1]
            if len(argv) > 2:
                state["trace_name"] = argv[2]
            # Fresh plugin so a new dir never inherits another dir's tracers.
            state["plugin"] = None
            return (
                f"ctxvm-trace: tracing enabled, dir={state['trace_dir']}, "
                f"name={state['trace_name'] or '<session-id>'}"
            )

        if sub == "stop":
            _witness("trace stop -> flush all tracers")
            _flush_traces()
            state["trace_dir"] = None
            state["plugin"] = None
            return "ctxvm-trace: tracing stopped, traces flushed."

        if sub == "status":
            plugin = state["plugin"]
            if plugin is None:
                detail = "plugin=None (no tracer yet — hooks firing will not record)"
            else:
                tracers = getattr(plugin, "_tracers", {})
                rows = []
                for sid, tracer in sorted(tracers.items()):
                    events = getattr(tracer, "_events", [])
                    declares = sum(1 for e in events if e.get("type") == "page.declare")
                    rows.append(f"{sid[:16] or '<empty>'}:events={len(events)},pages={declares}")
                detail = "tracers=[" + "; ".join(rows) + "]" if rows else "tracers=[]"
            return (
                f"ctxvm-trace: enabled={_traced()}, "
                f"dir={_active_trace_dir() or '<none>'}, "
                f"name={state['trace_name'] or '<session-id>'}, "
                f"version={PLUGIN_VERSION}, "
                f"register_calls={state['register_calls']}, "
                f"{detail}"
            )

        return (
            f"Unknown subcommand '{sub}'. "
            "Usage: /ctxvm-trace start <dir> [name] | stop | status"
        )


    def _handle_forensics_cmd(raw_args: str) -> str:
        """Handle /ctxvm-forensics <subcommand> [args...].

        Subcommands (thin wrappers around the committed Rust CLI binaries):

          replay <trace> [--turn N] [--pin ref|(ref,hash)]... [--output FILE]
            Point-in-time replay + counterfactual force-resident overlay.

          profile <trace> [--event <type>]... [--turns spec] [--source <src>] [--output FILE]
            Forensic aggregation: fault/eviction rows, turn tallies.

          diff <a.jsonl> <b.jsonl> [--output FILE]
            Positional two-trace comparison.

          export <trace> [--turn N] [--output DIR] [--odps]
            Handoff snapshot builder (turn-N slice + page table).

          diagnose <trace> <turn>
            Verdict decomposition: context-management fault vs model reasoning
            fault for a page.fault at *turn*.

        Thin wrapper — the engine (Rust core) is untouched. This command only
        shells out to the already-built binaries and formats their JSON output.
        """
        argv = raw_args.strip().split()
        if not argv:
            return (
                "Usage: /ctxvm-forensics <replay|profile|diff|export|diagnose> [args...]\n"
                "  replay <trace> [--turn N] [--pin ref|(ref,hash)]... [--output FILE]\n"
                "  profile <trace> [--event <type>]... [--turns spec] [--source <src>] [--output FILE]\n"
                "  diff <a.jsonl> <b.jsonl> [--output FILE]\n"
                "  export <trace> [--turn N] [--output DIR] [--odps]\n"
                "  diagnose <trace> <turn>   — context-management vs model reasoning verdict\n"
            )

        ucs = _state().get("ucs", {})
        uc2 = ucs.get("uc2-forensics")
        if uc2 is None:
            return "ctxvm-forensics: UC2 module not available (is CTXVM_FEATURES=uc2-forensics set?)"

        sub = argv[0].lower()
        rest = argv[1:]

        if sub == "replay":
            trace = rest[0] if rest else None
            if not trace:
                return "Usage: /ctxvm-forensics replay <trace> [--turn N] [--pin ...] [--output FILE]"
            # Parse --turn, --pin, --output from the rest
            turn: Optional[int] = None
            pins: List[str] = []
            output: Optional[str] = None
            i = 1
            while i < len(rest):
                if rest[i] == "--turn" and i + 1 < len(rest):
                    try:
                        turn = int(rest[i + 1])
                    except ValueError:
                        return f"ctxvm-forensics: --turn requires a number, got '{rest[i+1]}'"
                    i += 2
                elif rest[i] == "--pin" and i + 1 < len(rest):
                    pins.append(rest[i + 1])
                    i += 2
                elif rest[i] == "--output" and i + 1 < len(rest):
                    output = rest[i + 1]
                    i += 2
                else:
                    return f"ctxvm-forensics: unknown replay arg '{rest[i]}'"
            result = uc2.replay(trace, turn=turn, pins=pins if pins else None, output=output)
            report = result["report"]
            if isinstance(report, dict):
                return json.dumps(report, indent=2)
            return str(report)

        if sub == "profile":
            trace = rest[0] if rest else None
            if not trace:
                return "Usage: /ctxvm-forensics profile <trace> [--event <type>]... [--turns spec] [--source <src>] [--output FILE]"
            events: List[str] = []
            turns: Optional[str] = None
            source: Optional[str] = None
            output: Optional[str] = None
            i = 1
            while i < len(rest):
                if rest[i] == "--event" and i + 1 < len(rest):
                    events.append(rest[i + 1])
                    i += 2
                elif rest[i] == "--turns" and i + 1 < len(rest):
                    turns = rest[i + 1]
                    i += 2
                elif rest[i] == "--source" and i + 1 < len(rest):
                    source = rest[i + 1]
                    i += 2
                elif rest[i] == "--output" and i + 1 < len(rest):
                    output = rest[i + 1]
                    i += 2
                else:
                    return f"ctxvm-forensics: unknown profile arg '{rest[i]}'"
            result = uc2.profile(trace, events=events if events else None, turns=turns, source=source, output=output)
            report = result["report"]
            if isinstance(report, dict):
                return json.dumps(report, indent=2)
            return str(report)

        if sub == "diff":
            if len(rest) < 2:
                return "Usage: /ctxvm-forensics diff <a.jsonl> <b.jsonl> [--output FILE]"
            output: Optional[str] = None
            i = 2
            while i < len(rest):
                if rest[i] == "--output" and i + 1 < len(rest):
                    output = rest[i + 1]
                    i += 2
                else:
                    return f"ctxvm-forensics: unknown diff arg '{rest[i]}'"
            result = uc2.diff(rest[0], rest[1], output=output)
            report = result["report"]
            if isinstance(report, dict):
                return json.dumps(report, indent=2)
            return str(report)

        if sub == "export":
            trace = rest[0] if rest else None
            if not trace:
                return "Usage: /ctxvm-forensics export <trace> [--turn N] [--output DIR] [--odps]"
            turn: Optional[int] = None
            output: Optional[str] = None
            odps = False
            i = 1
            while i < len(rest):
                if rest[i] == "--turn" and i + 1 < len(rest):
                    try:
                        turn = int(rest[i + 1])
                    except ValueError:
                        return f"ctxvm-forensics: --turn requires a number, got '{rest[i+1]}'"
                    i += 2
                elif rest[i] == "--output" and i + 1 < len(rest):
                    output = rest[i + 1]
                    i += 2
                elif rest[i] == "--odps":
                    odps = True
                    i += 1
                else:
                    return f"ctxvm-forensics: unknown export arg '{rest[i]}'"
            result = uc2.export(trace, turn=turn, output=output, odps=odps)
            report = result["report"]
            if isinstance(report, dict):
                return json.dumps(report, indent=2)
            return str(report)

        if sub == "diagnose":
            if len(rest) < 2:
                return "Usage: /ctxvm-forensics diagnose <trace> <turn>"
            try:
                fault_turn = int(rest[1])
            except ValueError:
                return f"ctxvm-forensics: --turn requires a number, got '{rest[1]}'"
            result = uc2.diagnose(rest[0], fault_turn)
            return json.dumps(result, indent=2)

        return f"ctxvm-forensics: unknown subcommand '{sub}'. Usage: /ctxvm-forensics <replay|profile|diff|export|diagnose> [args...]"

    def _handle_handoff_cmd(raw_args: str) -> str:
        """Handle /ctxvm-handoff <dir> [turn] [--stop].

        Pause: flush live tracers → era snapshot → package through export
        (--turn N --output <dir>/handoff/ --odps) → print artifacts + DQ/KPI.

        Thin wrapper around the committed Rust export/replay binaries.
        """
        ucs = _state().get("ucs", {})
        uc1 = ucs.get("uc1-handoff")
        if uc1 is None:
            return "ctxvm-handoff: UC1 module not available (is CTXVM_FEATURES=handoff set?)"

        argv = raw_args.strip().split()
        if not argv:
            return (
                "Usage: /ctxvm-handoff <dir> [turn] [--stop]\n"
                "  <dir>    — flush/pause target directory (or CTXVM_HANDOFF_DIR)\n"
                "  [turn]   — handoff turn (default: flush at current turn)\n"
                "  [--stop] — after packaging, stop tracing (same as /ctxvm-trace stop)\n"
            )

        trace_dir = argv[0]
        turn: Optional[int] = None
        stop_after = False
        i = 1
        while i < len(argv):
            if argv[i] == "--stop":
                stop_after = True
                i += 1
            else:
                try:
                    turn = int(argv[i])
                except ValueError:
                    return f"ctxvm-handoff: turn requires a number, got '{argv[i]}'"
                i += 1

        result = uc1.pause(trace_dir, turn=turn)
        report = result.get("report", {})
        if isinstance(report, dict):
            out = json.dumps(report, indent=2)
        else:
            out = str(report)
        out += f"\nctxvm-handoff: exit_code={result['exit_code']} verified={result.get('verified')} divergences={result.get('divergences')}"
        if result.get("stderr"):
            out += f"\nctxvm-handoff stderr: {result['stderr']}"
        if stop_after:
            stop_out = _handle_trace_cmd("stop")
            out += f"\n{stop_out}"
        return out

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

    # Register slash command for UC2 forensics: replay/profile/diff/export/diagnose
    if UC2_FEATURE in _features():
        ctx.register_command(
            "ctxvm-forensics",
            _handle_forensics_cmd,
            description="UC2 forensics: replay/profile/diff/export/diagnose traces.",
        )

    # Register slash command for UC1 handoff pause: flush → era snapshot → export package
    if HANDOFF_FEATURE in _features():
        ctx.register_command(
            "ctxvm-handoff",
            _handle_handoff_cmd,
            description="UC1 pause: flush → era snapshot → export package (handoff snapshot).",
        )

    # Register cleanup on plugin unload
    ctx.on_unload(lambda: _flush_traces())

    # Flush on process exit too. Guarded by process-global state so repeated
    # register() calls cannot stack duplicate atexit handlers.
    if not state.get("atexit_registered"):
        state["atexit_registered"] = True
        import atexit
        atexit.register(_flush_traces)