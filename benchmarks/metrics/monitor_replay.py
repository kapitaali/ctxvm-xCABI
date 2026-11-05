#!/usr/bin/env python3
"""Tier-1 monitor replay (W18): score deterministic detectors over RECORDED traces.

What this is
------------
A monitor is a pure function of a trace. Tier 1 runs such functions over the frozen
corpus and reports decisions, TPR and FPR — no model calls, no clock, no randomness, so
two runs must agree byte for byte. That determinism is the point: it keeps the recorded
tier of the harness outside the non-determinism that model-in-loop interventions carry.

What this is NOT
----------------
The corpus has no sabotage labels. Its labels are SCENARIO names (healthy, echo,
thrashing, recall, pause/resume), stated by each drop's README and provenance. So tier 1
evaluates a PATHOLOGY monitor, not a safety monitor. A number from this file says that
the harness can score a recorded-trace detector reproducibly; it says nothing about
whether any model is dangerous, deceptive or sandbagging.

The `fault_density` monitor is a DIAGNOSTIC, not a detector: its feature is built from
`page.fault` events, and the thrashing scenario is defined by repeated re-reads, so the
feature and the label share a cause. It is included because a reader will ask what the
fault-derived rule does, not because it is evidence.

Labels, thresholds and the label basis live in `monitor_labels.json`. Both are declared
before scoring and are not tuned on the corpus: with four positives, a tuned threshold
would be an anecdote.

Usage
-----
    python -m benchmarks.metrics.monitor_replay            # human table
    python -m benchmarks.metrics.monitor_replay --json     # print results JSON
    python -m benchmarks.metrics.monitor_replay --check    # exit 1 if the committed
                                                           # results file is stale
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

from benchmarks.metrics.metrics import read_events, thrash_index, waste

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = Path(__file__).with_name("monitor_labels.json")
RESULTS_PATH = Path(__file__).with_name("monitor-results.json")
CORPUS_GLOB = "corpus/m*/*.jsonl"


def feature_fault_density(events: list[dict]) -> float | None:
    """Mean faults per turn (existing `thrash_index`). DIAGNOSTIC: shares a cause with
    the thrashing label — reported, never counted as detector evidence."""
    return thrash_index(events)


def feature_waste(events: list[dict]) -> float | None:
    """Share of rendered tokens that no fault ever referred back to (existing `waste`)."""
    return waste(events)


def feature_token_pressure(events: list[dict]) -> float | None:
    """Peak resident tokens over the session's declared budget; None when either is absent."""
    budget = next((e.get("budgetTokens") for e in events if e["type"] == "session.open"), None)
    peak = max((e.get("residentTokens", 0) for e in events if e["type"] == "turn.render"), default=0)
    if not budget or not isinstance(budget, int) or budget <= 0:
        return None
    return peak / budget


MONITORS: dict[str, dict[str, Any]] = {
    "fault_density": {
        "feature": feature_fault_density,
        "threshold": 0.5,  # faults per turn; declared, not tuned
        "kind": "diagnostic",
        "rule": "flag when mean faults per turn > 0.5",
    },
    "waste": {
        "feature": feature_waste,
        "threshold": 0.5,
        "kind": "detector",
        "rule": "flag when the unreferenced share of rendered tokens > 0.5",
    },
    "token_pressure": {
        "feature": feature_token_pressure,
        "threshold": 0.9,
        "kind": "detector",
        "rule": "flag when peak resident tokens > 90% of the declared budget",
    },
}


def wilson(successes: int, n: int, z: float = 1.96) -> list[float] | None:
    """Wilson score interval; None when n is 0 (undefined is never fudged)."""
    if n <= 0:
        return None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def decide(feature_value: float | None, threshold: float) -> bool | None:
    """True = flagged, False = not flagged, None = abstain (feature undefined)."""
    if feature_value is None:
        return None
    return feature_value > threshold


def load_labels() -> dict[str, Any]:
    return json.loads(LABELS_PATH.read_text(encoding="utf-8"))


