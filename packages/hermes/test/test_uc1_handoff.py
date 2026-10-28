"""
ORG-1 UC1 handoff pause tests — CTXVM_FEATURES-gated UC1 handoff submodule.

Tests the UC1Handoff class: pause (flush → era snapshot → export package)
wrapping the committed Rust CLI binaries.

Run: python test/test_uc1_handoff.py
"""

import hashlib
import json
import os
import re
import shutil
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
import uc1_handoff  # noqa: E402  (module handle for mock.patch in PauseWire tests)
from uc1_handoff import UC1Handoff  # noqa: E402
from unittest import mock  # noqa: E402
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
            # UC1-PAUSE-WIRE retarget: the counterproof is LIVE — the packaged
            # zst is replayed at its slice turn and the era pair is diffed
            # expecting `identical` (m6 law) — a healthy anchor verifies True.
            self.assertEqual(result["diff_relation"], "identical")
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


class UC1PauseWireTests(unittest.TestCase):
    """Backfill for UC1-PAUSE-WIRE (their 5e1dcfd) — pause() retarget semantics.

    The card's three fixes landed without tests; this class covers them on the
    hermes side: the retargeted counterproof (glob zst → temp decompress →
    replay --turn N → era pair diff expecting `identical`, m6 law), the
    type-guarded divergence reader (non-dict replay stdout no longer crashes),
    and the junk-env arm-but-degrade loud line (turn=None, capture continues).
    """

    def setUp(self):
        _clear_env_for_tests()
        export_bin = _REPO_ROOT / "rust/target/release/export"
        replay_bin = _REPO_ROOT / "rust/target/release/replay"
        if not (export_bin.is_file() and replay_bin.is_file()):
            self.skipTest("release binaries not built")
        src = _REPO_ROOT / "corpus/m1/session-healthy.jsonl"
        if not src.is_file():
            self.skipTest("corpus anchor missing")
        self.src = src
        self.uc1 = UC1Handoff()

    def _stage(self, name: str = "handoff"):
        """Temporary pause target containing a flushed base file for `name`."""
        td = tempfile.TemporaryDirectory()
        shutil.copyfile(self.src, Path(td.name) / f"{name}.jsonl")
        return td

    def test_junk_env_degrades_loud_with_turn_none(self):
        """Junk CTXVM_HANDOFF_TURN → loud stderr line, trigger rides off (turn=None)."""
        import contextlib
        import io

        with self._stage() as td:
            os.environ["CTXVM_HANDOFF_TURN"] = "not-a-number"
            buf = io.StringIO()
            try:
                with contextlib.redirect_stderr(buf):
                    result = self.uc1.pause(td, turn=None)
            finally:
                del os.environ["CTXVM_HANDOFF_TURN"]
            self.assertEqual(result["exit_code"], 0, result["stderr"])
            # trigger off: flush label, no turn, era diff simply skipped
            self.assertEqual(result["snapshot"]["label"], "flush")
            self.assertIsNone(result["snapshot"]["turn"])
            self.assertIsNone(result["diff_relation"])
            self.assertIn(
                "CTXVM_HANDOFF_TURN=not-a-number not an integer — handoff trigger disarmed",
                buf.getvalue(),
                f"stderr captured: {buf.getvalue()!r}",
            )

    def test_pause_dir_chain_arg_beats_env(self):
        """pause() dir chain is ARG-FIRST: explicit trace_dir beats leaked
        CTXVM_HANDOFF_DIR (m7 leak regression, mirrors TS 2bb339a law test)."""
        with self._stage("dirarg") as td:
            os.environ["CTXVM_HANDOFF_DIR"] = str(Path(td) / "leaked-no-such-dir")
            try:
                result = self.uc1.pause(td, turn=None, handoff_name="dirarg")
            finally:
                del os.environ["CTXVM_HANDOFF_DIR"]
            self.assertEqual(result["exit_code"], 0, result["stderr"])
            self.assertEqual(
                result["snapshot"].get("jsonl"),
                str(Path(td) / "dirarg-flush.jsonl"),
            )

    def test_era_preseed_divergent_unverified(self):
        """Pre-seeded divergent era copy survives cp -n → counterproof unverified."""
        with self._stage() as td:
            # Lawful divergent pre-seed = a REAL different trace. (A junk byte
            # file would make the diff CLI exit 2 unparseable → relation None,
            # which the pause's best-effort counterproof records as `None` and
            # skips — disclosed in RR-UC1PAUSEWIRE; only junk on the RESUME
            # side fail-closes.)
            thrash = _REPO_ROOT / "corpus/m1/session-thrashing.jsonl"
            shutil.copyfile(thrash, Path(td) / "handoff-turn-2.jsonl")
            result = self.uc1.pause(td, turn=2)
            self.assertEqual(result["exit_code"], 0, result["stderr"])
            # cp -n law: the pre-seed era is NOT clobbered by the fresh copy
            self.assertEqual(
                (Path(td) / "handoff-turn-2.jsonl").read_bytes(),
                thrash.read_bytes(),
            )
            # era pair is canonical (m6 law): anything but `identical` unverifies
            self.assertFalse(result["verified"])
            self.assertEqual(result["diff_relation"], "divergent")

    def test_replay_non_dict_json_no_crash(self):
        """Type-guarded divergence reader: a non-dict replay stdout ('[]') is fine."""
        real_run = uc1_handoff._run

        def fake_run(name, args):
            if name == uc1_handoff._REPLAY_BIN:
                return {"exit_code": 0, "stdout": "[]", "stderr": ""}
            return real_run(name, args)

        with self._stage() as td:
            with mock.patch.object(uc1_handoff, "_run", fake_run):
                result = self.uc1.pause(td, turn=2)
        self.assertEqual(result["exit_code"], 0, result["stderr"])
        # no crash; a non-dict parse records NO divergences and the replay
        # exit code still verifies the package
        self.assertEqual(result["divergences"], [])
        self.assertTrue(result["verified"])

    def test_env_int_turn_used(self):
        """Positive int CTXVM_HANDOFF_TURN rides the env turn law (turn=3)."""
        with self._stage() as td:
            os.environ["CTXVM_HANDOFF_TURN"] = "3"
            try:
                result = self.uc1.pause(td, turn=None)
            finally:
                del os.environ["CTXVM_HANDOFF_TURN"]
        self.assertEqual(result["snapshot"]["turn"], 3)
        self.assertEqual(result["snapshot"]["label"], "turn-3")
        self.assertTrue(result["verified"])


