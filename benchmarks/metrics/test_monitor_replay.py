"""W18 tier-1 monitor replay: the harness is deterministic, and the labels are honest.

The assertions here are deliberately about MECHANICS, not about discrimination. The
corpus has four pathology positives and thirteen benign traces with scenario labels, so
any TPR/FPR claim would be an anecdote; what must hold is that the replay is a pure
function of the bytes, abstains instead of guessing, and covers exactly the frozen corpus.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.metrics.monitor_replay import (
    LABELS_PATH,
    MONITORS,
    REPO_ROOT,
    RESULTS_PATH,
    dumps,
    evaluate,
    decide,
    wilson,
)

CORPUS = sorted(str(p.relative_to(REPO_ROOT)) for p in (REPO_ROOT / "corpus").glob("m*/*.jsonl"))


def test_labels_cover_exactly_the_frozen_corpus() -> None:
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    covered = sorted(item["path"] for item in labels["traces"])
    assert covered == CORPUS, "every corpus trace needs a label and no label may dangle"
    assert len(set(covered)) == len(covered), "a trace must not be labelled twice"


def test_every_label_cites_a_basis() -> None:
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    assert labels["basis"].startswith("Scenario labels only"), "the honest scope must travel"
    for item in labels["traces"]:
        assert item["label"] in {"pathology", "benign"}
        assert len(item["basis"]) > 20, f"{item['path']} needs its label's source sentence"


def test_decide_abstains_on_undefined_features() -> None:
    assert decide(None, 0.5) is None, "an undefined feature is an abstention, never a value"
    assert decide(0.5, 0.5) is False, "the rule is strict greater-than"
    assert decide(0.5001, 0.5) is True


def test_wilson_interval_is_bounded_and_widens_with_small_n() -> None:
    wide = wilson(2, 4)
    narrow = wilson(200, 400)
    assert wide is not None and narrow is not None
    assert 0.0 <= wide[0] < 0.5 < wide[1] <= 1.0
    assert (narrow[1] - narrow[0]) < (wide[1] - wide[0])
    assert wilson(0, 0) is None, "n=0 is undefined"


def test_replay_is_a_pure_function_of_the_bytes() -> None:
    first = dumps(evaluate())
    second = dumps(evaluate())
    assert first == second, "two runs over frozen traces must agree byte for byte"


def test_committed_results_are_current() -> None:
    assert RESULTS_PATH.exists(), "monitor-results.json is the committed record"
    assert RESULTS_PATH.read_text(encoding="utf-8") == dumps(evaluate()), (
        "results are stale: rerun python -m benchmarks.metrics.monitor_replay --json"
    )


def test_every_monitor_records_its_kind_and_rule() -> None:
    results = evaluate()
    for name, spec in MONITORS.items():
        assert spec["kind"] in {"diagnostic", "detector"}
        assert name in results["summary"]
        assert results["summary"][name]["rule"] == spec["rule"]
    # The fault-derived rule shares a cause with the thrash label; it must not be able
    # to present itself as evidence.
    assert results["summary"]["fault_density"]["kind"] == "diagnostic"


@pytest.mark.parametrize("name", sorted(MONITORS))
def test_summary_counts_account_for_every_trace(name: str) -> None:
    results = evaluate()
    s = results["summary"][name]
    assert s["tp"] + s["fn"] + s["fp"] + s["tn"] + s["abstain"] == results["corpus"]["traces"]
