"""UC3-WINDOWSHEET gate — the committed window-family fixture stays reproducible.

RR-UC3-BASELINE finding 3: "P-pathology windows change thrash_index by 3x and
must be part of any thrash claim." This test makes the fixture backing such
claims non-divergible: test_rebuild re-derives the whole sheet in-process
through the same committed implementation (tools/window-sheet.py ->
benchmarks.metrics; no subprocesses) and compares against the committed JSON,
while test_anchor_laws pin the RR-UC3-BASELINE / m5-era values against the
COMMITTED artifact without recomputation.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from benchmarks.metrics.metrics import parse_windows

_REPO = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO / "benchmarks" / "metrics" / "fixtures" / "window-families.json"

_spec = importlib.util.spec_from_file_location(
    "window_sheet", _REPO / "tools" / "window-sheet.py"
)
ws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ws)


@pytest.fixture(scope="module")
def committed() -> dict:
    return json.loads(_FIXTURE.read_text())


@pytest.fixture(scope="module")
def rebuilt() -> dict:
    return ws.build_families()


def test_rebuild_matches_committed_fixture(committed, rebuilt):
    assert committed["traces"] == rebuilt, (
        "window-families.json diverged from a fresh in-process rebuild — "
        "re-run: venvs/odps/bin/python tools/window-sheet.py"
    )
    assert committed["anchors"] == {
        f"{rel} {spec}": want for (rel, spec), want in ws.ANCHORS.items()
    }
    assert committed["family"].startswith("whole + non-overlapping 2-turn windows")


def test_anchor_laws_in_committed_artifact(committed):
    """The pinned laws, read straight from the committed fixture (no recompute):
    RR-UC3-BASELINE finding 3 + the m5/m4 whole-trace capture values."""
    traces = committed["traces"]
    t = traces["corpus/m2/live-thrash.jsonl"]
    assert t["windows"]["0-1"]["thrashIndexMean"] == 5.0
    assert t["whole"]["thrashIndexMean"] == pytest.approx(10 / 6)
    assert traces["corpus/m5/opencode-live-session-01.jsonl"]["whole"]["thrashIndexMean"] \
        == pytest.approx(17 / 14)
    assert traces["corpus/m4/hermes-live-session-01.jsonl"]["whole"]["thrashIndexMean"] == 0.5


def test_family_covers_each_trace_exactly(committed):
    """Structural guarantee of the canonical family: per trace, the committed
    2-turn window specs partition the trace's turn space [0, turns)."""
    for rel, fam in committed["traces"].items():
        spans_sets = [set(range(w[0], w[1] + 1))
                      for w in (parse_windows(spec)[0] for spec in fam["windows"])]
        union: set[int] = set().union(*spans_sets)
        assert union == set(range(fam["turns"])), f"{rel}: windows do not cover 0..turns-1"
        assert sum(map(len, spans_sets)) == len(union), f"{rel}: overlapping windows"
        singles = [spec for spec, sp in zip(fam["windows"], spans_sets) if len(sp) == 1]
        assert len(singles) <= 1, f"{rel}: multiple one-turn windows: {singles}"
        if singles:
            assert int(singles[0]) == fam["turns"] - 1, f"{rel}: single-turn window must trail"