class UC1DispatcherTests(unittest.TestCase):
    """live/register() dispatches /ctxvm-handoff slash command when handoff feature is enabled."""

    def setUp(self):
        _clear_env_for_tests()

    def _make_ctx(self):
        calls = []

        class FakeCtx:
            def __init__(self):
                self.calls = calls
                self.handlers = {}

            def register_hook(self, name, cb):
                self.calls.append(("hook", name))
                return lambda: None

            def on_unload(self, cb):
                self.calls.append(("unload", cb.__name__))
                return None

            def register_command(self, name, handler, description=""):
                self.calls.append(("command", name))
                self.handlers[name] = handler
                return None

        return FakeCtx(), calls

    def test_handoff_command_registered_with_feature(self):
        """With CTXVM_FEATURES=handoff, /ctxvm-handoff command is registered."""
        os.environ["CTXVM_FEATURES"] = "handoff"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertIn(("command", "ctxvm-handoff"), calls)
        self.assertIsNotNone(ctx.handlers["ctxvm-handoff"])

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
        out = ctx.handlers["ctxvm-handoff"]("")
        self.assertIn("Usage:", out)
        self.assertIn("ctxvm-handoff", out)
        del os.environ["CTXVM_FEATURES"]

    def test_handoff_passes_trace_name_as_handoff_name(self):
        """m7 run-1 failure mode: /ctxvm-handoff must pass handoff_name=CTXVM_TRACE_NAME
        when set, so flush and package use the same name (not the default 'handoff')."""
        os.environ["CTXVM_FEATURES"] = "handoff"
        os.environ["CTXVM_TRACE_NAME"] = "session-a"
        ctx, calls = self._make_ctx()
        live.register(ctx)

        # Inject a mock uc1 that records pause kwargs.
        import types

        class MockUC1:
            name = "uc1-handoff"
            feature = "handoff"

            def __init__(self):
                self.pause_calls = []

            def enabled(self, features):
                return True

            def flush(self):
                return None

            def pause(self, trace_dir, turn=None, handoff_name=None):
                self.pause_calls.append(
                    {"trace_dir": trace_dir, "turn": turn, "handoff_name": handoff_name}
                )
                return {
                    "exit_code": 0,
                    "verified": True,
                    "divergences": [],
                    "stderr": "",
                    "report": {},
                }

        mock_uc1 = MockUC1()
        live._state()["ucs"]["uc1-handoff"] = mock_uc1

        td = tempfile.mkdtemp()
        out = ctx.handlers["ctxvm-handoff"](f"{td} 3")
        self.assertEqual(len(mock_uc1.pause_calls), 1)
        self.assertEqual(mock_uc1.pause_calls[0]["handoff_name"], "session-a")
        del os.environ["CTXVM_TRACE_NAME"]
        del os.environ["CTXVM_FEATURES"]

    def test_resume_command_registered_with_feature(self):
        """With CTXVM_FEATURES=handoff, /ctxvm-resume command is registered."""
        os.environ["CTXVM_FEATURES"] = "handoff"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertIn(("command", "ctxvm-resume"), calls)
        self.assertIsNotNone(ctx.handlers["ctxvm-resume"])
        del os.environ["CTXVM_FEATURES"]

    def test_resume_command_not_registered_without_feature(self):
        """Without CTXVM_FEATURES=handoff, no ctxvm-resume command."""
        ctx, calls = self._make_ctx()
        live.register(ctx)
        self.assertNotIn(("command", "ctxvm-resume"), calls)

    def test_resume_usage_output(self):
        """resume command with no args returns usage."""
        os.environ["CTXVM_FEATURES"] = "handoff"
        ctx, calls = self._make_ctx()
        live.register(ctx)
        out = ctx.handlers["ctxvm-resume"]("")
        self.assertIn("Usage:", out)
        self.assertIn("ctxvm-resume", out)
        del os.environ["CTXVM_FEATURES"]


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
        # v-next keys (UC1-VERIFY-CHECKS): same fixture fields on both sides.
        self.assertEqual(ev["manifest"], golden["manifest"])
        self.assertEqual(ev["projection"], golden["projection"])
        self.assertEqual(ev["diff"], golden["diff"])


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


