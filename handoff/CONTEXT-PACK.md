# CONTEXT-PACK — the stable brief (a dated snapshot; re-derive numbers with the cited commands)

## 1. What ctxvm and xCABI are
1. ctxvm is a virtual-memory manager for LLM agent context; xCABI is the portable trace standard it emits (00-README.md).
2. A trace is a JSONL file, one event per line, in the nine sealed v0 verbs (spec/rfc-0/RFC-0-xCABI.md).
3. RFC-0.1 adds additive fields only (schemaVersion, ts, toolEffect, providerUsage, environmentId, latencyMs, prefix, turn); sealed v0 keeps rejecting v0.1-only lines (spec/rfc-0.1/).
4. The Rust core (`rust/`) page table and renderer runs deterministically; it never mutates messages — telemetry first, control later (08-HANDOFF.md §0).
5. `ctxvm replay` re-derives the page table and checks embedded turn totals; divergence exits 1 (08-HANDOFF.md §5/T1d).
6. Harness adapters capture real agents: OpenCode, Hermes (capture default-on), AI SDK, shared tracer `@ctxvm/node`.
7. Measurement stack: metric formulas + fixtures + policy simulator (`benchmarks/metrics/`), packaged as ODPS data products.
8. W8's "does paging help?" is CLOSED FAILED: paging never bent the request curve; the task was search-bound (`reports/RR-W8INDEX-20261107.md`).
9. What a trace does NOT record: a page OMITTED from the request — RFC-0 v0 has no omission verb (`page.evict` requires `stubText`), `turn.render.evictedTokens` is unchecked in v0 (OPEN T-OVICT) and is a LAGGING CUMULATIVE, and `turn.render.residentTokens` is TABLE residency, not request residency (`reports/RR-SHAPEGAP-20261113.md`, `reports/RR-OMISSION-20261113.md`).
10. The sidecar's `enginePlan` names the plan's **reason** (`fits` | `floor_bust` | `evicted`) but does **not** say whether the request changed (`fits` also covers a reposition-only rewrite), its `residentTokens` is **request** residency (not the wire's table residency), and its `prefixHash` is a probe whose window moves with the cut (`reports/RR-H9LANDING-20261114.md`).

## 2. Glossary (one line each, from the repo)
- page — content a tool result contributes to a turn, addressed without carrying its bytes (white-paper.md §4.1; RFC-0 event table).
- page_id — `(logical_ref, content_hash)` identity, content-blind (rust/crates/ctxvm-codec/src/model.rs:14–21).
- turn — index of request cycles; `page.evict` @ t makes the stub visible AT turn t (RFC-0 ordering, line 91).
- render — per-turn mirror of what the model sees as `turn.render`; totals embedded for replay.
- fault — `page.fault`: model re-requests resident/stubbed content; sources tool_recall | identifier_scan | explicit_api | semantic.
- stub — the recovery text an evicted page leaves; instructions only, never prompt pollution.
- protected floor — system prompt + protected head/tail + pins; over vBudget `_plan` returns early, no selection (context_engine.py:287–292; RR-ENGINEGAP-20261106).

## 3. Repo map (directories)
- `00-09 numbered docs` — plan, event draft, tracer API, ODPS manifest, llms.txt, integration findings, benchmark gates, handoff, update prompt.
- `rust/` — ctxvm-codec (wire + strict codec; fields declared before `ts`), ctxvm-core (page table, replay, diff, profile, export), ctxvm-tokenizer (apx4-char + tiktoken), ctxvm-conformance (CLI + vectors).
- `packages/` — node/opencode/ai-sdk/hermes/py. `spec/rfc-0/` + `spec/rfc-0.1/` — sealed + additive layers with validators. `corpus/m1–m8/` — checksummed drops.
- `benchmarks/metrics/` — metrics.py, prices.json, bootstrap.py, policies.py, monitor_replay.py. `hub/` — ODPC catalog. `design/` — plans of record. `tools/` — run-ci.sh + handoff tools. `reports/` — RR cards + LOG.md. `research/` — white-paper lane.

Five files first: `00-README.md`; `08-HANDOFF.md` §0–§4; `spec/rfc-0/RFC-0-xCABI.md`; `07-benchmarks-go-no-go.md`; `reports/RR-W8INDEX-20261107.md`.

## 4. Metric definitions and formulas (paths)
`benchmarks/metrics/metrics.py` (docstring lines 6–15, executable): net_token_reduction (124), refetch_rate (146), hard_fault_recall (159), touch_ratio (14; waste = 1 − TR), thrash_index (15; windows mandatory for thrash claims — RR-UC3-WINDOWSHEET-20261025).
CIs: `bootstrap.py`, seed 20261029, 2000 resamples (RR-W3-20261029). Pricing: `prices.json`, priceModelVersion 2, USD per 1M, owner-supplied; unknowns null, NEVER substituted with 0; cache-write unmodeled in v0.
W8's NTR (plan §4d): `1 − paged_input / naive_input` on provider receipts (`perApiRequest` request evidence; turn.render when present, never imputed; design/w8-run-plan.md; RR-W8RESCOPE-20261107). Tier-1 monitor: `monitor_replay.py` → `monitor-results.json` (`--check` fails on drift).

## 5. The determinism boundary (five lines)
1. Core = pure replayable engine: no LLM, no embedding, no network in the deterministic layer (white-paper.md §5.2).
2. Semantic/embedding fault classes are policy plugins, marked non-deterministic (08-HANDOFF.md §4-LIST).
3. Proven byte-identical across machines: page-table derivation per given trace — render geometry: page table, resident/stub composition, stub text, token math (AGENTS.md law 8).
4. Not claimed: full input byte-reproduction (pages carry identity, not payloads — RR-WP2REV), model-output determinism, "deterministic" without that scope (08.1 W9).
5. Tier-2 model runs marked nonDeterministic always (design/W19); tier-1 monitors are zero-model-call functions of recorded traces.

## 6. Status vocabulary and evidence levels
Workstream: LANDED/DONE (card + gate green), DRY-RUN LANDED, BLOCKED / NOT RUNNABLE, CLOSED. Claims: UNVERIFIED / UNVERIFIED-<date>, UNMEASURED, directional / single-corpus. Data: prices.json observed | UNVERIFIED | null. Gates: preregistered PASS/FAIL with CIs (w8-run-plan M0; paired non-inferiority δ=10pp).
Papers: Part I "verified" only with locators; Part II (draft) grades every read (read-in-full / abstract / snippet / secondary) and refuses to run experiments — below full read cannot be asserted (RR-WP2REV-20261107).

## 7. Standing reviewer questions (ask of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply all five to their own work BEFORE asking; an item that cannot answer (1) or (2) from repo evidence is not ready for review.

## 8. Labels (how to read the books)
- W-numbers: workstream IDs, defined in `08.1-UPDATE-PROMPT.md` §W (e.g. W8 does-paging-help, W19 tier-2 interventions).
- W8 vocabulary: cell = one preregistered task×page-family measurement point; slice = the two-cell restart prompt (`design/W8-PROMPT-SLICE.md`); arm = the naive-vs-paged half of a paired run.
- D-numbers: the decision ledger — D1–D12 owner-ruled (e.g. D9 ts opt-out, D11 signing); D13–D19 tracked in PROJECT-STATE.
- RR-<slug>-<date>[-n]: one card's report file under `reports/`; `reports/LOG.md` rows `| card | area | summary |` are the append-only ledger. Some cards exist only as a LOG row beside the commit carrying them (e.g. RR-W8BOOK-20261107 → `89ff8e4`).
- lane: one agent session owning one scope; owned paths + must-not-write map in `handoff/LANES.md`.
