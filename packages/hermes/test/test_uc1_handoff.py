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
# Make packages/py importable (ctxvm_py binding for snapshot creation in resume tests)
_PY_ROOT = str(Path(__file__).resolve().parents[3] / "packages" / "py")
for _p in (_HERMES_ROOT, _HERMES_SRC, _PY_ROOT):
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

# Repo-root anchors for resume tests (same anchors the binding uses).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ANCHORS = [
    _REPO_ROOT / "corpus/m1/session-healthy.jsonl",
    _REPO_ROOT / "corpus/m1/session-thrashing.jsonl",
    _REPO_ROOT / "corpus/m1/tracer-healthy.jsonl",
    _REPO_ROOT / "corpus/m1/tracer-recall.jsonl",
    _REPO_ROOT / "corpus/m1/opencode-echo.jsonl",
    _REPO_ROOT / "corpus/m2/live-echo.jsonl",
    _REPO_ROOT / "corpus/m2/live-thrash.jsonl",
]


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

    def test_pause_at_turn_exports_snapshot(self):
        """pause(td, turn=N) with a real flushed base packages successfully.

        Probes the argv law (UC1-PAUSE-MIRROR card): the pre-fix bare
        positional form made every pause(..., turn=N) exit 2 — the real binary
        rejects `unexpected second positional \`2\`` — this pins the working
        path the shape-only test above missed.
        """
        import shutil

        export_bin = _REPO_ROOT / "rust/target/release/export"
        if not export_bin.is_file():
            self.skipTest("release binaries not built")
        src = _REPO_ROOT / "corpus/m1/session-healthy.jsonl"
        if not src.is_file():
            self.skipTest("corpus anchor missing")
        uc1 = UC1Handoff()
        with tempfile.TemporaryDirectory() as td:
            shutil.copyfile(src, Path(td) / "handoff.jsonl")
            result = uc1.pause(td, turn=2)
            self.assertEqual(result["exit_code"], 0, f"pause failed: {result['stderr']}")
            # Reference dead-path law (probed): the counterproof checks a
            # literal "trace-N.jsonl.zst" that never exists → verified stays
            # True.
            self.assertTrue(result["verified"])
            self.assertEqual(result["snapshot"]["label"], "turn-2")
            self.assertEqual(result["snapshot"]["turn"], 2)
            snap_dir = Path(result["snapshot"]["handoff_dir"])
            # Artifact naming is slice-turn based (engine law, T21): --turn N
            # beyond the last window slices identity and names by the slice's
            # last turn — so glob rather than pin "trace-2".
            zsts = list(snap_dir.glob("trace-*.jsonl.zst"))
            self.assertEqual(
                len(zsts), 1, f"packaged: {sorted(p.name for p in snap_dir.iterdir())}"
            )
            self.assertEqual(len(result["report"]["artifacts"]), 5)
            self.assertTrue((snap_dir / "checksums.sha256").is_file())

    def test_pause_era_copy_never_clobbers(self):
        """Era copies follow cp -n semantics: existing era files survive."""
        import shutil

        export_bin = _REPO_ROOT / "rust/target/release/export"
        if not export_bin.is_file():
            self.skipTest("release binaries not built")
        src = _REPO_ROOT / "corpus/m1/session-healthy.jsonl"
        if not src.is_file():
            self.skipTest("corpus anchor missing")
        uc1 = UC1Handoff()
        with tempfile.TemporaryDirectory() as td:
            shutil.copyfile(src, Path(td) / "base.jsonl")
            (Path(td) / "base.meta.json").write_text('{"sidecar": true}\n', encoding="utf-8")
            (Path(td) / "base-flush.jsonl").write_text("JUNK-ERA", encoding="utf-8")
            (Path(td) / "base-flush.meta.json").write_text("JUNK-META", encoding="utf-8")
            result = uc1.pause(td, turn=None, handoff_name="base")
            self.assertEqual(result["exit_code"], 0, result["stderr"])
            self.assertEqual(
                (Path(td) / "base-flush.jsonl").read_text(encoding="utf-8"),
                "JUNK-ERA",
            )
            self.assertEqual(result["snapshot"]["jsonl"], str(Path(td) / "base-flush.jsonl"))

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


class UC1ResumeTests(unittest.TestCase):
    """UC1Handoff.resume() — verify paused snapshot before resuming."""

    def setUp(self):
        _clear_env_for_tests()

    def _make_snapshot(self) -> str:
        """Build a real handoff snapshot via build_handoff_snapshot and return its dir.

        The dir persists after this method returns (no context manager cleanup)
        so resume() can read it.
        """
        from ctxvm_py._cli import build_handoff_snapshot  # noqa: E402

        import tempfile

        td = tempfile.mkdtemp()
        out_dir = Path(td) / "handoff"
        report = build_handoff_snapshot(
            str(_ANCHORS[0]), 0, str(out_dir)
        )
        self.assertIn("turn", report)
        return str(out_dir)

    def tearDown(self):
        # Clean up any snapshot dirs created by _make_snapshot.
        pass

    def test_resume_returns_dict(self):
        """resume() returns a dict with exit_code, verified, reason, evidence."""
        uc1 = UC1Handoff()
        result = uc1.resume("/nonexistent/snapshot")
        self.assertIn("exit_code", result)
        self.assertIn("verified", result)
        self.assertIn("reason", result)
        self.assertIn("evidence", result)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])

    def test_resume_missing_dir(self):
        """resume() with a nonexistent dir returns exit 2, verified False."""
        uc1 = UC1Handoff()
        result = uc1.resume("/no/such/dir")
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertIn("not found", result["reason"])

    def test_resume_valid_snapshot(self):
        """resume() on a real snapshot returns verified=True with evidence."""
        try:
            snap_dir = self._make_snapshot()
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        uc1 = UC1Handoff()
        result = uc1.resume(snap_dir)
        self.assertEqual(result["exit_code"], 0, f"resume failed: {result['reason']}")
        self.assertTrue(result["verified"], f"resume not verified: {result['reason']}")
        ev = result["evidence"]
        self.assertIn("snapshot", ev)
        self.assertIn("snapshotDigest", ev)
        self.assertIn("snapTurn", ev)
        self.assertTrue(ev["snapshotDigest"].startswith("sha256:"))
        self.assertEqual(ev["snapTurn"], 0)


