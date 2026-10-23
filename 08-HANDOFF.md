# CtxVM — MASTER HANDOFF (agent-facing)

> **You are a fresh AI agent continuing the CtxVM project.** Everything you need is in
> `/home/theb/Documents/ctxvm/`. Read §0–§4 fully before doing anything. Then pick ONE task
> card from §5, execute it, and report per §4. Do not skip ahead, do not re-plan.

*Last updated: 2026-10-23 · Maintainer rule: whoever completes a task MUST update its card
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
**Next frontier:** Stage 2 COMPLETE — **T8 DONE** (`@ctxvm/node` v0 tracer), **T9 DONE**
(`@ctxvm/opencode` adapter spike), **T10 DONE** (corpus drop M1 in `corpus/m1/` + the repo
CI gate: `tools/run-ci.sh` mirrors `.github/workflows/ci.yml`; ALL GATES GREEN locally
2026-10-22, re-witnessed 2026-10-23; GitHub-public remote **live** at
`github.com/kapitaali/ctxvm-xCABI` — first Actions run GREEN 2026-10-23, 4/4 jobs
(RR-ACTIONS-GREEN-20261023)).
**umpire M0 DONE 2026-10-22** (orchestrator green-lit): separate repo `~/Documents/umpire/`,
first commit `d7896df` — decision-ledger v0 as an xCABI-0.1 profile; its validator PASSES
(125 checks, 10/10 negatives) with byte-identical roundtrip ×2, and ctxvm's own
validator/replay consume its ledgers verbatim (details: umpire `reports/RR-M0-20261022.md`).
**T12 DONE 2026-10-23 (M2 live capture):** OpenCode v2 promise-plugin adapter
(`packages/opencode/live/ctxvm.ts`, `export default { id, setup }`, env-gated) → two real
sessions in `corpus/m2/` (echo beats + 5×5 sustained re-fetch) on the free-tier
`opencode/deepseek-v4.1-flash-free` at USD 0; both schema-PASS and replay-divergence-free;
manifest → 0.2.0 (`x-cabi.latestDrop`) + hub re-linked (RR-T12-20261023).
Board complete (T0–T12). Remaining proposals need orchestrator input: umpire M2 calibration
corpus (T13) and umpire M3 hosted-vs-local decision (T14); the Vercel AI SDK adapter (T15)
is a future card, not yet formally proposed. Actions-green remains live
(`RR-ACTIONS-GREEN-20261023`).

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

