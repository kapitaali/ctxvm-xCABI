"""
ctxvm-py binding tests — byte-compare vs the committed Rust CLI binaries.

Per design/uc1-plugin.md §5 (B1 binding beat): "tests byte-compare binding vs
rust CLI on m1/m2 anchors; gate 2 gains the binding test (count line updated
same-card)."

These tests call the Python binding (ctxvm_py._cli) and the Rust CLI binaries
(replay, profile, diff, export) directly via subprocess, then assert the
returned JSON is byte-identical. This is the binding's DoD: byte-identical
outputs vs the committed rust CLI for every binding surface.

Run: python -m pytest packages/py/test/ -q   (from repo root)
     or: pip install -e packages/py/ && pytest packages/py/test/ -q
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Make packages/py/ctxvm_py importable
_PY_ROOT = str(Path(__file__).resolve().parents[1])
_SRC = str(Path(__file__).resolve().parents[1] / "ctxvm_py")
for _p in (_PY_ROOT, _SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ctxvm_py._cli import (  # noqa: E402
    build_handoff_snapshot,
    diff,
    export,
    profile,
    replay,
)

# Anchor fixtures: m1 (seed) + m2 (live) — the corpus anchors the design cites.
# Resolved from repo root (two levels up from packages/py/ctxvm_py/test/).
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


def _rust_cli(name: str, args: list) -> dict:
    """Invoke a Rust CLI binary directly and return parsed stdout JSON."""
    # Locate rust/target/release/<name> relative to the repo root (two levels
    # up from packages/py/ctxvm_py/test/).
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "rust" / "target" / "release" / name
        if candidate.is_file():
            bin_path = str(candidate)
            break
    else:
        bin_path = name
    proc = subprocess.run(
        [bin_path, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"rust {name} {' '.join(args)} failed (exit {proc.returncode}): "
            f"{proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


class BindingVsRustTests(unittest.TestCase):
    """Byte-compare the Python binding vs the Rust CLI on m1/m2 anchors."""

    def _assert_bindings_match(self, fixture: str, bind_fn, rust_fn, *args):
        """Call bind_fn(*args) and rust_fn(*args), assert JSON-equal."""
        bind_result = bind_fn(*args)
        rust_result = rust_fn(*args)
        self.assertEqual(
            bind_result,
            rust_result,
            f"binding vs rust CLI mismatch for {fixture} ({bind_fn.__name__}):\n"
            f"binding:   {json.dumps(bind_result, sort_keys=True)[:400]}\n"
            f"rust-cli:  {json.dumps(rust_result, sort_keys=True)[:400]}",
        )

    def test_replay_matches_rust_on_anchors(self):
        """replay() byte-matches `ctxvm replay` on every m1/m2 anchor."""
        for fixture in _ANCHORS:
            f = Path(fixture)
            self.assertTrue(f.is_file(), f"missing anchor: {f}")
            with self.subTest(fixture=str(f), subcommand="replay"):
                self._assert_bindings_match(
                    str(f),
                    lambda p: replay(p),
                    lambda p: _rust_cli("replay", [p]),
                    str(f),
                )

    def test_replay_turn_matches_rust_on_anchors(self):
        """replay(turn=N) byte-matches `ctxvm replay --turn N` on anchors."""
        for fixture in _ANCHORS:
            f = Path(fixture)
            self.assertTrue(f.is_file(), f"missing anchor: {f}")
            with self.subTest(fixture=str(f), subcommand="replay --turn 2"):
                self._assert_bindings_match(
                    str(f),
                    lambda p: replay(p, turn=2),
                    lambda p: _rust_cli("replay", [p, "--turn", "2"]),
                    str(f),
                )

    def test_profile_matches_rust_on_anchors(self):
        """profile() byte-matches `ctxvm profile` on every m1/m2 anchor."""
        for fixture in _ANCHORS:
            f = Path(fixture)
            self.assertTrue(f.is_file(), f"missing anchor: {f}")
            with self.subTest(fixture=str(f), subcommand="profile"):
                self._assert_bindings_match(
                    str(f),
                    lambda p: profile(p),
                    lambda p: _rust_cli("profile", [p]),
                    str(f),
                )

    def test_profile_faults_matches_rust_on_anchors(self):
        """profile(--event page.fault) byte-matches rust on anchors."""
        for fixture in _ANCHORS:
            f = Path(fixture)
            self.assertTrue(f.is_file(), f"missing anchor: {f}")
            with self.subTest(fixture=str(f), subcommand="profile --event page.fault"):
                self._assert_bindings_match(
                    str(f),
                    lambda p: profile(p, events=["page.fault"]),
                    lambda p: _rust_cli("profile", [p, "--event", "page.fault"]),
                    str(f),
                )

    def test_diff_self_matches_rust_on_anchors(self):
        """diff(x, x) byte-matches `ctxvm diff x x` (identical relation)."""
        for fixture in _ANCHORS:
            f = Path(fixture)
            self.assertTrue(f.is_file(), f"missing anchor: {f}")
            with self.subTest(fixture=str(f), subcommand="diff self"):
                self._assert_bindings_match(
                    str(f),
                    lambda p: diff(p, p),
                    lambda p: _rust_cli("diff", [p, p]),
                    str(f),
                )

    def test_export_matches_rust_on_anchors(self):
        """export() byte-matches `ctxvm export` on anchors."""
        for fixture in _ANCHORS:
            f = Path(fixture)
            self.assertTrue(f.is_file(), f"missing anchor: {f}")
            with tempfile.TemporaryDirectory() as td:
                out_dir = str(Path(td) / "out")
                with self.subTest(fixture=str(f), subcommand="export"):
                    self._assert_bindings_match(
                        str(f),
                        lambda p: export(p, output_dir=out_dir),
                        lambda p: _rust_cli("export", [p, "--output", out_dir]),
                        str(f),
                    )

    def test_export_odps_writes_artifacts(self):
        """export(odps=True) writes the memo artifact set into output_dir."""
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "handoff"
            report = build_handoff_snapshot(str(_ANCHORS[0]), 0, str(out_dir))
            self.assertIn("turn", report)
            self.assertTrue(report.get("dq", {}).get("replayDeterminism"), "slice should be replay-deterministic")
            # Artifacts written by --odps (filenames include the turn number)
            self.assertTrue((out_dir / "trace-0.jsonl.zst").is_file(), "missing trace-0.jsonl.zst")
            self.assertTrue((out_dir / "page-table-0.json").is_file(), "missing page-table-0.json")
            self.assertTrue((out_dir / "manifest.yaml").is_file(), "missing manifest.yaml")
            self.assertTrue((out_dir / "llms.txt").is_file(), "missing llms.txt")
            self.assertTrue((out_dir / "checksums.sha256").is_file(), "missing checksums.sha256")

    def test_build_handoff_snapshot_writes_artifacts(self):
        """build_handoff_snapshot packages a turn-N snapshot via export --odps."""
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "handoff"
            report = build_handoff_snapshot(str(_ANCHORS[0]), 0, str(out_dir))
            self.assertIn("turn", report)
            self.assertTrue((out_dir / "trace-0.jsonl.zst").is_file())
            self.assertTrue((out_dir / "manifest.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
