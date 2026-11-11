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
    pre_api_request    → call.meta latency (W2b)
    post_api_request   → providerUsage     (W8: provider receipt, last-write-wins)
    on_session_end     → finish_all() flush

Trace output (flushes on session end and plugin unload):
    <trace-dir>/<session-id>.jsonl        — RFC-0 xCABI JSONL trace
    <trace-dir>/<session-id>.meta.json    — session id, harness, hook counts, trace stats
    <trace-dir>/<session-id>.coverage.json — W17 coverage manifest (FULL flush only;
        no sidecar at write-through partials). Validates against the trace bytes
        with tools/coverage_check.py — the checker, not this file, is the law.

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

import hashlib
import json
import os
import re
import time
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
# The W8 engine module (context_engine.py) is a live/-sibling in the committed
# tree and a plugin-local file in the installed copy: this directory carries
# it either way. Kept AFTER the src insert so `plugin`/`uc*` always resolve to
# packages/hermes/src first (the shadowing order the flat imports expect).
if str(_plugin_dir) not in sys.path:
    sys.path.insert(1, str(_plugin_dir))

from plugin import create_ctxvm_plugin, identity_from_payload  # noqa: E402
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
PLUGIN_VERSION = "0.11.0"

# --- KIT-1 sidecar + witness canonicalization (09-plugin-parity.md §3, §5) ----
# Both flush paths build .meta.json through _canon_meta so the harnesses emit
# identical sidecar SHAPES (packages/opencode/live/ctxvm.ts is the GO mirror).


def _rfc3339_z(dt: datetime) -> str:
    """RFC-3339 with the mandated Z suffix (canonical capturedAt form)."""
    return dt.isoformat().replace("+00:00", "Z")


# --- trace-dir resolution (adoption fixes, 2026-11-01) -----------------------
# Three defects made capture look broken: `~` was not expanded (a literal "~"
# directory appeared under the process cwd), the default was OFF (so an
# unconfigured harness wrote nothing), and `stop` said "flushed" whether or not
# anything was written. All three are fixed here, and mirrored in
# packages/opencode/live/ctxvm.ts (09-plugin-parity.md §5).

def _default_trace_dir() -> str:
    """State dir used when CTXVM_TRACE_DIR is unset: capture is ON by default."""
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "ctxvm", "traces")


def _resolve_trace_dir(raw: Optional[str]) -> Optional[str]:
    """Normalise a trace-dir input to an absolute path, or None to disable.

    ``CTXVM_TRACE=0|off|false|no`` disables outright; an empty string disables;
    a path is expanded (``~`` and ``$VAR``) and resolved; ``None`` (unset) yields
    the default state dir so an unconfigured harness still records.
    """
    if os.environ.get("CTXVM_TRACE", "").strip().lower() in {"0", "off", "false", "no"}:
        return None
    if raw is None:
        return _default_trace_dir()
    raw = raw.strip()
    if not raw:
        return None
    return str(Path(os.path.expandvars(os.path.expanduser(raw))).resolve())


def _ensure_trace_dir(trace_dir: str) -> None:
    """Create the trace dir 0700 — session content lives in here."""
    Path(trace_dir).mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(trace_dir, 0o700)
    except OSError:
        pass


def _trace_dir_source() -> str:
    """Where the active dir came from, for `/ctxvm-trace status`."""
    state = _state()
    if state["trace_dir"] == "":
        return "disabled in this process (/ctxvm-trace stop)"
    if state.get("trace_dir_cmd_started"):
        return "slash command"
    if os.environ.get("CTXVM_TRACE_DIR") is not None:
        return "env CTXVM_TRACE_DIR"
    if state["trace_dir"]:
        return "start (defaults)"
    if os.environ.get("CTXVM_TRACE", "").strip().lower() in {"0", "off", "false", "no"}:
        return "env CTXVM_TRACE=0"
    return "default (set CTXVM_TRACE=0 to disable)"


def _witness(msg: str) -> None:
    """Best-effort diagnostic witness (09-plugin-parity.md §5): append one
    timestamped line to hooks-witness.log in the active trace dir so a missing
    flush is diagnosable. Failures are swallowed by design — a broken witness
    must never break capture."""
    try:
        trace_dir = _active_trace_dir()
        if not trace_dir:
            return
        _ensure_trace_dir(trace_dir)
        with open(Path(trace_dir, "hooks-witness.log"), "a", encoding="utf-8") as fh:
            fh.write(f"{_rfc3339_z(datetime.now(timezone.utc))} {msg}\n")
    except Exception:
        pass


def _flush_base() -> Optional[str]:
    """Preferred filename root for flushed captures — parity with opencode's
    `base || sessionID`: slash-command name first, env second, else None."""
    state = _state()
    return state.get("trace_name") or os.environ.get("CTXVM_TRACE_NAME")


# --- write-through + retention (2026-11-01) ---------------------------------
# Default-ON capture has two obligations: a crash must not lose the session, and
# the directory must not grow without bound. Write-through persists a partial
# snapshot every N events; retention prunes old captures at flush time.

