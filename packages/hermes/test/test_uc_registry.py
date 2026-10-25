"""
ORG-1 per-UC tests — CTXVM_FEATURES gating + UC module dispatch.

Mirrors the opencode parity approach: these tests assert that the
`live/` entry is a thin dispatcher and that UC submodules (uc1-handoff,
uc2-forensics, uc3-planner) are feature-gated no-ops until their logic
lands. The `trace` UC (existing tracer) is the default, always-on feature.

Run: python test/test_uc_registry.py
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
from uc_registry import (  # noqa: E402
    TRACE_FEATURE,
    UC1_FEATURE,
    UC2_FEATURE,
    UC3_FEATURE,
    HANDOFF_FEATURE,
    parse_features,
)
from uc1_handoff import UC1Handoff  # noqa: E402
from uc2_forensics import UC2Forensics  # noqa: E402
from uc3_planner import UC3Planner  # noqa: E402


class FakeCtx:
    """Minimal PluginContext double for registering hooks."""

    def __init__(self):
        self.hooks = {}
        self.commands = {}
        self.unload = None

    def register_hook(self, name, cb):
        self.hooks[name] = cb
        return lambda: None

    def on_unload(self, cb):
        self.unload = cb
        return lambda: None

    def register_command(self, name, handler, description=""):
        self.commands[name] = handler
        return lambda: None


class FeatureParsingTests(unittest.TestCase):
    """parse_features: default, unset, comma-separated, case-insensitive."""

    def test_default_trace_when_unset(self):
        os.environ.pop("CTXVM_FEATURES", None)
        self.assertEqual(parse_features(None), {TRACE_FEATURE})
        self.assertEqual(parse_features(""), {TRACE_FEATURE})
        self.assertEqual(parse_features("   "), {TRACE_FEATURE})

    def test_comma_separated(self):
        self.assertEqual(
            parse_features("trace,uc1-handoff,uc2-forensics"),
            {TRACE_FEATURE, UC1_FEATURE, UC2_FEATURE},
        )

    def test_case_insensitive_and_deduped(self):
        self.assertEqual(
            parse_features("TRACE, Uc1-Handoff , uc1-handoff, UC3-PLANNER"),
            {TRACE_FEATURE, UC1_FEATURE, UC3_FEATURE},
        )

    def test_unknown_names_ignored(self):
        self.assertEqual(
            parse_features("trace,uc9-nonexistent"), {TRACE_FEATURE}
        )


class UCModuleStubTests(unittest.TestCase):
    """UC stub modules are no-ops and report their feature correctly."""

    def test_uc1_handoff_noop(self):
        uc = UC1Handoff()
        self.assertEqual(uc.name, UC1_FEATURE)
        self.assertEqual(uc.feature, HANDOFF_FEATURE)
        # All handlers are no-ops (return None)
        self.assertIsNone(uc.on_session_start({"session_id": "s"}))
        self.assertIsNone(uc.on_pre_tool_call({"tool": "t"}))
        self.assertIsNone(uc.on_post_tool_call({"tool": "t", "status": "ok"}))
        self.assertIsNone(uc.on_pre_llm_call({"session_id": "s"}))
        self.assertIsNone(uc.on_session_end({"session_id": "s"}))
        self.assertIsNone(uc.flush())

    def test_uc2_forensics_noop(self):
        uc = UC2Forensics()
        self.assertEqual(uc.name, UC2_FEATURE)
        self.assertEqual(uc.feature, UC2_FEATURE)
        self.assertIsNone(uc.on_session_start({"session_id": "s"}))
        self.assertIsNone(uc.flush())

    def test_uc3_planner_noop(self):
        uc = UC3Planner()
        self.assertEqual(uc.name, UC3_FEATURE)
        self.assertEqual(uc.feature, UC3_FEATURE)
        self.assertIsNone(uc.on_session_end({"session_id": "s"}))
        self.assertIsNone(uc.flush())

    def test_enabled_respects_features(self):
        uc1 = UC1Handoff()
        self.assertTrue(uc1.enabled({HANDOFF_FEATURE}))
        self.assertFalse(uc1.enabled({TRACE_FEATURE}))
        self.assertFalse(uc1.enabled(set()))

        # trace UC (feature None) is always enabled
        from uc_registry import UCModule

        class TraceUC(UCModule):
            name = "trace"
            feature = None

        trace_uc = TraceUC()
        self.assertTrue(trace_uc.enabled({}))
        self.assertTrue(trace_uc.enabled({UC1_FEATURE}))


class DispatcherTests(unittest.TestCase):
    """live/register() dispatches hooks to enabled UC modules."""

    def setUp(self):
        _clear_env_for_tests()

    def test_trace_default_enabled_pages_declared(self):
        """With default features ({trace}), a completed tool call declares a page."""
        os.environ["CTXVM_TRACE_DIR"] = tempfile.mkdtemp()
        os.environ["CTXVM_MODEL"] = "test/model"
        os.environ["CTXVM_PROVIDER"] = "test"
        os.environ["CTXVM_AGENT_ID"] = "test"
        os.environ["CTXVM_BUDGET_TOKENS"] = "120000"

        ctx = FakeCtx()
        register(ctx)

        ctx.hooks["on_session_start"](session_id="s1")
        ctx.hooks["pre_tool_call"](
            session_id="s1", tool="read", args={"path": "a.txt"}
        )
        ctx.hooks["post_tool_call"](
            session_id="s1",
            tool="read",
            args={"path": "a.txt"},
            status="ok",
            result="hello page",
        )
        ctx.hooks["pre_llm_call"](session_id="s1", conversation_history=[])
        ctx.hooks["on_session_end"](session_id="s1")

        # Unload to flush
        if ctx.unload:
            ctx.unload()

        files = list(Path(os.environ["CTXVM_TRACE_DIR"]).glob("*.jsonl"))
        self.assertEqual(len(files), 1, f"expected 1 jsonl, got {files}")
        content = files[0].read_text()
        declares = [l for l in content.splitlines() if '"page.declare"' in l]
        self.assertGreaterEqual(len(declares), 1, "trace UC should declare pages")

    def test_trace_disabled_no_pages(self):
        """With CTXVM_FEATURES=uc1-handoff (no trace), no pages are declared."""
        os.environ["CTXVM_TRACE_DIR"] = tempfile.mkdtemp()
        os.environ["CTXVM_FEATURES"] = UC1_FEATURE
        os.environ["CTXVM_MODEL"] = "test/model"
        os.environ["CTXVM_PROVIDER"] = "test"
        os.environ["CTXVM_AGENT_ID"] = "test"
        os.environ["CTXVM_BUDGET_TOKENS"] = "120000"

        ctx = FakeCtx()
        register(ctx)

        ctx.hooks["on_session_start"](session_id="s2")
        ctx.hooks["pre_tool_call"](
            session_id="s2", tool="read", args={"path": "a.txt"}
        )
        ctx.hooks["post_tool_call"](
            session_id="s2",
            tool="read",
            args={"path": "a.txt"},
            status="ok",
            result="hello page",
        )
        ctx.hooks["on_session_end"](session_id="s2")

        if ctx.unload:
            ctx.unload()

        files = list(Path(os.environ["CTXVM_TRACE_DIR"]).glob("*.jsonl"))
        self.assertEqual(
            len(files), 0, f"expected no jsonl when trace disabled, got {files}"
        )

    def test_multiple_features_enabled(self):
        """trace + uc1-handoff: pages declared, UC1 stub called (no-op)."""
        os.environ["CTXVM_TRACE_DIR"] = tempfile.mkdtemp()
        os.environ["CTXVM_FEATURES"] = "trace,uc1-handoff"
        os.environ["CTXVM_MODEL"] = "test/model"
        os.environ["CTXVM_PROVIDER"] = "test"
        os.environ["CTXVM_AGENT_ID"] = "test"
        os.environ["CTXVM_BUDGET_TOKENS"] = "120000"

        ctx = FakeCtx()
        register(ctx)

        ctx.hooks["on_session_start"](session_id="s3")
        ctx.hooks["post_tool_call"](
            session_id="s3",
            tool="read",
            args={"path": "a.txt"},
            status="ok",
            result="hello page",
        )
        ctx.hooks["on_session_end"](session_id="s3")

        if ctx.unload:
            ctx.unload()

        files = list(Path(os.environ["CTXVM_TRACE_DIR"]).glob("*.jsonl"))
        self.assertEqual(len(files), 1)
        content = files[0].read_text()
        declares = [l for l in content.splitlines() if '"page.declare"' in l]
        self.assertGreaterEqual(len(declares), 1)


if __name__ == "__main__":
    unittest.main()
