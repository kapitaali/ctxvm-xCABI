"""UC3 §3 build-first tests: eviction-policy simulator (policies.py).

Every expected number below was computed BY HAND against 07's formulas run
over the simulated event stream (same reference implementations as real
traces). Non-integer comparisons use approx; None asserts exactly — undefined
is never fudged.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.metrics.metrics import (
    counterfactual_naive,
    net_token_reduction,
    summarize,
)
from benchmarks.metrics.policies import POLICIES, reference_string, simulate

HERE = Path(__file__).parent
THRASHING_TEXT = (HERE / "fixtures" / "session-thrashing.jsonl").read_text()


def parse(text: str) -> list[dict]:
    from benchmarks.metrics.metrics import parse_jsonl
    return parse_jsonl(text)


def ev_open() -> dict:
    return {"type": "session.open", "agentId": "sim-test", "model": "m",
            "provider": "p", "budgetTokens": 10_000, "tokenizerId": "t"}


def ev_declare(ref: str, h: str, tokens: int, kind: str = "file") -> dict:
    return {"type": "page.declare",
            "page": {"id": {"logicalRef": ref, "contentHash": h},
                     "kind": kind, "tokens": tokens}}


def ev_serve(ref: str, h: str, turn: int) -> dict:
    return {"type": "page.render", "turn": turn,
            "page": {"logicalRef": ref, "contentHash": h}, "mode": "full"}


def ev_fault(ref: str, h: str, turn: int, source: str = "tool_recall") -> dict:
    return {"type": "page.fault", "turn": turn,
            "page": {"logicalRef": ref, "contentHash": h}, "source": source}


def ev_anchor(turn: int, resident: int) -> dict:
    # recorded residentTokens are replaced by the sim's own anchor tallies
    return {"type": "turn.render", "turn": turn, "residentTokens": resident}


def ev_meta(turn: int, miss: int = 0) -> dict:
    return {"type": "call.meta", "turn": turn,
            "cacheEstimate": {"estMissTokens": miss}}


def trace_A_B(anchors: dict[int, int]) -> list[dict]:
    """AAA hand paper: A=100 served@0 (@1), B=200 served@0 (@2),
    anchors after each turn's demands (recorded numbers replaced)."""
    return [
        ev_open(),
        ev_declare("file:A", "sha256:a", 100),
        ev_declare("file:B", "sha256:b", 200),
        ev_serve("file:A", "sha256:a", 0),
        ev_serve("file:B", "sha256:b", 0),
        ev_anchor(0, anchors[0]),
        ev_serve("file:A", "sha256:a", 1),
        ev_anchor(1, anchors[1]),
        ev_serve("file:B", "sha256:b", 2),
        ev_anchor(2, anchors[2]),
        ev_meta(2),
    ]


# ── S1 lru rotation (budget 250 < 300 declared) ──────────────────────────────
# walks: A@0 cold (100 ≤ 250) → B@0 needs 300 > 250 → evict LRU=A → B in
#        → A@1 cold: evict LRU=B → A in → B@2 cold: evict LRU=A → B in
# sim evictions 3 (one per post-first bring-in), misses = cold × 4
# (A@0, B@0, A@1, B@2); anchors: t0 B=200, t1 A=100, t2 B=200.
# rendered = 200+100+200 = 500; naive = 300×3 = 900 (miss 0 both sides)
# → NTR = 1 − 500/900 = 0.44444…  recall = 2/3 — faults A@0,B@0,A@1,B@2:
#   A@0 → A rendered@1 > 0 ✓; B@0 → B rendered@2 ✓; A@1 → later A render? none ✗;
#   B@2 → none ✗ → recovered 2 / evictions 3 = 2/3. touch = 300/500 = 0.6.
# thrash mean = 4 faults / 3 anchored turns = 1.3333…
def test_lru_rotation_hand_summed():
    events = trace_A_B({0: 0, 1: 0, 2: 0})
    out = simulate(events, "lru", 250)
    sim, meta = out["sim_events"], out["meta"]
    assert meta["policy"] == "lru" and meta["budget"] == 250
    assert meta["simEvictions"] == 3
    assert meta["simFaults"] == 4  # four cold entries
    assert meta["residentAtEndTokens"] == 200
    assert meta["residentAtEndSlots"] == 1
    summary = summarize(sim)
    assert summary["netTokens"] == {"rendered": 500, "estimatedMisses": 0, "total": 500}
    assert summary["faultRecall"] == pytest.approx(2 / 3)
    assert summary["touchRatio"] == pytest.approx(0.6)
    assert summary["waste"] == pytest.approx(0.4)
    assert summary["thrashIndex"]["mean"] == pytest.approx(4 / 3)
    reduction = net_token_reduction(sim)
    assert reduction == pytest.approx(1 - 500 / 900)


