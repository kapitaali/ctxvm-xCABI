# CtxVM — MASTER HANDOFF (agent-facing)

> **You are a fresh AI agent continuing the CtxVM project.** Everything you need is in
> `/home/theb/Documents/ctxvm/`. Read §0–§4 fully before doing anything. Then pick ONE task
> card from §5, execute it, and report per §4. Do not skip ahead, do not re-plan.

*Last updated: 2026-10-22 · Maintainer rule: whoever completes a task MUST update its card
status in §5 and append the report index line in `reports/LOG.md`. This file is always the
single source of truth for "what's next".*

---

## §0. 30-second context

**Project:** `ctxvm` — a virtual-memory manager for LLM agent context, delivered as
(a) **xCABI**: a portable, deterministic agent-trace/page/fault standard (RFC-0 pending),
(b) `ctxvm-core`: a Rust engine (page table, event log, deterministic renderer, replay),
(c) bindings/tooling (TS via napi-rs, Py via PyO3), and (d) an open measurement stack
(trace corpus → simulator → policy leaderboard) packaged as **ODPS 4.1 / LF** data products.

**Strategic wedge (locked):** telemetry-first, control-later. v0 = read-only flight recorder
for any agent loop (OpenTelemetry playbook). Paging control ships later behind an opt-in policy.

**Current state (2026-10-22):** planning artifacts complete; ODPS manifest + ODCS contract
**empirically validated green**; repo initialized (git main); persistent local venvs under
`venvs/`; Rust toolchain user-provided (cargo/rustc 1.99.1 — non-login shells need
`. "$HOME/.cargo/env"` once per invocation).
**M0 COMPLETE (T1a–T1d done):** codec (strict JSONL, byte-identical vectors) + engine
(page table, deterministic renderer) + replay w/ divergence detection + `replay` CLI.
28 tests, 0 warnings.
**Next frontier:** T3 (metric simulator over JSONL traces) + toolchain-free cards
T2 (upstream issue drafts), T5 (ODPC hub proof), T6 (MCP tool-shim note), T7 (adapter
survey). Rust M0 + RFC-0 done.

## §1. Workspace map

```
/home/theb/Documents/ctxvm/
├── 00-README.md                 # overview + locked-decisions table + file index
├── 01-PLAN.md                   # full plan: thesis, prior art, architecture, milestones
├── 02-xcabi-events-v0.md        # xCABI event vocabulary draft + log invariants  ← SPEC SOURCE
├── 03-tracer-api-ts.md          # v0 tracer API + CLI surface
├── 04-odps-dataproduct-corpus.yaml   # ODPS manifest — VALIDATED (see header for proof)
├── 05-llms.txt                  # ODPS-recommended AI discovery file
├── 06-odps-integration.md       # ODPS/ODCS findings + validation results + upstream issue list
├── 07-benchmarks-go-no-go.md    # benchmark suites + metric formulas + M0 pass/fail gates
├── 08-HANDOFF.md                # THIS FILE
└── contracts/corpus-0.1.odcs.yaml    # ODCS v3.0.2 contract — LINT GREEN
```

## §2. Environment & tooling (READ — venvs are ephemeral, recreate as needed)

Two validated toolchains, now **persistent as workspace-local venvs** (built by
`tools/setup-env.sh`, committed in T0). Prefer these over any `/tmp` venv.

| Purpose | Command | Interpreter constraint |
|---|---|---|
| ODPS manifest validation (SDK 0.4.0) | `venvs/odps/bin/open-data-products validate 04-…yaml --json` | any ≥3.9 (venv built on py3.14) |
| ODCS contract lint + product audit | `venvs/odcs/bin/datacontract lint contracts/…`; `venvs/odcs/bin/open-data-products product audit 04-…yaml --json` | **must be Python ≤3.12** — `datacontract-cli` is gated `python_version < "3.13"` and pip SILENTLY SKIPS it on ≥3.13 |
| (planned) Rust M0 | **user provisions Rust globally — agents MUST NOT self-install rustup or any toolchain** (user removed a local install on 2026-10-22). Verify with `cargo --version` first | none known |

Historical (may be dead): ODPS venv `/tmp/opencode/ctxvm-venv` (py3.14, base miniforge);
contract venv `/tmp/opencode/odcs-venv` (py3.12, from conda env `ctxvm-odcs`).

