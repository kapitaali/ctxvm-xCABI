# RR-REDLINE-20261108 — Redline Benchmark (16k)

Date: 2026-11-08
Card: REDLINE (PROMPT.md Phases 0-4)
Condition: B — strictly outside ctxvm-xCABI. The benchmark workspace is outside this repo and is written `<benchmark-dir>` throughout; the ctxvm checkout is its read-only sibling. Neither location is a personal directory in this record.
Repo HEAD: `a1d2efb7519406e4dca6c0fa61726a461fadfdda` (matches `git ls-remote --heads origin` main).
Machine: Linux 6.12.115+deb13.1-amd64. Python 3.14.7 (venv `redline-benchmark/.venv`, tiktoken 0.14.0, fastapi 0.162.2). Node 26.10.0, cargo 1.99.1. Rust built with `--release` (+ `--features tiktoken` for tiktoken-rs 0.12.1).
Sample: n = 1 run per arm, 51 calls per arm. Seed: 20261108. Tokenizer: `o200k_base` exact (tiktoken), never `apx4-char`. Model: `offline-deterministic-responder-v1` (no real LLM call) — see Limitations.

## 0. Terminology — what counts as a token here

- `proxy prompt_tokens` = exact `tiktoken o200k_base` count of serialized `system + user + rendered tool_results` as received by MockLLMProxy.handle(). Logged per call in `proxy.jsonl`. This is the only token figure used in §4's providerReported comparison.
- `providerReported` = proxy-reported exact BPE count. The proxy stands in for the provider in offline test mode (PROMPT Phase 1 Rule 2). In xCABI `call.meta.cacheEstimate.providerReported=true` (proxy is the simulated provider). This is **not** OpenAI/real-provider usage — no real spend exists.
- `residentTokens` (xCABI `turn.render`) = Σ declared `page.tokens` of full (non-stubbed) pages per replay tally semantics (`render.rs tally_at`). All 50 declared pages count from turn 0 (m5 pattern: incremental declare, constant slot total). This is slot accounting, **not** proxy prompt tokens. Both are reported; they are not conflated.
- `netTokens` via repo `benchmarks/metrics/metrics.py` = Σ `residentTokens` + Σ `call.meta estMissTokens` (= proxy prompt tokens here). See `logs/*/metrics.json`.

## 1. Executive Summary

**Claim tested:** active context management yields 1.5x net-token reduction without extra hard faults or degraded completion (PROMPT).

**Result (this synthetic benchmark only): 1.10x, not 1.5x. Claim disproved under this workload/definition.**

- Proxy prompt tokens (51 calls summed): baseline 608,480 vs ctxvm 554,772. Ratio **1.0968x**, reduction **8.83%** (53,708 tokens saved). Required for 1.5x: ctxvm ≤ 405,653 (i.e., 33.3% reduction). Observed ctxvm is 149,119 tokens above that threshold.
- Final turn prompt: baseline 15,875 vs ctxvm 13,883 (1.1435x). Still <1.5x.
- xCABI rendered Σ `residentTokens`: baseline 1,351,024 vs ctxvm 1,279,916 (1.056x). `metrics.py` counterfactual net reduction: baseline 0.098, ctxvm 0.134.
- Completion: both arms success (needle found). 1/1 each, n=1 — no rate can be claimed.
- Hard faults observed (re-reads): 0 both. Gate `hard_fault_recall ≥95% (n≥30)` is **UNMEASURED** (n=0 here; real corpus n=4 per README).

No cost-saving claim beyond token counts is made (AGENTS Law 7). Priced net cost not computed: mock provider has no verified price (repo `prices.json` v2: openai unverified, nvidia/opencode free-tier observed — neither applies to this offline responder).

## 2. Baseline Metrics (native blind truncation)

- Task completion: success. `output.txt` = `FOUND AE79C0`. Final turn needle scan found needle in full-rendered page 32.
- Calls: 51 (50 read turns + FINAL). Status 200 on all 51. Proxy 413 count: 0 in benchmark runs (harness truncates before proxy). 413 path verified separately: `handle` with 20,005 tokens → 413, logged, processed 0.
- Tokens attempted (as received by proxy after truncation) = 608,480. Tokens processed = 608,480. Completion tokens = 105 (50×"READ_OK" + FINAL). Total proxy = 608,585.
- Per-call average prompt: 11,931. Final prompt: 15,875 (≤16,000).
- Evictions/truncations: 25 pages stubbed by end (final stubbed 25/50). Blind policy: if total >16,000, oldest full page → stub (`[CONTEXT REDACTED BY CTXVM - FAULT TOLERANT]` placeholder in rendered prompt) until ≤16,000. Dropped pages are placeholder slots, not removed (shape stability).
- Hard faults (re-reads performed): 0. No recovery loop was run. "Needle would need re-read if lost" is not counted as a hard fault (repo W3 ground truth = explicit re-calls only).
- Needle residency at FINAL: full (page 32 never stubbed). `needle_resident_full=true`.
- xCABI trace: 1,503 events, schema PASS (3,066 checks over 2 traces + negative cases), `replay` exit 0, divergences [], violations [].
- Metrics: rendered 1,351,024, estimatedMisses 608,480, net total 1,959,504. Counterfactual netTokenReduction 0.098. refetchRate 0.0, touchRatio 0.0, thrash 0.0.