class UC1ResumeVerifyChecksTests(unittest.TestCase):
    """UC1 v-next in-module verify checks (UC1-VERIFY-CHECKS, design §3
    (1)(3)(4)) — mirrors packages/opencode/test/uc1-handoff.test.ts's v-next
    section: the reason strings are asserted byte-for-byte on BOTH sides.

    Disclosed baseline (card RR): the resume DIGEST hashes only the recorded
    checksum hex strings, so a corrupted artifact passed boot verification
    before this card — (1) byte-level row re-verification closes it.
    """

    def setUp(self):
        _clear_env_for_tests()

    def _make_snapshot_abs(self, anchor: Path) -> str:
        """Build a real snapshot from an ABSOLUTE anchor (cwd-independent)."""
        from ctxvm_py._cli import build_handoff_snapshot  # noqa: F401,E402

        td = tempfile.mkdtemp()
        out_dir = Path(td) / "handoff"
        try:
            build_handoff_snapshot(str(anchor), 0, str(out_dir))
        except RuntimeError:
            self.skipTest("release binaries not built — run the cargo build gate")
        return str(out_dir)

    @staticmethod
    def _fix_row(snap_dir: str, name: str, digest_hex: str) -> None:
        """Re-stamp one checksums row after an intentional artifact edit so a
        LATER check becomes reachable without tripping the byte-level row
        verification first."""
        checksums = Path(snap_dir) / "checksums.sha256"
        pat = re.compile(r"^\s*\S+\s+" + re.escape(name) + r"\s*$")
        lines = checksums.read_text(encoding="utf-8").splitlines()
        out = [f"{digest_hex}  {name}" if pat.match(line) else line for line in lines]
        checksums.write_text("\n".join(out) + "\n", encoding="utf-8")

    def test_corrupted_artifact_checksum_mismatch(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        pt = Path(snap_dir) / "page-table-0.json"
        pt.write_text(pt.read_text(encoding="utf-8") + " ", encoding="utf-8")
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "checksum mismatch for page-table-0.json")
        self.assertEqual(result["evidence"], {"turn": 0, "snapshot": snap_dir})

    def test_checksummed_artifact_missing(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        os.remove(Path(snap_dir) / "llms.txt")
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "checksummed artifact missing: llms.txt")

    def test_checksums_file_missing(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        os.remove(Path(snap_dir) / "checksums.sha256")
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(
            result["reason"], f"checksums.sha256 missing: {snap_dir}"
        )

    def test_manifest_sliceturn_contradiction(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        manifest = Path(snap_dir) / "manifest.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace("sliceTurn: 0", "sliceTurn: 1"),
            encoding="utf-8",
        )
        self._fix_row(
            snap_dir,
            "manifest.yaml",
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "manifest sliceTurn 1 != trace turn 0")

    def test_era_copy_identical(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        first = UC1Handoff().resume(snap_dir)  # also drops trace-0.jsonl in-dir
        self.assertTrue(first["verified"], first["reason"])
        shutil.copyfile(
            Path(snap_dir) / "trace-0.jsonl",
            Path(snap_dir) / "foo-turn-0.jsonl",
        )
        result = UC1Handoff().resume(snap_dir)
        self.assertTrue(result["verified"], result["reason"])
        self.assertEqual(
            result["evidence"]["diff"],
            {"source": "foo-turn-0.jsonl", "relation": "identical"},
        )

    def test_era_copy_mismatch_unverified(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        # The full m1 anchor as a turn-0 "era": diff(full, slice) =
        # a_extends_b — not identical → real anomaly under the law-aware rule.
        shutil.copyfile(_ANCHORS[0], Path(snap_dir) / "foo-turn-0.jsonl")
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(
            result["reason"],
            "era diff foo-turn-0.jsonl: relation a_extends_b expected identical",
        )

    def test_derivedfrom_divergence_diagnostic_only(self):
        """Reproduce the m6 shape from committed corpus files only: the staged
        derivedFrom source is overwritten after packaging (the exact
        "flushed file overwritten by the continued session" mutation) —
        diff divergence is the knowledge-stateful lawful shape and must NOT
        unverify."""
        try:
            from ctxvm_py._cli import build_handoff_snapshot  # noqa: F402
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        td = tempfile.mkdtemp()
        src = Path(td) / "src.jsonl"
        shutil.copyfile(_ANCHORS[0], src)
        out_dir = Path(td) / "pkg"
        try:
            build_handoff_snapshot(str(src), 0, str(out_dir))
        except RuntimeError:
            self.skipTest("release binaries not built — run the cargo build gate")
        shutil.copyfile(_REPO_ROOT / "corpus/m6/opencode-pause-session-a.jsonl", src)
        result = UC1Handoff().resume(str(out_dir))
        self.assertTrue(result["verified"], result["reason"])
        self.assertEqual(
            result["evidence"]["diff"],
            {"source": str(src), "relation": "divergent"},
        )

    def test_diff_skipped_when_no_source(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        manifest = Path(snap_dir) / "manifest.yaml"
        manifest.write_text(
            re.sub(
                r"derivedFrom: '[^']*'",
                "derivedFrom: 'corpus/nonexistent-anchor.jsonl'",
                manifest.read_text(encoding="utf-8"),
            ),
            encoding="utf-8",
        )
        self._fix_row(
            snap_dir,
            "manifest.yaml",
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )
        result = UC1Handoff().resume(snap_dir)
        self.assertTrue(result["verified"], result["reason"])
        self.assertIsNone(result["evidence"]["diff"])

    def test_projection_surfaced(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        table = json.loads(
            (Path(snap_dir) / "page-table-0.json").read_text(encoding="utf-8")
        )
        result = UC1Handoff().resume(snap_dir)
        self.assertTrue(result["verified"], result["reason"])
        self.assertEqual(
            result["evidence"]["projection"],
            {"turn": 0, "slots": len(table["slots"])},
        )

    def test_page_table_unreadable(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        pt = Path(snap_dir) / "page-table-0.json"
        pt.write_text("not-json\n", encoding="utf-8")
        self._fix_row(snap_dir, "page-table-0.json", hashlib.sha256(pt.read_bytes()).hexdigest())
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "page-table-0.json unreadable")

    def test_page_table_turn_mismatch(self):
        try:
            snap_dir = self._make_snapshot_abs(_ANCHORS[0])
        except ImportError:
            self.skipTest("ctxvm_py not importable — anchor path may differ")
        pt = Path(snap_dir) / "page-table-0.json"
        table = json.loads(pt.read_text(encoding="utf-8"))
        table["turn"] = 1
        pt.write_text(json.dumps(table) + "\n", encoding="utf-8")
        self._fix_row(snap_dir, "page-table-0.json", hashlib.sha256(pt.read_bytes()).hexdigest())
        result = UC1Handoff().resume(snap_dir)
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "page-table turn 1 != trace turn 0")


if __name__ == "__main__":
    unittest.main()