## §3. Rules of engagement

1. **Never redesign locked decisions.** §4-LIST below is authoritative. If a task card seems
   to contradict them, stop, write the conflict into your report, and pick a different task.
2. **Stay in the lane of the card.** No scope creep, no "while I'm here" refactors,
   no dependency upgrades. Discoveries go into the report, not the codebase.
3. **Never delete or edit other agents' reports.** Append-only `reports/`.
4. **All validation claims must include the actual command + output** (or truncated JSON)
   in the report. Saying "it worked" without the command output is a failed report.
5. **Do not rename files** (`00-…` numbering is load-bearing). Do not create new top-level
   directories not listed in a card. Reports and task-specified output dirs are exempt.
6. If environment setup fails after two serious attempts: mark the card BLOCKED in §5,
   write the report with exact errors, pick another card that needs no toolchain.

## §4. Reporting protocol (this is how the orchestrator hears from you)

When a card's Definition-of-Done is met:

1. Create `reports/RR-<TASK-ID>-<YYYYMMDD>.md` (e.g. `RR-T0-20261022.md`) containing, in order:
   - **Card executed:** id + title
   - **What was done:** bullet list (files written/changed, commands run)
   - **Verification:** commands + real outputs proving each DoD item
   - **Deviations from card:** anything you did differently and why (or "none")
   - **Discoveries:** facts that should update other files/cards (be specific)
   - **Open questions:** for the orchestrator (or "none")
2. Append one line to `reports/LOG.md`: `| RR-<TASK-ID>-<date> | <task id> | <one-line summary> |`
3. Update the card's **Status** row in §5 below (and shift the "Next frontier" line in §0).
4. Finally, print a ≤10-line summary of the report to the user.

**If blocked or confused:** write the report with status `BLOCKED` + exact error text, then
still print the summary. A failed task documented well is a completed task's equal.

**§4-LIST — locked decisions (do not revisit):** Rust core + napi-rs/PyO3 bindings ·
telemetry-first v0 (tracer never mutates messages) · determinism boundary (no LLM/embedding
in core; semantic faults = plugins) · zero prompt pollution in v0 · evictions batched at
turn boundaries · `call.meta` carries estimated cache cost · ODPS/ODCS strictly at the edge
(never in Rust core) · corpus DQ maps replay-determinism→`validity`(ODPS)/`conformity`(ODCS) ·
Vanilla names not yet final (`ctxvm`/`xCABI` working names — renaming is an explicit
orchestrator task only).

## §5. Task board (pick any card whose status is OPEN and whose dependencies are DONE)

| ID | Title | Size | Depends | Status |
|---|---|---|---|---|
| T0 | Repo init + env setup script | S | — | **DONE** (RR-T0-20261022, commit `bba1f8f`) |
| T1a | Rust workspace scaffold (crates only) | S | T0 | **DONE** (RR-T1a-20261022 + RESOLUTION; cargo 1.99.1, 4/4 tests green) |
| T1b | Event model + JSONL codec + roundtrip vectors | M | T1a | **DONE** (RR-T1b-20261022; 15 tests green, vectors byte-identical) |
| T1c | Page table + deterministic renderer | L | T1b | **DONE** (RR-T1c-20261022; 10 core tests, determinism property green) |
| T1d | Replay engine + conformance vectors crate | M | T1c | **DONE** (RR-T1d-20261022; `replay` CLI exit-1-on-divergence, M0 gate met) |
| T2 | Upstream issue drafts (ODPS + CLI + templates) | S | — | OPEN |
| T3 | Metric simulator reference impl (Python) | M | T1b | OPEN |
| T4 | xCABI RFC-0: spec md + JSON Schema | M | T1b | **DONE** (RR-T4-20261022; schema PASS 55/55 vs all fixtures) |
| T5 | ODPD hub pipeline: ODPC catalog via odpc-build | S | T0 | OPEN |
| T6 | MCP tool-shim design note | S | — | OPEN |
| T7 | Harness adapter survey (OpenCode, Vercel AI SDK) | M | — | OPEN |

---