def _env_flag(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() not in {"0", "off", "false", "no"}


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _partial_paths(trace_dir: str, file: str):
    return (Path(trace_dir, f"{file}.partial.jsonl"), Path(trace_dir, f"{file}.partial.meta.json"))


def _maybe_write_through(vm: Any, stats: Dict[str, int]) -> None:
    """Persist a partial snapshot when enough new events have accrued."""
    if vm is None or not _env_flag("CTXVM_TRACE_WRITETHROUGH"):
        return
    trace_dir = _active_trace_dir()
    if not trace_dir:
        return
    state = _state()
    events = sum(len(getattr(t, "_events", [])) for t in getattr(vm, "_tracers", {}).values())
    if events - int(state.get("last_written_events") or 0) < _env_int("CTXVM_TRACE_WRITETHROUGH_EVERY", 10):
        return
    _ensure_trace_dir(trace_dir)
    base = _flush_base()
    written = 0
    flushed = state.get("flushed_sessions") or set()
    for record in vm.finish_all():
        session_id = record["sessionID"]
        if session_id in flushed:
            continue
        trace = record["trace"]
        file = base or session_id
        jsonl_path, meta_path = _partial_paths(trace_dir, file)
        jsonl_path.write_text(trace.jsonl, encoding="utf-8")
        meta_path.write_text(
            json.dumps(_canon_meta(session_id, stats, trace.stats,
                                   resume_from=state.get("resume_from"),
                                   identity=_tracer_identity(vm.tracer_for(session_id))),
                       indent=2) + "\n",
            encoding="utf-8",
        )
        written += 1
    state["last_written_events"] = events
    if written:
        _witness(f"write-through events={events} traces={written} (partial)")



def _evict_stale_tracers(vm: Any) -> int:
    """Release tracers for sessions that have finished and gone quiet.

    Keeping a tracer after its full flush is what lets a multi-turn session
    accumulate into one capture (defect 4, RR-REVIEW-H6: popping it reset the
    session every prompt). Keeping it FOREVER is the price: every later flush
    rewrites every tracer's trace, and the process grows with the session count.
    So a flushed session is retained for CTXVM_TRACER_RETAIN_MINUTES (default 30)
    and then dropped; the trace on disk is already complete.
    """
    state = _state()
    now = time.time()
    window = _env_int("CTXVM_TRACER_RETAIN_MINUTES", 30) * 60
    flushed_at = state.setdefault("flushed_at", {})
    dropped = 0
    for session_id, stamp in list(flushed_at.items()):
        if now - float(stamp) < window:
            continue
        tracers = getattr(vm, "_tracers", {})
        tracers.pop(session_id, None)
        (state.get("flushed_sessions") or set()).discard(session_id)
        flushed_at.pop(session_id, None)
        dropped += 1
    return dropped


def _prune_traces(trace_dir: str, keep: Optional[str] = None) -> int:
    """Delete old captures beyond the retention budget; never the one just written.

    CTXVM_TRACE_RETAIN_MAX (default 200 files) and CTXVM_TRACE_RETAIN_DAYS
    (default 30) bound a directory that is on by default.
    """
    max_files = _env_int("CTXVM_TRACE_RETAIN_MAX", 200)
    retain_days = _env_int("CTXVM_TRACE_RETAIN_DAYS", 30)
    max_bytes = _env_int("CTXVM_TRACE_RETAIN_BYTES", 512 * 1024 * 1024)
    try:
        captures = sorted(Path(trace_dir).glob("*.jsonl"),
                          key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return 0
    deleted = 0
    kept_bytes = 0
    now = time.time()
    for idx, path in enumerate(captures):
        if path.name.endswith(".partial.jsonl"):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if keep and path.name == keep:
            kept_bytes += size   # the file just written always counts against the budget
            continue
        too_many = idx >= max_files
        try:
            too_old = (now - path.stat().st_mtime) > retain_days * 86400
        except OSError:
            continue
        too_big = (kept_bytes + size) > max_bytes
        if not (too_many or too_old or too_big):
            kept_bytes += size
            continue
        meta = path.with_name(path.name[: -len(".jsonl")] + ".meta.json")
        coverage = path.with_name(path.name[: -len(".jsonl")] + ".coverage.json")
        for victim in (path, meta, coverage):
            try:
                victim.unlink()
                deleted += 1
            except OSError:
                pass
    if deleted:
        _witness(f"retention deleted={deleted} files (max={max_files}, days={retain_days}, bytes={max_bytes})")
    return deleted


def _tracer_identity(tracer: Any) -> Optional[Dict[str, str]]:
    """{model, provider} as the tracer stamped them into session.open."""
    init = getattr(tracer, "_init", None)
    if init is None:
        return None
    return {"model": getattr(init, "model", None), "provider": getattr(init, "provider", None)}


def _canon_meta(
    session_id: str, hook_stats: Dict[str, int], trace_stats: Any,
    resume_from: Optional[Dict[str, Any]] = None,
    identity: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Canonical .meta.json sidecar (09-plugin-parity.md §3). Both writers route
    through this; the package parity tests assert the exact key sets.

    ``resumeFrom`` (B3): opt-in sidecar extension — null when not resuming,
    {snapshot, snapshotDigest, snapTurn} when resuming from a paused snapshot.
    """
    meta = {
        "sessionID": session_id,
        "harness": "hermes-python-plugin",
        "harnessVersion": os.environ.get("CTXVM_HERMES_VERSION"),
        "pluginVersion": PLUGIN_VERSION,
        "model": (identity or {}).get("model") or os.environ.get("CTXVM_MODEL"),
        "provider": (identity or {}).get("provider") or os.environ.get("CTXVM_PROVIDER"),
        "budgetTokens": _state().get("budget_tokens") or _budget_from_env(),
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
        "resumeFrom": resume_from,
    }
    return meta


ENV_KEYS = [
    "CTXVM_TRACE_DIR",
    "CTXVM_TRACE_NAME",
    "CTXVM_MODEL",
    "CTXVM_PROVIDER",
    "CTXVM_AGENT_ID",
    "CTXVM_BUDGET_TOKENS",
    # W8: the paged arm's engine reads the T0 lock surface (design §5).
    "CTXVM_VBUDGET",
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


def _budget_from_settings(ctx) -> tuple:
    """Return (budget_tokens, source). Precedence: profile setting > env > 200000.

    `ctx.get_config(key)` reads `plugins.entries.<plugin_id>.settings.<key>`, which lives in the
    SERVING profile's config.yaml. That is the only per-arm declaration that survives a shared
    gateway without an env ritual, and it is the reason this function exists: a W8 pair ran at the
    200,000 default while the plan called for 24,000, because no env var was set and no setting
    existed. The source is recorded so that defect cannot be silent again.
    """
    raw = None
    try:
        raw = ctx.get_config("budgetTokens")
    except Exception:
        raw = None
    if raw is not None:
        try:
            value = int(raw)
            if value > 0:
                return value, "settings"
        except (TypeError, ValueError):
            pass
    if os.environ.get("CTXVM_BUDGET_TOKENS"):
        return _budget_from_env(), "env"
    return 200000, "default"


# W15 (RFC-0.1 §R7): the side-effect class is decided at tool REGISTRATION and
# is never inferred from model text or result content. The table mirrors
# hermes-agent's own read/search bucket (hermes-agent/model_tools.py:615,
# `_READ_SEARCH_TOOLS`) so a hermes capture reports registration-true classes.
# Everything outside the table is MUTATING — the fail-safe default; the v0.1
# consumer law treats an absent toolEffect the same way, so older producers
# replay without a safety upgrade. Audit only: no WAL, no precondition check,
# no claim that MUTATING tools are actually prevented from running.
_HERMES_READ_ONLY_TOOLS: frozenset[str] = frozenset({"read_file", "search_files"})


def _tool_effect(tool: Any) -> str:
    return "READ_ONLY" if tool in _HERMES_READ_ONLY_TOOLS else "MUTATING"


# --- W17: the coverage sidecar ----------------------------------------------
# Mirrors tools/coverage_check.py — the single authoritative checker — exactly.
# Any drift between this builder and the checker must land in the SAME card and
# in 09-plugin-parity.md §3. The manifest is written at FULL FLUSH only (never
# at write-through partials; partial pruning would leave coverage describing
# bytes that no longer exist), is NOT a tenth trace event (the sealed nine-verb
# envelope is untouched), and its digest ties it to the bytes physically
# present at the flushed path (RR-LIVE-20261104: trace names can be reused).

_HERMES_FAULT_SOURCES = ("tool_recall", "identifier_scan", "explicit_api", "semantic")
_HERMES_TOOL_EFFECTS = ("READ_ONLY", "MUTATING")


def _collision_safe_file(trace_dir: str, file: str, session_id: str) -> str:
    """Return a flush name that cannot replace another session's capture (W21).

    A reused trace name silently replaced earlier bytes at the same path
    (RR-LIVE-20261104: a post-restart capture overwrote the 13:0x evidence under
    identical filenames). The rule: if the meta sidecar at ``file`` belongs to a
    DIFFERENT session, append eight hex digits of the session id's digest. The
    same session keeps the same name, so repeated flushes stay idempotent and a
    mid-session flush still supersedes its own earlier bytes.
    """
    try:
        meta = json.loads(Path(trace_dir, f"{file}.meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return file
    owner = meta.get("sessionID") if isinstance(meta, dict) else None
    if owner in (None, session_id):
        return file
    return f"{file}-{hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:8]}"


def _per_call_samples(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One sample per turn.render, in trace order: the per-turn resident series."""
    out: List[Dict[str, Any]] = []
    for row in rows:
        if row.get("type") != "turn.render":
            continue
        sample: Dict[str, Any] = {"turn": row.get("turn"),
                                  "residentTokens": row.get("residentTokens")}
        prefix = row.get("prefix") if isinstance(row.get("prefix"), dict) else {}
        for key in ("requestChars", "approxInputTokens"):
            if isinstance(prefix.get(key), int) and not isinstance(prefix.get(key), bool):
                sample[key] = prefix[key]
        out.append(sample)
    return out


def _serving_profile() -> Optional[str]:
    """The profile this turn is being served for — not the host's own.

    `os.environ["HERMES_HOME"]` is process-wide and in the gateway names the HOST home, which
    is why a `-p w8-naive` cell recorded `.hermes` (2026-11-07). The host sets a contextvar
    per turn instead (`gateway/run.py` `_profile_runtime_scope`, "reaches the agent worker via
    copy_context()"), and `hermes_constants.get_hermes_home()` reads it first. Ask the host.
    """
    try:
        from hermes_cli.profiles import get_active_profile_name
        name = get_active_profile_name()
        if isinstance(name, str) and name.strip():
            return name.strip()
    except Exception:  # noqa: BLE001 - outside the hermes runtime
        pass
    home = os.environ.get("HERMES_HOME")
    return os.path.basename(home) if home else None


def _engine_selections_from_instance() -> Optional[int]:
    """Selections counted on the engine THIS plugin registered, if any.

    An instance attribute cannot be shared across profiles; the module global can, because
    the sibling module is imported flat. The manifest prefers the instance.
    """
    engine = _state().get("engine_obj")
    meter = getattr(engine, "_meter", None)
    if isinstance(meter, dict) and isinstance(meter.get("select"), int):
        return meter["select"]          # shared with every clone of this engine
    value = getattr(engine, "_selections", None)
    return value if isinstance(value, int) else None


def _engine_activated() -> Optional[str]:
    """Engine name only if the host actually selected with it in this process."""
    try:
        from context_engine import ACTIVATIONS
    except Exception:  # noqa: BLE001 - outside the hermes runtime the module may not exist
        return None
    count = _engine_selections_from_instance()
    if count is None:
        count = ACTIVATIONS.get("select", 0)
    return _state().get("engine_registered") if count > 0 else None


def _engine_skipped_control() -> Optional[int]:
    """Times the engine declined to act because this session's profile says compressor."""
    engine = _state().get("engine_obj")
    meter = getattr(engine, "_meter", None)
    if isinstance(meter, dict) and "skipped_control" in meter:
        return int(meter["skipped_control"])
    return 0


def _engine_selections() -> int:
    try:
        from context_engine import ACTIVATIONS
    except Exception:  # noqa: BLE001
        return 0
    count = _engine_selections_from_instance()
    return int(count if count is not None else ACTIVATIONS.get("select", 0))


def _coverage_manifest(session_id: str, file: str, trace_jsonl: str,
                       api_samples: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Build the W17 `<file>.coverage.json` body for one flushed capture.

    Session facts (environmentId/model/provider) come from the trace's own
    session.open row — never from env — so the claims are byte-true by
    construction and the checker verifies them against the same bytes. The
    instrumentation dict is lane-fixed: the hermes reference lane has no
    per-run toggles (parity test pins the constants).
    """
    rows = [json.loads(line) for line in trace_jsonl.splitlines() if line.strip()]
    open_note = [r for r in rows if r.get("type") == "session.open"]
    session_open = open_note[0] if open_note else {}
    declares = [r for r in rows if r.get("type") == "page.declare"]
    tool_results = [r for r in declares
                    if isinstance(r.get("page"), dict)
                    and r["page"].get("kind") == "tool_result"]
    faults = [r for r in rows if r.get("type") == "page.fault"]
    by_class = {k: 0 for k in _HERMES_TOOL_EFFECTS}
    for row in tool_results:
        if row.get("toolEffect") in by_class:
            by_class[row["toolEffect"]] += 1
    by_source = {k: 0 for k in _HERMES_FAULT_SOURCES}
    for row in faults:
        if row.get("source") in by_source:
            by_source[row["source"]] += 1
    turns = {r["turn"] for r in rows
             if r.get("type") == "turn.render"
             and isinstance(r.get("turn"), int) and not isinstance(r.get("turn"), bool)}
    page_ids = {(r["page"]["id"]["logicalRef"], r["page"]["id"]["contentHash"])
                for r in declares
                if isinstance(r.get("page"), dict) and isinstance(r["page"].get("id"), dict)}
    return {
        "xcabiCoverage": "0.1",
        "traceFile": f"{file}.jsonl",
        "traceDigest": hashlib.sha256(trace_jsonl.encode("utf-8")).hexdigest(),
        "session": {
            "sessionID": session_id,
            "environmentId": session_open.get("environmentId"),
            "model": session_open.get("model"),
            "provider": session_open.get("provider"),
        },
        "toolTable": {
            "readOnlyRegistered": sorted(_HERMES_READ_ONLY_TOOLS),
            "default": "MUTATING",
        },
        "instrumentation": {
            "ts": True,
            "toolEffect": True,
            "identifierScan": True,
        },
        "plugin": {
            "version": PLUGIN_VERSION,
            "harness": "hermes-python-plugin",
            "harnessVersion": os.environ.get("CTXVM_HERMES_VERSION"),
            # Arm identity (2026-11-07). The experiment's two arms differ only by the
            # profile's context.engine, and a capture that does not say which engine was
            # registered cannot be attributed afterwards — the pilot's sidecars carried no
            # such field, so a silent profile miss would have produced a full set of
            # "paged" runs that were naive runs. `engine` is the registered engine's name
            # or None; `profile` is the profile directory that served the session.
            # ACTIVATION, not construction. `build_engine()` runs unconditionally at load,
            # so engine_registered is set in every process and can never be null for the
            # naive arm (measured 2026-11-07: a -p w8-naive cell wrote "engine": "ctxvm").
            # The field now means "select_context() was called in this process", which is
            # the only behavioural evidence the plugin can offer. It is meaningful only when
            # one gateway serves one arm (plan 4c); a multiplexer serving both cannot attest
            # either, and the runner must enforce the single-arm gateway.
            "engine": _engine_activated(),
            "engineSelections": _engine_selections(),
            # The arm this SESSION belongs to, resolved from its home at hook time, and the
            # engine that profile declares. `engine` above says the process used the engine;
            # `engineSetting` says which arm asked for it. A control session with engine ctxvm
            # still shows `skippedControl > 0` and no selections.
            "profile": _state().get("serving_profile") or _serving_profile(),
            "arm": _state().get("arm"),
            "engineSetting": _state().get("engine_setting"),
            "skippedControl": _engine_skipped_control(),
            "budgetTokens": _state().get("budget_tokens") or _budget_from_env(),
            "budgetSource": _state().get("budget_source") or "default",
        },
        "captures": {
            "turns": len(turns),
            "pages": len(page_ids),
            "declares": len(declares),
            "declaresByClass": by_class,
            "faults": len(faults),
            "faultsBySource": by_source,
        },
        # The per-turn resident series, read straight out of the trace rows this sidecar
        # describes — so the claim is byte-true and coverage_check.py can verify it. Added
        # 2026-11-07 (W8 instrument fix): the emitter used to stamp every render with the
        # flush-time total, which made a long session's series flat and the NTR noise.
        "perCall": _per_call_samples(rows),
        # One sample per API request the host made (W8 instrument fix, sidecar-only): the
        # request-size series NTR is computed from. It lives here because the wire's
        # `residentTokens` is pinned to ctxvm-core's whole-table `tally_at`, and a
        # per-turn value there makes replay exit 1. Shape: turn, call (1-based within the
        # turn), and the measured counters the host exposed.
        "perApiRequest": list(api_samples or []),
    }


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
            "trace_dir": _resolve_trace_dir(os.environ.get("CTXVM_TRACE_DIR")),
            "trace_name": os.environ.get("CTXVM_TRACE_NAME"),
            "features": parse_features(os.environ.get("CTXVM_FEATURES")),
            "plugin": None,
            "resume_from": None,  # B3: CTXVM_RESUME_FROM boot check result
            # True only when /ctxvm-start or /ctxvm-trace start passed a directory;
            # a no-argument start keeps the resolved default and says so.
            "trace_dir_cmd_started": False,
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
            "last_written_events": 0,
            "flushed_sessions": set(),
        }
        setattr(sys, _STATE_ATTR, state)
    return state


def _traced() -> bool:
    """True when a trace dir is active (env or slash-command set)."""
    return bool(_active_trace_dir())


def _active_trace_dir() -> Optional[str]:
    """Active trace dir: slash-command value wins, env is the fallback."""
    state = _state()
    value = state["trace_dir"]
    if value == "":  # explicitly stopped in this process; do not fall back to env
        return None
    return value or _resolve_trace_dir(os.environ.get("CTXVM_TRACE_DIR"))


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


def _identity_from_settings(ctx: Any) -> Dict[str, str]:
    """Identity the HOST itself is configured with, from the plugin settings subtree.

    Why: hermes v0.22.5 hook payloads do not carry provider at tracer-creation time —
    ``pre_llm_call`` (turn prep, the first observed hook when ``on_session_start`` does
    not fire) sends ``model``/``platform`` only (packages/hermes/HOOKS.md §1,
    source-verified against the pinned runtime), while the ``provider`` value only
    reaches the request-side ``pre_api_request``/``post_api_request`` payloads, after
    the tracer already exists. Identity is stamped once, so the settings source exists
    so a gateway CAN complete its identity before the first request.

    Reserved-root law (found live on 2026-11-06): the host refuses a plugin settings
    key whose FIRST segment is ``model``, ``plugins``, ``security`` or ``settings``
    (``hermes_cli/plugins_state.py:17``). ``ctx.get_config("model")`` therefore raises,
    and the earlier version of this function — one try around the whole loop — aborted
    on ``model`` before it ever asked for ``provider``. The documented remedy for
    ``provider: unknown`` was dead for that reason, and the failure was invisible
    because the exception was swallowed.

    Shape now: read the one non-reserved mapping ``identity`` first, then each field in
    its own try, so a refused root is an absence for that field only. Absence is never
    fabricated; a blank or non-string value is skipped.
    """
    out: Dict[str, str] = {}
    getter = getattr(ctx, "get_config", None)
    if not callable(getter):
        return out
    try:
        identity = getter("identity")
    except Exception:
        identity = None
    if isinstance(identity, dict):
        for field in ("model", "provider"):
            value = identity.get(field)
            if isinstance(value, str) and value.strip():
                out[field] = value.strip()
    # Only `provider` is asked for bare. `model` is a reserved root on every host
    # version seen, so asking for it can only raise and log a rejection warning on
    # every load — the noise that hid this defect in the first place. Model comes
    # from the `identity` mapping or not at all.
    if "provider" not in out:
        try:
            value = getter("provider")
        except Exception:
            value = None
        if isinstance(value, str) and value.strip():
            out["provider"] = value.strip()
    return out


# W14 (RFC-0.1 §R8): environment identity. Hermes does not disclose the session's
# workspace — this plugin runs inside the gateway process, whose cwd is the
# gateway's, not the project's — so the id is taken only from an explicit
# registration value. Deriving it from a tool argument or a cwd would be
# inference, which is the one thing the capture contract forbids.
_ENVIRONMENT_ID_RE = re.compile(r"^env-[0-9a-f]{12}$")


def _environment_id() -> Optional[str]:
    """The opaque environment id, or None. A malformed value is dropped, never coerced."""
    value = (os.environ.get("CTXVM_ENVIRONMENT_ID") or "").strip()
    return value if _ENVIRONMENT_ID_RE.match(value) else None


_GIT_REMOTE_CACHE: Dict[str, str] = {}


def _normalize_remote(url: str) -> str:
    """Canonical remote form: no scheme, no credentials, no port, no `.git`, lowercase.

    `https://user:token@host/Org/Repo.git` and `git@host:Org/Repo.git` are the same
    repository and must hash to the same id — that is the whole point of normalising.
    An explicit port (`host:2222/path`) folds into the path; it is deterministic, and
    the id is only ever compared with ids produced by the same rule.
    """
    value = url.strip()
    if "://" in value:
        value = value.split("://", 1)[1]
    at = value.rfind("@")
    if at >= 0:
        value = value[at + 1 :]
    value = value.replace(":", "/", 1)
    if value.endswith(".git"):
        value = value[: -len(".git")]
    return value.lower()


def _git_remote(cwd: str) -> str:
    """`remote.origin.url` for a directory, cached and tightly bounded.

    One subprocess per directory, not per event: this runs when a session's tracer is
    created. A missing git, a non-repo, or a timeout all yield "" and the caller falls
    back to the path basis.
    """
    if cwd in _GIT_REMOTE_CACHE:
        return _GIT_REMOTE_CACHE[cwd]
    remote = ""
    try:
        import shutil
        import subprocess

        if shutil.which("git"):
            done = subprocess.run(
                ["git", "-C", cwd, "config", "--get", "remote.origin.url"],
                capture_output=True, text=True, timeout=1.5,
            )
            if done.returncode == 0:
                remote = done.stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):  # type: ignore[name-defined]
        remote = ""
    _GIT_REMOTE_CACHE[cwd] = remote
    return remote


def _derive_environment_id(cwd: str) -> Optional[str]:
    """W14 §R8 digest-only environment id for a workspace path.

    `env-` + 12 hex of sha256 over `remote:<normalized remote>` when the directory is a
    clone with an origin, else `path:<absolute path>`. Only the digest is emitted; the
    path and the remote never reach the trace.
    """
    if not cwd:
        return None
    try:
        resolved = str(Path(cwd).resolve())
    except OSError:
        return None
    if not os.path.isdir(resolved):
        return None
    remote = _git_remote(resolved)
    basis = f"remote:{_normalize_remote(remote)}" if remote else f"path:{resolved}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    return f"env-{digest[:12]}"


def _session_environment_id(session_id: str) -> Optional[str]:
    """Per-session environment id: explicit registration wins, else the host's workspace.

    Hermes exposes the calling session's recorded working directory to a plugin handle
    (`ctx.session_cwd()` — hermes_cli/plugins.py:605, backed by hermes_cli/plugin_session.py
    whose docstring says explicitly it is "never the gateway process's own cwd"). That is
    a host-owned fact, so deriving from it is registration, not inference. An empty
    string means the host records none, and then the key is absent.
    """
    explicit = _environment_id()
    if explicit:
        return explicit
    cache = _state().setdefault("env_by_session", {})
    if session_id in cache:
        return cache[session_id]
    derived: Optional[str] = None
    ctx = _state().get("ctx")
    getter = getattr(ctx, "session_cwd", None) if ctx is not None else None
    if callable(getter):
        try:
            cwd = getter()
        except Exception:  # fail-open: a hook must never raise into the host
            cwd = ""
        if isinstance(cwd, str):
            derived = _derive_environment_id(cwd)
    cache[session_id] = derived
    return derived

def _make_plugin() -> Optional[Any]:
    """Create a tracer plugin if tracing is enabled; None otherwise.

    Identity priority: hook payload (the plugin-level law) > host-owned plugin
    settings (ctx_identity stashed at register) > CTXVM_* env > 'unknown'.
    Settings outrank env because they are the running gateway's own declared
    configuration, while env may be an artifact of an unrelated shell.
    """
    if not _traced():
        return None
    identity = _state().get("ctx_identity") or {}
    return create_ctxvm_plugin({
        "agentId": os.environ.get("CTXVM_AGENT_ID", "hermes"),
        "model": identity.get("model") or os.environ.get("CTXVM_MODEL", "unknown/unknown"),
        "provider": identity.get("provider") or os.environ.get("CTXVM_PROVIDER", "unknown"),
        "budgetTokens": _state().get("budget_tokens") or _budget_from_env(),
        "environmentId": _environment_id(),
    })


def register(ctx) -> None:
    """Hermes plugin entry point. Hooks always registered; tracing gated lazily."""
    state = _state()
    state["register_calls"] += 1
    # The plugin handle is how the host exposes per-session facts (session_cwd), so keep it.
    state["ctx"] = ctx
    state["ctx_identity"] = _identity_from_settings(ctx)
    _witness(f"init name={state.get('trace_name') or os.environ.get('CTXVM_TRACE_NAME') or '<session-id>'}")
    if state["ctx_identity"]:
        _witness(f"settings identity={state['ctx_identity']}")
    stats = state["stats"]
    features = _features()  # parsed once; UC modules read it via _enabled_stubs()
    state["ucs"] = {
        "uc1-handoff": UC1Handoff(),
        "uc2-forensics": UC2Forensics(),
        "uc3-planner": UC3Planner(),
    }

    # --- B3 resume: CTXVM_RESUME_FROM boot check ---------------------------
    # With CTXVM_RESUME_FROM=<snapshot dir>, verify the snapshot BEFORE the
    # first model request: manifest + checksums, replay exit 0 at turn N,
    # shared-prefix diff relation. Any failure = loud witness line, tracer
    # continues UNVERIFIED (never blocks the agent loop).
    resume_from_env = os.environ.get("CTXVM_RESUME_FROM")
    if resume_from_env:
        uc1 = state["ucs"].get("uc1-handoff")
        if uc1 is not None:
            resume_result = uc1.resume(resume_from_env)
            state["resume_from"] = resume_result.get("evidence", {})
            _witness(
                f"resume_from={resume_from_env} "
                f"verified={resume_result.get('verified')} "
                f"reason={resume_result.get('reason')}"
            )
            # §3(3)(4) surfacing (UC1-VERIFY-CHECKS): on a verified snapshot
            # the operator sees the projection (fidelity reference) and the
            # diff relation (law-aware: era `identical` required, derivedFrom
            # diagnostic only, no source = skipped). Failures stay loud via
            # the reason line. Python-style rendering so the witness logs
            # byte-match across harnesses (mirrored: live/ctxvm.ts).
            if resume_result.get("verified"):
                ev = resume_result.get("evidence", {})
                proj = ev.get("projection")
                if proj:
                    _witness(
                        f"projection: {proj.get('slots')} slot(s) "
                        f"at turn {proj.get('turn')}"
                    )
                diff = ev.get("diff")
                _witness(
                    f"diff: source={diff['source']} relation={diff['relation']}"
                    if diff
                    else "diff: skipped — no source slice on disk"
                )
            if not resume_result.get("verified"):
                _witness(
                    f"resume_from={resume_from_env} UNVERIFIED — "
                    f"tracer continues, snapshot not trusted"
                )
        else:
            _witness(
                f"resume_from={resume_from_env} uc1-handoff module not "
                f"available (is CTXVM_FEATURES=handoff set?)"
            )

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
        _ensure_trace_dir(trace_dir)
        trace = tracer.finish()
        file = _collision_safe_file(trace_dir, _flush_base() or session_id, session_id)
        jsonl_path = Path(trace_dir) / f"{file}.jsonl"
        meta_path = Path(trace_dir) / f"{file}.meta.json"
        jsonl_path.write_text(trace.jsonl, encoding="utf-8")
        _witness(f"flush {file}.jsonl bytes={len(trace.jsonl)} session={session_id}")
        meta_path.write_text(
            json.dumps(
                _canon_meta(
                    session_id, stats, trace.stats,
                    resume_from=state.get("resume_from"),
                    identity=_tracer_identity(tracer),
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _flush_traces() -> int:
        """Write all finished tracers to the active trace dir; return how many."""
        features = _features()
        vm = _ensure_plugin()
        trace_dir = _active_trace_dir()
        written = 0
        keep_name: Optional[str] = None
        if vm is not None and trace_dir:
            _ensure_trace_dir(trace_dir)
            base = _flush_base()
            finished = vm.finish_all()
            for record in finished:
                session_id = record["sessionID"]
                trace = record["trace"]
                file = _collision_safe_file(trace_dir, base or session_id, session_id)
                keep_name = f"{file}.jsonl"
                Path(trace_dir, f"{file}.jsonl").write_text(
                    trace.jsonl, encoding="utf-8"
                )
                written += 1
                _witness(f"flush {file}.jsonl bytes={len(trace.jsonl)} session={session_id}")
                Path(trace_dir, f"{file}.meta.json").write_text(
                    json.dumps(
                        _canon_meta(
                            session_id, stats, trace.stats,
                            resume_from=state.get("resume_from"),
                            identity=_tracer_identity(vm.tracer_for(session_id)),
                        ),
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                # W17: the coverage sidecar rides every FULL flush, last slot —
                # its digest ties it to the jsonl bytes just written. Write-
                # through partials never write coverage (the partial is what a
                # later full flush supersedes).
                Path(trace_dir, f"{file}.coverage.json").write_text(
                    json.dumps(
                        _coverage_manifest(
                            session_id, file, trace.jsonl,
                            api_samples=(vm.tracer_for(session_id).api_samples()
                                         if hasattr(vm.tracer_for(session_id), "api_samples")
                                         else None),
                        ),
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                # Track flushed sessions so write-through partials are not recreated.
                # The tracer is intentionally kept so multi-turn sessions accumulate;
                # _evict_stale_tracers releases it once the session has gone quiet.
                state.setdefault("flushed_sessions", set()).add(session_id)
                state.setdefault("flushed_at", {})[session_id] = time.time()
        # A complete capture supersedes its partial snapshot, and the directory is
        # pruned so default-ON capture cannot grow without bound.
        if trace_dir:
            partial_jsonl = list(Path(trace_dir).glob("*.partial.jsonl"))
            for path in partial_jsonl:
                for victim in (path, path.with_name(path.name[: -len(".jsonl")] + ".meta.json")):
                    try:
                        victim.unlink()
                    except OSError:
                        pass
            _prune_traces(trace_dir, keep=keep_name)
        _evict_stale_tracers(vm)
        # UC stubs flush (no-op for current stubs; real UCs write artefacts)
        for uc in _enabled_stubs(features):
            uc.flush()
        return written

    # --- Hook handlers ------------------------------------------------------

    def _stamp_environment(kwargs: Dict[str, Any]) -> None:
        """Attach the session's environment id to a hook payload, if one is derivable.

        Every hook carries `session_id`, and `on_session_start` does not fire in every
        build — so the stamp cannot live there alone; whichever hook creates the tracer
        first must carry the key.
        """
        session_id = kwargs.get("session_id", "") or ""
        environment = _session_environment_id(session_id)
        if environment:
            kwargs["environmentId"] = environment
        # Same law as the environment id: whichever hook fires first must carry the profile,
        # because the flush happens after the turn's profile scope has been reset.
        # Resolved from the SESSION's home (contextvar-aware), not from the process: one gateway
        # serves every profile, so a value captured at registration is the wrong arm for all but
        # one of them (measured 2026-11-11: naive reported `ctxvm` and `70000/settings`).
        try:
            from profile_policy import policy as _policy_for_turn
            pol = _policy_for_turn()
        except Exception:  # noqa: BLE001
            pol = None
        st = _state()
        # A policy whose home is not on disk is not a session (the plugin's own tests, or a host
        # that has not created the home yet); fall back to what the hook reported.
        if pol and os.path.isdir(pol.get("home") or ""):
            st["serving_profile"] = pol["profile"]
            st["budget_tokens"] = pol["budget"]
            st["budget_source"] = pol["budgetSource"]
            st["arm"] = pol["arm"]
            st["engine_setting"] = pol["engine"]
        elif not st.get("serving_profile"):
            st["serving_profile"] = _serving_profile()

    def on_session_start(**kwargs: Any) -> None:
        _stamp_environment(kwargs)
        stats["session_starts"] += 1
        _witness(f"session_start identity={identity_from_payload(kwargs)}")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_session_start(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_session_start(kwargs)

    def on_pre_tool_call(**kwargs: Any) -> None:
        _stamp_environment(kwargs)
        stats["pre_tool_calls"] += 1
        # W17: the same effective-name law as the post path — live payloads
        # name the tool via `tool_name`, and the witness must show the tool
        # the run actually rendered, not a synthetic-key absence.
        _witness(f"before tool={kwargs.get('tool') or kwargs.get('tool_name')}")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_tool_call(kwargs)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_pre_tool_call(kwargs)

    def on_post_tool_call(**kwargs: Any) -> None:
        _stamp_environment(kwargs)
        stats["post_tool_calls"] += 1
        status = kwargs.get("status")
        # W17 (found by tools/coverage_check.py against real round-trip bytes):
        # the live payload carries the tool under `tool_name` (HOOKS.md hook
        # table; 447 witness rows read `after tool=None` while the refs named
        # the tool fine through the adapter's own fallback) — so the class
        # stamp must read the SAME effective name the adapter's ref-builder
        # uses, or every live hermes capture classified as MUTATING.
        tool = kwargs.get("tool") or kwargs.get("tool_name")
        _witness(f"after tool={tool} status={status}")
        if status not in ("ok", "completed"):
            stats["errored"] += 1
        else:
            stats["completed"] += 1
        # W15 (§R7): tag the class at registration time, on the payload the
        # core receives; the core forwards it verbatim and classifies nothing.
        kwargs["toolEffect"] = _tool_effect(tool)
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_post_tool_call(kwargs)
            _maybe_write_through(vm, stats)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_post_tool_call(kwargs)

    def on_pre_llm_call(**kwargs: Any) -> None:
        _stamp_environment(kwargs)
        stats["pre_llm_calls"] += 1
        _witness("pre_llm (context)")
        features = _features()
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_llm_call(kwargs)
            _maybe_write_through(vm, stats)
        elif TRACE_FEATURE in features:
            stats["skipped_untraced"] += 1
        for uc in _enabled_stubs(features):
            uc.on_pre_llm_call(kwargs)

    def on_session_end(**kwargs: Any) -> None:
        _stamp_environment(kwargs)
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
                "  stop                — flush; env-configured capture stays armed\n"
                "  stop --hard         — flush and disable capture in this process\n"
                "  status              — show whether tracing is active"
            )

        sub = argv[0].lower()

        if sub == "start":
            # No argument is the normal case: the default state dir (or
            # CTXVM_TRACE_DIR) already resolved at import. Passing a dir is the
            # override, not the requirement.
            raw_dir = argv[1] if len(argv) > 1 else None
            if raw_dir is None:
                # No argument: keep the directory already resolved for this process
                # (env, or the default). After a stop the sentinel is empty, so
                # fall back to re-resolving the default.
                resolved = state["trace_dir"] or _resolve_trace_dir(None)
            else:
                resolved = _resolve_trace_dir(raw_dir)
            if not resolved:
                return "ctxvm-trace: refusing an empty/disabled dir — pass a path"
            state["trace_dir"] = resolved
            # A no-argument start records the resolved default; say so instead of
            # calling it a command override.
            state["trace_dir_cmd_started"] = raw_dir is not None
            if len(argv) > 2:
                state["trace_name"] = argv[2]
            # Fresh plugin so a new dir never inherits another dir's tracers.
            state["plugin"] = None
            return (
                f"ctxvm-trace: tracing enabled, dir={state['trace_dir']} "
                f"(source: {_trace_dir_source()}), "
                f"name={state['trace_name'] or '<session-id>'}"
            )

        if sub == "stop":
            # Semantics (2026-11-07): a gateway serves many sessions from one process.
            # Capture configured by the DEPLOYMENT's environment is not one session's
            # preference, so stop flushes and then falls back to the env instead of
            # disabling the process. A silent disable looks like a quiet system, not a
            # stopped one: it cost an afternoon of "no captures" on 2026-11-07, with
            # every -z run in that process writing nothing while the env said otherwise.
            hard = "--hard" in argv[1:]
            _witness("trace stop -> flush all tracers" + (" (hard)" if hard else ""))
            written = _flush_traces()
            env_dir = _resolve_trace_dir(os.environ.get("CTXVM_TRACE_DIR"))
            command_started = bool(state.get("trace_dir_cmd_started"))
            state["plugin"] = None
            if env_dir and not command_started and not hard:
                state["trace_dir"] = None   # drop any override; env is the fallback again
                state["trace_name"] = os.environ.get("CTXVM_TRACE_NAME") or ""
                return (
                    f"ctxvm-trace: {written} trace(s) flushed; capture STAYS ARMED from the "
                    f"environment at {env_dir} (this process serves many sessions — use "
                    f"/ctxvm-trace stop --hard to silence it)."
                )
            state["trace_dir"] = ""   # sentinel: disabled in this process
            if written:
                return f"ctxvm-trace: tracing stopped, {written} trace(s) flushed."
            return (
                "ctxvm-trace: tracing stopped; nothing was pending to flush. Each session "
                "flushes at its own end, so this is normal when every session already "
                "closed — it does not mean no events were captured."
            )

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
                f"dir={_active_trace_dir() or '<none>'} "
                f"(source: {_trace_dir_source()}), "
                f"name={state['trace_name'] or '<session-id>'}, "
                f"version={PLUGIN_VERSION}, "
                f"register_calls={state['register_calls']}, "
                f"{detail}"
            )

        return (
            f"Unknown subcommand '{sub}'. "
            "Usage: /ctxvm-trace start <dir> [name] | stop | status"
        )


    # ---------------------------------------------------------------------
    # /ctxvm-help — one command earns its keep only if a user can find out
    # what the others do without reading this file.
    # ---------------------------------------------------------------------

    HELP_TOPICS: Dict[str, Dict[str, str]] = {
        "ctxvm-start": {
            "usage": "/ctxvm-start [dir] [name]",
            "summary": "Start tracing. No arguments uses the configured defaults.",
            "detail": (
                "Starts capture for this gateway process.\n"
                "\n"
                "With no arguments: the directory is CTXVM_TRACE_DIR when set, otherwise\n"
                "  ${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces (created 0700), and the\n"
                "  file name is CTXVM_TRACE_NAME when set, otherwise <session-id>.\n"
                "With a directory: that path wins, expanded (~ and $VARs) and resolved.\n"
                "With a name too: the capture is written to <dir>/<name>.jsonl.\n"
                "\n"
                "Capture is already on by default; this command is for starting after a\n"
                "stop, or redirecting output. /ctxvm-trace start does the same thing."
            ),
        },
        "ctxvm-trace": {
            "usage": "/ctxvm-trace start [dir] [name] | stop | status",
            "summary": "Start, stop or inspect capture; status shows the resolved dir and its source.",
            "detail": (
                "start  — same as /ctxvm-start; a fresh tracer, so a new dir never inherits\n"
                "         another dir's sessions.\n"
                "stop   — flush every tracer. When the deployment sets CTXVM_TRACE_DIR,\n"
                "         capture STAYS ARMED afterwards: one gateway process serves many\n"
                "         sessions, so a single session's stop must not silence the rest.\n"
                "stop --hard\n"
                "         flush and disable capture in this process regardless of the env.\n"
                "         The count is honest: nothing pending is not 'nothing captured' —\n"
                "         each session flushes at its own end.\n"
                "status — enabled, resolved directory and WHERE it came from (env, default,\n"
                "         or a start argument), name, plugin version, per-session event and\n"
                "         page counts."
            ),
        },
        "ctxvm-forensics": {
            "usage": "/ctxvm-forensics replay|profile|diff|export|diagnose <trace...>",
            "summary": "Run the offline engine on a trace (only when CTXVM_FEATURES~forensics).",
            "detail": (
                "Spawns the Rust binaries on a trace file; nothing here touches the live\n"
                "session.\n"
                "  replay   — re-derive the page table and report divergences (exit 0 = none)\n"
                "  profile  — per-page decision history, faults, per-turn residency\n"
                "  diff     — compare two traces under the law-aware relation\n"
                "  export   — write a slice/package of a trace\n"
                "  diagnose — UC2 fault diagnosis for one turn\n"
                "Enable with CTXVM_FEATURES=forensics (or handoff,forensics)."
            ),
        },
        "ctxvm-handoff": {
            "usage": "/ctxvm-handoff [turn]",
            "summary": "Pause: flush, snapshot the era, and package a handoff (CTXVM_FEATURES~handoff).",
            "detail": (
                "Writes a snapshot directory (trace-N.jsonl.zst + checksums + manifest) that\n"
                "/ctxvm-resume can verify later. Flush happens first, so the package is never\n"
                "ahead of the trace. With a turn, packages at that turn boundary."
            ),
        },
        "ctxvm-resume": {
            "usage": "/ctxvm-resume <snapshot-dir>",
            "summary": "Verified boot: check a paused snapshot and continue from it.",
            "detail": (
                "Verifies checksums byte-level, cross-checks the manifest sliceTurn, runs a\n"
                "replay counterproof and reports the diff relation and projection. Any failure\n"
                "returns verified=false with the reason — it never blocks the agent loop."
            ),
        },
        "environment": {
            "usage": "/ctxvm-help environment",
            "summary": "Every CTXVM_* variable this plugin reads, with its value and default.",
            "detail": (
                "Prints each variable with what it currently holds, what the plugin falls back\n"
                "to, and what it changes. Also shows the resolved trace directory and whether\n"
                "capture is on, so a wrong setting is visible rather than inferred."
            ),
        },
    }

    # (name, default, what it does) — read from this module, not from memory.
    ENV_TOPICS: List[tuple] = [
        ("CTXVM_TRACE", "on", "0/off/false/no disables capture outright"),
        ("CTXVM_TRACE_DIR", "<state>/ctxvm/traces", "capture directory; ~ and $VAR expand"),
        ("CTXVM_TRACE_NAME", "<session-id>", "file stem for this capture"),
        ("CTXVM_TRACE_TS", "on", "0 drops every ts (byte-stability only)"),
        ("CTXVM_TRACE_WRITETHROUGH", "on", "persist a partial every N events"),
        ("CTXVM_TRACE_WRITETHROUGH_EVERY", "10", "events between partial snapshots"),
        ("CTXVM_TRACE_RETAIN_MAX", "200", "complete captures kept"),
        ("CTXVM_TRACE_RETAIN_DAYS", "30", "age limit for complete captures"),
        ("CTXVM_TRACE_RETAIN_BYTES", "536870912", "byte budget for complete captures"),
        ("CTXVM_ENVIRONMENT_ID", "unset", "env-<12 hex>; hermes cannot derive it, so this is the only source"),
        ("CTXVM_AGENT_ID", "hermes", "agentId on session.open"),
        ("CTXVM_MODEL", "unknown/unknown", "fallback model when the host payload has none"),
        ("CTXVM_PROVIDER", "unknown", "fallback provider when the host payload has none"),
        ("CTXVM_BUDGET_TOKENS", "200000", "declared page budget (drives turn.render headroom)"),
        ("CTXVM_VBUDGET", "24000 (preregistered)", "W8 paged arm: conf/raises only — a value below 24000 is refused and flagged"),
        ("CTXVM_FEATURES", "unset", "comma list: forensics, handoff"),
        ("CTXVM_HANDOFF_DIR", "unset", "where /ctxvm-handoff packages"),
        ("CTXVM_RESUME_FROM", "unset", "snapshot to verify at boot"),
    ]

    def _env_report() -> str:
        def effective(name: str, default: str) -> str:
            raw = os.environ.get(name)
            if raw is None:
                return f"unset -> {default}"
            if raw.strip() == "":
                return "empty -> disabled" if name in ("CTXVM_TRACE", "CTXVM_TRACE_DIR") else "empty -> default"
            return raw

        lines = [
            "ctxvm environment (read once at import; a gateway restart is required after a change)",
            f"  capture enabled: {_traced()}",
            f"  trace dir:       {_active_trace_dir() or '<none>'} (source: {_trace_dir_source()})",
            "",
            "  variable                            value                       effect",
        ]
        for name, default, effect in ENV_TOPICS:
            lines.append(f"  {name:<34}  {effective(name, default):<26}  {effect}")
        return "\n".join(lines)

    def _handle_help_cmd(raw_args: str) -> str:
        argv = raw_args.strip().split()
        if not argv:
            lines = ["ctxvm — commands (details: /ctxvm-help <command>)", ""]
            for name, topic in HELP_TOPICS.items():
                lines.append(f"  {topic['usage']}")
                lines.append(f"      {topic['summary']}")
            return "\n".join(lines)

        topic_key = argv[0].lower().lstrip("/")
        if topic_key in ("env", "environment", "envvars", "vars"):
            return _env_report()
        topic = HELP_TOPICS.get(topic_key)
        if topic is None:
            known = ", ".join(HELP_TOPICS)
            return f"ctxvm-help: no topic '{argv[0]}'\n  known: {known}"

        head = f"{topic['usage']}\n\n{topic['summary']}\n\n{topic['detail']}"
        if topic_key == "environment":
            head += "\n\n" + _env_report()
        return head

    def _handle_start_cmd(raw_args: str) -> str:
        """Start capture; arguments are optional overrides."""
        return _handle_trace_cmd(("start " + raw_args).strip())

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

        _flush_traces()  # flush live tracers before packaging (docstring promise)
        result = uc1.pause(trace_dir, turn=turn, handoff_name=_flush_base())
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

    def _handle_resume_cmd(raw_args: str) -> str:
        """Handle /ctxvm-resume <snapshot-dir>.

        Verified-boot resume: verify a paused snapshot (checksums byte-level,
        manifest sliceTurn cross-check, replay counterproof, law-aware diff
        relation, projection surfacing) and print a brief result.
        Never blocks the agent loop: any failure returns verified=False with a
        loud reason.
        """
        argv = raw_args.strip().split()
        if not argv:
            return (
                "Usage: /ctxvm-resume <snapshot-dir>\n"
                "  <snapshot-dir> — directory of a paused handoff snapshot\n"
                "  (contains trace-N.jsonl.zst, checksums.sha256, manifest.yaml)\n"
            )
        snapshot_dir = argv[0]
        ucs = _state().get("ucs", {})
        uc1 = ucs.get("uc1-handoff")
        if uc1 is None:
            return ("ctxvm-resume: UC1 module not available "
                    "(is CTXVM_FEATURES=handoff set?)")
        result = uc1.resume(snapshot_dir)
        if not isinstance(result, dict):
            return f"ctxvm-resume: {result}"
        verified = result.get("verified", False)
        reason = result.get("reason", "")
        ev = result.get("evidence", {})
        digest = ev.get("snapshotDigest", "")
        proj = ev.get("projection")
        diff = ev.get("diff")
        lines = [
            f"ctxvm-resume: exit_code={result.get('exit_code')} "
            f"verified={verified}",
            f"  reason: {reason}",
        ]
        if digest:
            lines.append(f"  snapshotDigest: {digest}")
        if proj:
            lines.append(f"  projection: {proj.get('slots')} slot(s) at turn {proj.get('turn')}")
        if diff:
            lines.append(f"  diff: source={diff.get('source')} relation={diff.get('relation')}")
        return "\n".join(lines)

    # Register hooks (always; tracing gated lazily inside each handler)
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
    def on_pre_api_request(**kwargs: Any) -> None:
        """W13: the request the model is about to receive — static cost, per turn."""
        _stamp_environment(kwargs)
        stats["events_seen"] = stats.get("events_seen", 0) + 1
        if not _traced():
            return
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_pre_api_request(kwargs)
            _maybe_write_through(vm, stats)

    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_api_request", on_pre_api_request)

    def on_post_api_request(**kwargs: Any) -> None:
        """W8 D12: the provider's own receipt — strict intake, absence is not a zero."""
        stats["events_seen"] = stats.get("events_seen", 0) + 1
        if not _traced():
            return
        vm = _ensure_plugin()
        if vm is not None:
            vm.on_post_api_request(kwargs)

    ctx.register_hook("post_api_request", on_post_api_request)

    ctx.register_hook("on_session_end", on_session_end)

    # Register slash command for runtime start/stop/status
    ctx.register_command(
        "ctxvm-trace",
        _handle_trace_cmd,
        description="Start/stop/show ctxvm trace capture.",
    )

    ctx.register_command(
        "ctxvm-help",
        _handle_help_cmd,
        description="ctxvm commands; /ctxvm-help <command> for detail, /ctxvm-help environment for settings.",
    )

    ctx.register_command(
        "ctxvm-start",
        _handle_start_cmd,
        description="Start ctxvm capture with the configured defaults (optional dir/name override).",
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

    # Register slash command for UC1 verified-boot resume: verify snapshot, print brief result
    if HANDOFF_FEATURE in _features():
        ctx.register_command(
            "ctxvm-resume",
            _handle_resume_cmd,
            description="UC1 resume: verified-boot a paused snapshot, print brief result.",
        )

    # --- W8 gate 3: register the paged arm's context engine (fail-open) ----
    # design/w8-capture-design.md §3.3: the host activates the engine ONLY
    # when a profile carries `context.engine: "ctxvm"` (the naive arm runs the
    # default profile — the one-factor design). Outside the hermes runtime
    # (the plugin's own test suite) build_engine() returns None and nothing
    # registers; a host that refuses the registration must never break the
    # observer duties — the hooks above stay fully functional either way.
    try:
        from context_engine import build_engine  # live/-sibling, flat import
        # No budget at registration: one gateway serves every profile, so a snapshot taken here is
        # the wrong arm for all but one session. The engine resolves it per call (profile_policy).
        _v_budget_at_load, _budget_source_at_load = _budget_from_settings(ctx)
        engine = build_engine(v_budget=None)
        if engine is not None and hasattr(ctx, "register_context_engine"):
            ctx.register_context_engine(engine)
            state["engine_obj"] = engine
            state["engine_registered"] = engine.name
            state["budget_tokens"] = _v_budget_at_load
            state["budget_source"] = _budget_source_at_load
            # NOTE (0.10.8, falsified the same day): `ctx.get_config(key)` reads
            # `plugins.entries.<plugin_id>.settings.<key>`, NOT the profile's top-level
            # `context.engine`. Measured on a live `-p w8-paged` probe: the field came back null
            # for a profile whose config says "ctxvm". There is no public accessor for the
            # profile's engine setting, so the sidecar does not pretend to have one — attribution
            # stays with the runner's ledger plus the engine's own activation count on a real cell.
            _witness(f"engine={engine.name} registered")
    except Exception as exc:  # noqa: BLE001 - fail-open is the design law here
        state["engine_registered"] = None
        _witness(f"engine_register=skip reason={type(exc).__name__}: {exc}")

    # Register cleanup on plugin unload
    ctx.on_unload(lambda: _flush_traces())

    # Flush on process exit too. Guarded by process-global state so repeated
    # register() calls cannot stack duplicate atexit handlers.
    if not state.get("atexit_registered"):
        state["atexit_registered"] = True
        import atexit
        atexit.register(_flush_traces)