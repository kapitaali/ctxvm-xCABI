# RR-BOARD-COMPLETE — task board T0–T7 finished

**Date:** 2026-10-22 · **Per `08-HANDOFF.md` §6**: all §5 cards are DONE; this report
summarizes state and proposes the next three tasks. **No new scope is opened here.**

## Where the project stands after the initial board

**Standard (xCABI)**
- RFC-0 named + normative semantics locked at `spec/rfc-0/RFC-0-xCABI.md` (event tables,
  §5 timing: same-turn render / t+1 fault effect; §7 stub format; §8 fault rules) with
  strict 2020-12 JSON Schema; conformance validator extended through the board to a
  **108/108 PASS** baseline (50 vector lines + 5 negative gates + 2 fixtures via argv).
- M0 semantics survived three independent consumer exercises (T3 metrics, T6 shim,
  T7 adapters) **without a single format change** — the telemetry-first wedge holds.

**Engine (Rust)**
- `rust/` workspace: codec (byte-identical vectors), page table + deterministic renderer,
  replay engine (exit-1-on-divergence), conformance vectors crate — 28+ tests green.

**Measurement stack (open)**
- `benchmarks/metrics/` — 07's four formulas + counterfactual baseline + CLI as an
  executable reference (18/18 pytest), with two replay-consistent, schema-valid fixtures
  (healthy / thrashing) exercising the validator end-to-end.
- `hub/` — ODPC v1.0 catalog + HTML built only by their SDK (`tools/build-hub.sh`),
  byte-identical across rebuilds; hub-as-ODPC-repo claim proven and committed.
- Empirically validated ODPS 4.1 (`valid`, `compliance_level: full`) + ODCS v3.0.2
  (audit fully green).

**Integration designs (zero code, zero scope creep)**
- `design/mcp-shim.md` (T6) — callTool decorator contract: verbatim mirror (v0) / RFC-0 §7
  stub (v1), canonical tool+args matching, resident re-calls priced via the existing
  `FaultOfResidentPage` ledger rows, 3-flag surface.
- `design/adapters.md` (T7) — OpenCode plugin + Vercel AI SDK middleware/tap integration
  plans with file/function anchors pinned at descriptor commits
  (OpenCode `e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b`; vercel/ai `36e4ce7c7f4c2a51676167634adb8c4eb3b18e77`),
  glue ≤ 50 LoC each, test strategies + risk lists.

**Upstream posture**
- `upstream/issues-drafts.md` (T2) — five file-ready issues with every validator line
  live-reproduced on SDK 0.4.0 / datacontract-cli 1.2.7 (incl. new finding: SLA
  `displayTitle`/`displaytitle` double-definition in the bundled schema).

**Commits this session (marker points on `main`):**
`4ce99b2` (T3) · `9760337` (T5) · `a835af3` (T6) · `096c0bc` (T7) · `c44d38b` (T2).

## Proposed next three tasks (awaiting orchestrator approval)

1. **T8 — `@ctxvm/node` v0 tracer (M).** TypeScript implementation of the T6/T7
   contract surfaces (`trace()`, `vm.page_raw`, `vm.render`, `vm.observe_recall`,
   `vm.scan_text`), emitting RFC-0-valid JSONL; fixtures replayed through
   `validate_schema.py`. DoD: unit tests green; two fixture-traces pass the 108-check
   validator; no paging/eviction logic (mirror only).
2. **T9 — OpenCode adapter spike (M).** Load the T7 plugin in a dev OpenCode build;
   run one MCP echo session; capture real hook payloads as fixtures; resolve the two
   open questions flagged in RR-T7 (`toolOutput.truncate` reach-through, provider-executed
   tools); validate the resulting trace (schema + replay divergence check).
   DoD: committed fixture set + validator-passing trace + report.
3. **T10 — Corpus drop M1 + CI (L).** First ODPS-packaged public corpus slice
   (recorded benchmark sessions incl. a real thrashing capture), hub re-linked via
   `tools/build-hub.sh`, plus GitHub Actions gate: `cargo test` + schema validator +
   hub byte-identity check. DoD: green CI workflow + corpus manifest re-validated.

Rationale: T8→T9 unblocks the first real-harness measurement (M2 = the next milestone
after M0); T10 turns the repo into a continuously-validated, publishable artifact.

## Protocol tail

Board statuses live in `08-HANDOFF.md` §5 (all DONE); report index in `reports/LOG.md`.
Per §6, **stopping here** — awaiting orchestrator decision on T8/T9/T10 before any
further work.