### T0 — Repo init + env setup script (S)
**Objective:** make the workspace reproducible for all future agents.
**Steps:**
1. `git init` in `/home/theb/Documents/ctxvm/`; create `.gitignore` covering `reports/`? NO —
   reports are committed; ignore instead: `.open-data-products/`, `*.log`, `.DS_Store`,
   `node_modules/`, `target/`.
2. Write `tools/setup-env.sh` (bash, idempotent, `set -euo pipefail`) doing exactly this:
   - venv A `venvs/odps/`: any python ≥3.10 available; `pip install open-data-products`
   - venv B `venvs/odcs/`: a python ≤3.12 (system may have only 3.13/3.14 → check for
     conda: `conda create -y -n ctxvm-odcs python=3.12` then `python -m venv venvs/odcs` from
     that env; if conda is missing, emit a 5-line instruction to a human and exit 0)
   - print final paths of both `bin/open-data-products` binaries
   - if datacontract tooling missing in venv B, exit non-zero with a clear message
3. Run it; commit all files (excluding ignored) with message `T0: repo init + env setup`.
**DoD:** `tools/setup-env.sh` runs green twice in a row (idempotent); vitals committed;
`contracts/corpus-0.1.odcs.yaml` lints green via venv B; report per §4.

### T1a — Rust workspace scaffold (S)
**Objective:** cargo workspace skeleton matching the architecture in `01-PLAN.md` §3-arch.
**Steps:** create `rust/` as a cargo workspace with crates `ctxvm-core`, `ctxvm-codec`,
`ctxvm-tokenizer`, `ctxvm-conformance` (the last two: stub modules + TODOs). Prefer
`serde`/`serde_json` in core-modules participating in codec; no other deps yet (tokenizer
features deferred). `cargo build && cargo test` green for empty tests. Note the workspace
in `reports/` and commit as `T1a: workspace scaffold`.
**DoD:** `cargo --version` output quoted; `cargo test` passes; crate layout maps 1:1 to
§3-arch of the plan; report + commit.

