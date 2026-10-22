# Benchmarks & Go/No-Go Gates

## Suites (v0)

1. **S-swe** — SWE-bench-lite-style file-cycling;
   measured: net input token cost, fault recall, thrash detection.
2. **L-longqa** — long-horizon multi-session QA (needle-in-haystack + recall-borrowed from
   Pichay's fault-rate methodology);
3. **C-coding** — OpenCode-style sessions, real repos — the corpus generation pilot.
4. **P-pathology** — synthetic paging stress: 5× sustained budget pressure (thrash
   detection per OS theory — Pichay reports thrashing under extreme pressure).

Harnesses: naive context-stuffing baseline vs ctxvm tracer(s) vs (v1) paged.
Adapters: OpenCode + Vercel AI SDK (both emitting identical xCABI traces — portability is
itself a measurable claim).

## Metric definitions (formulas that must live in productStrategy.calculation)

```
net_token_reduction = 1 - (paged_net_tokens / naive_tokens)
  where net = rendered tokens + Σ estimated cache-miss cost re-normalization
fault_recall     = recovered_faults / evictions
touch_ratio      = touched_tokens / rendered_tokens       (waste = 1 - touch_ratio)
thrash_index     = mean(faults_per_turn) over P-pathology sustained-pressure windows
```

## M0 go/no-go (decisive)

| Gate | Threshold | Fail ⇒ |
|---|---|---|
| Net token reduction at equal accuracy | ≥1.5× | pivot to pure telemetry-only (no control-plane claims) |
| Fault recall (identifier_scan + tool_recall layered) | ≥95% | add stub-driven hints; forbid prompt pollution |
| Replay determinism | 100% (byte-identical) | core design bug, block |
| Corpus conformance | 100% golden vectors pass | block; spec unstable |

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
