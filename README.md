# ctxvm

[![ci](https://github.com/kapitaali/ctxvm-xCABI/actions/workflows/ci.yml/badge.svg)](https://github.com/kapitaali/ctxvm-xCABI/actions/workflows/ci.yml)

**A trace format and replay engine for LLM agent context.** `xCABI` records what an agent
put in its context window — as pages, faults and a replayable page table — and `ctxvm`
replays that record deterministically. Rust core, four harness adapters (OpenCode, Hermes,
Vercel AI SDK, Node), and a public trace corpus. `ctxvm` / `xCABI` are working names.

> **v0 is a read-only flight recorder.** Nothing is evicted, rewritten, or injected into a
> prompt by the tracer. The trace is the product; paging control is not built.

## Adoption status (read this first)

- **One author, one machine.** Every trace in `corpus/` was captured by the same person on
  the same laptop. No outside contributor has sent a trace, a bug report, or a patch.
- **Not published.** Nothing is on npm, crates.io, or PyPI. The only consumer outside this
  repo is [`umpire`](https://github.com/kapitaali/umpire), which is also this author's.
- **No foundation, no affiliation.** The project is Apache-2.0 and unattached. It is not an
  LF/CNCF/OpenSSF project and does not claim to be governed by one (see
  [Governance](#governance)).
- **What would count as adoption:** a second implementer of the schema, a trace captured by
  someone else's harness, or a downstream product reading the format. None of those exist
  today.

## Measured limitations (2026-10-29)

These are the numbers the repo can currently defend. Anything not listed here is not
measured, and the docs say so where it matters.

| Limitation | Evidence |
|---|---|
| **No real session has ever paged.** All 4 `page.evict` events in the corpus sit on one *synthetic* trace (`m1/session-thrashing`); the 10 real captures have zero evictions. | `page.evict` census over `corpus/m1`–`m8` (17 traces: 10 real, 7 synthetic) |
| **The paging gate is unmeasured.** The v0 gate is hard-fault recall ≥ 95 % (95 % CI lower bound, n ≥ 30). Real captures carry **n = 4** hard faults. | `reports/RR-W3-20261029.md` |
| **Token counts are estimates.** `apx4-char` = ⌈characters / 4⌉; `tiktoken` BPE backends exist behind a feature but are not what the corpus used. **0 of 85** `call.meta` records carry provider-reported usage. | `benchmarks/metrics/prices.json`, `corpus/*/` census |
| **Fault counts depend on the capture surface.** The Hermes `identifier_scan` surface is dead on live payloads (the adapter reads a shape Hermes does not send), so `m4`/`m7` under-report faults to zero. Fix proposed, not landed. | `packages/hermes/OBSERVABILITY.md`, `reports/RR-W4-20261029.md` |
| **Cross-harness comparisons are not yet apples-to-apples.** A Hermes "turn" is a user turn; an OpenCode/AI-SDK turn is a model request. | `design/`, `corpus/m7` vs `m8` |
| **Single corpus, free tiers.** Captures used free-tier or locally-shaped models at USD 0; the corpus is small (17 traces, 118 pages) and does not represent production traffic. | `corpus/*/provenance.json` |
| **The control-plane claim is untested.** The plan's 1.5× net-token-reduction milestone has no experiment behind it yet. | `01-PLAN.md` M0 gate, `07-benchmarks-go-no-go.md` |

## Status (2026-10-29)

| track | state |
|---|---|
| **engine (M0)** | `rust/` — codec (strict JSONL, byte-identical vectors) + page table + deterministic renderer + replay/profile/diff/export CLIs · **59 tests** (60 with `--features tiktoken`), 0 warnings |
| **standard (RFC-0)** | `spec/rfc-0/` — normative semantics + strict JSON Schema; conformance **PASS (682 checks)** over 27 fixtures, 17 of them corpus traces |
| **measurement** | `corpus/m1`–`m8` (17 traces: seed, live OpenCode, Hermes, resume pairs, AI-SDK) each with `provenance.json` + `checksums.sha256` · `benchmarks/metrics/` reference impl (44 tests) + eviction-policy simulator · ODPS manifest `productVersion 0.8.0` validated by SDK 0.4.0 |
| **instrumentation** | `packages/node` (13 tests) · `packages/opencode` live v2 plugin (58) · `packages/hermes` plugin (80) · `packages/ai-sdk` middleware/tap (45) · `packages/py` binding (8) |
| **CI** | `tools/run-ci.sh` mirrors `.github/workflows/ci.yml` — 4 jobs (rust / ts / schema+corpus / hub parity) |
| **design** | `design/` — MCP tool-shim, harness adapters (pinned contracts), UC1 pause/resume, **OTel mapping + a working OTLP/JSON projector** (`tools/otel-export.mjs`) |

## Verify it yourself

```sh
tools/run-ci.sh            # local mirror of the Actions workflow
```

Output of the witness run on 2026-10-29 (local mirror; the same four gates run in Actions):

```text
[ctxvm-ci] rust suite green
[ctxvm-ci] tokenizer tiktoken feature green (real BPE backends)
[ctxvm-ci] ts suites green (13 + 58 + 45 tests); python suites green (80 + 44 + 8 tests)
positive: 677 event lines validated across 27 fixtures
negative: 5 engineered bad cases correctly rejected
SCHEMA CONFORMANCE: PASS (682 checks)
[ctxvm-ci] hub byte-identity green
[ctxvm-ci] ALL GATES GREEN
```

**What those gates prove:** the codec round-trips byte-identically, replay is
divergence-free on every committed trace, the schema rejects engineered bad input, the
corpus checksums match, and the published hub regenerates byte-identically.
**What they do not prove:** that paging helps, that the token counts are the provider's,
or that the format transfers between people. Those are the open items above, not CI's job.

## Governance

Today: a single maintainer, decisions recorded in `08-HANDOFF.md` §4 (locked decisions) and
in `reports/` (one report per change), schema changes gated by an explicit owner decision.
RFC-0 is **sealed** for v0 — proposals that would change it are written as proposals first
(`reports/*-PROPOSAL-*.md`) and only applied with the owner's sign-off.

Roadmap, in the order the evidence allows:

1. Reproduce the portability claim (one task, two harnesses, `ctxvm diff`) before any
   standards claim — workstream W5.
2. Fix the capture surface so a fault count means the same thing in every harness.
3. Only then propose RFC-0.1 (clock, provider usage, turn on `page.declare`) and publish a
   conformance kit.
4. Governance changes (a second maintainer, a foundation, a versioned change policy) follow
   the first *external* implementer — not before.

## Repo map

Curated details live in [`00-README.md`](00-README.md) (file index + locked-decisions table).

| path | what |
|---|---|
| [`01-PLAN.md`](01-PLAN.md) | full plan — thesis, prior art (locators at first mention), architecture, milestones |
| [`02-xcabi-events-v0.md`](02-xcabi-events-v0.md) | event vocabulary + log invariants (spec source) |
| [`spec/rfc-0/`](spec/rfc-0/) | **xCABI RFC-0** + `x-cabi.schema-v0.json` + conformance validator |
| [`rust/`](rust/) | cargo workspace: `ctxvm-core`, `ctxvm-codec`, `ctxvm-tokenizer`, `ctxvm-conformance` (vectors + CLIs) |
| [`packages/`](packages/) | `@ctxvm/node` · `@ctxvm/opencode` · `@ctxvm/ai-sdk` · Hermes plugin · Python binding |
| [`corpus/`](corpus/) | 8 drops, `provenance.json` + `checksums.sha256` each |
| [`benchmarks/metrics/`](benchmarks/metrics/) | metric definitions executable + tested, policy simulator, pinned price model |
| [`design/`](design/) | MCP shim, harness adapters, UC1 pause/resume, **OTel mapping** |
| [`reports/`](reports/) | per-task reports + append-only `LOG.md` index |
| [`08-HANDOFF.md`](08-HANDOFF.md) | **agent entry point** — rules of engagement, task board, protocol |

## For agents

Read [`08-HANDOFF.md`](08-HANDOFF.md) §0–§4 before doing anything: it is the single source
of truth for the task board and reporting protocol. Integrity rule: every external claim
carries its locator at first mention; unverified claims are marked, never stated as fact.

## License

Apache-2.0 — see [`LICENSE`](LICENSE). The trace corpus is packaged and licensed per its
ODPS manifest ([`04-odps-dataproduct-corpus.yaml`](04-odps-dataproduct-corpus.yaml)); each
drop carries its own `provenance.json` (what was captured, on what harness, with what was
redacted).