## 3. ctxvm Active Metrics (prototype sidecar)

- Task completion: success. `output.txt` = `FOUND AE79C0`. Same needle, same file.
- Calls: 51, all 200. Proxy 413 count: 0.
- Tokens attempted = processed = 554,772. Completion = 105. Total proxy = 554,877.
- Per-call average: 10,878. Final prompt: 13,883 (≤14,000 budget; ≤16,000 proxy).
- Events: `page.compress` 30, `page.evict` (hard) 0, sidecar errors (fail-open triggers) 0. Stubbed pages final: 30/50. Policy: if total >14,000, compress oldest full page (50-token extractive synopsis) until ≤14,000; hard-evict only if still over. Hard-evict never needed in this run.
- Summarizer (exact, generic, no needle knowledge): first 2 lines + last 2 lines + any lines containing `id=`/`needle=`/`resp=`, deduplicated, truncated to 50 tokens. Preserves structured `key=` lines generically.
- Needle residency: full (page 32 never compressed). `needle_resident_full=true`, `needle_in_synopsis=false`. Success did not depend on summarizer fidelity in this run — see §5.
- Classification used: SYSTEM immutable, USER_QUERY immutable, TOOL_RESULT evictable/compressible, MEMORY — none in this run (no extraction before FINAL).
- xCABI trace: 1,508 events, replay exit 0, divergences [], violations []. Schema PASS. (Note: `page.compress` is a v1 controller event; in v0 trace it appears as `page.evict` with stub=synopsis, plus `sidecar_decisions.jsonl` records compress vs hard-evict split.)
- Metrics: rendered 1,279,916, misses 554,772, total 1,834,688. Counterfactual reduction 0.134. refetch 0.0, touch 0.0, thrash 0.0.

## 4. The Delta — exact providerReported math

Definitions (all counts are proxy-logged exact BPE, no `apx4-char`):

```
baseline processed   B = Σ_{turn=0..50} prompt_tokens_baseline(turn) = 608,480
ctxvm processed      C = Σ_{turn=0..50} prompt_tokens_ctxvm(turn)    = 554,772
ratio  B/C           = 608480 / 554772 = 1.0968
reduction 1 - C/B    = 1 - 554772/608480 = 0.0883  (8.83%)
savings  B - C       = 53,708 tokens
1.5x requirement     C_req = B / 1.5 = 405,653. Observed C - C_req = +149,119 over threshold.
```

Secondary (same logs):

```
final-turn ratio  15875 / 13883 = 1.1435
per-call avg ratio  11931 / 10878 = 1.0968 (same as summed ratio)
xCABI rendered ratio  1351024 / 1279916 = 1.0560
repo counterfactual: baseline 0.098, ctxvm 0.134 (metrics.py, seed 20261029, 2000 bootstrap)
```

Attempted vs processed: identical for both arms (608,480 / 554,772) because policy (truncate §2, compress §3) runs **before** proxy. Proxy never received >16,000 in benchmark runs, so 413=0 and attempted=processed. The "raw" workload total (30,615 tokens, manifest; 30,664 declared) is the unstripped corpus size, not a baseline run — a naive no-truncation final prompt would be ~30,700 tokens and would 413. It is not used as denominator.

Workload construction (exact): `generate_workload.py`, `random.Random(20261108)`, needle drawn first = `AE79C0`, 50 files ~600 tokens each (600-649 range, file-32 has needle line inserted at 60% and is 649 tokens), total 30,615.

## 5. Failure Analysis

No task failure occurred in either arm, so no eviction-policy vs reasoning-error attribution is needed.

Evidence:
- Both arms: `success=true`, `needle_resident_full=true`. Needle file (index 32) lies in the newest (retained) window at FINAL under both policies: baseline keeps files ~25-49 full (25 oldest stubbed); ctxvm keeps ~20-49 full (30 oldest compressed). Index 32 is full in both.
- `needle_in_synopsis=false`: the needle was never summarized away because its page was never the oldest when budget pressure hit. A mid-file needle *would* be lost by a naive head-only summarizer; this run does not test that path (summarizer picks `key=` lines including `needle=`, but it never had to).
- Hard faults: 0 observed. No agent re-read. Therefore "without increasing hard faults" is vacuously 0 vs 0 for this trace, not a gate pass (gate needs n≥30; here n=0).
- LLM reasoning error: none measurable — responder is deterministic string scan, not an LLM. No reasoning variance, no model nondeterminism claimed (AGENTS Law 8: only page-table derivation determinism is claimed, and only for replay determinism which holds).
- If the needle had been in file 5 (early), baseline truncation would have stubbed it (needle lost → FINAL `NOT_FOUND`), and ctxvm would have compressed it. Whether the `key=`-preserving summarizer saves it depends on synopsis truncation order (head-truncated to 50). That counterexample workload was **not** run; its outcome is UNMEASURED here.

