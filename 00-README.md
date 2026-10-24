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
see `reports/RR-BOARD-COMPLETE-20261022.md`. **Extension stage 2:** `@ctxvm/node` v0
mirror tracer DONE (T8 — 12 unit tests; both committed fixtures pass the schema gate
and are replay-divergence-free); T9 adapter spike DONE (`@ctxvm/opencode` — recorded-
payload replay validated; RR-T7's two open questions source-resolved; live dev-build echo
deferred). **T10 DONE** — corpus drop M1 (`corpus/m1/`: 5 provenance-labeled checksummed
traces; manifest 0.1.1 re-validated; hub re-linked + `hub/hub.sha256` baseline) and the
repo CI gate (`tools/run-ci.sh` byte-equivalent to `.github/workflows/ci.yml` — ALL GATES
GREEN locally 2026-10-22; Actions-green starts once a git remote exists) — see
`reports/RR-T10-20261022.md`. **T12 DONE 2026-10-23** — live M2 capture: the OpenCode v2
promise-plugin adapter (`packages/opencode/live/`) drove two real sessions into `corpus/m2/`
(echo beats + 5×5 sustained re-fetch) on a free-tier model at USD 0; schema PASS,
replay-divergence-free, manifest → 0.2.0 (`x-cabi.latestDrop`) + hub re-linked — see
`reports/RR-T12-20261023.md`. **T17.8 DONE 2026-10-24** — first **live** Hermes capture:
`corpus/m4/hermes-live-session-01.jsonl` (23 events, 13 pages, 1 `tool_recall` fault,
1 errored call, 2 turns) recorded by plugin v0.2.0 inside a running session; schema PASS,
replay-divergence-free, manifest → 0.4.0 (`x-cabi.latestDrop corpus/m4`) + hub re-linked —
see `reports/RR-T17.8-20261024.md` and `packages/hermes/BUG_REPORT.md` for the fixed defect.

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
| `rust/` | Rust workspace (T1a–T1d complete: codec + engine + replay + conformance vectors; 52 workspace tests, 0 warnings — `replay <file> [--turn N] [--pin <logical-ref>|(ref, hash)]... [--output FILE]`, `profile <file> [--event <type>]... [--turns a-b,c-d] [--source <src>] [--output FILE]`, `diff <a.jsonl> <b.jsonl> [--output FILE]`, `export <trace.jsonl> [--turn N] [--output DIR] [--odps]` UC1/UC2 forensic + handoff surfaces, per RR-UC2REPLAY/RR-T18-PROFILE/RR-T19-DIFF/RR-T20-PINPRECISION/RR-T21-EXPORT-20261024) |
| `upstream/` | T2 upstream issue drafts (file-ready: ODPS schema/docs + datacontract-cli, evidence from real validator runs) |
| `projects/` | Standalone project specs to be *implemented with* this stack (not framework features; orchestrator go/no-go) — `01-open-decision-primitive.md` (`umpire`) went **M0 GO 2026-10-22**: repo split to `~/Documents/umpire/`, first commit `d7896df`, gates green; this file remains the proposal-of-record |
| `design/` | Integration designs: `mcp-shim.md` (T6 — callTool decorator contract) · `adapters.md` (T7 — OpenCode plugin + Vercel AI SDK middleware/tap, pinned anchors) |
| `packages/hermes/` | **T17 Hermes plugin**: Python port of `@ctxvm/node` tracer wired into Hermes hook domains (`packages/hermes/live/__init__.py` + `src/plugin.py`); env-gated `register(ctx)` emitting RFC-0 xCABI JSONL (`npm test` / `python test/test_plugin.py` in-dir) |
| `packages/opencode/` | **T9 spike**: `@ctxvm/opencode` — OpenCode plugin (T7 Adapter A) wiring `@ctxvm/node` via pinned hook contracts (e965774f); recorded echo-session payloads → validated, replay-clean trace (`npm test / gen` in-dir) |
| `corpus/` | **T10/T12/T17.8 drops**: `m1/` seed slice — 5 xCABI traces; `m2/` live slice — 2 OpenCode harness captures; `m3/` Hermes plugin traces — 2 synthetic sessions (echo + sustained pressure); `m4/` first **live** Hermes capture — 1 redacted session (23 events, 13 pages, 1 fault); each drop has `provenance.json` + `checksums.sha256`; manifest-linked via `x-cabi.firstDrop`/`latestDrop` (v0.4.0) |
| `tools/` | `build-hub.sh` (T5 hub regen chain — venv-or-PATH SDK resolution) · `run-ci.sh` (T10 byte-equivalent local CI mirror) |
| `.github/` | **T10**: `workflows/ci.yml` — 4 jobs (rust / ts / schema+corpus / hub parity), pins mirroring the local toolchain; runs once the repo has a git remote |

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