def evaluate() -> dict[str, Any]:
    labels = load_labels()
    rows: list[dict[str, Any]] = []
    for item in labels["traces"]:
        path = REPO_ROOT / item["path"]
        events = read_events(str(path))
        row: dict[str, Any] = {
            "path": item["path"],
            "label": item["label"],
            "events": len(events),
            "monitors": {},
        }
        for name, spec in MONITORS.items():
            value = spec["feature"](events)
            row["monitors"][name] = {
                "value": None if value is None else round(value, 4),
                "flagged": decide(value, spec["threshold"]),
            }
        rows.append(row)

    summary: dict[str, Any] = {}
    for name, spec in MONITORS.items():
        tp = fn = fp = tn = abstain = 0
        for row in rows:
            flagged = row["monitors"][name]["flagged"]
            if flagged is None:
                abstain += 1
                continue
            positive = row["label"] == "pathology"
            if positive and flagged:
                tp += 1
            elif positive:
                fn += 1
            elif flagged:
                fp += 1
            else:
                tn += 1
        positives, negatives = tp + fn, fp + tn
        summary[name] = {
            "kind": spec["kind"],
            "rule": spec["rule"],
            "threshold": spec["threshold"],
            "tp": tp, "fn": fn, "fp": fp, "tn": tn, "abstain": abstain,
            "tpr": None if positives == 0 else round(tp / positives, 4),
            "tpr_ci95": wilson(tp, positives),
            "fpr": None if negatives == 0 else round(fp / negatives, 4),
            "fpr_ci95": wilson(fp, negatives),
        }

    return {
        "card": "W18",
        "tier": 1,
        "topology": "recorded traces only; no model calls; deterministic",
        "corpus": {
            "glob": CORPUS_GLOB,
            "traces": len(rows),
            "positives": sum(1 for r in rows if r["label"] == "pathology"),
            "negatives": sum(1 for r in rows if r["label"] == "benign"),
            "label_basis": labels["basis"],
        },
        "summary": summary,
        "rows": rows,
    }


def render(results: dict[str, Any]) -> str:
    out: list[str] = []
    c = results["corpus"]
    out.append(f"traces={c['traces']} positives={c['positives']} negatives={c['negatives']}")
    out.append("")
    header = f"{'monitor':16s} {'kind':11s} {'TP':>3s} {'FN':>3s} {'FP':>3s} {'TN':>3s} {'AB':>3s} {'TPR':>6s} {'TPR 95%':>16s} {'FPR':>6s} {'FPR 95%':>16s}"
    out.append(header)
    for name, s in results["summary"].items():
        def f(v: float | None) -> str:
            return "  n/a" if v is None else f"{v:.3f}"
        def ci(v: list[float] | None) -> str:
            return "             n/a" if v is None else f"[{v[0]:.3f}, {v[1]:.3f}]"
        out.append(
            f"{name:16s} {s['kind']:11s} {s['tp']:3d} {s['fn']:3d} {s['fp']:3d} {s['tn']:3d}"
            f" {s['abstain']:3d} {f(s['tpr']):>6s} {ci(s['tpr_ci95']):>16s}"
            f" {f(s['fpr']):>6s} {ci(s['fpr_ci95']):>16s}"
        )
    out.append("")
    out.append("per trace (value / flagged):")
    for row in results["rows"]:
        cells = []
        for name, m in row["monitors"].items():
            v = "n/a" if m["value"] is None else f"{m['value']:.3f}"
            mark = "-" if m["flagged"] is None else ("FLAG" if m["flagged"] else "ok")
            cells.append(f"{name}={v}/{mark}")
        out.append(f"  {row['label']:9s} {row['path']:52s} " + " ".join(cells))
    return "\n".join(out)


def dumps(results: dict[str, Any]) -> str:
    return json.dumps(results, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tier-1 monitor replay over recorded traces.")
    parser.add_argument("--json", action="store_true", help="print the results JSON instead of the table")
    parser.add_argument("--check", action="store_true", help="exit 1 if the committed results file is stale")
    args = parser.parse_args(argv)

    results = evaluate()
    text = dumps(results)

    if args.check:
        if not RESULTS_PATH.exists():
            print(f"monitor_replay: violated results-missing: {RESULTS_PATH.name}", file=sys.stderr)
            return 1
        if RESULTS_PATH.read_text(encoding="utf-8") != text:
            print("monitor_replay: violated results-stale: rerun without --check", file=sys.stderr)
            return 1
        print(f"monitor_replay: consistent ({results['corpus']['traces']} traces, "
              f"{len(results['summary'])} monitors, results byte-identical)")
        return 0

    if args.json:
        sys.stdout.write(text)
    else:
        print(render(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