**Integrity rule (added 2026-10-22, after a prior-art audit in `01-PLAN.md`):** any
external/prior-art claim written into a repo doc must carry its locator (URL / arXiv id /
repo path) at first mention. Unverified → mark `UNVERIFIED-<date>`, never cite as fact.
Web-verify before the white paper or any published prose repeats a claim.

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
| T2 | Upstream issue drafts (ODPS + CLI + templates) | S | — | **DONE** (RR-T2-20261022; upstream/issues-drafts.md — 5 drafts, validator lines live-reproduced) |
| T3 | Metric simulator reference impl (Python) | M | T1b | **DONE** (RR-T3-20261022; 18/18 green, CLI verified, fixtures schema-PASS 108/108) |
| T4 | xCABI RFC-0: spec md + JSON Schema | M | T1b | **DONE** (RR-T4-20261022; schema PASS 55/55 vs all fixtures) |
| T5 | ODPD hub pipeline: ODPC catalog via odpc-build | S | T0 | **DONE** (RR-T5-20261022; SDK-built catalog+HTML in hub/, clean twice, byte-identical) |
| T6 | MCP tool-shim design note | S | — | **DONE** (RR-T6-20261022, commit `a835af3`; design/mcp-shim.md 145/180 lines) |
| T7 | Harness adapter survey (OpenCode, Vercel AI SDK) | M | — | **DONE** (RR-T7-20261022; design/adapters.md, anchors @ e965774f / 36e4ce7c) |
| T8 | `@ctxvm/node` v0 TS tracer (stage 2) | M | T4,T6,T7 | **DONE** (RR-T8-20261022; packages/node — 12/12 unit tests, both fixtures schema-PASS + replay-divergence-free) |
| T9 | OpenCode adapter spike wiring `@ctxvm/node` (stage 2) | M | T8 | **DONE** (RR-T9-20261022; packages/opencode — 6/6 glue tests, trace schema-PASS (72 checks) + replay divergence-free; RR-T7's two open questions source-resolved) |
| T10 | Trace corpus M1 seed + CI gate (stage 2) | M | T4 | **DONE** (RR-T10-20261022; `corpus/m1/` — 5 provenance-labeled checksummed traces, manifest 0.1.1 SDK-validated + hub re-linked; `tools/run-ci.sh` + `ci.yml` ALL GATES GREEN locally — Actions-green awaits a remote) |
| T11 | Publish prep: Apache-2.0 LICENSE + Actions-green handover (orchestrator-directed 2026-10-23) | S | T10 | **DONE** (RR-T11-20261023; canonical LICENSE added; all gates re-witnessed green; `ci.yml` verified @`335d986`; **pushed 2026-10-23** to `github.com/kapitaali/ctxvm-xCABI` — first Actions run green after fixing a latent YAML bug (`@`-prefixed step names), run `39942443159` 4/4 jobs green — RR-ACTIONS-GREEN-20261023) |
| T12 | M2 live capture: OpenCode wiring + live corpus drop (orchestrator-approved 2026-10-23) | M | T9, T11 | **DONE** (RR-T12-20261023; v2 promise-plugin adapter `packages/opencode/live/` env-gated + 8 tests; live echo + sustained-pressure sessions on free-tier `opencode/deepseek-v4.1-flash-free` at USD 0, v2.1.2-vs-pinned-2.1.3 diff documented; `corpus/m2/` schema-PASS + replay-divergence-free; manifest 0.2.0 + hub re-linked) |

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

### T8 — `@ctxvm/node` v0 TS tracer — stage 2 (M)
**Objective:** TypeScript telemetry-first mirror tracer implementing the T6/T7 contract
surfaces, emitting RFC-0-valid JSONL. No paging/eviction logic (mirror only).
**Steps:** scaffold `packages/node/` (zero runtime deps; Node ≥22.6 type-stripping, sources
run directly); identity minting per T6 §2 (keys-sorted canonical-JSON args, `sha256:<8hex>`,
>120-char refs truncate + `#hash8`); tracer = page/recall/render/scan/pin/unpin/finish;
committed fixtures via `test/generate.ts`.
**DoD:** unit suite green (`npm test` in packages/node); two fixture traces PASS the repo
schema validator AND are replay-divergence-free (`cargo replay`, exit 0, both); report +
commit per §4.

### T9 — OpenCode adapter spike — stage 2 (M)
**Objective:** realize the T7 "Adapter A" mapping in an OpenCode plugin; resolve RR-T7's
two open questions by reading the pinned source; produce a validated session trace.
Mirror-only.
**Steps:** implement `packages/opencode/` handler-per-hook against the pinned payload
contracts (`anomalyco/opencode` @ `e965774f`); reconstruct one echo-session hook-payload
fixture (realistic shapes); generate the xCABI trace; resolve
`toolOutput.truncate` reach-through (`runner/step.ts` + `core/tool-output.ts`) and the
provider-executed gap (same file).
**DoD:** committed fixture set + validator-passing, replay-divergence-free trace + glue
tests + report. (Live dev-build echo session deferred: needs an orchestrator-approved
provider spend and a build at/past the pinned SHA.)

### T10 — Trace corpus M1 seed + CI gate — stage 2 (M)
**Objective:** first ODPS-packaged public corpus slice with honest provenance; re-link the
hub; stand up the repository CI gate — authored as a byte-equivalent local mirror too,
since the repo has no git remote.
**Steps:** materialize `corpus/m1/` (5 traces copied from committed fixtures/generators,
`provenance.json` + `checksums.sha256`); manifest → 0.1.1 + `x-cabi.firstDrop` (SDK
re-validated); `tools/build-hub.sh` regen + `hub/hub.sha256` baseline; `tools/run-ci.sh`
+ `.github/workflows/ci.yml` (pins: py 3.14, jsonschema 4.26.0, open-data-products==0.4.0,
node 26, rust stable); `build-hub.sh` gains venv-or-PATH SDK resolution for CI.
**DoD:** (a) corpus manifest re-validated by their SDK ✓ (b) hub re-linked, regen
byte-identity baselined ✓ (c) green gate witnessed by the local mirror ✓. Deferred:
Actions-green (needs a git remote) and the live thrashing capture (M2, shares T9's
approved-spend prerequisite).

### T11 — Publish prep: Apache-2.0 LICENSE + Actions-green handover (S) — orchestrator-directed 2026-10-23
**Objective:** make the repo pushable to a public GitHub remote without loose ends.
**Steps:** add `LICENSE` (canonical Apache-2.0 text, appendix copyright "2026 the ctxvm
authors"); re-witness `tools/run-ci.sh` ALL GATES GREEN; verify `.github/workflows/ci.yml`
is committed; prepare the create-repo + push handover block for the owner; keep board/LOG
current. Do not touch `research/` (in-progress external work, untracked by design).
**DoD:** gates green; LICENSE present; handover block in RR-T11; report per §4. Owner-only
residue (needs their credentials): repo creation + push + the first Actions run.

### T12 — M2 live capture: OpenCode wiring + live corpus drop (M) — orchestrator-approved 2026-10-23
**Objective:** replace the M1 "live lands with M2" placeholder with real harness captures.
**Steps:** wire the T9 mapping through the OpenCode v2 external plugin surface (no source
patch); capture one echo-beat session and one sustained-pressure session on the free tier;
package `corpus/m2/` (traces + metas + provenance + checksums); bump the manifest and re-link
the hub; extend both CI gates. Version honesty: the available binary was v2.1.2 while T9
pinned contracts at v2.1.3 (`e965774f`) — the observed payload diff is documented in
`corpus/m2/provenance.json`.
**DoD:** schema PASS + replay-divergence-free for both traces ✓; corpus checksummed and
provenance-labeled ✓; manifest SDK-validated + hub byte-identity ✓; all gates green ✓;
Actions green after push.

---

## §6. If you finish the whole board

Do NOT invent new scope. Write a report `RR-BOARD-COMPLETE-<date>.md` summarizing state and
proposing the next three tasks for orchestrator approval. Then stop.
