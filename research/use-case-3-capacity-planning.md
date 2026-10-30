# ctxvm Use Case #3 — Context Capacity Planning & Eviction Policy Benchmarking

**Status:** Design concept — not yet implemented in code
**Source:** White paper Phase 3 (§3.9 measurement stack, §6 metrics); ODPS/ODCS packaging (T5); benchmark suites (07); metric simulator (T3)

## 1. The Problem

Teams deploying LLM agents face three unanswered questions:

1. **How much context budget do I need?** Is 120K tokens enough? 200K? 1M? The answer depends on the workload, the eviction policy, and the waste profile — none of which are measured today.
2. **Which eviction policy should I use?** LRU? Fault-driven pinning? Size-based? Stale-result-first? Every team builds their own pager with private policies and no way to compare.
3. **Is my current pager wasting tokens?** How much rendered context is never touched? How many evicted pages are re-requested (faults)? What is the net token cost after cache-normalization?

Without answers, teams over-provision (wasting money on oversized context windows) or under-provision (suffering context death and lost information). There is no shared measurement framework, no public corpus of paging traces, and no conformance test for trace engines.

## 2. What ctxvm Provides

ctxvm's measurement stack makes context capacity planning and eviction policy benchmarking executable:

- **Metric simulator** (`benchmarks/metrics/metrics.py`): Pure Python functions over JSONL event streams implementing four formulas:
  - `net_token_reduction = 1 - (paged_net_tokens / naive_tokens)` — how many tokens the pager saves vs naive stuffing
  - `fault_recall = recovered_faults / evictions` — share of evictions the pager recovered from
  - `touch_ratio = touched_tokens / rendered_tokens` — **defined proxy**: share of rendered tokens that were referenced (touched) at least once; waste = 1 - touch_ratio. *Note: "touched" is defined as token identifiers appearing in subsequent model output or tool calls; this is an operational proxy, not ground truth of what the model "read".*
  - `thrash_index = mean(faults_per_turn)` — fault rate under sustained-pressure windows
- **Reference implementation**: 18/18 pytest green, two synthetic fixtures (healthy and thrashing session), CLI prints JSON
- **ODPS 4.1 packaging**: Trace corpus packaged as an open data product with manifest, llms.txt, checksums, DQ checks, and KPIs
- **ODPC v1.0 hub**: `hub/` contains `catalog.yaml` and static HTML, built byte-identically by `tools/build-hub.sh`
- **Replay engine**: `ctxvm replay` enforces byte-identical re-render; divergence exits 1

Cache-miss normalization is noted, not invented: net cost subtracts estimated cache misses (`call.meta.cacheEstimate`) so benchmarks report *net* cost.

## 3. How Capacity Planning Works

Capacity planning proceeds in four steps: record, package, simulate, decide.

### Step 1 — Record Benchmark Sessions

Record real agent sessions as xCABI traces. The tracer (`03-tracer-api-ts.md`) emits JSONL events: `session.open`, `page.declare`, `page.render`, `page.evict`, `page.fault`, `page.pin`/`page.unpin`, `turn.render`, `call.meta`.