# ── S2 fault-pin: second demand pins (over the same demands) ─────────────────
# A@0 cold(100≤250, not pinned) → B@0: 300>250 → evict unpinned A → B in
# A@1: demand #2 → PIN A; cold: evict unpinned B → A in
# B@2: demand #2 → PIN B (not resident); bring-in: unpinned candidates none,
#        100+200 > 250 → PIN CRUNCH miss (B not served)
# evictions 2, pinCrunch 1, misses 4 (cold ×3 + crunch ×1)
# anchors: t0 B=200; t1 A=100; t2 A=100 → rendered 400 → NTR = 1 − 400/900
# recall: A@0 → A rendered@1 ✓; B@0 → no later B render ✗; A@1 ✗; B@2 ✗
#   → 1/2 = 0.5.  touch = faulted {A,B} = 300/400 = 0.75. thrash = 4/3.
def test_fault_pin_second_demand_pins_and_crunches():
    events = trace_A_B({0: 0, 1: 0, 2: 0})
    out = simulate(events, "fault-pin", 250)
    sim, meta = out["sim_events"], out["meta"]
    assert meta["simEvictions"] == 2
    assert meta["pinCrunch"] == 1
    assert meta["simFaults"] == 4
    assert set(meta["pinnedPages"]) == {"file:A (sha256:a)", "file:B (sha256:b)"}
    summary = summarize(sim)
    assert summary["netTokens"]["rendered"] == 400
    assert summary["faultRecall"] == pytest.approx(0.5)
    assert summary["touchRatio"] == pytest.approx(0.75)
    assert summary["thrashIndex"]["mean"] == pytest.approx(4 / 3)
    assert net_token_reduction(sim) == pytest.approx(1 - 400 / 900)


# ── S3 size-based victim + declaration-order tie-break ───────────────────────
# Three equal pages A,B,C = 100 tok each, budget 250, demands:
# A@0 cold (resident 100) → B@0 cold (200 ≤ 250) → C@1: 300 > 250 → victim tie
# (100 == 100) broken by declaration order → A evicted, C in → A@2 cold:
# candidates {B,C} tie → B (index 1) evicted, A in.
# evictions exactly 2, victims [A, B] in that order; anchors: t0 {A,B} = 200,
# t1 {B,C} = 200, t2 {A,C} = 200 → rendered 600. faults = 4 colds. recall:
# recovered = 1/2 → A@0 is covered by A's later full render @2 (A re-served
# after being evicted); B@0's only render is self-served @0 → unrecovered.
# touch = 300/600 = 0.5; thrash = 4/3; residentAtEnd = {A,C} = 200.
def test_size_based_evicts_largest_then_ties_by_declaration():
    events = [
        ev_open(),
        ev_declare("file:A", "sha256:a", 100),
        ev_declare("file:B", "sha256:b", 100),
        ev_declare("file:C", "sha256:c", 100),
        ev_serve("file:A", "sha256:a", 0),
        ev_serve("file:B", "sha256:b", 0),
        ev_anchor(0, 0),
        ev_serve("file:C", "sha256:c", 1),
        ev_anchor(1, 0),
        ev_serve("file:A", "sha256:a", 2),
        ev_anchor(2, 0),
    ]
    out = simulate(events, "size-based", 250)
    sim, meta = out["sim_events"], out["meta"]
    assert meta["simEvictions"] == 2
    victims = [e["page"]["logicalRef"] for e in sim if e["type"] == "page.evict"]
    assert victims == ["file:A", "file:B"]  # declaration-order tie-break
    assert "pinCrunch" not in meta  # fault-pin-only metadata absent
    assert meta["residentAtEndTokens"] == 200
    tallies = [e["residentTokens"] for e in sim if e["type"] == "turn.render"]
    assert tallies == [200, 200, 200]
    summary = summarize(sim)
    assert summary["netTokens"]["rendered"] == 600
    assert summary["faultRecall"] == pytest.approx(0.5)  # A@0 → A render@2
    assert meta["simFaults"] == 4
    assert summary["touchRatio"] == pytest.approx(0.5)
    assert summary["thrashIndex"]["mean"] == pytest.approx(4 / 3)


