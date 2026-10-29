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
    hard_fault_recall,
    hard_faults,
    load_prices,
    net_cost,
    net_tokens,
    net_token_reduction,
    parse_jsonl,
    refetch_rate,
    summarize,
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


# ── W3: ground truth (hard faults), deterministic CIs, the price model ───────
# Every expectation hand-computed; undefined is None, never fudged.


class TestW3GroundTruth:
    def test_refetch_rate_is_the_old_formula(self) -> None:
        # 07 §W3 rename: same arithmetic fault_recall ever had (2/4)
        assert refetch_rate(THRASH) == pytest.approx(0.5)
        assert fault_recall(THRASH) == refetch_rate(THRASH)  # legacy alias

    def test_hard_fault_recall_on_thrash_is_2_over_2(self) -> None:
        # ground truth = explicit re-calls only: B@2 + B@6 (tool_recall);
        # A@9 is identifier_scan — an INFERENCE surface, excluded.
        # recovered: B@2 (full render fact @3), B@6 (full render fact @7) ⇒ 2/2.
        assert hard_fault_recall(THRASH) == pytest.approx(1.0)

    def test_hard_fault_recall_undefined_without_hard_faults(self) -> None:
        # HEALTHY's single fault is identifier_scan — no ground truth ⇒ None
        assert hard_fault_recall(HEALTHY) is None
        assert hard_fault_recall([]) is None

    def test_identifier_scan_never_enters_ground_truth(self) -> None:
        e = [
            {"type": "page.declare", "page": {"id": {"logicalRef": "x", "contentHash": "h"},
                                              "kind": "file", "tokens": 10}},
            {"type": "page.render", "turn": 1, "page": {"logicalRef": "x", "contentHash": "h"},
             "mode": "full"},
            {"type": "page.fault", "turn": 0, "page": {"logicalRef": "x", "contentHash": "h"},
             "source": "identifier_scan"},
        ]
        assert hard_faults(e) == []
        assert hard_fault_recall(e) is None

    def test_semantic_is_also_not_ground_truth(self) -> None:
        e = [{"type": "page.fault", "turn": 0,
              "page": {"logicalRef": "x", "contentHash": "h"}, "source": "semantic"}]
        assert hard_faults(e) == []


class TestW3Bootstrap:
    def test_ci_is_deterministic_same_seed(self) -> None:
        assert summarize(THRASH)["ci"] == summarize(THRASH)["ci"]

    def test_single_turn_record_ci_collapses_to_the_point(self) -> None:
        # one turn ⇒ every resample is the same record ⇒ ci95 == [point, point]
        one = [
            {"type": "page.declare", "page": {"id": {"logicalRef": "x", "contentHash": "h"},
                                              "kind": "file", "tokens": 50}},
            {"type": "turn.render", "turn": 0, "residentTokens": 100, "evictedTokens": 0},
            {"type": "page.fault", "turn": 0, "page": {"logicalRef": "x", "contentHash": "h"},
             "source": "tool_recall"},
        ]
        ci = summarize(one)["ci"]["touchRatio"]
        assert ci["point"] == pytest.approx(0.5)
        assert ci["ci95"] == [pytest.approx(0.5), pytest.approx(0.5)]
        assert ci["failed"] == 0
        assert ci["seed"] == 20261029

    def test_undefined_replicates_are_dropped_never_fudged(self) -> None:
        zero = [
            {"type": "turn.render", "turn": 0, "residentTokens": 0, "evictedTokens": 9},
        ]
        ci = summarize(zero)["ci"]["touchRatio"]
        assert ci["point"] is None
        assert ci["ci95"] is None
        assert ci["successful"] == 0
        assert ci["failed"] == ci["replicates"]

    def test_hard_fault_recall_ci_on_thrash_is_constant_one(self) -> None:
        # both hard faults recovered ⇒ every replicate is 1.0
        ci = summarize(THRASH)["ci"]["hardFaultRecall"]
        assert ci["point"] == pytest.approx(1.0)
        assert ci["ci95"] == [1.0, 1.0]

    def test_refetch_rate_takes_no_ci_by_law(self) -> None:
        # the eviction-denominator metric is continuity-only (07 §W3)
        assert "refetchRate" not in summarize(THRASH)["ci"]


class TestW3Prices:
    def test_pinned_model_shape(self) -> None:
        prices = load_prices(str(HERE / "prices.json"))
        assert prices["priceModelVersion"] >= 1
        assert prices["providers"]["nvidia"]["verified"] == "observed"
        assert prices["providers"]["nvidia"]["usdPer1mInput"] == 0.0
        assert prices["providers"]["openai"]["usdPer1mInput"] is None  # UNVERIFIED

    def test_net_cost_arithmetic_with_a_test_entry(self) -> None:
        trace = [
            {"type": "call.meta", "turn": 0, "provider": "testprov",
             "cacheEstimate": {"estHitTokens": 300, "estMissTokens": 200,
                               "providerReported": False}},
            {"type": "turn.render", "turn": 0, "residentTokens": 1000, "evictedTokens": 0},
        ]
        prices = {"priceModelVersion": 1, "providers": {"testprov": {
            "usdPer1mInput": 1.0, "usdPer1mCachedRead": 0.1, "usdPer1mCacheWrite": None,
            "verified": "test", "source": "test"}}}
        out = net_cost(trace, prices)
        # (300 hit × 0.1 + 200 miss × 1.0) / 1e6 = 230 / 1e6
        assert out["byProvider"]["testprov"]["usd"] == pytest.approx(230 / 1e6)

    def test_unknown_provider_never_substitutes_a_rate(self) -> None:
        trace = [{"type": "call.meta", "turn": 0, "provider": "ghost",
                  "cacheEstimate": {"estHitTokens": 1, "estMissTokens": 1,
                                    "providerReported": False}}]
        out = net_cost(trace, load_prices(str(HERE / "prices.json")))
        assert out["byProvider"]["ghost"]["usd"] is None
        assert "no price entry" in out["byProvider"]["ghost"]["reason"]

    def test_null_priced_provider_is_unverified_never_zero(self) -> None:
        # HEALTHY's call.meta names openai — synthetic fixtures, no real spend
        out = net_cost(HEALTHY, load_prices(str(HERE / "prices.json")))
        assert out["byProvider"]["openai"]["usd"] is None
        assert "UNVERIFIED" in out["byProvider"]["openai"]["reason"]
