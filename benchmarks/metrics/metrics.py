"""CtxVM metrics — reference implementation of 07-benchmarks-go-no-go.md formulas.

Formulas (verbatim from `07` §Metric definitions; interpretation choices are
documented inline, never invented silently):

    net_token_reduction = 1 - (paged_net_tokens / naive_tokens)
        where net = rendered tokens + Σ estimated cache-miss cost re-normalization
    refetch_rate       = recovered_faults / evictions   (the OLD fault_recall —
                          a re-fetch rate against the eviction denominator, NOT
                          detection quality; 07 §W3)
    hard_fault_recall  = recovered_hard_faults / hard_faults  (W3 GROUND TRUTH:
                          explicit re-calls only — tool_recall + explicit_api;
                          Pichay §3.2 denominator law, arXiv 2603.09023)
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
- W3 CI law: every gate metric carries a deterministic percentile bootstrap CI
   (random.Random(seed), seed recorded — `bootstrap.py`); `refetch_rate` takes
   NO CI (its per-unit recovery is not well-defined under the eviction
   denominator — continuity metric, not a gate).
- W3 price law: net COST is computed only from an explicit versioned price
   model (`prices.json`); an unknown provider resolves to null with a reason —
   never a silently substituted rate.
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

try:
    from benchmarks.metrics.bootstrap import DEFAULT_REPLICATES, DEFAULT_SEED, bootstrap_ci
except ImportError:  # script invocation: repo root not on sys.path[0]
    from bootstrap import DEFAULT_REPLICATES, DEFAULT_SEED, bootstrap_ci

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


def _recovered_count(faults: list[dict], events: list[dict]) -> int:
    """Recovery law (unchanged): the faulted page has a `page.render` FACT
    (mode=full) at any turn > the fault turn — facts, not derivations."""
    full_render_turns: dict[tuple, list[int]] = defaultdict(list)
    for e in events:
        if e["type"] == "page.render" and e["mode"] == "full":
            full_render_turns[_key(e["page"])].append(e["turn"])
    return sum(
        1
        for e in faults
        if any(t > e["turn"] for t in full_render_turns.get(_key(e["page"]), []))
    )


def refetch_rate(events: list[dict]) -> float | None:
    """The OLD fault_recall formula under its honest name (07 §W3):
    recovered faults / EVICTIONS. Measures the re-fetch rate against the
    eviction denominator — NOT detection quality. Continuity metric; the gate
    is `hard_fault_recall`. (Pichay §3.2: only Read evictions produce faults;
    a denominator that is not ground truth makes the rate unfalsifiable.)"""
    evictions = [e for e in events if e["type"] == "page.evict"]
    if not evictions:
        return None  # undefined without evictions — never fudged
    faults = [e for e in events if e["type"] == "page.fault"]
    return _recovered_count(faults, events) / len(evictions)  # 07 denominator


def hard_fault_recall(events: list[dict]) -> float | None:
    """W3 GROUND TRUTH: detection-quality recall restricted to hard faults —
    explicit re-materializations only (`tool_recall` = the model re-invoked
    the tool; `explicit_api` = the harness re-materialized by explicit API).
    `identifier_scan`/`semantic` are INFERENCE surfaces and never ground
    truth. recovered / hard faults, same recovery law as `refetch_rate`."""
    hs = hard_faults(events)
    if not hs:
        return None  # no hard faults ⇒ recall undefined — never fudged
    return _recovered_count(hs, events) / len(hs)


def fault_recall(events: list[dict]) -> float | None:
    """DEPRECATED name kept for continuity — 07 renamed this `refetch_rate`
    (W3): recovered/evictions is a re-fetch rate, not detection quality. New
    code calls `hard_fault_recall` (the gate metric)."""
    return refetch_rate(events)


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


# ── W3: ground-truth records, deterministic CIs, the explicit price model ────

HARD_FAULT_SOURCES = ("tool_recall", "explicit_api")


def hard_faults(events: list[dict]) -> list[dict]:
    """Ground-truth faults (07 §W3): explicit re-materializations only —
    `tool_recall` (the model re-invoked the tool) and `explicit_api` (the
    harness re-materialized by explicit API). `identifier_scan`/`semantic`
    are INFERENCE surfaces, never ground truth (Pichay §3.2 denominator law:
    only Read evictions produce faults — counting inferred touches blurs the
    denominator and unfalsifies any rate; arXiv 2603.09023)."""
    return [
        e for e in events
        if e["type"] == "page.fault" and e.get("source") in HARD_FAULT_SOURCES
    ]


def _turn_records(events: list[dict]) -> list[dict]:
    """Per-turn cluster records — the honest bootstrap unit for turn-decomposable
    metrics. Each record carries that turn's rendered/miss/touchedNew/faults
    plus the counterfactual naive baseline (every declared page full at every
    turn — the `counterfactual_naive` law; declared_total is constant per turn)."""
    rendered = {e["turn"]: e["residentTokens"] for e in events if e["type"] == "turn.render"}
    misses: dict[int, int] = defaultdict(int)
    for e in events:
        if e["type"] == "call.meta":
            misses[e["turn"]] += e["cacheEstimate"]["estMissTokens"]
    fault_counts: dict[int, int] = defaultdict(int)
    for e in events:
        if e["type"] == "page.fault" and e["turn"] in rendered:
            fault_counts[e["turn"]] += 1
    declared: dict[tuple, int] = {}
    first_fault: dict[tuple, int] = {}
    for e in events:
        if e["type"] == "page.declare":
            k = _key(e["page"]["id"])
            declared[k] = e["page"]["tokens"]
        elif e["type"] == "page.fault":
            k = _key(e["page"])
            if k not in first_fault or e["turn"] < first_fault[k]:
                first_fault[k] = e["turn"]
    declared_total = sum(declared.values())
    return [
        {
            "turn": t,
            "rendered": rendered[t],
            "miss": misses.get(t, 0),
            "touchedNew": sum(
                toks for k, toks in declared.items() if first_fault.get(k) == t
            ),
            "faults": fault_counts.get(t, 0),
            "naive": declared_total,
        }
        for t in sorted(rendered)
    ]


def _stat_touch(records: list[dict]) -> float | None:
    r = sum(x["rendered"] for x in records)
    return None if r == 0 else sum(x["touchedNew"] for x in records) / r


def _stat_waste(records: list[dict]) -> float | None:
    t = _stat_touch(records)
    return None if t is None else 1 - t


def _stat_thrash(records: list[dict]) -> float | None:
    return None if not records else sum(x["faults"] for x in records) / len(records)


def _stat_ntr(records: list[dict]) -> float | None:
    paged = sum(x["rendered"] + x["miss"] for x in records)
    naive = sum(x["naive"] for x in records)
    return None if naive == 0 else 1 - paged / naive


def _hard_fault_records(events: list[dict]) -> list[dict]:
    """Per-hard-fault Bernoulli records (the bootstrap unit for
    hard_fault_recall); recovery is judged against the FULL event set — the
    render facts are fixed context, not resampled."""
    hs = hard_faults(events)
    full_render_turns: dict[tuple, list[int]] = defaultdict(list)
    for e in events:
        if e["type"] == "page.render" and e["mode"] == "full":
            full_render_turns[_key(e["page"])].append(e["turn"])
    return [
        {
            "recovered": any(
                t > e["turn"] for t in full_render_turns.get(_key(e["page"]), [])
            )
        }
        for e in hs
    ]


def _stat_recovered(records: list[dict]) -> float | None:
    return None if not records else sum(1 for x in records if x["recovered"]) / len(records)


def load_prices(path: str) -> dict:
    """The explicit price model (07 §W3): versioned JSON; entries carry source
    + verified status. Unknown providers never silently substitute a rate."""
    return json.loads(Path(path).read_text())


def net_cost(events: list[dict], prices: dict) -> dict:
    """Net cost under the PINNED price model. v0 arithmetic: hit tokens price
    at `usdPer1mCachedRead`, miss tokens at `usdPer1mInput`; cache-write is
    UNMODELED (v0 `call.meta` records hit/miss only). The provider is matched
    EXACTLY as recorded in `call.meta` (the turn-level truth) — an unknown or
    null-priced provider yields `usd: null` + a reason, never a fudged 0."""
    seen: dict[str, dict[str, int]] = {}
    for e in events:
        if e["type"] == "call.meta":
            agg = seen.setdefault(e.get("provider", "?"), {"hit": 0, "miss": 0})
            agg["hit"] += e["cacheEstimate"]["estHitTokens"]
            agg["miss"] += e["cacheEstimate"]["estMissTokens"]
    costs = {}
    for prov in sorted(seen):
        entry = prices.get("providers", {}).get(prov)
        if entry is None:
            costs[prov] = {
                "usd": None,
                "reason": "no price entry — add one with a locator (never substituted)",
            }
            continue
        if entry.get("usdPer1mInput") is None or entry.get("usdPer1mCachedRead") is None:
            costs[prov] = {
                "usd": None,
                "reason": f"UNVERIFIED/null prices ({entry.get('verified', 'unverified')}) — never fudged to 0",
            }
            continue
        agg = seen[prov]
        usd = (agg["hit"] * entry["usdPer1mCachedRead"] + agg["miss"] * entry["usdPer1mInput"]) / 1e6
        costs[prov] = {
            "usd": round(usd, 6),
            "hitTokens": agg["hit"],
            "missTokens": agg["miss"],
            "cacheWrite": "unmodeled in v0 (call.meta has no write premium)",
        }
    return {
        "priceModelVersion": prices.get("priceModelVersion"),
        "netTokens": net_tokens(events),
        "byProvider": costs,
    }


# ── CLI (`python -m benchmarks.metrics.metrics`) ─────────────────────────────


def summarize(
    events: list[dict],
    windows: list[tuple[int, int]] | None = None,
    boot: bool = True,
    seed: int = DEFAULT_SEED,
    replicates: int = DEFAULT_REPLICATES,
) -> dict:
    series, unanchored = fault_series(events)
    tr = touch_ratio(events)
    out = {
        "events": len(events),
        "netTokens": net_tokens(events),
        "refetchRate": refetch_rate(events),
        "faultRecall": refetch_rate(events),  # legacy key — 07 §W3 renamed it
        "hardFaultRecall": hard_fault_recall(events),
        "touchRatio": tr,
        "waste": None if tr is None else 1 - tr,
        "thrashIndex": {"mean": thrash_index(events, windows), "faultsPerTurn": series,
                        "unanchoredFaults": unanchored},
    }
    if boot:
        records = _turn_records(events)
        out["ci"] = {
            "seed": seed,
            "replicates": replicates,
            "touchRatio": bootstrap_ci(records, _stat_touch, replicates=replicates, seed=seed),
            "waste": bootstrap_ci(records, _stat_waste, replicates=replicates, seed=seed),
            "hardFaultRecall": bootstrap_ci(
                _hard_fault_records(events), _stat_recovered, replicates=replicates, seed=seed
            ),
            "netTokenReduction": bootstrap_ci(records, _stat_ntr, replicates=replicates, seed=seed),
            # windowed thrash CI: future work — windows change the unit, the
            # whole-trace case is the one the gate uses
            "thrashIndex": None if windows is not None else bootstrap_ci(
                records, _stat_thrash, replicates=replicates, seed=seed
            ),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CtxVM metrics over an xCABI JSONL trace")
    p.add_argument("trace")
    p.add_argument("--baseline", help="recorded naive-context-stuffing trace (default: counterfactual)")
    p.add_argument("--windows", help="P-pathology windows for thrash_index, e.g. 4-7,9-9")
    p.add_argument("--policy", help="UC3 §3 alternative eviction policy to simulate "
                                    f"(one of {', '.join(POLICIES)}; requires --budget)")
    p.add_argument("--budget", type=int, help="simulated capacity in tokens (requires --policy)")
    p.add_argument("--prices", help="pinned price model (prices.json) — adds netCost")
    p.add_argument("--no-boot", action="store_true", help="skip the deterministic bootstrap CIs")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED, help="bootstrap seed (recorded in output)")
    p.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = p.parse_args(argv)

    if (args.policy is None) != (args.budget is None):
        p.error("--policy and --budget must be used together")

    events = read_events(args.trace)
    windows = parse_windows(args.windows)
    boot_opts = dict(replicates=args.replicates, seed=args.seed)
    if args.policy:
        sim = simulate(events, args.policy, args.budget)
        sim_events = sim["sim_events"]
        out = {"trace": args.trace, **summarize(sim_events, windows, boot=not args.no_boot, **boot_opts)}
        out["netTokenReduction"] = {
            "baseline": "counterfactual-no-paging",
            "value": net_token_reduction(sim_events),
        }
        rec = {"evictions": sum(1 for e in events if e["type"] == "page.evict"),
               "faults": sum(1 for e in events if e["type"] == "page.fault")}
        out["policySim"] = {**sim["meta"], "simEvents": len(sim_events),
                            "recordedRealization": rec}
        if args.prices:
            out["netCost"] = net_cost(sim_events, load_prices(args.prices))
    else:
        out = {"trace": args.trace, **summarize(events, windows, boot=not args.no_boot, **boot_opts)}
        if args.baseline:
            naive = read_events(args.baseline)
            label = f"recorded:{args.baseline}"
        else:
            naive = None
            label = "counterfactual-no-paging"
        out["netTokenReduction"] = {"baseline": label, "value": net_token_reduction(events, naive)}
        if args.prices:
            out["netCost"] = net_cost(events, load_prices(args.prices))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