# ── S4 unserviceable serving miss (page larger than budget) ──────────────────
def test_unserviceable_page_never_resident_but_misses():
    events = [
        ev_open(),
        ev_declare("file:big", "sha256:z", 500),
        ev_declare("file:small", "sha256:s", 100),
        ev_serve("file:small", "sha256:s", 0),
        ev_serve("file:big", "sha256:z", 0),
        ev_fault("file:big", "sha256:z", 1, source="identifier_scan"),
        ev_anchor(0, 0),
        ev_anchor(1, 0),
    ]
    out = simulate(events, "lru", 300)
    sim, meta = out["sim_events"], out["meta"]
    assert meta["unservicedPages"] == ["file:big (sha256:z)"]
    assert meta["simFaults"] == 3  # cold small + big's serve miss + big recall
    assert meta["residentAtEndTokens"] == 100
    assert meta["simEvictions"] == 0  # the small page is never forced out
    # recorded demand sources preserved on the synthetic stream verbatim
    srcs = [e.get("source") for e in sim if e["type"] == "page.fault"]
    assert srcs == [None, None, "identifier_scan"]
    tallies = [e["residentTokens"] for e in sim if e["type"] == "turn.render"]
    assert tallies == [100, 100]


# ── S5 recorded faults on sim-resident pages are touches, not faults ─────────
# budget ≥ roster: everything resident after first serves; the recorded
# tool_recall faults become plain hits (no sim fault events at all).
def test_resident_recalls_are_touches_under_capacity():
    events = [
        ev_open(),
        ev_declare("file:A", "sha256:a", 100),
        ev_serve("file:A", "sha256:a", 0),
        ev_fault("file:A", "sha256:a", 1),  # double-fetch on resident page
        ev_anchor(0, 0),
        ev_anchor(1, 0),
    ]
    out = simulate(events, "lru", 1000)
    sim, meta = out["sim_events"], out["meta"]
    assert meta["simFaults"] == 1  # only A's cold entry (the hit is a touch)
    assert meta["simEvictions"] == 0
    # stream shape: cold serve = fault + render; the recorded double-fetch on
    # the resident page survives verbatim as demand evidence
    kinds = [e["type"] for e in sim if e["type"] in ("page.fault", "page.render")]
    assert kinds == ["page.fault", "page.render", "page.fault"]
    summary = summarize(sim)
    # thrashIndex counts stream fault events (incl. the double-fetch):
    assert summary["thrashIndex"]["mean"] == pytest.approx(1.0)


