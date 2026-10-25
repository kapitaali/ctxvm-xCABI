"""
ORG-1 UC2 forensics tests — CTXVM_FEATURES-gated UC2 forensics submodule.

Tests the UC2Forensics class: thin wrappers around the committed Rust CLI
binaries (replay, profile, diff, export) plus verdict decomposition.

Run: python test/test_uc2_forensics.py
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
from uc2_forensics import UC2Forensics  # noqa: E402


class UC2ForensicsTests(unittest.TestCase):
    """UC2Forensics wrapper methods — shell out to Rust binaries."""

    def setUp(self):
        _clear_env_for_tests()

    def test_uc2_forensics_instantiation(self):
        """UC2Forensics is a UCModule with the right name/feature."""
        uc2 = UC2Forensics()
        self.assertEqual(uc2.name, "uc2-forensics")
        self.assertEqual(uc2.feature, "uc2-forensics")
        self.assertTrue(uc2.enabled({"uc2-forensics"}))
        self.assertFalse(uc2.enabled({"trace"}))
        self.assertFalse(uc2.enabled(set()))

    def test_replay_returns_dict_with_exit_code(self):
        """replay() returns a dict with exit_code, report, stderr."""
        uc2 = UC2Forensics()
        result = uc2.replay("/nonexistent/trace.jsonl")
        self.assertIn("exit_code", result)
        self.assertIn("report", result)
        self.assertIn("stderr", result)
        self.assertEqual(result["exit_code"], 2)  # file not found

    def test_profile_returns_dict_with_exit_code(self):
        """profile() returns a dict with exit_code, report, stderr."""
        uc2 = UC2Forensics()
        result = uc2.profile("/nonexistent/trace.jsonl")
        self.assertIn("exit_code", result)
        self.assertIn("report", result)
        self.assertIn("stderr", result)
        self.assertEqual(result["exit_code"], 2)

    def test_diff_returns_dict_with_exit_code(self):
        """diff() returns a dict with exit_code, report, stderr."""
        uc2 = UC2Forensics()
        result = uc2.diff("/nonexistent/a.jsonl", "/nonexistent/b.jsonl")
        self.assertIn("exit_code", result)
        self.assertIn("report", result)
        self.assertEqual(result["exit_code"], 2)

    def test_export_returns_dict_with_exit_code(self):
        """export() returns a dict with exit_code, report, stderr."""
        uc2 = UC2Forensics()
        result = uc2.export("/nonexistent/trace.jsonl")
        self.assertIn("exit_code", result)
        self.assertIn("report", result)
        self.assertEqual(result["exit_code"], 2)

    def test_diagnose_returns_verdict_dict(self):
        """diagnose() returns a verdict dict with fault_turn, verdict, reason, evidence."""
        uc2 = UC2Forensics()
        result = uc2.diagnose("/nonexistent/trace.jsonl", 5)
        self.assertIn("fault_turn", result)
        self.assertIn("verdict", result)
        self.assertIn("reason", result)
        self.assertIn("evidence", result)
        self.assertEqual(result["fault_turn"], 5)
        self.assertEqual(result["verdict"], "inconclusive")


class UC2DispatcherTests(unittest.TestCase):
    """live/register() dispatches /ctxvm-forensics slash command when uc2-forensics feature is enabled."""

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

    def test_forensics_command_registered_with_uc2_feature(self):
        """With CTXVM_FEATURES=uc2-forensics, /ctxvm-forensics command is registered."""
        os.environ["CTXVM_FEATURES"] = "uc2-forensics"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertIn(("command", "ctxvm-forensics"), calls)
        self.assertIsNotNone(ctx.handler)

    def test_forensics_command_not_registered_without_feature(self):
        """Without CTXVM_FEATURES=uc2-forensics, no ctxvm-forensics command."""
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertNotIn(("command", "ctxvm-forensics"), calls)

    def test_diagnose_returns_inconclusive_for_missing_file(self):
        """diagnose via slash command returns inconclusive verdict for missing trace."""
        os.environ["CTXVM_FEATURES"] = "uc2-forensics"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        out = ctx.handler("diagnose /nonexistent/trace.jsonl 3")
        result = json.loads(out)
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertEqual(result["fault_turn"], 3)


class UC2GoldenParityTests(unittest.TestCase):
    """KIT-1 §4 DoD, UC2-MIRROR (2026-10-25): the golden fixture pins BOTH sides.

    Fixture: packages/opencode/test/fixtures/uc2-diagnose-golden.json — diagnose
    outputs on real corpus anchors, GENERATED BY THIS implementation (meta records
    it). The opencode TS mirror (packages/opencode/src/uc2-forensics.ts) must
    deep-equal the SAME fixture in its own test — engine or port drift fails
    both sides loudly. Requires the release binaries (cargo build --release):
    the anchor evidence comes from the real profile/replay CLI.
    """

    def setUp(self):
        _clear_env_for_tests()

    def test_diagnose_matches_opencode_golden_fixture(self):
        fixture_path = (
            Path(__file__).resolve().parents[3]
            / "packages/opencode/test/fixtures/uc2-diagnose-golden.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertIn(
            "packages/hermes/src/uc2_forensics.py",
            fixture["meta"]["generatedBy"],
            "fixture must be generated by this (hermes) reference implementation",
        )
        uc2 = UC2Forensics()
        repo_root = Path(__file__).resolve().parents[3]
        for anchor in fixture["anchors"]:
            result = uc2.diagnose(str(repo_root / anchor["trace"]), anchor["faultTurn"])
            self.assertEqual(
                result,
                anchor["diagnose"],
                f"golden drift at {anchor['trace']} turn {anchor['faultTurn']}",
            )
            self.assertEqual(result["verdict"], anchor["expectedVerdict"])


if __name__ == "__main__":
    unittest.main()
