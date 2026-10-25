#!/usr/bin/env python3
"""UC3-WINDOWSHEET — canonical P-pathology window families per corpus trace.

The whole trace is the fair cross-trace reference, but P-pathology claims
(thrash_index over short spans) collapse or amplify dramatically with the
window spec (RR-UC3-BASELINE finding 3: `--windows 0-1` on m2/live-thrash is
5.0/turn vs 1.67/turn whole). This sheet fixes ONE canonical family and
commits it as a fixture so any windowed thrash claim cites a stable artifact:

    whole trace  +  all non-overlapping 2-turn windows ("0-1", "2-3", ...)

Metrics are computed by the committed reference implementation
(benchmarks/metrics/metrics.py) through the exact code path the CLI uses for
`--policy`-less runs: summarize(events[, windows]) + the counterfactual
netTokenReduction that main() attaches (module docstring: approximation,
labeled as such). No policy simulation here — policy values live in the
BUDGETSWEEP artifacts.

Re-derivable idempotently:  venvs/odps/bin/python tools/window-sheet.py
(regenerates benchmarks/metrics/fixtures/window-families.json; CI re-derives
it in-process and compares — benchmarks/metrics/test_window_sheet.py).

Every trace also records whole:thrashIndex.faultsPerTurn (the service metric
that must accompany any NTR quote) and unanchoredFaults.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so this file also works as a bare script
# (pytest imports it with the repo already importable; the insert is idempotent)

from benchmarks.metrics.metrics import net_token_reduction, parse_windows, summarize  # noqa: E402

OUT = ROOT / "benchmarks" / "metrics" / "fixtures" / "window-families.json"

TRACES = [
    "corpus/m1/session-healthy.jsonl",
    "corpus/m1/session-thrashing.jsonl",
    "corpus/m1/tracer-healthy.jsonl",
    "corpus/m1/tracer-recall.jsonl",
    "corpus/m1/opencode-echo.jsonl",
    "corpus/m2/live-echo.jsonl",
    "corpus/m2/live-thrash.jsonl",
    "corpus/m3/hermes-echo-synthetic.jsonl",
    "corpus/m3/hermes-thrash-synthetic.jsonl",
    "corpus/m4/hermes-live-session-01.jsonl",
    "corpus/m5/opencode-live-session-01.jsonl",
]

# Anchors pinned by RR-UC3-BASELINE / the m5-era capture (regression rails).
# Exact float targets: committed metrics compute these as the same integer
# divisions (10/6, 17/14, 1/2), so a 1e-9 tolerance is generous.
ANCHORS: dict[tuple[str, str], float] = {
    ("corpus/m2/live-thrash.jsonl", "whole"): 10 / 6,   # 1.666.. thrash/turn
    ("corpus/m2/live-thrash.jsonl", "0-1"): 5.0,         # the 3x window lesson
    ("corpus/m5/opencode-live-session-01.jsonl", "whole"): 17 / 14,
    ("corpus/m4/hermes-live-session-01.jsonl", "whole"): 1 / 2,
}


def read_events(rel: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / rel).read_text().splitlines() if line.strip()]


def turn_space(events: list[dict]) -> int:
    """Canonical window grid = max turn index in the trace + 1 (thrash_index
    itself selects only turn.render turns — metrics.py fault_series)."""
    return max((e["turn"] for e in events if "turn" in e), default=-1) + 1


def window_specs(turns: int) -> list[str]:
    """Non-overlapping 2-turn pairs covering the turn space (a trailing odd
    turn becomes its own one-turn window; parse_windows accepts `a` alone)."""
    return [f"{i}" if i + 1 >= turns else f"{i}-{i + 1}" for i in range(0, turns, 2)]


def cli_metrics(events: list[dict], windows: list[tuple[int, int]] | None) -> dict:
    """metrics.py main() output for a --policy-less run (verbatim code path)."""
    out = summarize(events, windows)
    out["netTokenReduction"] = {"baseline": "counterfactual-no-paging",
                                "value": net_token_reduction(events)}
    return out


def core(out: dict) -> dict:
    net = out["netTokens"]
    return {
        "events": out["events"],
        "netTokens": {k: net[k] for k in ("rendered", "estimatedMisses", "total")},
        "faultRecall": out["faultRecall"],
        "touchRatio": out["touchRatio"],
        "waste": out["waste"],
        "thrashIndexMean": out["thrashIndex"]["mean"],
        "netTokenReduction": out["netTokenReduction"]["value"],
    }


def whole_record(out: dict) -> dict:
    # faultsPerTurn serialized with str turn keys (JSON-object friendly; the
    # in-memory int-keyed dict would otherwise not round-trip for rebuild tests).
    return {**core(out),
            "faultsPerTurn": {str(t): n for t, n in out["thrashIndex"]["faultsPerTurn"].items()},
            "unanchoredFaults": len(out["thrashIndex"]["unanchoredFaults"])}


def build_families() -> dict:
    families: dict[str, dict] = {}
    for rel in TRACES:
        events = read_events(rel)
        turns = turn_space(events)
        windows = {spec: core(cli_metrics(events, parse_windows(spec)))
                   for spec in window_specs(turns)}
        whole_out = cli_metrics(events, None)
        whole_thr = whole_out["thrashIndex"]["mean"]
        max_win = max((w["thrashIndexMean"] for w in windows.values()), default=None)
        ratio = None if (whole_thr is None or max_win is None) else max_win / whole_thr
        families[rel] = {
            "turns": turns,
            "whole": whole_record(whole_out),
            "windows": windows,
            "maxWindowThrashRatio": ratio,
        }
    # Anchor laws (RR-UC3-BASELINE finding 3 + m5/m4 whole-trace values).
    for (rel, spec), expected in ANCHORS.items():
        got = (families[rel]["whole"]["thrashIndexMean"] if spec == "whole"
               else families[rel]["windows"][spec]["thrashIndexMean"])
        if got is None or abs(got - expected) > 1e-9:
            raise AssertionError(f"ANCHOR {rel} {spec}: got {got!r}, want {expected!r}")
    return families


def main() -> int:
    families = build_families()
    doc = {
        "generator": "tools/window-sheet.py (UC3-WINDOWSHEET)",
        "codePath": "benchmarks/metrics/metrics.py main() -policy path: summarize + counterfactual netTokenReduction",
        "family": "whole + non-overlapping 2-turn windows (trailing odd turn as its own one-turn window)",
        "note": "windowed values are slice-local reconstructions; quote NTR only alongside "
                "service metrics (thrashIndex.faultsPerTurn here, faults/renders in the trace)",
        "anchors": {f"{rel} {spec}": want for (rel, spec), want in ANCHORS.items()},
        "traces": families,
    }
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for rel, fam in families.items():
        thr = {k: w["thrashIndexMean"] for k, w in fam["windows"].items()}
        print(f"{rel:44s} turns={fam['turns']:2d} whole={fam['whole']['thrashIndexMean']}"
              f" max/whole={None if fam['maxWindowThrashRatio'] is None else round(fam['maxWindowThrashRatio'], 2)}"
              f" windows={thr}")
    print(f"anchors OK ({len(ANCHORS)} pinned laws) -> fixture {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