Benchmark suites (from `07-benchmarks-go-no-go.md`):
- **S-swe**: SWE-bench-lite-style file cycling — measures net input token cost, fault recall, thrash detection
- **L-longqa**: Long-horizon multi-session QA (needle-in-haystack + recall-borrowed from Pichay's fault-rate methodology)
- **C-coding**: OpenCode-style sessions, real repos — the corpus generation pilot
- **P-pathology**: Synthetic paging stress: 5× sustained budget pressure (thrash detection per OS theory)

Example session recording:

```bash
# Wrap any agent loop with the tracer
const vm = trace({
  agent: "coding-agent-benchmark",
  model: "openai/gpt-5",
  budgetTokens: 120_000,
})

// Per tool result: vm.page(...)
// Per turn: vm.render(messages)
// After turn: vm.observe(modelOutputText)
```

### Step 2 — Package as ODPS Data Product

Package recorded sessions as versioned, checksummed open data products:

```bash
# Package a session corpus as an ODPS data product (example path; corpus layout is m1/m2)
ctxvm export --odps corpus/0.1/sessions/ --tag benchmark-q4-2026

# Produces:
# corpus/0.1/
# ├── corpus.jsonl.zst          # Versioned, checksummed JSONL trace
# ├── manifest.yaml              # ODPS 4.1 manifest with DQ checks and KPIs
# ├── llms.txt                   # Agent discovery file
# ├── checksums.sha256           # SHA-256 checksums for all artifacts
# └── conformance.jsonl          # Golden conformance vectors
```

The manifest carries:
- **DQ checks**: `replayDeterminism` (validity, 100%), `pinLint` (completeness, 99%), `redactionScan` (uniqueness, 99%)
- **KPIs**: `kpi-agent-token-efficiency` (target 50%), `kpi-fault-recall` (target 95%), `kpi-net-token` (target 40%), `kpi-touch-ratio` (target 60%)
- **SLA**: updateFrequency (1 week), timeToDetect (1 day), errorRate (1 percent)

### Step 3 — Simulate Different Eviction Policies

Run the metric simulator over the corpus under different policies:

```bash
# Baseline: naive context stuffing (no eviction)
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline naive

# Policy A: LRU eviction
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline lru

# Policy B: Fault-driven pinning (Pichay method)
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline fault-pin

# Policy C: Size-based eviction (largest first)
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline size-based
```

**Honest scope note:** Policy simulation over a recorded trace is **approximative**, not exact. The fault stream in the recorded trace was produced under whatever policy actually ran. Re-simulating LRU/fault-pin/size-based over the same events reshuffles consequences *without the model in the loop*: different stubs produce different model behavior, which in turn produces different faults. The simulated metrics are estimates, not ground truth. For precise measurement, run live A/B sessions under each policy (cheap on local pinned models where determinism holds; expensive on hosted coding-agent sessions where each turn costs provider tokens).

Example output (illustrative — actual numbers depend on the recorded trace and policy simulation):

```
Metric              | Naive   | LRU     | Fault-Pin | Size-Based
--------------------|---------|---------|-----------|------------
Net token reduction | 0.0%    | ~28%    | ~42%      | ~35%
Fault recall        | N/A     | ~0.82   | ~0.94     | ~0.76
Touch ratio         | 0.45    | ~0.71   | ~0.89     | ~0.68
Thrash index        | 0.0     | ~0.45   | ~0.12     | ~0.33
Waste (1 - touch)   | 55.0%   | ~29%    | ~11%      | ~32%
```

*The exact figures depend on the recorded trace and the fault model used by the simulator. Treat them as estimates, not measurements.*

### Step 4 — Decide

Based on the simulation results:

- If **fault recall** is low (< 95%), the pager is evicting too aggressively — increase budget or use fault-driven pinning
- If **touch ratio** is low (< 60%), too much rendered content is never read — evict more aggressively or improve stub quality
- If **thrash index** is high under sustained pressure, the working set exceeds the resident set — increase budget or use a more selective policy
- If **net token reduction** meets target (≥ 1.5× at equal accuracy per M0 gate), the pager is production-ready

**Scope note on the ≥1.5× gate:** On local pinned models where replay is deterministic, you can measure per-policy net token reduction by running live sessions under each policy and comparing. On hosted coding-agent sessions (provider APIs), each turn costs money and determinism is not guaranteed, so the ≥1.5× gate applies to local pinned deployments only. On hosted endpoints, use ODPS packaging to package traces and compare manifest KPIs instead.

The M0 go/no-go gates (from `07-benchmarks-go-no-go.md`):
- Net token reduction at equal accuracy ≥ 1.5× — pivot to pure telemetry-only if failed
- Fault recall ≥ 95% — add stub-driven hints; forbid prompt pollution if failed
- Replay determinism 100% byte-identical — core design bug if failed
- Corpus conformance 100% golden vectors pass — spec unstable if failed

## 4. What Makes This Possible

| ctxvm component | Role in capacity planning |
|-----------------|---------------------------|
| `benchmarks/metrics/metrics.py` | Pure Python metric simulator — four formulas, CLI output |
| Two synthetic fixtures | Healthy and thrashing sessions for 18/18 pytest coverage |
| ODPS 4.1 manifest | Machine-readable KPIs and DQ checks |
| ODPC v1.0 hub | `catalog.yaml` + `index.html`, built byte-identically |
| `ctxvm replay` | Byte-identical re-render — ensures simulations are reproducible |
| `contracts/corpus-0.1.odcs.yaml` | ODCS v3.0.2 data contract — lint green via datacontract-cli 1.2.7 |
| `tools/build-hub.sh` | Idempotent hub rebuild — byte-identical across rebuilds |

## 5. What ctxvm Does Not Do

- **No eviction policy is built in.** ctxvm observes only in v0. It does not evict, pin, or page. Paging control ships in v1 behind an opt-in `policy` flag.
- **No built-in policy library.** LRU, fault-pin, size-based, etc. must be implemented by the user or as v1 plugins.
- **No production traffic simulation.** The simulator runs over recorded JSONL traces, not live agent sessions. Real-session measurement is a T9/T10 frontier.
- **Semantic faults excluded.** `semantic_*` (embedding/LLM guesses) are v1 plugins, marked non-deterministic, excluded from core.
- **No exact touch_ratio ground truth.** "Touched" is defined as a proxy (identifier appearing in subsequent output/tool calls); it is not ground truth of what the model read.

## 6. Verification

All claims are backed by committed repo artifacts:

```bash
# Metric simulator reference implementation
python -m pytest benchmarks/metrics
# 18/18 pytest green, two synthetic fixtures (healthy and thrashing)

# Metric simulator (corrected CLI spelling)
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-thrashing.jsonl
# Both print JSON with all four metrics (netTokenReduction, faultRecall, touchRatio+waste, thrashIndex)
# healthy's faultRecall: null is the honest 0-eviction case

# ODPS manifest validation (SDK 4.1)
venvs/odps/bin/open-data-products validate 04-odps-dataproduct-corpus.yaml --json
# {valid: true, spec: odps 4.1, errors: [], warnings: [], hints: [], path: ..., version: ...}
# Note: compliance_level and production_ready are not emitted by the SDK 4.1 CLI.

# ODCS contract lint
venvs/odcs/bin/datacontract lint contracts/corpus-0.1.odcs.yaml
# Lint green

# Hub build (idempotent, byte-identical)
tools/build-hub.sh
# hub/catalog.yaml + hub/index.html — byte-identical across rebuilds
```

## 7. Related Work in Repo

- `07-benchmarks-go-no-go.md` — Benchmark suites, metric definitions, M0 go/no-go gates
- `benchmarks/metrics/` — Metric simulator reference implementation (18/18 pytest green)
- `04-odps-dataproduct-corpus.yaml` — ODPS 4.1 manifest for the trace corpus (validated)
- `contracts/corpus-0.1.odcs.yaml` — ODCS v3.0.2 data contract (lint green)
- `hub/` — ODPC v1.0 catalog + static HTML (byte-identical rebuilds)
- `tools/build-hub.sh` — Idempotent hub build script
- `reports/RR-T3-20261022.md` — T3 metric simulator report
- `reports/RR-T5-20261022.md` — T5 ODPC hub pipeline report
- `08-HANDOFF.md` §5 — Task board; T10 (corpus drop M1 + CI) is the next frontier

---

**Next step:** This use case maps directly to T10 (corpus drop M1 + CI) from `08-HANDOFF.md` §6. The missing piece is a recorded corpus of real benchmark sessions including a thrashing capture, plus GitHub Actions CI (`cargo test` + schema validator + hub byte-identity check). The metric simulator (T3) and ODPS packaging (T5) are already complete.

---

## Implementation Plan: Context Capacity Planning & Eviction Policy Benchmarking

This section describes how to implement context capacity planning and eviction policy benchmarking as plugins for two harnesses: OpenCode and Hermes Agent. Both use the same metric simulator and ODPS packaging, so results are comparable across harnesses.

### 1. Shared Measurement Surface

Both harness plugins implement the same metric collection:

| Metric | Formula | What it measures |
|--------|---------|------------------|
| `net_token_reduction` | `1 - (paged_net_tokens / naive_tokens)` | Tokens saved vs naive stuffing |
| `fault_recall` | `recovered_faults / evictions` | Share of evictions recovered |
| `touch_ratio` | `touched_tokens / rendered_tokens` | Share of rendered tokens the model referenced (proxy) |
| `thrash_index` | `mean(faults_per_turn)` | Fault rate under sustained pressure |

All metrics subtract estimated cache misses (`call.meta.cacheEstimate`) so results report net cost.

### 2. OpenCode Plugin

**Location:** OpenCode plugin system.

**Hook points:**
- `onSessionStart` → Initialize trace session with `session.open` event.
- `onPageDeclare` → Record `page.declare` events with page descriptor, kind, tokens.
- `onPageEvict` → Record `page.evict` events with stub text.
- `onPageFault` → Record `page.fault` events with source and latency.
- `onTurnRender` → Record `turn.render` with resident/evicted token totals.
- `onCallMeta` → Record `call.meta` with provider, cache hit/miss estimate, latency.
- `onSessionEnd` → Export trace to JSONL, run metric simulator, emit KPIs.

**CLI commands:**
```
# Record a benchmark session
opencode ctxvm trace --session bench-session --budget 120000
# ... run agent benchmark ...

# Simulate metrics over the recorded trace
opencode ctxvm metrics --session bench-session --policy naive
opencode ctxvm metrics --session bench-session --policy lru
opencode ctxvm metrics --session bench-session --policy fault-pin
opencode ctxvm metrics --session bench-session --policy size-based

# Export as ODPS data product
opencode ctxvm export --odps --session bench-session --output corpus/0.1/
```

**Plugin surface (~60 lines of glue):**
- Wrap all tool results, renders, evictions, faults, and call metadata into xCABI events.
- After session ends, run `benchmarks/metrics/metrics.py` over the trace.
- Export manifest, llms.txt, checksums, and conformance vectors per ODPS 4.1.

### 3. Hermes Plugin

**Location:** Hermes plugin system (`~/.hermes/plugins/`).

**Hook points:**
- Hermes agent loop hooks: `onPageDeclare`, `onPageEvict`, `onPageFault`, `onTurnRender`, `onCallMeta`, `onSessionEnd`.
- Hermes cron: Schedule periodic corpus collection and metric simulation.
- Hermes session management: Persist traces to `~/.hermes/sessions/<session-id>/trace.jsonl`.

**CLI commands (Hermes native):**
```
# Record a Hermes benchmark session
hermes ctxvm trace --session bench-session --budget 120000
# ... run agent benchmark ...

# Simulate metrics
hermes ctxvm metrics --session bench-session --policy lru
hermes ctxvm metrics --session bench-session --policy fault-pin

# Export as ODPS data product
hermes ctxvm export --odps --session bench-session --output corpus/0.1/
```

**Plugin surface (~60 lines of glue):**
- Same hook points as OpenCode using Hermes's plugin API.
- Hermes's cron system can schedule periodic corpus drops and metric re-computation:
  ```
  hermes cron add corpus-drop \
    --schedule "every monday 9am" \
    --command "hermes ctxvm export --odps --session corpus/ --output corpus/0.1/"
  ```
- Hermes's MCP tool-shim (T6 design note) provides verbatim mirror of tool results, ensuring accurate page declaration.

### 4. ODPS Packaging and Leaderboard

**Packaging pipeline:**
```
# 1. Record sessions
hermes ctxvm trace --session bench-session --budget 120000

# 2. Export as ODPS data product
hermes ctxvm export --odps --session bench-session --output corpus/0.1/
# Produces: corpus.jsonl.zst, manifest.yaml, llms.txt, checksums.sha256, conformance.jsonl

# 3. Validate manifest
venvs/odps/bin/open-data-products validate corpus/0.1/manifest.yaml --json
# {valid: true, spec: odps 4.1, errors: [], warnings: [], hints: [], path: ..., version: ...}
# Note: compliance_level and production_ready are not emitted by the SDK 4.1 CLI.

# 4. Validate ODCS contract
venvs/odcs/bin/datacontract lint contracts/corpus-0.1.odcs.yaml
# Lint green

# 5. Rebuild hub catalog
tools/build-hub.sh
# hub/catalog.yaml + hub/index.html — byte-identical rebuild

# 6. CI gate (GitHub Actions)
cargo test && python spec/rfc-0/validate_schema.py corpus/0.1/trace.jsonl && tools/build-hub.sh --check-identity
```

**ODPS manifest KPIs:**
- `kpi-agent-token-efficiency`: target 50%, calculation `1 - (net_paged_tokens / naive_baseline_tokens)`
- `kpi-fault-recall`: target 95%, calculation `recovered_faults / evictions`
- `kpi-net-token`: target 40%, calculation `1 - (paged_tokens / naive_tokens)`, cache-normalized
- `kpi-touch-ratio`: target 60%, calculation `touched_tokens / rendered_tokens`

**DQ checks:**
- `replayDeterminism` (validity, 100%): `ctxvm replay` exit 0 on all traces
- `pinLint` (completeness, 99%): Zero dangling pins or unclaimed faults
- `redactionScan` (uniqueness, 99%): Zero secret/PII matches

### 5. Cross-Harness Comparability

Because both plugins emit the same xCABI event vocabulary and use the same metric simulator, results are directly comparable:

```
# OpenCode session
opencode ctxvm trace --session oc-session --budget 120000
opencode ctxvm export --odps --session oc-session --output corpus/opencode/

# Hermes session
hermes ctxvm trace --session hermes-session --budget 120000
hermes ctxvm export --odps --session hermes-session --output corpus/hermes/

# Compare metrics across harnesses (trace positionals; --baseline flag only)
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline fault-pin
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-thrashing.jsonl --baseline fault-pin
```

**Honest scope note:** Cross-harness comparison compares traces recorded under each harness's own paging behavior. Differences reflect both the pager policy and the harness's message assembly. Treat comparisons as indicative, not definitive.

### 6. Dependencies

- **T3** (`benchmarks/metrics/`): Metric simulator reference implementation. Already complete (18/18 pytest green).
- **T5** (`hub/`): ODPC hub pipeline. Already complete (byte-identical rebuilds).
- **T10** (corpus drop M1 + CI): Recorded corpus of real benchmark sessions including thrashing capture, plus GitHub Actions CI gate. Missing piece.
- **Rust M0** (`ctxvm-core`, `ctxvm-conformance`): Replay engine and conformance validator. Already complete.
- **ODPS 4.1 manifest** (`04-odps-dataproduct-corpus.yaml`): Validated (`valid`, spec odps 4.1, errors empty).
- **ODCS v3.0.2 contract** (`contracts/corpus-0.1.odcs.yaml`): Lint green via datacontract-cli 1.2.7.

### 7. Verification

```
# End-to-end capacity planning test
opencode ctxvm trace --session bench-test --budget 120000
# ... run agent benchmark ...

# Simulate metrics under different policies (trace positionals; --baseline/--windows flags only)
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline naive
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-healthy.jsonl --baseline fault-pin

# Export and validate
ctxvm export --odps --session bench-test --output corpus/0.1/
venvs/odps/bin/open-data-products validate corpus/0.1/manifest.yaml --json
# {valid: true, spec: odps 4.1, errors: [], warnings: [], hints: [], path: ..., version: ...}
# Note: compliance_level and production_ready are not emitted by the SDK 4.1 CLI.

# Hub re-build (byte-identical check)
tools/build-hub.sh
# hub/catalog.yaml + hub/index.html — byte-identical

# CI gate
cargo test
python spec/rfc-0/validate_schema.py corpus/0.1/trace.jsonl
tools/build-hub.sh --check-identity
```

**Exit criteria:**
- `validate_schema.py` exit 0 (108 checks qualify with two-fixture argv: healthy + thrashing fixtures)
- `cargo test` exit 0 (28+ tests green)
- `tools/build-hub.sh` produces byte-identical artifacts
- ODPS manifest validation passes (`valid`, spec odps 4.1, errors empty).
- M0 gates met: net token reduction ≥ 1.5×, fault recall ≥ 95%, replay determinism 100%, corpus conformance 100%
