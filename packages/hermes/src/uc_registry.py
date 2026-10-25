"""
ctxvm use-case registry — CTXVM_FEATURES gating + UC module dispatch base.

KIT-1 org decision (09-plugin-parity.md §1): use cases are CTXVM_FEATURES-gated
submodules inside each plugin, dispatched by a thin live/ entry. This file
defines the shared registry surface:

- FEATURE_* constants (trace, uc1-handoff, uc2-forensics, uc3-planner)
- parse_features(raw) -> set[str]       (default {trace})
- is_enabled(features, feature) -> bool
- UCModule base class                   (no-op hook handlers, .flush())

Concrete UC modules live in their own files:
  src/uc1_handoff.py  -> UC1Handoff
  src/uc2_forensics.py -> UC2Forensics
  src/uc3_planner.py  -> UC3Planner

The `trace` UC (the existing @ctxvm/node-equivalent tracer in src/plugin.py)
is the default, always-on feature. It is wired inline in live/__init__.py
rather than as a separate module file, to keep the capture path byte-compatible
and avoid a risky refactor of working tracer code.
"""

from __future__ import annotations

from typing import Any, Dict, Set

TRACE_FEATURE = "trace"
UC1_FEATURE = "uc1-handoff"
UC2_FEATURE = "uc2-forensics"
UC3_FEATURE = "uc3-planner"
HANDOFF_FEATURE = "handoff"

ALL_UC_FEATURES = frozenset({UC1_FEATURE, UC2_FEATURE, UC3_FEATURE, HANDOFF_FEATURE})
ALL_FEATURES = frozenset({TRACE_FEATURE, *ALL_UC_FEATURES})


def parse_features(raw: str | None) -> Set[str]:
    """Parse CTXVM_FEATURES into a feature set.

    Comma/whitespace-separated, case-insensitive, duplicates collapsed.
    Unrecognized names are silently ignored (forward compatibility). When the
    env is unset or empty, the default feature set is {trace} so existing
    deployments keep working unchanged.
    """
    if not raw or not raw.strip():
        return {TRACE_FEATURE}
    parsed = {f.strip().lower() for f in raw.split(",") if f.strip()}
    # Keep only known features; ignore unrecognized ones for forward compatibility.
    return parsed & ALL_FEATURES


def is_enabled(features: Set[str], feature: str) -> bool:
    return feature in features


class UCModule:
    """Base interface for a ctxvm use-case submodule.

    All hook handlers are no-ops by default; concrete UCs override the ones
    they care about. ``flush`` is called on session end / unload / atexit so
    a UC can write its own artefacts (none for stubs).
    """

    name: str = "uc-base"
    feature: str | None = None  # None => always-on (the trace UC)

    def enabled(self, features: Set[str]) -> bool:
        if self.feature is None:
            return True
        return self.feature in features

    # --- Hook dispatch (all no-op by default) -----------------------------
    def on_session_start(self, payload: Dict[str, Any]) -> None:
        return None

    def on_pre_tool_call(self, payload: Dict[str, Any]) -> None:
        return None

    def on_post_tool_call(self, payload: Dict[str, Any]) -> None:
        return None

    def on_pre_llm_call(self, payload: Dict[str, Any]) -> None:
        return None

    def on_session_end(self, payload: Dict[str, Any]) -> None:
        return None

    def flush(self) -> None:
        return None
