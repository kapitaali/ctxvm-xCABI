"""CtxVM metrics — reference implementation of 07-benchmarks-go-no-go.md formulas.

Formulas (verbatim from `07` §Metric definitions; interpretation choices are
documented inline, never invented silently):

    net_token_reduction = 1 - (paged_net_tokens / naive_tokens)
        where net = rendered tokens + Σ estimated cache-miss cost re-normalization
    fault_recall        = recovered_faults / evictions
    touch_ratio         = touched_tokens / rendered_tokens   (waste = 1 - touch_ratio)
    thrash_index        = mean(faults_per_turn) over sustained-pressure windows

Operationalization notes (v0, RFC-0 vocabulary only):
- "rendered tokens"  = Σ `turn.render.residentTokens` (per-turn recorded receipts).
- "touched"          = the only model-behavior surface v0 records is `page.fault`;
                       touched tokens = Σ declared tokens of DISTINCT faulted pages.
                       (A dedicated `page.touch` fact is an RFC-1 candidate — gap,
                       not invention.)
- "recovered_fault"  = the faulted page has a `page.render` FACT (mode=full) at any
                       turn > the fault turn. Derived-schedule recovery is trivially
                       100% by construction (fault@t schedules full@t+1), so facts —
                       not derivations — are the honest signal.
- undecided cases return None (JSON null), never a fudged 0/1 (division by zero,
   unknown denominators).
- `thrash_index` windows: P-pathology defines the sustained-pressure windows; a bare
  trace has none — default is the whole trace, `--windows a-b,c-d` slices it.
- `net_token_reduction` baselines: recorded baseline trace when provided; otherwise
  a *counterfactual* (same session, no paging) — an approximation labeled as such,
  keeping the recorded `call.meta` miss estimates (conservative and honest).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# policy simulator lives beside this module; import works both as an
# installed package (pytest) and as a standalone script (documented CLI)
try:
    from benchmarks.metrics.policies import POLICIES, simulate
except ImportError:  # script invocation: repo root not on sys.path[0]
    from policies import POLICIES, simulate

# ── parsing ──────────────────────────────────────────────────────────────────


def parse_jsonl(text: str) -> list[dict]:
    events = []
    for no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"line {no}: {e}") from e
    return events


def read_events(path: str) -> list[dict]:
    return parse_jsonl(Path(path).read_text())


def _key(page: dict) -> tuple:
    return (page.get("logicalRef"), page.get("contentHash"))


# ── 07 formulas ──────────────────────────────────────────────────────────────


def net_tokens(events: list[dict]) -> dict:
    rendered = sum(e["residentTokens"] for e in events if e["type"] == "turn.render")
    misses = sum(
        e["cacheEstimate"]["estMissTokens"] for e in events if e["type"] == "call.meta"
    )
    return {
        "rendered": rendered,
        "estimatedMisses": misses,
        "total": rendered + misses,  # 07: net = rendered + Σ cache-miss re-norm
    }


def counterfactual_naive(events: list[dict]) -> list[dict]:
    """Simulated no-paging baseline: same declarations, same misses, every page
    full at every observed turn. Labeled approximation — see module docstring."""
    declared: dict[tuple, int] = {}
    turns: set[int] = set()
    kept = []
    for e in events:
        t = e["type"]
        if t == "page.declare":
            declared[_key(e["page"]["id"])] = e["page"]["tokens"]
            kept.append(e)
        elif t in ("session.open", "call.meta"):
            kept.append(e)
        elif t == "turn.render":
            turns.add(e["turn"])
    total = sum(declared.values())
    for turn in sorted(turns):
        kept.append(
            {"type": "turn.render", "turn": turn, "residentTokens": total, "evictedTokens": 0}
        )
    kept.sort(key=lambda e: e.get("turn", -1))
    return kept


def net_token_reduction(paged: list[dict], naive: list[dict] | None = None) -> float | None:
    naive = counterfactual_naive(paged) if naive is None else naive
    naive_total = net_tokens(naive)["total"]
    if naive_total == 0:
        return None
    return 1 - net_tokens(paged)["total"] / naive_total


def fault_recall(events: list[dict]) -> float | None:
    evictions = [e for e in events if e["type"] == "page.evict"]
    if not evictions:
        return None  # undefined without evictions — never fudged
    full_render_turns: dict[tuple, list[int]] = defaultdict(list)
    for e in events:
        if e["type"] == "page.render" and e["mode"] == "full":
            full_render_turns[_key(e["page"])].append(e["turn"])
    recovered = sum(
        1
        for e in events
        if e["type"] == "page.fault"
        and any(t > e["turn"] for t in full_render_turns.get(_key(e["page"]), []))
    )
    return recovered / len(evictions)  # 07 denominator: evictions (not faults)


def touch_ratio(events: list[dict]) -> float | None:
    rendered = sum(e["residentTokens"] for e in events if e["type"] == "turn.render")
    if rendered == 0:
        return None
    declared = {
        _key(e["page"]["id"]): e["page"]["tokens"]
        for e in events
        if e["type"] == "page.declare"
    }
    faulted = {_key(e["page"]) for e in events if e["type"] == "page.fault"}
    touched = sum(tokens for key, tokens in declared.items() if key in faulted)
    return touched / rendered  # 07: waste = 1 - touch_ratio


def waste(events: list[dict]) -> float | None:
    r = touch_ratio(events)
    return None if r is None else 1 - r


def fault_series(events: list[dict]) -> tuple[dict[int, int], list[int]]:
    counts: dict[int, int] = defaultdict(int)
    unanchored: list[int] = []
    turns = {e["turn"] for e in events if e["type"] == "turn.render"}
    for e in events:
        if e["type"] == "page.fault":
            if e["turn"] in turns:
                counts[e["turn"]] += 1
            else:
                unanchored.append(e["turn"])
    return dict(counts), unanchored


def parse_windows(spec: str | None) -> list[tuple[int, int]] | None:
    if not spec:
        return None
    windows = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        windows.append((int(a), int(b) if b else int(a)))
    return windows


def thrash_index(events: list[dict], windows: list[tuple[int, int]] | None = None) -> float | None:
    """Mean faults-per-turn over the window's turns (zero-fault turns included),
    or over the whole trace when no P-pathology windows are given."""
    turns_all = sorted({e["turn"] for e in events if e["type"] == "turn.render"})
    if not turns_all:
        return None
    counts, _unanchored = fault_series(events)
    if windows is None:
        selected = turns_all
    else:
        selected = [t for t in turns_all if any(a <= t <= b for (a, b) in windows)]
        if not selected:
            return None
    return sum(counts.get(t, 0) for t in selected) / len(selected)


# ── CLI (`python -m benchmarks.metrics.metrics`) ─────────────────────────────


def summarize(events: list[dict], windows: list[tuple[int, int]] | None = None) -> dict:
    series, unanchored = fault_series(events)
    net = net_tokens(events)
    recall = fault_recall(events)
    tr = touch_ratio(events)
    return {
        "events": len(events),
        "netTokens": net,
        "faultRecall": recall,
        "touchRatio": tr,
        "waste": None if tr is None else 1 - tr,
        "thrashIndex": {"mean": thrash_index(events, windows), "faultsPerTurn": series,
                        "unanchoredFaults": unanchored},
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CtxVM metrics over an xCABI JSONL trace")
    p.add_argument("trace")
    p.add_argument("--baseline", help="recorded naive-context-stuffing trace (default: counterfactual)")
    p.add_argument("--windows", help="P-pathology windows for thrash_index, e.g. 4-7,9-9")
    p.add_argument("--policy", help="UC3 §3 alternative eviction policy to simulate "
                                    f"(one of {', '.join(POLICIES)}; requires --budget)")
    p.add_argument("--budget", type=int, help="simulated capacity in tokens (requires --policy)")
    args = p.parse_args(argv)

    if (args.policy is None) != (args.budget is None):
        p.error("--policy and --budget must be used together")

    events = read_events(args.trace)
    windows = parse_windows(args.windows)
    if args.policy:
        sim = simulate(events, args.policy, args.budget)
        sim_events = sim["sim_events"]
        out = {"trace": args.trace, **summarize(sim_events, windows)}
        out["netTokenReduction"] = {
            "baseline": "counterfactual-no-paging",
            "value": net_token_reduction(sim_events),
        }
        rec = {"evictions": sum(1 for e in events if e["type"] == "page.evict"),
               "faults": sum(1 for e in events if e["type"] == "page.fault")}
        out["policySim"] = {**sim["meta"], "simEvents": len(sim_events),
                            "recordedRealization": rec}
    else:
        out = {"trace": args.trace, **summarize(events, windows)}
        if args.baseline:
            naive = read_events(args.baseline)
            label = f"recorded:{args.baseline}"
        else:
            naive = None
            label = "counterfactual-no-paging"
        out["netTokenReduction"] = {"baseline": label, "value": net_token_reduction(events, naive)}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
