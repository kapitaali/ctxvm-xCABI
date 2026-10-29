# Benchmarks & Go/No-Go Gates

## Suites (v0)

1. **S-swe** — SWE-bench-lite-style file-cycling;
   measured: net input token cost, fault recall, thrash detection.
2. **L-longqa** — long-horizon multi-session QA (needle-in-haystack + recall-borrowed from
   Pichay's fault-rate methodology — system "Pichay", arXiv 2603.09023);
3. **C-coding** — OpenCode-style sessions, real repos — the corpus generation pilot.
4. **P-pathology** — synthetic paging stress: 5× sustained budget pressure (thrash
   detection per OS theory — Pichay reports the thrashing pathology under extreme
   sustained pressure, arXiv 2603.09023).

Harnesses: naive context-stuffing baseline vs ctxvm tracer(s) vs (v1) paged.
Adapters: OpenCode + Vercel AI SDK (both emitting identical xCABI traces — portability is
itself a measurable claim).

## Metric definitions (formulas that must live in productStrategy.calculation)

```
net_token_reduction = 1 - (paged_net_tokens / naive_tokens)
  where net = rendered tokens + Σ estimated cache-miss cost re-normalization
refetch_rate       = recovered_faults / evictions
                     (the OLD "fault_recall" — a re-fetch rate against the
                     eviction denominator, NOT detection quality; continuity
                     metric, takes no CI)
hard_fault_recall  = recovered_hard_faults / hard_faults
                     (W3 GROUND TRUTH: explicit re-calls only — tool_recall +
                     explicit_api; identifier_scan/semantic are inference
                     surfaces and never ground truth — Pichay §3.2, arXiv
                     2603.09023)
touch_ratio        = touched_tokens / rendered_tokens     (waste = 1 - touch_ratio)
thrash_index       = mean(faults_per_turn) over P-pathology sustained-pressure windows
```

Every reported metric carries a **deterministic bootstrap CI** (seed recorded,
default 20261029/2000 replicates); net COST is computed only from the explicit
versioned price model (`benchmarks/metrics/prices.json`, pinned
`priceModelVersion` — see §W3 falsifiability fix below). Reference
implementation: `benchmarks/metrics/metrics.py` + `bootstrap.py`.

## M0 go/no-go (decisive)

| Gate | Threshold | Fail ⇒ |
|---|---|---|
| Net token reduction at equal accuracy | ≥1.5× | pivot to pure telemetry-only (no control-plane claims) |
| Hard-fault recall (ground truth = explicit re-calls; bootstrap CI(95%) lower bound; n ≥ 30 hard faults) | ≥95% | add stub-driven hints; forbid prompt pollution |
| Replay determinism | 100% (byte-identical) | core design bug, block |
| Corpus conformance | 100% golden vectors pass | block; spec unstable |

## §W3 falsifiability fix (2026-10-29)

The old `fault_recall = recovered_faults / evictions` measured the **re-fetch
rate**, not detection quality, and its denominator was not ground truth —
exactly the flaw Pichay's own §3.2 names: "Only paging (Read evictions) can
produce faults… Conflating them inflates the eviction denominator and deflates
the apparent fault rate" (arXiv 2603.09023). W3 therefore:

1. **Renames** the old formula `refetch_rate` (kept for continuity; takes NO
   confidence interval — its per-unit recovery is not well-defined under the
   eviction denominator).
2. **Defines the ground truth**: a HARD fault is an explicit re-materialization
   — `page.fault` with `source: tool_recall` (the model re-invoked the tool) or
   `explicit_api` (the harness re-materialized by explicit API).
   `identifier_scan` and `semantic` are INFERENCE surfaces, never ground truth.
   `hard_fault_recall = recovered hard faults / hard faults` (recovery = a
   full-render FACT after the fault turn — unchanged law).
3. **Re-anchors the M0 gate** to `hard_fault_recall ≥ 0.95` at the bootstrap
   95% CI lower bound with `n ≥ 30` hard faults. Honest status: current REAL
   captures carry **n = 4** hard faults (m8: 1 + 3) — the gate is **UNMEASURED
   on real data**; it is falsifiable in principle now, and W8 must supply the
   volume. The ablation ground truth (remove a page, test whether the next
   action changes) needs a real model in the loop — that is the W8-grade
   method; the hard-fault restriction is the v0 falsifiable one.
4. **Pins the price model**: `benchmarks/metrics/prices.json`
   (`priceModelVersion: 1`, explicit input). Entries carry `source` +
   `verified`; null prices are UNVERIFIED and never silently substituted (0.0
   = an OBSERVED free tier, null = unknown). v0 arithmetic: hit tokens at
   `usdPer1mCachedRead`, miss tokens at `usdPer1mInput`; cache-write is
   UNMODELED in v0 (the trace schema records no write premium). Rankings must
   state the pinned version.
5. **Adds deterministic CIs**: percentile bootstrap via `random.Random(seed)`
   (default seed 20261029, 2000 replicates — seed and replicate count ride
   every output). Unit of resampling: TURNS for turn-decomposable metrics,
   the fault events themselves for hard-fault recall; undefined replicates
   are dropped and counted, never coerced to 0.

## Corpus release process (from tracer → ODPS)

1. `ctxvm export --odps` per session → manifest + llms.txt + checksum.
2. CI: their SDK validation + our replay-determinism DQ + redaction DQ.
3. Git-tag release → ODPC catalog entry → leaderboard incremental update.

## Leaderboard (v1)

- Rankings parsed from ODPS manifests (`productKPIs`) — self-serve, self-verifying.
- Simulation harness: `ctxvm-policy` runs any pluggable eviction policy over the corpus
  trace replay (per Neural Paging need: the missing trace corpus + simulator).
- Rules: report net cost; estimate-cache-miss honesty mandatory; non-deterministic policies
  must submit variance over ≥3 seeds.