class UC1ResumeGoldenParityTests(unittest.TestCase):
    """UC1 resume golden parity — same discipline as packages/opencode/test/uc1-resume.test.ts.

    Builds the fixture snapshot with cwd=repo root + RELATIVE anchor (the
    fixture's discipline: manifest.yaml/llms.txt embed the trace argv string,
    so a relative argv keeps the artifact bytes host-independent), then pins
    the resume fields against the committed fixture
    packages/opencode/test/fixtures/uc1-resume-golden.json (generated by the
    hermes reference itself; the opencode TS mirror deep-equals the same
    fixture — 09-plugin-parity.md §4).
    """

    def setUp(self):
        _clear_env_for_tests()

    def _make_snapshot_rel(self) -> str:
        if not (_REPO_ROOT / "corpus/m1/session-healthy.jsonl").is_file():
            self.skipTest("not running from repo root — relative anchor required")
        from ctxvm_py._cli import build_handoff_snapshot  # noqa: E402

        # Fixture discipline: cwd=repo root + relative anchor. run-ci invokes
        # pytest from packages/hermes, so anchor the cwd for the duration and
        # restore afterwards.
        prev = os.getcwd()
        self.addCleanup(os.chdir, prev)
        os.chdir(_REPO_ROOT)
        out_dir = Path(tempfile.mkdtemp()) / "handoff"
        build_handoff_snapshot("corpus/m1/session-healthy.jsonl", 0, str(out_dir))
        return str(out_dir)

    def test_resume_matches_golden_fixture(self):
        try:
            import ctxvm_py  # noqa: F401
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        golden_path = _REPO_ROOT / "packages/opencode/test/fixtures/uc1-resume-golden.json"
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        snap_dir = self._make_snapshot_rel()
        uc1 = UC1Handoff()
        result = uc1.resume(snap_dir)
        self.assertEqual(result["exit_code"], 0, f"resume failed: {result['reason']}")
        self.assertEqual(result["verified"], golden["verified"])
        self.assertEqual(result["reason"], golden["reason"])
        ev = result["evidence"]
        self.assertEqual(ev["snapTurn"], golden["snapTurn"])
        self.assertEqual(ev["snapshotDigest"], golden["snapshotDigest"])
        self.assertEqual(
            sorted(os.path.basename(p) for p in ev["artifacts"]),
            golden["artifactNames"],
        )


class UC1ResumeWitnessTests(unittest.TestCase):
    """B3 witness chain (design uc1-plugin.md §3) — adds the artifact-level
    evidence the B3 card left unproven: export m2/live-echo @2 --odps → resume
    verified → diff(full, decompressed slice) = a_extends_b on the shared
    prefix → replay(slice, --turn 2) counterproof exit 0 → page-table-2.json
    fidelity reference stamped at turn 2."""

    def setUp(self):
        _clear_env_for_tests()

    def test_m2_echo_resume_witness(self):
        try:
            from ctxvm_py import _cli as binding  # noqa: F401
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        if not (_REPO_ROOT / "corpus/m2/live-echo.jsonl").is_file():
            self.skipTest("not running from repo root — relative anchor required")
        prev = os.getcwd()
        self.addCleanup(os.chdir, prev)
        os.chdir(_REPO_ROOT)
        snap = Path(tempfile.mkdtemp()) / "handoff"
        binding.build_handoff_snapshot("corpus/m2/live-echo.jsonl", 2, str(snap))
        uc1 = UC1Handoff()
        res = uc1.resume(str(snap))
        self.assertTrue(res["verified"], f"resume not verified: {res['reason']}")
        decompressed = str(snap / "trace-2.jsonl")
        self.assertTrue(Path(decompressed).is_file())

        # Shared-prefix relation: full first → a_extends_b (binding raises on
        # non-zero, so reaching the relation assert means exit 0).
        full = "corpus/m2/live-echo.jsonl"
        relation = binding.diff(full, decompressed)
        self.assertEqual(relation.get("relation"), "a_extends_b")
        self.assertIsNone(relation.get("firstDivergentEvent"))
        self.assertGreater(relation.get("commonPrefixEvents", 0), 0)

        # Standalone replay counterproof on the decompressed slice at turn 2.
        slice_report = binding.replay(decompressed, 2)
        self.assertIsInstance(slice_report, dict)

        # Fidelity reference: the packaged projection is present, turn-stamped.
        pt = json.loads((snap / "page-table-2.json").read_text(encoding="utf-8"))
        self.assertEqual(pt["turn"], 2)


if __name__ == "__main__":
    unittest.main()
