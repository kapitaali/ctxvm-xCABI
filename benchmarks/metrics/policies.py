"""Eviction-policy simulator (UC3 §3 build-first) — pure Python over xCABI v0 traces.

Reconstructs the *reference string* demand surface of a recorded trace and
re-runs it under an alternative eviction policy:

  demand kinds (stream order preserved):
  - "serve":  a recorded `page.render` FACT with mode="full" (content WAS served)
  - "recall": a recorded `page.fault` (model/tool asked for the page)

Recorded `page.render` stub facts and `page.evict` facts are the real pager's
answers, so policy-sim REPLACES them (they are not demands). The simulated
stream is evaluated with the SAME 07 formulas as real traces by synthesising an
in-memory xCABI event list — `page.declare` (verbatim), `page.render` (mode=full
on sim bring-in), `page.evict` (on sim eviction), `page.fault` (only when the
simulator actually missed a serving or recall demand, plus recorded recalls
landing on sim-resident pages — real double-fetch facts, preserved verbatim), `turn.render` (per-anchor
sim `residentTokens`), plus `session.open` and `call.meta` copied verbatim so
net-token reduction isolates slot math (recorded cache-miss estimates are kept
on BOTH sides of the reduction).

HONEST SCOPE (mirrors the memo §3 note): policy simulation over a recorded trace
is approximative. The reference string was produced under whatever policy
actually ran; re-running it under another policy reshuffles consequences WITHOUT
the model in the loop — different stubs would have changed what the model asked
next. Simulated metrics are estimates, never ground truth. The simulated event
list is never persisted or emitted as facts (the code returns metrics only).

Engine law (reactive paging, same as v0): eviction happens only when a bring-in
would exceed the budget; no proactive eviction. A demand for a page whose token
size alone exceeds the budget can never be served (`unserviceablePages`).

Policies (v0, deterministic):
- `lru`        : evict the least-recently-used resident page (use = any demand:
                 serve or recall); ties broken by declaration order.
- `fault-pin`  : Pichay-style fault-driven pinning — a page's SECOND demand pins
                 it against eviction for the rest of the trace. When pinned
                 pages alone fill the budget (pin crunch), the demand is served
                 as a miss and counted in `pinCrunch`.
- `size-based` : evict the largest resident page first (memo §3 policy C);
                 ties broken by declaration order.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

POLICIES = ("lru", "fault-pin", "size-based")


def _demand_key(page_id: dict) -> tuple:
    return (page_id.get("logicalRef"), page_id.get("contentHash"))


def reference_string(events: list[dict]) -> Tuple[OrderedDict, list, list]:
    """Extract (declarations, demands, anchors) in stream order.

    declares : OrderedDict[key] -> {"tokens", "kind", "page": raw declare page}
               FIRST declaration wins (RFC-0 redeclare is an idempotent
               observation, not a mutation).
    demands  : [{"kind": "serve" | "recall", "turn": int, "source": str|None,
                 "page": raw demand page dict as recorded}]
    anchors  : turn ints, one per recorded `turn.render` (stream order, not
               sorted — tallies in the real engine are taken at the anchors'
               stream positions).
    """
    declares: "OrderedDict[tuple, dict]" = OrderedDict()
    demands: list[dict] = []
    anchors: list[int] = []
    for e in events:
        t = e["type"]
        if t == "page.declare":
            key = _demand_key(e["page"]["id"])
            if key not in declares:
                declares[key] = e["page"]
        elif t == "page.render" and e.get("mode") == "full":
            demands.append({"kind": "serve", "turn": e["turn"],
                            "source": None, "page": e["page"]})
        elif t == "page.fault":
            demands.append({"kind": "recall", "turn": e["turn"],
                            "source": e.get("source"), "page": e["page"]})
        elif t == "turn.render":
            anchors.append(e["turn"])
    return declares, demands, anchors


class _Sim:
    """Single-policy walk over the reference string. In-memory only."""

    def __init__(self, declares: OrderedDict, policy: str, budget: int):
        self.policy = policy
        self.budget = budget
        self.sizes = {k: v["tokens"] for k, v in declares.items()}
        self.decl_index = {k: i for i, k in enumerate(declares)}
        self.resident: dict[tuple, int] = {}  # key -> last_use stream position
        self.pinned: set = set()
        self.demand_count: dict[tuple, int] = {}
        self.evictions = 0
        self.misses = 0
        self.pin_crunch = 0
        self.unserviceable: set = set()

    @property
    def resident_tokens(self) -> int:
        return sum(self.sizes[k] for k in self.resident)

    # ── victim selection ─────────────────────────────────────────────────
    def _victims(self) -> set:
        if self.policy == "fault-pin":
            return {k for k in self.resident if k not in self.pinned}
        return set(self.resident)

    def _victim(self) -> Optional[tuple]:
        candidates = self._victims()
        if not candidates:
            return None
        if self.policy == "size-based":
            return max(candidates, key=lambda k: (self.sizes[k],
                                                  -self.decl_index[k]))
        # lru (and fault-pin fallback): least-recently-used, decl-order ties
        return min(candidates, key=lambda k: (self.resident[k],
                                              self.decl_index[k]))

    # ── demand handling ──────────────────────────────────────────────────
    def demand(self, key: tuple, pos: int) -> tuple[str, list]:
        """Process one demand; returns ("hit"| "cold" | "pin-crunch" |
        "unserviceable", keys evicted to make room)."""
        self.demand_count[key] = self.demand_count.get(key, 0) + 1
        if (self.policy == "fault-pin"
                and self.demand_count[key] >= 2):
            self.pinned.add(key)  # pin on second demand (served or not)
        if key in self.resident:
            self.resident[key] = pos
            return "hit", []
        tokens = self.sizes[key]
        if tokens > self.budget:
            self.unserviceable.add(key)
            self.misses += 1
            return "unserviceable", []
        evicted: list[tuple] = []
        while self.resident_tokens + tokens > self.budget:
            victim = self._victim()
            if victim is None:
                break  # nothing evictable (pin crunch)
            del self.resident[victim]
            self.evictions += 1
            evicted.append(victim)
        if self.resident_tokens + tokens > self.budget:
            self.pin_crunch += 1  # couldn't fit, couldn't evict pinned pages
            self.misses += 1
            return "pin-crunch", evicted
        self.resident[key] = pos
        self.misses += 1  # cold entry is a demand-page miss (OS-faithful)
        return "cold", evicted


def simulate(events: list[dict], policy: str, budget: int) -> dict:
    """Run the recorded reference string under `policy` at `budget` tokens.

    Returns {"sim_events": [...], "meta": {...}}. The simulated event list
    follows the xCABI v0 shapes the 07 formula functions expect (flat page ids
    for render/evict/fault; nested id for declare) with the SAME turn anchors
    as the recorded trace. Recorded `page.pin`/`page.unpin` rows are realized
    pager residency answers — dropped (like evictions and stub renders) but
    counted in the output as `droppedPinFacts`, so the replacement is visible.
    It is never persisted or emitted as xCABI output — see the module
    docstring for the honest-scope note.
    """
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")
    if budget <= 0:
        raise ValueError("budget must be a positive token count")

    declares, demands, anchors = reference_string(events)
    sim = _Sim(declares, policy, budget)

    # verbatim passthrough: declarations, session.open, call.meta (removed
    # types are recorded page renders/evicts — the realization we replace)
    sim_events: list[dict] = []
    demand_positions: list[int] = []
    anchor_positions: list[int] = []
    passthrough: dict[int, dict] = {}
    dropped_pins = 0
    for pos, e in enumerate(events):
        t = e["type"]
        if t == "page.declare":
            sim_events.append(e)
            demand_positions.append(None)  # placeholder to keep index alignment
            anchor_positions.append(None)
        elif t in ("session.open", "call.meta"):
            sim_events.append(e)
            demand_positions.append(None)
            anchor_positions.append(None)
        elif t == "page.render" and e.get("mode") == "full":
            demand_positions.append(pos)
            anchor_positions.append(None)
        elif t == "page.fault":
            demand_positions.append(pos)
            anchor_positions.append(None)
        elif t == "turn.render":
            anchor_positions.append(pos)
            demand_positions.append(None)
        elif t in ("page.pin", "page.unpin"):
            # recorded-realization facts of the pager that ran (same class as
            # page.evict rows: residency answers, not demands) — dropped like
            # evictions but COUNTED, so the drop is visible in the output
            dropped_pins += 1
        # page.render(mode=stub): recorded pager answer — dropped

    # strip the None placeholders, keep walk order
    walk: list[tuple[int, str, int]] = []
    for idx, (dp, ap) in enumerate(zip(demand_positions, anchor_positions)):
        if dp is not None:
            walk.append((dp, "demand", idx))
        if ap is not None:
            walk.append((ap, "anchor", idx))

    demand_i = 0
    anchor_i = 0
    for event_pos, kind, idx in sorted(walk, key=lambda w: w[0]):
        if kind == "demand":
            d = demands[demand_i]
            demand_i += 1
            key = _demand_key(d["page"])
            if key not in sim.sizes:
                raise ValueError(
                    f"line {event_pos}: {d['kind']} demand for undeclared page "
                    f"{key[0]!r} — policy simulation requires a declared roster")
            state, evicted = sim.demand(key, event_pos)
            turn = d["turn"]
            for vk in evicted:  # make-room evictions precede the answer
                sim_events.append({
                    "type": "page.evict", "turn": turn,
                    "page": {"logicalRef": vk[0], "contentHash": vk[1]},
                })
            fault_evt: dict[str, Any] = {
                "type": "page.fault", "turn": turn, "page": d["page"],
            }
            if d["source"] is not None:
                fault_evt["source"] = d["source"]
            if state == "hit":
                if d["kind"] == "serve":
                    sim_events.append({
                        "type": "page.render", "turn": turn, "page": d["page"],
                        "mode": "full",
                    })
                else:
                    # recorded recall landing on a sim-resident page: a real
                    # double-fetch fact — preserved verbatim (it is demand
                    # evidence, not a pager answer)
                    sim_events.append(fault_evt)
            elif state == "cold":
                sim_events.append(fault_evt)
                sim_events.append({
                    "type": "page.render", "turn": turn, "page": d["page"],
                    "mode": "full",
                })
            else:  # pin-crunch | unserviceable — served-as-miss
                sim_events.append(fault_evt)
        else:
            turn = anchors[anchor_i]
            anchor_i += 1
            sim_events.append({
                "type": "turn.render", "turn": turn,
                "residentTokens": sim.resident_tokens,
            })

    meta = {
        "policy": policy,
        "budget": budget,
        "simEvictions": sim.evictions,
        "simFaults": sim.misses,
        "residentAtEndTokens": sim.resident_tokens,
        "residentAtEndSlots": len(sim.resident),
        "unservicedPages": sorted(f"{k[0]} ({k[1]})" for k in sim.unserviceable),
        "scope": ("estimate: reference string recorded under the real policy; "
                  "policy simulation runs without the model in the loop"),
        "droppedPinFacts": dropped_pins,
    }
    if policy == "fault-pin":
        meta["pinCrunch"] = sim.pin_crunch
        meta["pinnedPages"] = sorted(f"{k[0]} ({k[1]})" for k in sim.pinned)
    return {"sim_events": sim_events, "meta": meta}
