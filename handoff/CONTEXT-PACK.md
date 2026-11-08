# CONTEXT-PACK — the stable brief (a dated snapshot; re-derive numbers with the cited commands)

## 1. What ctxvm and xCABI are
1. ctxvm is a virtual-memory manager for LLM agent context; xCABI is the portable trace standard it emits (00-README.md).
2. A trace is a JSONL file, one event per line, in a sealed v0 vocabulary: session.open, page.declare, page.render, page.evict, page.fault, page.pin, page.unpin, turn.render, call.meta (spec/rfc-0/RFC-0-xCABI.md).
3. RFC-0.1 adds additive fields only (schemaVersion, ts, toolEffect, providerUsage, environmentId, latencyMs, prefix, turn); sealed v0 must keep rejecting v0.1-only lines (spec/rfc-0.1/).
4. The Rust core (`rust/`) page table and renderer runs deterministically; it never mutates messages — telemetry first, control later (08-HANDOFF.md §0).
5. `ctxvm replay` re-derives the page table from events and checks against the trace's embedded totals; divergence exits 1 (08-HANDOFF.md §5/T1d).
6. Harness adapters capture real agents: OpenCode (`packages/opencode`), Hermes Agent (`packages/hermes`, capture default-on), Vercel AI SDK (`packages/ai-sdk`), shared tracer `@ctxvm/node`.
7. Measurement stack: metric formulas + fixtures + policy simulator (`benchmarks/metrics/`), packaged as ODPS data products (manifest + hub).
8. Determinism boundary: no LLM, no embedding, no network in the core; semantic faults live in policy plugins, marked non-deterministic (research/white-paper/white-paper.md §5.2).
9. Corpus: m1–m8 checksummed drops; the hub is an ODPC catalog.
10. W8's "does paging help?" is CLOSED FAILED on record: paging never bent the request curve; the task was search-bound (reports/RR-W8INDEX-20261107.md).

## 2. Glossary (one line each, from the repo)
- page — content a tool result contributes to a turn, addressed without carrying its bytes (white-paper.md §4.1; RFC-0 event table).
- page_id — `(logical_ref, content_hash)` identity, content-blind (rust/crates/ctxvm-codec/src/model.rs:14–21).
- trace — the JSONL event stream of one capture; "The trace is the only artifact" (white-paper.md §5.1).
- turn — index of request cycles; `page.evict` @ t makes the stub visible AT turn t (RFC-0 ordering, line 91).
- render — per-turn mirror of what the model sees as `turn.render`; totals embedded for replay (white-paper.md §5.1).
- fault — `page.fault`: model re-requests content already resident/stubbed; sources tool_recall | identifier_scan | explicit_api | semantic (RFC-0 fault taxonomy; white-paper.md §3.6).
- stub — the identity/recovery text an evicted page leaves: recovery instructions only, no prompt pollution (00-README decided table; `page.evict.stubText`).
- harness — the upstream agent runtime captured (OpenCode, Hermes Agent, ai-sdk apps); one plugin per harness (00-README decided table).
- intervention run — a tier-2 model run with one thing changed; artifact is a sidecar `<run>.intervention.json` (parent digest, target, sampling, model); never in the deterministic boundary (design/W19-tier2-interventions.md).
- protected floor — system prompt + protect_first_n=3 head + protect_last_n=6 tail + pins; when it exceeds vBudget, `_plan` returns early, selection does nothing (packages/hermes/live/context_engine.py:12,287–292; RR-ENGINEGAP-20261106).
- touch ratio — touched_tokens / rendered_tokens; honestly "identifier-touched share", an upper bound (benchmarks/metrics/metrics.py:14; 08.1 W1).
- fault recall — hard_fault_recall = explicit re-calls / hard faults (Pichay §3.2; metrics.py:159, W3); old recovered/evictions survives as refetch_rate (metrics.py:146).
- net token reduction — `1 − (paged_net_tokens / naive_tokens)`; a ratio metric (metrics.py:124; saving claims violate law 7; W8 closed failed).

