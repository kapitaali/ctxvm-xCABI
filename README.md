# ctxvm

[![ci](https://github.com/kapitaali/ctxvm-xCABI/actions/workflows/ci.yml/badge.svg)](https://github.com/kapitaali/ctxvm-xCABI/actions/workflows/ci.yml)

**A trace format and replay engine for LLM agent context.** `xCABI` records what an agent
put in its context window — as pages, faults and a replayable page table — and `ctxvm`
replays that record deterministically. Rust core (codec, page table, renderer, CLIs), a
host-side paging engine in the Hermes adapter (`packages/hermes/live/context_engine.py`),
four harness adapters (OpenCode, Hermes, Vercel AI SDK, Node), and a public trace corpus.
`ctxvm` / `xCABI` are working names.

> **v0 tracing is read-only: the tracer evicts, rewrites, and injects nothing.** The paging
> engine is a separate, opt-in host-side layer that selects and drops pages under a token
> budget; the trace records what the engine dropped (`turn.render.evictedTokens`). The first
> counted W8 pair is measured — see [Measured limitations](#measured-limitations-2026-11-11).

## Adoption status (read this first)

- **One author, one machine.** Every trace in `corpus/` was captured by the same person on
  the same laptop. No outside contributor has sent a trace, a bug report, or a patch.
- **One external index selection — live.** [XERJ](https://xerj.org/) selected the
  [W3 metrics implementation](https://github.com/kapitaali/ctxvm-xCABI/commit/7a4f499765da082f7b5d5a2c05fc896b5b6a8988)
  ([report](reports/RR-W3-20261029.md)) for inclusion in its public
  [Corpus Hub](https://hub.xerj.org/) index, under Apache-2.0 with attribution. **Both pages verified
  live on 2026-11-11**, and XERJ's founder confirmed the same day that the contributor page carries the
  attribution: contributor page
  [`hub.xerj.org/contributors/kapitaali`](https://hub.xerj.org/contributors/kapitaali) and
  corpus page [`hub.xerj.org/corpus/kapitaali--ctxvm-xcabi`](https://hub.xerj.org/corpus/kapitaali--ctxvm-xcabi)
  (1 corpus, 1 selected commit, 5 source files / 494 lines, Apache-2.0, 1 GitHub star).
  [![XERJ Corpus Hub contributor](https://hub.xerj.org/contributors/kapitaali/badge.svg)](https://hub.xerj.org/contributors/kapitaali)
  This is a reference-index selection of one artifact, not adoption of xCABI: no XERJ
  trace in `corpus/`, no second implementation, and no outside downstream xCABI reader
  is public. One discrepancy: the Hub pages say the author "agreed by email on
  2026-10-29", but the repo's record shows no reply had been sent as of that date
  (`reports/RR-XERJ-20261029.md`); the agreement came later.
- **Not published.** Nothing is on npm, crates.io, or PyPI. The only *runtime* consumer
  outside this repo is [`umpire`](https://github.com/kapitaali/umpire), which is also this
  author's.
- **No foundation, no affiliation.** The project is Apache-2.0 and unattached. It is not an
  LF/CNCF/OpenSSF project and does not claim to be governed by one (see
  [Governance](#governance)).
- **What would count as adoption:** a second implementer of the schema, a trace captured by
  someone else's harness, or a downstream product reading the format. None of those exist
  today; the XERJ selection above is distribution, not adoption.

## Quickstart (5 minutes, from a checkout)

Nothing is published yet — npm, crates.io and PyPI publication is pending the packaging
work in [`design/packaging.md`](design/packaging.md). Today the install is a clone plus a
Rust build.

```sh
git clone https://github.com/kapitaali/ctxvm-xCABI.git
cd ctxvm-xCABI
cargo build --release

# the synthetic thrash demo: evictions, faults, per-turn residency
./rust/target/release/replay corpus/m1/session-thrashing.jsonl    # exit 0 = no replay divergence
./rust/target/release/profile corpus/m1/session-thrashing.jsonl  # per-page/turn profile
./rust/target/release/stream ~/.local/state/ctxvm/traces          # sessions grouped by environment
```

`profile` prints every page's decision history, faults and the per-turn residency for any
RFC-0 trace. `stream` groups trace files by `environmentId` (W14) and orders them by start. **A file is a process slice, not a whole conversation:** each restart builds a new tracer and each stop truncates, so one long session can appear as several rows — era copies (`tools/snapshot-capture.sh`) are the only way to keep the earlier segments over
time, which is the only way the cross-session questions become observable: how many
declarations repeat across sessions of one repository, and how many a render never showed.
Row fields are counts of DISTINCT keys — `turns` counts distinct turn boundaries (one turn
index = one turn, whatever the index), `pages`/`rendered` count unique page keys — and
`residentTokens` pairs with the highest turn index.
`cargo install --path rust/crates/ctxvm-conformance` puts all six binaries (`replay`,
`profile`, `diff`, `export`, `tokens`, `stream`) on `PATH`.

**Wrap an agent.** Nothing is captured unless a trace directory is set.

*OpenCode* — add a one-line shim at `<project>/.opencode/plugins/ctxvm.ts`:

```ts
export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts";
```

then run with capture enabled:

```sh
CTXVM_TRACE_DIR=/tmp/ctxvm-capture CTXVM_TRACE_NAME=demo \
CTXVM_MODEL=<provider/model> CTXVM_PROVIDER=<provider> \
opencode run --standalone --auto -m <provider/model> "your task"
```

The trace and its sidecar appear when the process exits gracefully.

*Hermes* — copy `packages/hermes/live/` to `~/.hermes/plugins/ctxvm-tracer/`, enable it,
then from inside Hermes:

```
/ctxvm-trace start /tmp/ctxvm-capture demo
... run your task ...
/ctxvm-trace stop
```

Either way, profile the result with
`./rust/target/release/profile /tmp/ctxvm-capture/demo.jsonl`. Full recipes:
[`packages/opencode/live/README.md`](packages/opencode/live/README.md) and
[`packages/hermes/live/README.md`](packages/hermes/live/README.md).

## Measured limitations (2026-11-11)

These are the numbers the repo can currently defend. Anything not listed here is not
measured, and the docs say so where it matters.

| Limitation | Evidence |
|---|---|
| **The corpus has no real evictions; the experiment does.** All 4 `page.evict` events in `corpus/` sit on one *synthetic* trace (`m1/session-thrashing`); the 10 real captures have zero. Live W8C runs page, but this engine drops rather than stubs, so the count rides `turn.render.evictedTokens` and no `page.evict` row is emitted. | `page.evict` census over `corpus/m1`–`m8` (17 traces: 10 real, 7 synthetic); `reports/RR-W8CEVICT-20261111.md` |
| **`residentTokens` is table residency, not request residency.** Under a removal policy the wire value is the whole-table tally — 21 pages / 86,569 tokens — while the request carried 12 pages (47,805); RFC-0 v0 has no verb for omission, `turn.render.evictedTokens` is unchecked in v0, and the derived table is not turn-scoped, so a trace-only reader cannot say which pages a given request omitted. | `reports/RR-SHAPEGAP-20261113.md` (21 / 86,569 vs 12 / 47,805; provider receipts at ratio 0.563), `reports/RR-W8DERRATUM-20261113.md`; capture `local-d60a50c4…` |
| **The paging gate is unmeasured under the new fault semantics.** The v0 gate is hard-fault recall ≥ 95 % (95 % CI lower bound, n ≥ 30). Plugin 0.12.0 redefined a fault as "the model asked for the same page again" (`tool_recall`), so the corpus's n = 4 hard faults no longer maps to the gate's definition. | `reports/RR-W3-20261029.md`, `reports/RR-W8C-INSTRUMENT-20261111.md` |
| **Token counts are estimates in the corpus; the experiment now has provider usage.** `apx4-char` = ⌈characters / 4⌉; `tiktoken` BPE backends exist behind a feature but are not what the corpus used. **0 of 85** `call.meta` records carry provider-reported usage. W8C cell-01 reads provider usage from the Hermes DB sessions table (`cache_read`/`cache_write`), outside the corpus. | `benchmarks/metrics/prices.json`, `corpus/*/` census, `reports/RR-W8CCELL01-20261111.md` |
| **Fault counts depend on the capture surface — fix landed in plugin 0.12.0.** The Hermes `identifier_scan` surface no longer emits faults (it was a second, independent rule); prose mentions are telemetry (`page["prose_mentions"]`), and `page.fault` now has two honest producers: `tool_recall` and `explicit_api`. | `packages/hermes/OBSERVABILITY.md`, `reports/RR-W8C-INSTRUMENT-20261111.md` |
| **Cross-harness comparisons are not apples-to-apples, and the factor is measured.** A Hermes "turn" is a user turn (`turn.render` buckets about two model requests under it); an OpenCode or AI-SDK turn is a model request. The same six-prompt file-read task yields **6 `turn.render` rows on Hermes and 13 on OpenCode** with the same model (18 with a second free model), so any denominator of `turn.render` is harness-specific. Our measurements survive only because they are within-Hermes or denominated in sessions/requests. | `reports/RR-OCDIFF-20261113.md`; OpenCode drops are `corpus/m2`, `m5`, `m6` (`m7` is Hermes, `m8` AI-SDK — `provenance.json`) |
| **Provider-reported usage exists on one adapter only.** `call.meta.providerUsage` is present on **6/6** Hermes receipts in the same task and **0/13** (OpenCode, longcat) and **0/18** (OpenCode, deepseek). No cost, cache or window claim may be made from an OpenCode capture; the RFC-0.1 additive field is emitted by the Hermes lane, not by that adapter. | `reports/RR-OCDIFF-20261113.md` field-coverage table |
| **The corpus is v0 and carries none of the additive fields.** No drop has `schemaVersion`, `providerUsage` or `ts` placement, and none records a user-prompt count, so requests-per-turn for a corpus drop is UNKNOWN rather than derivable. | `corpus/*/provenance.json`, `spec/rfc-0/` |
| **Single corpus, free tiers.** Captures used free-tier or locally-shaped models at USD 0; the corpus is small (17 traces, 112 distinct `page.declare` keys) and does not represent production traffic. | `corpus/*/provenance.json` |
| **The control-plane effect is measured on a free and a paid subject; no saving may be claimed.** W8C cell-02 (longcat, free tier): the request stops at ~61 k from turn 12 (final 64,733 against the control's 107,794, 0.60×), 210,856 evicted tokens, parsed-equal. W8C cell-03 (`openai/gpt-6-luna`, paid, 20 prompts, budget 60,000): the request is held at 0.57×, 275,362 evicted tokens, 44 selections, and the gateway's own cost estimate is $0.1580 against the control's $0.0748 — **2.11×** — pair $0.2328. Fewer tokens sent, more dollars spent: the rewritten prefix is a cache miss every turn. Two cells, n = 1 each, no grid; law 7: no cost-saving claim. | `reports/RR-W8CCELL02-RUN-20261112.md`, `reports/RR-W8CCELL03-RUN-20261112.md` |
| **The first counted W8 pair is negative.** Naive 5 calls / $0.0175 vs paged 14 / $0.1264 — 3.14× input tokens and 7.2× dollars; mechanism = prefix-cache forfeiture, not selection quality. | `design/w8-cache-stable-selection.md` |

## Status (2026-11-12)

| track | state |
|---|---|
| **engine (M0)** | `rust/` — codec (strict JSONL, byte-identical vectors) + page table + deterministic renderer + replay/profile/diff/export/stream CLIs · **77 tests** (78 with `--features tiktoken`), 0 warnings |
| **paging engine** | `packages/hermes/live/context_engine.py` — host-side page selection/drop under a token budget; reports `turn.render.evictedTokens`; plugin **0.13.1** |
| **standard (RFC-0)** | `spec/rfc-0/` — normative semantics + strict JSON Schema; conformance **PASS (682 checks)** over 27 fixtures, 17 of them corpus traces |
| **standard (RFC-0.1)** | `spec/rfc-0.1/` — additive shape + validator (`validate_schema_v0_1.py`); CI runs it as a separate gate |
| **measurement** | `corpus/m1`–`m8` (17 traces: seed, live OpenCode, Hermes, resume pairs, AI-SDK) each with `provenance.json` + `checksums.sha256` · `benchmarks/metrics/` reference impl (66 tests) + eviction-policy simulator · ODPS manifest `productVersion 0.8.0` validated by SDK 0.4.0 |
| **instrumentation** | `packages/node` (24 tests) · `packages/opencode` live v2 plugin (62) · `packages/hermes` plugin (200) · `packages/ai-sdk` middleware/tap (46) · `packages/py` binding (8) |
| **CI** | `tools/run-ci.sh` mirrors `.github/workflows/ci.yml` — 4 jobs (rust / ts / schema+corpus / hub parity) · pre-push check: `python3 tools/ci-rehearsal.py --committed` (the committed tree only) |
| **design** | `design/` — MCP tool-shim, harness adapters (pinned contracts), UC1 pause/resume, **OTel mapping + a working OTLP/JSON projector** (`tools/otel-export.mjs`), W8B/W8C plans, **cache-stable selection** (`w8-cache-stable-selection.md`), RFC-0.1 |
| **experiment (W8)** | naive-vs-paged cells; **three W8C cells measured** — cell-02 (free, 0.60× request) and cell-03 (paid, 0.57× request at 2.11× cost), cell-01 void as an instrument bug; spend ledger `reports/W8-SPEND.md` |

## Verify it yourself

```sh
tools/run-ci.sh            # local mirror of the Actions workflow
```

Output of the witness run on 2026-11-11 (local mirror; the same four gates run in Actions):

```text
[ctxvm-ci] rust suite green
[ctxvm-ci] tokenizer tiktoken feature green (real BPE backends)
[ctxvm-ci] ts suites green (24 + 62 + 46 tests); python suites green (200 + 8 + 66 tests)
positive: 677 event lines validated across 27 fixtures
negative: 5 engineered bad cases correctly rejected
SCHEMA CONFORMANCE: PASS (682 checks)
[ctxvm-ci] hub byte-identity green
[ctxvm-ci] ALL GATES GREEN
```

**What those gates prove:** the codec round-trips byte-identically, replay is
divergence-free on every committed trace, the schema rejects engineered bad input, the
corpus checksums match, and the published hub regenerates byte-identically.
**What they do not prove:** that paging helps (the first counted W8 pair is negative — see
[Measured limitations](#measured-limitations-2026-11-11)), that the token counts are the
provider's, or that the format transfers between people. Those are the open items above,
not CI's job.

## Governance

Today: a single maintainer, decisions recorded in `08-HANDOFF.md` §4 (locked decisions) and
in `reports/` (one report per change), schema changes gated by an explicit owner decision.
RFC-0 is **sealed** for v0 — proposals that would change it are written as proposals first
(`reports/*-PROPOSAL-*.md`) and only applied with the owner's sign-off.

Roadmap, in the order the evidence allows:

1. Reproduce the portability claim (one task, two harnesses, `ctxvm diff`) before any
   standards claim — workstream W5.
2. Fix the capture surface so a fault count means the same thing in every harness —
   landed in plugin 0.12.0 (see [Measured limitations](#measured-limitations-2026-11-11)).
3. RFC-0.1 is applied (owner decision D4, 2026-10-30) and runs as an additive CI gate; the
   conformance kit for third-party implementers is the open item.
4. Governance changes (a second maintainer, a foundation, a versioned change policy) follow
   the first *external* implementer — not before.

## Support this project

Every number here was measured on free-tier models — which is why the corpus stays small.
The decisive paging experiment (W8) is now measured, and its first counted pair is negative
(see [Measured limitations](#measured-limitations-2026-11-11)); donations buy model compute
for larger measurement corpora and fund development.

Bitcoin: `bc1qrdah46qfwkd03nqv88d9rw9mpgqat3ymhv0268` (bech32 P2WSH)

**All donations are used to buy more compute and develop this project** — no legal
entity, no tax deductibility, no perks; one maintainer, Apache-2.0, and the only thing
on offer is more measurement. Donations raise the corpus budget above the current
preregistered cap; the cap and its spend stay recorded in `reports/`.

## Repo map

Curated details live in [`00-README.md`](00-README.md) (file index + locked-decisions table).

| path | what |
|---|---|
| [`01-PLAN.md`](01-PLAN.md) | full plan — thesis, prior art (locators at first mention), architecture, milestones |
| [`02-xcabi-events-v0.md`](02-xcabi-events-v0.md) | event vocabulary + log invariants (spec source) |
| [`spec/rfc-0/`](spec/rfc-0/) | **xCABI RFC-0** + `x-cabi.schema-v0.json` + conformance validator |
| [`spec/rfc-0.1/`](spec/rfc-0.1/) | **xCABI RFC-0.1** (additive) + `x-cabi.schema-v0.1.json` + validator |
| [`rust/`](rust/) | cargo workspace: `ctxvm-core`, `ctxvm-codec`, `ctxvm-tokenizer`, `ctxvm-conformance` (vectors + CLIs) |
| [`packages/`](packages/) | `@ctxvm/node` · `@ctxvm/opencode` · `@ctxvm/ai-sdk` · Hermes plugin (+ host-side paging engine) · Python binding |
| [`corpus/`](corpus/) | 8 drops, `provenance.json` + `checksums.sha256` each |
| [`benchmarks/metrics/`](benchmarks/metrics/) | metric definitions executable + tested, policy simulator, pinned price model |
| [`design/`](design/) | MCP shim, harness adapters, UC1 pause/resume, **OTel mapping**, W8B/W8C plans, **cache-stable selection** |
| [`reports/`](reports/) | per-task reports + append-only `LOG.md` index + W8 spend ledger |
| [`08-HANDOFF.md`](08-HANDOFF.md) | **agent entry point** — rules of engagement, task board, protocol |

## For agents

Read [`AGENTS.md`](AGENTS.md) first for the rules that a green test does not protect, then
[`08-HANDOFF.md`](08-HANDOFF.md) §0–§4 for the task board and reporting protocol. Integrity rule: every external claim
carries its locator at first mention; unverified claims are marked, never stated as fact.

## License

Apache-2.0 — see [`LICENSE`](LICENSE). The trace corpus is packaged and licensed per its
ODPS manifest ([`04-odps-dataproduct-corpus.yaml`](04-odps-dataproduct-corpus.yaml)); each
drop carries its own `provenance.json` (what was captured, on what harness, with what was
redacted).
