"""Deterministic percentile bootstrap for every reported metric (W3).

Law (07 §W3 falsifiability fix): a point estimate without an interval is not a
falsifiable claim — every metric the suite reports carries a CI, and the CI is
REPRODUCIBLE: `random.Random(seed)`, seed recorded in every output (default
20261029), so two machines produce byte-identical intervals.

Unit of resampling is metric-specific (the honest cluster, never events):
- turn-decomposable metrics (touch_ratio, waste, net_token_reduction,
  thrash_index): TURNS — events cluster within turns, so turns are resampled
  whole and the per-turn record carries that turn's contribution;
- fault-level metrics (hard_fault_recall): the FAULT events themselves — each
  hard fault is an independent Bernoulli observation (recovered or not).
`refetch_rate` takes no CI by law: under the eviction-denominator reading its
per-unit recovery is not well-defined (a fault can precede its page's
eviction), and it is a continuity metric — the gate metric is
`hard_fault_recall` (07 W3).

Undefined never fudged: a replicate whose stat is None (e.g. a resample with
zero rendered tokens) is DROPPED and counted in `failed`, not coerced to 0.
"""
from __future__ import annotations

import random

DEFAULT_SEED = 20261029
DEFAULT_REPLICATES = 2000


def _percentile(sorted_values: list[float], q: float) -> float:
    """Nearest-rank percentile on pre-sorted values (deterministic)."""
    if not sorted_values:
        raise ValueError("no successful replicates")
    i = min(len(sorted_values) - 1, max(0, int(q * len(sorted_values))))
    return sorted_values[i]


def bootstrap_ci(
    records: list[dict],
    stat,
    replicates: int = DEFAULT_REPLICATES,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict:
    """`stat(records_subset) -> float | None` resampled with replacement.

    Returns {"point", "ci95", "replicates", "seed", "successful", "failed"};
    `ci95` is None when NO replicate succeeded (undefined never fudged).
    """
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(replicates):
        sample = [records[rng.randrange(len(records))] for _ in records]
        v = stat(sample)
        if v is not None:
            values.append(v)
    values.sort()
    return {
        "point": stat(records),
        "ci95": None if not values else [_percentile(values, alpha / 2), _percentile(values, 1 - alpha / 2)],
        "replicates": replicates,
        "seed": seed,
        "successful": len(values),
        "failed": replicates - len(values),
    }