## 6. Artifacts (trace byte-identical; proxy timestamps vary)

All paths are relative to `<benchmark-dir>`:

- Workload: `experiments/redline-16k/workload/generate_workload.py`, `manifest.json` (seed 20261108, needle AE79C0), `files/file-*.log` (50).
- Proxy: `experiments/redline-16k/harness/mock_proxy.py` (413 + logging, stdlib HTTP server + in-process handle).
- Sidecar: `experiments/redline-16k/sidecar/ctxvm_sidecar.py` (14k budget, compress/evict, fail-open: parse exception → log + pass through unmodified; 0 errors in runs).
- Harness: `experiments/redline-16k/harness/harness.py` (baseline vs ctxvm, replay-clean xCABI emission).
- Baseline logs: `experiments/redline-16k/logs/baseline/{proxy.jsonl,trace.jsonl,summary.json,output.txt,metrics.json}` — 51 proxy lines, 1,503 trace events.
- ctxvm logs: `experiments/redline-16k/logs/ctxvm-active/{proxy.jsonl,trace.jsonl,sidecar_decisions.jsonl (30 lines),summary.json,output.txt,metrics.json}` — 51 proxy lines, 1,508 trace events. Canonical dir per PROMPT Phase 3 (`logs/ctxvm-active/`); `redline-benchmark/logs/` mirrors exist from Phase 0 setup.
- Workspace outputs: `redline-benchmark/workspace/output-baseline.txt`, `output-ctxvm.txt` (both `FOUND AE79C0`).
- Checkpoint: `experiments/redline-16k/PHASE0-CHECKPOINT.md`.
- This report: `reports/RR-REDLINE-20261108.md`.

Trace determinism: `trace.jsonl` contains no wall-clock `ts`, so re-runs of the same seed produce byte-identical traces (same 1,503 / 1,508 events). `proxy.jsonl` contains a `ts` unix timestamp per call, so its bytes vary by run time; token/status columns are deterministic. Schema PASS + replay exit 0 were re-verified after the final clean re-runs (2026-11-08 15:40-15:42).

Validation commands (all green; run from repo root for schema/replay, prompt dir for harness):

```sh
# reproduce workload (deterministic)
redline-benchmark/.venv/bin/python experiments/redline-16k/workload/generate_workload.py
# run arms (n=1 each)
redline-benchmark/.venv/bin/python experiments/redline-16k/harness/harness.py --arm baseline
redline-benchmark/.venv/bin/python experiments/redline-16k/harness/harness.py --arm ctxvm
cp -r experiments/redline-16k/logs/ctxvm/* experiments/redline-16k/logs/ctxvm-active/
# schema + replay (must be exit 0 / PASS)
python3 spec/rfc-0/validate_schema.py <baseline/trace.jsonl> <ctxvm-active/trace.jsonl>
./rust/target/release/replay <each trace>
# repo metrics
venvs/odps/bin/python benchmarks/metrics/metrics.py <trace>  # saved to logs/*/metrics.json
```

## Echo Law + scope

- No `ctxvm` core files modified. No diff. Only outside-repo Python sidecar/harness. Cargo build artifacts (`rust/target/`) are gitignored. Repo status unchanged beyond pre-existing dirty files; no push/commit.
- v0 remains read-only flight recorder. The sidecar is a prototype v1 controller (intercept before proxy, page-table classification, compress/evict) per PROMPT Phase 3; it does not alter RFC-0 (`spec/rfc-0/` sealed, untouched).
- Token counts are proxy-logged exact `o200k_base`, never `apx4-char` (PROMPT Telemetry First). Provider is mock; "providerReported" means proxy-reported (§0).
- Negative results given same prominence as successes (AGENTS §5): the 1.5x claim is disproved here.

## Limitations

- n=1 per arm, synthetic logs, offline responder — no LLM variance, no CI, no real-session generalisation. 1.5x under other workloads (different needle position, re-demand patterns, priced caches, real summariser models) is UNMEASURED / UNVERIFIED.
- Retry/re-read loop not run: hard-fault recovery unobserved (0 vs 0).
- Cost: no verified price for mock provider; net cost not computed (priceModelVersion 2 not applicable).
- Single needle position (file-32, late) favours both policies. Sensitivity to needle position and summariser design is the main open variable.
