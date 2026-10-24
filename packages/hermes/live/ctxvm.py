"""
T17 live adapter re-export — mirrors T12's `packages/opencode/live/ctxvm.ts` pattern.

Hermes plugins are Python, so this module re-exports the plugin's `register`
from ``__init__.py`` for naming consistency with the OpenCode adapter. The actual
plugin logic lives in ``packages/hermes/live/__init__.py`` (Hermes hook wiring)
and ``packages/hermes/src/plugin.py`` (tracer core, ported from @ctxvm/node).
"""

from . import register  # noqa: F401
from . import _clear_env_for_tests  # noqa: F401

__all__ = ["register", "_clear_env_for_tests"]