# ── S6 all-empty reference string: honest nulls ──────────────────────────────
def test_no_demands_gives_null_summary():
    events = [ev_open(), ev_declare("file:A", "sha256:a", 100)]
    out = simulate(events, "size-based", 50)
    assert out["meta"]["simEvictions"] == 0
    assert out["meta"]["simFaults"] == 0
    summary = summarize(out["sim_events"])
    assert summary["thrashIndex"]["mean"] is None
    assert summary["touchRatio"] is None
    assert summary["faultRecall"] is None
    # naive side still counts the never-served roster:
    naive = counterfactual_naive(out["sim_events"])
    from benchmarks.metrics.metrics import net_tokens
    assert net_tokens(naive)["total"] == 0  # no anchors → zero naive total


# ── S7 integration: the real thrashing fixture at EXACT roster capacity ──────
# budget 1400 = full roster (1000+400): reactive law evicts NOTHING, so the
# recorded realization's designed evictions (4) are policy-induced, not
# capacity-induced — the sim's honest capacity-conditional counterfactual.
def test_fixture_at_roster_capacity_reports_zero_policy_evictions():
    events = parse(THRASHING_TEXT)
    out = simulate(events, "lru", 1400)
    sim, meta = out["sim_events"], out["meta"]
    assert meta["simEvictions"] == 0
    assert meta["simFaults"] == 2  # two cold entries; recorded recalls = hits
    assert out["meta"]["recordedRealization" if False else "residentAtEndTokens"] == 1400
    summary = summarize(sim)
    # anchors all full-roster → rendered 1400×10; recorded misses kept: 300
    assert summary["netTokens"] == {"rendered": 14000, "estimatedMisses": 300,
                                    "total": 14300}
    assert net_token_reduction(sim) == pytest.approx(0.0)  # == naive exactly
    assert summary["faultRecall"] is None  # no sim evictions → undefined
    # stream: 2 cold entries + preserved double-fetch faults on resident pages
    assert summary["thrashIndex"]["faultsPerTurn"] == {0: 2, 2: 1, 6: 1, 9: 1}
    assert summary["thrashIndex"]["mean"] == pytest.approx(0.5)
    assert summary["touchRatio"] == pytest.approx(0.1)  # 1400 fault-touched / 14000


# ── S8 contract errors fail fast ─────────────────────────────────────────────
def test_contract_errors_are_valueerrors():
    events = parse(THRASHING_TEXT)
    with pytest.raises(ValueError, match="unknown policy"):
        simulate(events, "fifo", 1400)
    with pytest.raises(ValueError, match="budget"):
        simulate(events, "lru", 0)
    # undeclared demand:
    with pytest.raises(ValueError, match="undeclared"):
        simulate([ev_open(), ev_declare("file:A", "sha256:a", 100),
                  ev_serve("file:B", "sha256:b", 0)], "lru", 1400)
    # recorded pin facts are pager residency answers — dropped but counted:
    pin_tr = [ev_open(), ev_declare("file:A", "sha256:a", 100),
              {"type": "page.pin", "turn": 0,
               "page": {"logicalRef": "file:A", "contentHash": "sha256:a"}},
              ev_serve("file:A", "sha256:a", 0)]
    out = simulate(pin_tr, "lru", 1400)
    assert out["meta"]["droppedPinFacts"] == 1
    # sim stream: open + declare + cold serve (fault + render) = 4 rows
    assert len(out["sim_events"]) == 4


# ── S9 reference-string extraction ───────────────────────────────────────────
# thrashing fixture anatomy: serves = A@0-4 (5) + B@0,3,7 (3) = 8 full renders;
# recalls = B@2, B@6, A@9 = 3; anchors = the 10 recorded turn.render turns.
def test_reference_string_contract():
    events = parse(THRASHING_TEXT)
    declares, demands, anchors = reference_string(events)
    assert len(declares) == 2 and len(demands) == 11
    kinds = [d["kind"] for d in demands]
    assert kinds.count("serve") == 8
    assert kinds.count("recall") == 3
    assert anchors == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