### T1b — Event model + JSONL codec (M)
**Objective:** typed xCABI v0 events as Rust structs + JSONL codec with roundtrip golden vectors.
**Steps:** read `02-xcabi-events-v0.md` (event table + invariants are the spec). In
`ctxvm-codec`: `Page`, `Session`, 9 event types (`session.open`, `page.declare`,
`page.render`, `page.evict`, `page.fault`, `page.pin`, `page.unpin`, `turn.render`,
`call.meta`) with quoted tags (turn #, sources) per the table; JSONL reader/writer
(strings line-delimited); a **corpus-independent golden vector file** (~6 events covering
every type) under `ctxvm-conformance/vectors/`. Roundtrip: bytes → model → bytes MUST
reproduce identical bytes (property test).
**DoD:** unit tests: every event type deserializes from vector + re-serializes byte-identical;
`cargo test` green; vectors are committed artifacts; report notes any spec ambiguity found
(this feeds T4).

### T1c — Page table + deterministic renderer (L)
**Objective:** the heart of M0: from events → deterministic per-turn render, in Rust.
**Steps:** implement the engine described in `01-PLAN.md` §Decisions and `02` invariants:
stateful page table keyed by `(logical_ref, content_hash)`; apply events to build renderer
state: what's resident/stub'd at each turn; render turn messages (full content vs stub string
template from `02`'s stub format — the stub template is the ONLY prose in the spec; do not
invent new stub text); strict rule: **renders must be pure functions of (events, indices)**;
turn.render token accounting; module-level unit tests with ≥3 hand-summed scenario fixtures.
**DoD:** `cargo test` green incl. determinism property test (two renders => equal); a README
section in `ctxvm-core` documenting semantics briefly (≤60 lines); report.

### T1d — Replay engine + conformance vectors crate (M)
**Objective:** wire replay: read JSONL events → re-apply renderer → compare against
expectation embedded in trace (final renderTotals) → `ctxvm replay` semantics as a lib API.
**Steps:** build `ctxvm-conformance` as the place where vectors + replay checks live;
CLI-binnable binary target `replay` (lib-first, thin main). Green path + one divergence
fixture reported as structured error. Cross-check with `07`: M0 gate "Replay determinism:
100% byte-identical".
**DoD:** replay API green on all vectors incl. divergence detection; documented limits in
report; commit per crate.

### T2 — Upstream issue drafts (S)
**Objective:** file-ready GitHub issue texts for ODPS ecosystem upstreams.
**Steps:** read `06-odps-integration.md` (upstream list + all validation-learned frictions).
Produce `upstream/issues-drafts.md` with one full markdown issue per item: ① `hours` missing
from ODPS SLA unit enum ② doc-vs-schema drift pack (license wrapper, DQ executable array,
DQ spec-string-for-Custom, `displaytitle` casing, `dataHolder.en` wrapper, `version` float
hazard) ③ JSONL/Parquet `dataAccess.format` additions ④ `datacontract-cli` python `<3.13`
marker silently skipping `[contracts]` (SDK 0.4.0) ⑤ ODCS v2→v3 era mismatch in ODPS doc
examples. Each: Title, Context (quote actual validator line), Proposed fix, Evidence
(reference 06 + commands).
**DoD:** 5 complete drafts, each ≤80 lines, evidence real; report; commit.

### T3 — Metric simulator reference impl (M)
**Objective:** make `07`'s metric formulas executable and testable NOW (Python, pre-Rust).
**Steps:** write `benchmarks/metrics/metrics.py`: pure functions over JSONL event streams
implementing net_token_reduction / fault_recall / touch_ratio / thrash_index exactly as
defined in `07` (with cache-miss normalization noted, not invented). 40+ line test file with
two synthetic sessions (one healthy, one thrashing). Wire: `python -m` runner printing JSON.
**DoD:** `python -m pytest benchmarks/metrics` green well; CLI prints correct stats on the
two fixtures; formulas exactly match `07`; report.

### T4 — xCABI RFC-0: spec md + JSON Schema (M)
**Objective:** turn `02` (draft) into `spec/rfc-0/`: an RFC-style markdown (scope, status:
Draft, event tables, invariants, stub format, fault taxonomy, determinism boundary) +
`x-cabi.schema-v0.json` (JSON Schema for JSONL events, strict additionalProperties:false at
event level, tolerant at x- ext level per ODPS extension philosophy).
**Steps:** derive tables from `02`; mark every `OPEN QUESTION` unresolved as RFC "Open"
sections; validate schema against the T1b golden vectors IF they exist yet (else
self-test with 3 inline examples).
**DoD:** schema compiles via `jsonschema` (venv A ok); every event type covered; examples
validate; cross-refs to 02 kept exact; report.

### T5 — Hub pipeline: ODPC catalog via odpc-build (S)
**Objective:** prove the `hub.ctxvm.dev`-as-ODPC-repo claim from `06`.
**Steps:** in a scratch dir, run their SDK's `odpc-build` (see `open-data-products odpc-build
--help`) with fragments generated from `04` (`resources` + explain output as needed); build a
catalog.yaml + static HTML; add wrapper script `tools/build-hub.sh` (idempotent, uses venv A
or B as required).
**DoD:** catalog.yaml + HTML built by script; artifacts committed under `hub/`; script runs
clean twice; report with actual stdout tail.

### T6 — MCP tool-shim design note (S)
**Objective:** specify the loader-side shim that turns MCP tool results into ad-page handles
(fundamental approach in `03`).
**Steps:** produce `design/mcp-shim.md`: call interception point, handle shape (the JSON
seen by model), fault-through-tool_recall matching (Pichay method: same tool+args ⇒ fault),
zero-config flag surface, risk: double-fetch elimination vs cost of gathering; pseudocode ≤40
lines; keep all in pure markdown (no code yet).
**DoD:** doc ≤180 lines; consistent with `02` fault taxonomy; report.

### T7 — Harness adapter survey (M)
**Objective:** concrete, function-level integration plans for the two M2 target harnesses.
**Steps:** inspect OpenCode's session/agent loop (find repo, read the message-loop and
tool-result ingestion paths) and the Vercel AI SDK's streaming/tool-call API; write
`design/adapters.md`: for EACH, the exact hook point (file/function), what `vm.page()`
wraps, what `vm.observe()` needs, test strategy, risk list.
**DoD:** doc has file/function-level anchors (with absolute repo URLs/commit hashes),
both adapters plausible ≤50 LoC glue; report.

---

## §6. If you finish the whole board

Do NOT invent new scope. Write a report `RR-BOARD-COMPLETE-<date>.md` summarizing state and
proposing the next three tasks for orchestrator approval. Then stop.
