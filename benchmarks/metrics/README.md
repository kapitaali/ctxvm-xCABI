# Monitor replay, tier 1

Scores declared detectors over the **frozen** corpus with no model calls. Two runs over the
same bytes must agree exactly; `--check` fails the gate if the committed record drifts.

```sh
python -m benchmarks.metrics.monitor_replay            # table
python -m benchmarks.metrics.monitor_replay --json     # results JSON
python -m benchmarks.metrics.monitor_replay --check    # 0 consistent, 1 stale
```

## What the numbers mean, and what they do not

The corpus has **no sabotage labels**. `monitor_labels.json` records each trace's *scenario*
(healthy, echo, thrashing, recall, pause/resume) with the sentence it came from, and marks the
four thrash captures `pathology`. A TPR from this harness therefore says that a recorded-trace
detector separates a **pacing pathology** from ordinary work. It says nothing about danger,
deception or sandbagging, and the file name says so before the number does.

Thresholds are declared in `monitor_replay.py` before scoring and are not tuned. With four
positives, a tuned threshold would be an anecdote.

`fault_density` is marked `diagnostic`: its feature is built from `page.fault` events, and the
thrash label means repeated re-reads, so feature and label share a cause. It is reported because
a reader will ask, not because it is evidence.

## Results as of 2026-11-05 (17 traces: 4 pathology, 13 benign)

| monitor | rule | TPR [95%] | FPR [95%] |
|---|---|---|---|
| `fault_density` (diagnostic) | mean faults/turn > 0.5 | 0.500 [0.150, 0.850] | 0.308 [0.127, 0.576] |
| `waste` | unreferenced share of rendered tokens > 0.5 | 1.000 [0.510, 1.000] | 1.000 [0.772, 1.000] |
| `token_pressure` | peak resident tokens > 90% of budget | 0.000 [0.000, 0.490] | 0.000 [0.000, 0.228] |

All three fail to separate the corpus, for three different reasons, and each reason is a fact
about the corpus rather than a bug in the harness:

- **`fault_density`**: a benign live session (`corpus/m5`, 1.214 faults/turn) scores *higher* than
  two of the four labelled thrash captures (0.300 and 0.500). Ordinary interactive work produces
  identifier scans at a higher rate than the synthetic thrash fixtures. Fault counts are not a
  proxy for a pathology label.
- **`waste`**: the feature has almost no dynamic range here (0.667 to 1.000), because
  `touch_ratio` counts token mass that a fault later referred to, and faults touch few pages. A
  threshold below 0.5 would flag everything too; the metric needs a corpus where pages are
  actually evicted and re-fetched.
- **`token_pressure`**: the highest capture reaches 40.1% of its declared budget (`corpus/m7` resume), so a 90% rule never fires
  and its 0/0 TPR is uninformative rather than exculpatory.

The honest reading: tier 1 is a working, deterministic harness with nothing to measure it
against yet. Two things would change that — labelled safety traces (tier 2, requires interventions)
or a corpus with evictions and re-fetches under pressure.

## Invariants the tests enforce

- Labels cover exactly `corpus/m*/*.jsonl`, once each, each with a cited basis.
- An undefined feature abstains; it is never coerced to a value or to zero.
- Two evaluations of the same bytes are byte-identical, and the committed `monitor-results.json`
  must match a fresh evaluation.
- The fault-derived monitor cannot present itself as a detector (`kind: diagnostic` is asserted).
