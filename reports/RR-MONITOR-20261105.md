# RR-MONITOR-20261105 — W18 tier 1: a deterministic monitor-replay harness, and three nulls

Card: #3 in `research/synthesis-20261105.md` — "TPR/FPR for a monitor scored over recorded
`corpus/m1`–`m8` traces; deterministic, cheap, unblocks the measurement."

## What was built

`benchmarks/metrics/monitor_replay.py` scores declared detectors over every trace in the frozen
corpus. A monitor is a pure function of the events, so tier 1 runs entirely offline: no model calls,
no clock, no randomness, and two evaluations must agree byte for byte. `--check` compares a fresh
evaluation with the committed `monitor-results.json` and exits 1 when they differ, which is what the
gate runs.

Three rules, thresholds declared before scoring and never tuned:

| monitor | feature | rule | kind |
|---|---|---|---|
| `fault_density` | `thrash_index` (mean faults/turn) | > 0.5 | diagnostic |
| `waste` | `1 - touch_ratio` | > 0.5 | detector |
| `token_pressure` | peak resident / declared budget | > 0.9 | detector |

The feature functions reuse `benchmarks/metrics/metrics.py` rather than restating the formulas, so a
monitor and a metric cannot drift apart.

## Labels, and why they are not safety labels

`corpus/m1`–`m8` contains no sabotage, deception or sandbagging. What each drop documents is a
**scenario**: healthy, echo, thrashing, recall, pause/resume. `monitor_labels.json` records that
scenario per trace, with the sentence it came from, and marks the four thrash captures `pathology`.

`monitor_labels.json` opens with the scope sentence, and the module docstring repeats it: a TPR from
this harness separates a pacing pathology from ordinary work. It does not measure danger.

`fault_density` is marked `diagnostic` and a test asserts that it cannot present itself as a
detector. Its feature is built from `page.fault`, and the thrash scenario means repeated re-reads, so
feature and label share a cause. Reporting it is honest; counting it as evidence would not be.

## Results (17 traces: 4 pathology, 13 benign)

```
monitor          kind         TP  FN  FP  TN    TPR          TPR 95%    FPR          FPR 95%
fault_density    diagnostic    2   2   4   9  0.500   [0.150, 0.850]  0.308   [0.127, 0.576]
waste            detector      4   0  13   0  1.000   [0.510, 1.000]  1.000   [0.772, 1.000]
token_pressure   detector      0   4   0  13  0.000   [0.000, 0.490]  0.000   [0.000, 0.228]
```

All three fail to separate the corpus, for three different reasons:

1. **`fault_density` is confounded by real sessions.** `corpus/m5` is a benign interactive capture
   at 1.214 faults/turn — higher than two of the four labelled thrash traces (0.300 and 0.500).
   Ordinary work produces identifier scans faster than the synthetic thrash fixtures produce faults.
2. **`waste` has no dynamic range here.** Values run 0.667 to 1.000; the metric counts token mass a
   fault later referred to, and faults touch few pages. TPR 1.0 with FPR 1.0 means the rule flags
   everything, which is not a detector.
3. **`token_pressure` never approaches threshold.** The highest capture reaches 40.1% of its
   declared budget (`corpus/m7` resume). Its 0/0 does not exonerate the corpus; it means the
   declared budget is not a pressure point in these captures.

The result is that tier 1 is a working harness with nothing adequate to measure. That is a negative
result and it is recorded as one: the synthesis expected tier 1 to "unblock the measurement", and what
it unblocks is the *mechanics* — the labels are the gap.

## Verification

```sh
venvs/odps/bin/python -m benchmarks.metrics.monitor_replay           # table
venvs/odps/bin/python -m benchmarks.metrics.monitor_replay --check   # 0 consistent
venvs/odps/bin/python -m pytest benchmarks/metrics -q                # 54 passed (was 44)
bash tools/run-ci.sh                                                 # ALL GATES GREEN
```

The ten new tests pin: labels cover exactly the corpus, once each, each with a cited basis; an
undefined feature abstains rather than becoming zero; `decide` is strict greater-than; Wilson
intervals are bounded and widen as n falls, with n=0 undefined; two evaluations are byte-identical;
the committed results file is current; every summary's counts account for every trace; the
fault-derived monitor is `diagnostic`.

## Deviations

- The card said "TPR/FPR for a monitor". The corpus supports TPR/FPR only for a **pathology**
  monitor, so the harness reports that and names the gap. Building safety labels would require
  tier-2 interventions (hint injection, page removal), which the synthesis places outside the
  deterministic core.
- Labels live in `benchmarks/metrics/monitor_labels.json`, not inside `corpus/`, because the drops
  are frozen and their checksums pin the files they list. The label file cites the sentence each
  label came from.
- Wilson intervals, not bootstrap: n is 4 and 13, and the interval is a statement about how little
  four positives can say.

## Open

- Tier 2 (design note first, W16 precedent): interventions outside the core, runs marked
  non-deterministic, page ablation against the touch ratio.
- A corpus with evictions and re-fetches under real pressure would give `waste` a dynamic range and
  `token_pressure` a chance to fire. Neither exists yet.
