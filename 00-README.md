# ctxvm — Project Workspace

**Working title:** `ctxvm` (library) / **xCABI** (the standard). Rename pending — candidates: `pagefault`, `membrane`, `kctx`.

> The Context Base Layer: a virtual-memory manager for LLM agent context, delivered as an
> interoperable standard (xCABI), a deterministic engine (Rust core + TS/Py bindings), and an
> open measurement stack (corpus + simulator + policy leaderboard), packaged and distributed as
> ODPS/LF-native open data products.

## Status

Build in progress (see `08-HANDOFF.md` §5 board): Rust M0 complete (codec + engine replay,
28 tests green), xCABI RFC-0 + strict schema landed (55/55 conformance), metric simulator
green (T3), ODPC hub artifacts proven (T5), MCP shim + harness adapter designs landed
(T6/T7, `design/`), upstream issue drafts ready (T2, `upstream/`). Board complete —
see `reports/RR-BOARD-COMPLETE-20261022.md`.

## What is decided

| Decision | Choice |
|---|---|
| Core language | Rust (`ctxvm-core`, zero heavy deps) |
| Bindings | napi-rs (TypeScript/Node) + PyO3/maturin (Python) |
| v0 wedge | **Telemetry-first tracer** (read-only flight recorder; OpenTelemetry playbook) |
| Determinism | Semantic/LLM-based faults **excluded** from core (policy plugins, marked non-deterministic) |
| Prompt hygiene | No instructional prompt pollution in v0; identity stubs carry recovery instructions |
| Cache economics | Evictions batched at turn boundaries; `call.meta` records estimated cache cost |
| Standards packaging | ODPS 4.1 manifests at the edge (never in the Rust core); hub = ODPC Git repo |
| License target | Apache-2.0 (library + spec), corpus under ODPS `license` block |

## File index

| File | Contents |
|---|---|
| `01-PLAN.md` | Full consolidated plan: thesis, prior art, architecture, milestones, risks |
| `02-xcabi-events-v0.md` | Draft event vocabulary + log invariants for the xCABI trace format |
| `03-tracer-api-ts.md` | Telemetry-first tracer API sketch (TypeScript) + CLI surface |
| `04-odps-dataproduct-corpus.yaml` | ODPS 4.1 manifest for the trace corpus (Reusable Data Product + MCP port) |
| `05-llms.txt` | ODPS-recommended AI discovery file derived from the manifest |
| `06-odps-integration.md` | ODPS/ODPC/ODPV findings, frictions, upstream engagement list |
| `07-benchmarks-go-no-go.md` | Benchmark suites, metric definitions, M0 pass/fail gates |
| `08-HANDOFF.md` | **Master agent handoff**: rules of engagement, reporting protocol, task board (T0–T7). Hand this file to any agent to continue the work |
| `spec/rfc-0/` | **xCABI RFC-0** (per `08` card T4): `RFC-0-xCABI.md` (normative semantics, timing + ordering tables, replay contract) · `x-cabi.schema-v0.json` (strict JSON Schema) · `validate_schema.py` (55-check conformance validator over all vector fixtures) |
| `benchmarks/metrics/` | **T3 metric reference impl**: `metrics.py` (07's four formulas + counterfactual baseline + CLI), fixtures (healthy/thrashing), 18 tests |
| `hub/` | **T5 ODPC hub proof**: `catalog.yaml` (ODPC v1.0, SDK-built) + `index.html` — hub.ctxvm.dev as an ODPC repo; regen via `tools/build-hub.sh` |
| `rust/` | Rust workspace (T1a–T1d complete: codec + engine + replay + conformance vectors; 28+ tests) |
| `upstream/` | T2 upstream issue drafts (file-ready: ODPS schema/docs + datacontract-cli, evidence from real validator runs) |
| `design/` | Integration designs: `mcp-shim.md` (T6 — callTool decorator contract) · `adapters.md` (T7 — OpenCode plugin + Vercel AI SDK middleware/tap, pinned anchors) |

## Task/report flow

Work is managed via `08-HANDOFF.md` §5 task board. Completed work lands as a report in
`reports/RR-<TASK-ID>-<date>.md` + one index line in `reports/LOG.md`, and the task card's
status is updated in place. `contracts/` holds the ODCS v3.0.2 data contract (lint green).

## Next actions (in order)

1. ~~Validate manifest against their SDK~~ **DONE** — SDK 0.4.0: `valid`, `compliance_level:
   full`, `production_ready: true`. Results and schema-vs-docs drift table in `06-odps-integration.md`.
2. ~~Author ODCS contract~~ **DONE** — `contract audit` fully green (`product audit`:
   `passed: true`, `contract_valid: true`, ODCS v3.0.2 lint via datacontract-cli 1.2.7).
   Details and tooling constraints in `06-odps-integration.md`.
3. ~~**Rust M0 spike: `ctxvm-core`**~~ **DONE** — page table + event log + deterministic
   renderer + replay engine + conformance vectors; 28+ tests green (T1a–T1d).
4. ~~File upstream ODPS/CLI issues~~ **Drafted & evidence-verified (T2)** — see
   `upstream/issues-drafts.md`; filing venue + submission is an orchestrator follow-up.

*Tooling: ODPS validation — `/tmp/opencode/ctxvm-venv/bin/open-data-products` (py3.14);
contract validation/audit — `/tmp/opencode/odcs-venv/bin/` (py3.12, via conda env `ctxvm-odcs`).*