## 3. Repo map (directories)
- `00-09 numbered docs` — plan, event draft, tracer API, ODPS manifest, llms.txt, integration findings, benchmark gates, handoff, update prompt.
- `rust/` — ctxvm-codec (wire + strict codec; fields declared before `ts`), ctxvm-core (page table, replay, diff, profile, export), ctxvm-tokenizer (apx4-char + tiktoken feature), ctxvm-conformance (CLI + vectors).
- `packages/` — node/opencode/ai-sdk/hermes/py. `spec/rfc-0/` + `spec/rfc-0.1/` — sealed + additive layers, each with a validator. `corpus/m1–m8/` — checksummed drops.
- `benchmarks/metrics/` — metrics.py, prices.json, bootstrap.py, policies.py, monitor_replay.py, fixtures. `hub/` — ODPC catalog. `design/` — plans of record. `tools/` — run-ci.sh, ci-rehearsal.py, coverage_check.py, handoff tools. `reports/` — RR-* cards + append-only LOG.md. `research/` — white-paper lane, read-only for agents.

Five files first: `00-README.md`; `08-HANDOFF.md` §0–§4; `spec/rfc-0/RFC-0-xCABI.md`; `07-benchmarks-go-no-go.md`; `reports/RR-W8INDEX-20261107.md`.

## 4. Metric definitions and formulas (paths)
`benchmarks/metrics/metrics.py` (docstring lines 6–15, executable): net_token_reduction (124), refetch_rate (146), hard_fault_recall (159), touch_ratio (14; waste = 1 − TR), thrash_index (15; windows mandatory for thrash claims — `benchmarks/metrics/fixtures/window-families.json`, RR-UC3-WINDOWSHEET-20261025).
CIs: `benchmarks/metrics/bootstrap.py`, seed 20261029, 2000 resamples (RR-W3-20261029). Pricing: `benchmarks/metrics/prices.json`, priceModelVersion 2 (2026-11-06), USD per 1M, owner-supplied; unknowns are null, NEVER substituted with 0; cache-write unmodeled in v0.
W8's NTR (plan §4d): `1 − paged_input / naive_input` on provider receipts; request evidence = `.coverage.json` `perApiRequest`; turn.render used when present, never imputed (design/w8-run-plan.md; RR-W8RESCOPE-20261107). Tier-1 monitor: `benchmarks/metrics/monitor_replay.py` → `monitor-results.json` (`--check` fails on drift).

## 5. The determinism boundary (five lines)
1. Core = pure replayable engine: no LLM, no embedding, no network in the deterministic layer (white-paper.md §5.2).
2. Semantic/embedding fault classes are policy plugins, marked non-deterministic (08-HANDOFF.md §4-LIST).
3. Proven byte-identical across machines: page-table derivation per given trace — render geometry: page table, resident/stub composition, stub text, token math (AGENTS.md law 8).
4. Not claimed: full input-message byte-reproduction (pages carry identity, not payloads — RR-WP2REV-20261107 vs model.rs:14–21), model-output determinism, or "deterministic" without that scope (08.1 W9).
5. Tier-2 model runs marked nonDeterministic always (design/W19); tier-1 monitors are zero-model-call functions of recorded traces.

## 6. Status vocabulary and evidence levels
Workstream: LANDED/DONE (card + gate green), DRY-RUN LANDED, BLOCKED / NOT RUNNABLE (books gate), CLOSED. Claims: UNVERIFIED / UNVERIFIED-<date>, UNMEASURED, directional / single-corpus language (08.1 §2). Data: prices.json observed | UNVERIFIED | null — three legal states, none substituted. Gates: preregistered PASS/FAIL with CIs (design/w8-run-plan.md M0; paired non-inferiority δ=10pp).
Papers: Part I marks prior art "verified" only with locators; Part II (draft) grades every read — read-in-full / abstract / snippet / secondary — anything below full read cannot be asserted (recorded in RR-WP2REV-20261107), and states "This paper runs no experiment."

## 7. Standing reviewer questions (ask of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply all five to their own work BEFORE asking; an item that cannot answer (1) or (2) from repo evidence is not ready for review.
