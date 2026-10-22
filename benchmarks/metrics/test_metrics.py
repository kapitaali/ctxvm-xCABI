"""T3 DoD tests: two synthetic sessions (healthy, thrashing) + edge cases.

Every expected number below was computed BY HAND against 07's formulas
(see reports/RR-T3 for the arithmetic). Non-integer comparisons use approx;
None (undefined) cases assert exactly        — undefined is never fudged.
"""
from __future__ import annotations

import pytest

from benchmarks.metrics.metrics import (
    counterfactual_naive,
    fault_recall,
    fault_series,
    net_tokens,
    net_token_reduction,
    parse_jsonl,
    thrash_index,
    touch_ratio,
    waste,
)

from pathlib import Path

HERE = Path(__file__).parent
HEALTHY = parse_jsonl((HERE / "fixtures" / "session-healthy.jsonl").read_text())
THRASH = parse_jsonl((HERE / "fixtures" / "session-thrashing.jsonl").read_text())


# ── healthy session: 3 pages (700+8200+60), 3 turns × 8960 rendered, ──────────
# one resident-page fault (summary touch), one call.meta (200 est. misses).
class TestHealthy:
    def test_net_tokens(self) -> None:
        net = net_tokens(HEALTHY)
        assert net == {"rendered": 26880, "estimatedMisses": 200, "total": 27080}

    def test_counterfactual_is_identical_for_a_never_paged_trace(self) -> None:
        assert net_tokens(counterfactual_naive(HEALTHY))["total"] == 27080

    def test_net_token_reduction_is_zero_without_paging(self) -> None:
        assert net_token_reduction(HEALTHY) == pytest.approx(0.0)

    def test_fault_recall_undefined_without_evictions(self) -> None:
        assert fault_recall(HEALTHY) is None

    def test_touch_ratio_from_the_single_summary_touch(self) -> None:
        # touched = 60 (only C faulted) / rendered 26880
        assert touch_ratio(HEALTHY) == pytest.approx(60 / 26880)
        assert waste(HEALTHY) == pytest.approx(1 - 60 / 26880)

    def test_thrash_mean_over_all_turns(self) -> None:
        assert thrash_index(HEALTHY) == pytest.approx(1 / 3)


# ── thrashing session: A=1000 + B=400; resident trace. ───────────────────────
# resident per turn [1400,1000,1000,1400,1000,0,0,400,0,0] ⇒ 6200 rendered.
# (Plan-phase hand-sum said 7200 — wrong; corrected against the fixture in RR-T3.)
# evictions: B@1 B@4 A@5 B@8 = 4 · faults: B@2 B@6 A@9 = 3
# recovered (full render FACT after fault): B@2(@3) B@6(@7) = 2 — A is never
# re-rendered, B@4 was evicted faultlessly ⇒ recall 2/4 = 0.5.
class TestThrashing:
    def test_net_tokens(self) -> None:
        net = net_tokens(THRASH)
        assert net == {"rendered": 6200, "estimatedMisses": 300, "total": 6500}

    def test_counterfactual_raises_the_naive_baseline(self) -> None:
        naive = net_tokens(counterfactual_naive(THRASH))
        assert naive == {"rendered": 14000, "estimatedMisses": 300, "total": 14300}

    def test_net_token_reduction(self) -> None:
        # 6500 / 14300 = 5/11 ⇒ reduction = 6/11
        assert net_token_reduction(THRASH) == pytest.approx(1 - 6500 / 14300)

    def test_fault_recall_uses_evictions_as_denominator(self) -> None:
        assert fault_recall(THRASH) == pytest.approx(2 / 4)  # = 0.5

    def test_touch_ratio_dedupes_faulted_pages(self) -> None:
        # A and B both faulted ⇒ touched 1400 / rendered 6200 (B faulted twice: once)
        assert touch_ratio(THRASH) == pytest.approx(1400 / 6200)

    def test_thrash_index_means_over_all_ten_turns(self) -> None:
        assert thrash_index(THRASH) == pytest.approx(3 / 10)

    def test_thrash_index_windows_use_window_turn_count(self) -> None:
        # window turns 7-9: one fault (A@9) over 3 turns ⇒ 1/3
        assert thrash_index(THRASH, [(7, 9)]) == pytest.approx(1 / 3)
        # window 2-3: one fault (B@2) over 2 turns
        assert thrash_index(THRASH, [(2, 3)]) == pytest.approx(0.5)


class TestEdges:
    def test_empty_trace(self) -> None:
        e = []
        assert net_tokens(e) == {"rendered": 0, "estimatedMisses": 0, "total": 0}
        assert fault_recall(e) is None
        assert touch_ratio(e) is None
        assert waste(e) is None
        assert thrash_index(e) is None
        assert net_token_reduction(e) is None

    def test_zero_rendered_due_to_total_stubbing(self) -> None:
        stubbed = [
            {"type": "page.declare", "page": {"id": {"logicalRef": "x", "contentHash": "h"},
                                              "kind": "file", "tokens": 10}},
            {"type": "page.evict", "turn": 0, "page": {"logicalRef": "x", "contentHash": "h"}},
            {"type": "turn.render", "turn": 0, "residentTokens": 0, "evictedTokens": 9},
            {"type": "page.fault", "turn": 0, "page": {"logicalRef": "x", "contentHash": "h"},
             "source": "identifier_scan"},
        ]
        assert touch_ratio(stubbed) is None  # 0 rendered ⇒ ratio undefined
        assert fault_recall(stubbed) == 0.0  # 1 eviction, 0 recovered facts

    def test_unknown_faulted_page_adds_nothing_to_touched(self) -> None:
        t = [
            {"type": "page.declare", "page": {"id": {"logicalRef": "ok", "contentHash": "h1"},
                                              "kind": "file", "tokens": 100}},
            {"type": "turn.render", "turn": 0, "residentTokens": 100, "evictedTokens": 0},
            {"type": "page.fault", "turn": 0, "page": {"logicalRef": "ghost", "contentHash": "h"},
             "source": "identifier_scan"},
        ]
        assert touch_ratio(t) == pytest.approx(0.0)

    def test_thrash_ignores_unanchored_fault_turns(self) -> None:
        e = [
            {"type": "turn.render", "turn": 0, "residentTokens": 1, "evictedTokens": 0},
            {"type": "page.fault", "turn": 99, "page": {"logicalRef": "x", "contentHash": "h"},
             "source": "tool_recall"},
        ]
        series, unanchored = fault_series(e)
        assert series == {}
        assert unanchored == [99]
        assert thrash_index(e) == pytest.approx(0.0)  # 1 turn, 0 anchored faults

    def test_fixture_text_is_strict_jsonl(self) -> None:
        for f in ("session-healthy.jsonl", "session-thrashing.jsonl"):
            text = (HERE / "fixtures" / f).read_text()
            for line in text.splitlines():
                if line.strip():
                    parse_jsonl(line)  # raises on non-object/malformed JSON
