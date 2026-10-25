"""
ORG-1 UC1 handoff pause tests — CTXVM_FEATURES-gated UC1 handoff submodule.

Tests the UC1Handoff class: pause (flush → era snapshot → export package)
wrapping the committed Rust CLI binaries.

Run: python test/test_uc1_handoff.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Make packages/hermes/src and packages/hermes importable
_HERMES_ROOT = str(Path(__file__).resolve().parents[1])
_HERMES_SRC = str(Path(__file__).resolve().parents[1] / "src")
for _p in (_HERMES_ROOT, _HERMES_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import live  # noqa: E402  (after sys.path insert)
from live import _clear_env_for_tests, register  # noqa: E402
from uc1_handoff import UC1Handoff  # noqa: E402
from uc_registry import (  # noqa: E402
    HANDOFF_FEATURE,
    TRACE_FEATURE,
    parse_features,
)


class UC1HandoffTests(unittest.TestCase):
    """UC1Handoff wrapper methods — shell out to Rust binaries."""

    def setUp(self):
        _clear_env_for_tests()

    def test_uc1_handoff_instantiation(self):
        """UC1Handoff is a UCModule with name uc1-handoff and feature handoff."""
        uc1 = UC1Handoff()
        self.assertEqual(uc1.name, "uc1-handoff")
        self.assertEqual(uc1.feature, HANDOFF_FEATURE)
        self.assertTrue(uc1.enabled({HANDOFF_FEATURE}))
        self.assertFalse(uc1.enabled({TRACE_FEATURE}))
        self.assertFalse(uc1.enabled(set()))

    def test_pause_returns_dict(self):
        """pause() returns a dict with exit_code, snapshot, report, stderr."""
        uc1 = UC1Handoff()
        with tempfile.TemporaryDirectory() as td:
            result = uc1.pause(td, turn=3)
        self.assertIn("exit_code", result)
        self.assertIn("snapshot", result)
        self.assertIn("report", result)
        self.assertIn("stderr", result)
        self.assertIn("verified", result)
        self.assertIn("divergences", result)
        self.assertIn("witness", result)

    def test_pause_missing_binary_returns_exit_2(self):
        """pause() returns exit_code 2 when binary or trace is missing."""
        uc1 = UC1Handoff()
        with tempfile.TemporaryDirectory() as td:
            result = uc1.pause(td)
        # binary or trace missing → exit 2
        self.assertEqual(result["exit_code"], 2)
        self.assertTrue(
            "binary not found" in result["stderr"]
            or "cannot read" in result["stderr"],
            f"unexpected stderr: {result['stderr']}",
        )

    def test_parse_features_includes_handoff(self):
        """parse_features recognizes handoff as a known feature."""
        self.assertEqual(
            parse_features("trace,handoff"),
            {TRACE_FEATURE, HANDOFF_FEATURE},
        )
        self.assertEqual(
            parse_features("handoff"),
            {HANDOFF_FEATURE},
        )


class UC1DispatcherTests(unittest.TestCase):
    """live/register() dispatches /ctxvm-handoff slash command when handoff feature is enabled."""

    def setUp(self):
        _clear_env_for_tests()

    def _make_ctx(self):
        calls = []

        class FakeCtx:
            def __init__(self):
                self.calls = calls

            def register_hook(self, name, cb):
                self.calls.append(("hook", name))
                return lambda: None

            def on_unload(self, cb):
                self.calls.append(("unload", cb.__name__))
                return None

            def register_command(self, name, handler, description=""):
                self.calls.append(("command", name))
                self.handler = handler
                return None

        return FakeCtx(), calls

    def test_handoff_command_registered_with_feature(self):
        """With CTXVM_FEATURES=handoff, /ctxvm-handoff command is registered."""
        os.environ["CTXVM_FEATURES"] = "handoff"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertIn(("command", "ctxvm-handoff"), calls)
        self.assertIsNotNone(ctx.handler)

    def test_handoff_command_not_registered_without_feature(self):
        """Without CTXVM_FEATURES=handoff, no ctxvm-handoff command."""
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertNotIn(("command", "ctxvm-handoff"), calls)

    def test_handoff_usage_output(self):
        """handoff command with no args returns usage."""
        os.environ["CTXVM_FEATURES"] = "handoff"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        out = ctx.handler("")
        self.assertIn("Usage:", out)
        self.assertIn("ctxvm-handoff", out)


if __name__ == "__main__":
    unittest.main()
