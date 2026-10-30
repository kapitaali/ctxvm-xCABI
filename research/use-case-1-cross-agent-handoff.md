# ctxvm Use Case #1 — Cross-Agent Context Handoff (Session Resumption)

**Status:** Design concept — not yet implemented in code
**Scope note:** v0 observes only (no eviction/pin/page). The handoff described here is **within-harness**: resume a paused session on the same harness, with the trace providing deterministic replay of what the model saw at turn N. Cross-harness page-level state transfer is possible because page identity `(logical_ref, content_hash)` is harness-agnostic, but turn-level render bytes are per-harness — different harnesses assemble messages differently (system prompt placement, tool-definition formatting), so byte-identical re-render across harnesses is **not** claimed.
**Source:** White paper Phase 3 (§4.4 tracer-first adoption path); Rust M0 replay engine (T1d); ODPS corpus packaging (T5)

## 1. The Problem

LLM agent sessions grow unbounded. Every tool result, system prompt, and chat message stays in the context window for the lifetime of the session. When the context window fills, one of three things happens:

1. **Hard session break.** The agent is restarted with a summary, losing verbatim detail, tool outputs, and exact quotes.
2. **Sliding window truncation.** Oldest messages are silently dropped. Information mentioned once early in the session is permanently lost.
3. **Full-context resubmission.** The entire history is resent on every API call, paying prompt cost for tokens the model never reads.

None of these are satisfactory. The missing capability is **session handoff without loss**: the ability to pause an agent loop at turn N, capture exactly what the model saw, and resume — on the same harness — with byte-identical context state.

## 2. What ctxvm Provides

ctxvm's xCABI trace format and Rust replay engine make within-harness handoff possible:

- **Append-only JSONL trace.** Every page declaration, render, eviction, and fault is logged as one JSON object per line. The trace up to turn N is a complete, self-contained snapshot of everything the model has seen.
- **Deterministic renderer.** `ctxvm-core` renders turns as a pure function of (events, indices). Two renders of the same trace produce byte-identical output — **within the same harness**, because the renderer is part of the harness's message assembly.
- **Replay engine.** `ctxvm replay` re-applies the renderer to a trace and compares against expected render totals. Exit code 0 means byte-identical re-render.
- **Stubs.** Evicted pages leave inline placeholder text with identity and self-service recovery, so the model knows what was paged out and how to get it back.
- **ODPS packaging.** `ctxvm export --odps` packages a session as a versioned, checksummed data product with manifest and llms.txt.

## 3. How Within-Harness Handoff Works

The handoff happens at turn boundaries — the determinism unit in xCABI. A trace up to turn N is a complete snapshot of everything the model has seen through turn N.

### Step 1 — Capture the Trace

While the agent runs, the ctxvm tracer wraps its loop:

```ts
import { trace } from "@ctxvm/node"

const vm = trace({
  agent: "coding-agent",
  model: "openai/gpt-5",
  budgetTokens: 120_000,
})

// When tool results materialize, declare pages
const h = vm.page({ kind: "tool_result", ref: "tool:read_file(src/db/schema.sql)", tokens: n })

// Per turn: mirror what the model will see
vm.render(messages)

// After the turn: scan model output for identifiers → record faults
vm.observe(modelOutputText)
```

The tracer never mutates `messages`. It derives and logs only. At any turn, the trace up to that point is a complete snapshot.

### Step 2 — Export at Handoff

At the chosen handoff turn (e.g., turn 142), export the trace:

```bash
# Export a packaged snapshot at turn 142
ctxvm export --odps \
  --session session-a.jsonl \
  --turn 142 \
  --output handoff/turn-142/

# Produces:
# handoff/turn-142/
# ├── manifest.yaml              # ODPS 4.1 manifest with DQ checks
# ├── llms.txt                   # Agent discovery file
# ├── trace-142.jsonl.zst        # Checksummed JSONL trace, turns 1..142
# ├── page-table-142.json        # Deterministic page table state at turn 142
# └── checksums.sha256           # SHA-256 checksums for all artifacts
```

The manifest carries DQ checks (replay determinism, pin lint, redaction scan) and KPIs (fault recall, net token reduction, touch ratio). The page-table snapshot records exactly which pages are resident at turn 142 and which are stubbed.

### Step 3 — Resume on the Same Harness

Agent resumes from the snapshot:

```bash
# Start a new agent loop, seeded from the handoff snapshot
hermes ctxvm trace --session session-b.jsonl \
  --resume-from handoff/turn-142/ \
  --budgetTokens 120000
```

The resumed turn renders byte-identically to what the model saw at turn 142 **within the same harness**. Resident pages appear as full content; evicted pages appear as stubs with recovery instructions:

```
[Paged out: read src/auth/session.ts (8.2k tok, 187 lines).
 Re-call read_file(path="src/auth/session.ts") to re-materialize.]
```

The agent can call `vm.fault(handle)` to page back in any evicted content, recorded as a `page.fault` event with `source: explicit_api`.

### Step 4 — Verify Determinism

Before trusting the handoff, verify byte-identical replay:

```bash
# Verify the handoff trace replays identically
ctxvm replay handoff/turn-142/trace-142.jsonl --turn 142
# exit 0, divergences: []

# Cross-check against the original trace
ctxvm diff session-a.jsonl handoff/turn-142/trace-142.jsonl
# page-level divergence: only new events after turn 142; shared prefix matches
```

## 4. Scope Boundary: What This Is Not

**Cross-harness handoff (OpenCode → Hermes or vice versa) is not supported in v0.**

- Page identity (`page_id = (logical_ref, content_hash)`) is harness-agnostic, so page-level state *could* be transferred.
- Turn render is **not** byte-identical across harnesses: each harness assembles messages differently (system prompt placement, tool-definition ordering, image formatting). The xCABI renderer is pure within a harness's event stream; a different harness's renderer would produce different bytes.
- The stub format is harness-agnostic text, but how the harness renders stubs into its message array is harness-specific.

**Honest framing:** ctxvm gives you **page-level state transfer** (which pages were resident, which were stubbed, what the stubs said) and **within-harness turn-level byte-identical replay**. Cross-harness context handoff requires either a shared page-store convention (not yet specified) or accepting that the receiving harness re-assembles context from its own message format.

## 5. What ctxvm Does Not Do

- **v0 observes only.** ctxvm does not evict, pin, or page. The harness is responsible for eviction decisions; ctxvm records and replays them. Paging control ships in v1 behind an opt-in `policy` flag.
- **No cross-harness message mutation.** The tracer never changes `messages`. It mirrors and logs only.
- **Names are working names.** `ctxvm` and `xCABI` are not final; renaming is an explicit orchestrator task.

## 6. Verification

All claims are backed by committed repo artifacts:

```bash
# Rust M0 (T1d complete)
cargo test --package ctxvm-conformance
# 28+ tests green, 0 warnings, replay determinism byte-identical

# Replay CLI
ctxvm replay trace.jsonl --turn 142
# exit 0, divergences: []

# Schema validator
python spec/rfc-0/validate_schema.py trace.jsonl
# SCHEMA CONFORMANCE: PASS (108 checks qualify with two-fixture argv: healthy + thrashing fixtures)

# ODPS manifest validation (SDK 4.1)
venvs/odps/bin/open-data-products validate handoff.yaml --json
# {valid: true, spec: odps 4.1, errors: [], warnings: [], hints: [], path: ..., version: ...}
# Note: compliance_level and production_ready are not emitted by the SDK 4.1 CLI.
```

## 7. Related Work in Repo

- `03-tracer-api-ts.md` — TypeScript tracer API sketch (the `trace()` / `vm.page()` / `vm.render()` / `vm.observe()` surface)
- `02-xcabi-events-v0.md` — xCABI event vocabulary draft (session.open, page.declare, page.render, page.evict, page.fault, page.pin/unpin, turn.render, call.meta)
- `08-HANDOFF.md` §5 — Task board; T8 (`@ctxvm/node` tracer) is the next frontier
- `reports/RR-BOARD-COMPLETE-20261022.md` — Board completion summary with T8/T9/T10 proposals
- `spec/rfc-0/` — xCABI RFC-0 normative spec + strict JSON Schema + validator
- `rust/crates/ctxvm-conformance/` — Golden vectors and replay conformance checks

---

**Next step:** This use case maps directly to T8 (`@ctxvm/node` v0 tracer) from `08-HANDOFF.md` §6. The tracer implementation is the missing piece that makes within-harness handoff operational. Cross-harness handoff remains parked until a v1 pager and shared page-store convention exist.

---

## Implementation Plan: Cross-Agent Context Handoff (Within-Harness)

This section describes how to implement within-harness context handoff as plugins for OpenCode and Hermes Agent. Both plugins emit the same xCABI event vocabulary, so traces from both harnesses can be replayed by the same `ctxvm replay` engine.

### 1. Shared Integration Surface

Both harness plugins implement the same xCABI event vocabulary:

| Event | Trigger point | Payload |
|-------|---------------|---------|
| `session.open` | Agent loop start | agent id, model, provider, budget, tokenizer id |
| `page.declare` | Tool result materializes | page descriptor, kind, tokens |
| `page.render` | Per turn, before model call | turn #, mode (full/stub), resident/evicted token totals |
| `page.evict` | Before turn render, when evicting | turn #, stub text used |
| `page.fault` | After model output, on re-request | turn #, source (tool_recall/identifier_scan/explicit_api), latency |
| `turn.render` | After render complete | turn #, resident/evicted token totals, headroom |
| `call.meta` | Per turn | provider, est. cache hit/miss, latency |

The stub format (eviction placeholder) is normative from `02-xcabi-events-v0.md` §Stub format:

```
[Paged out: read src/auth/session.ts (8.2k tok, 187 lines).
 Re-call read_file(path="src/auth/session.ts") to re-materialize.]
```

### 2. OpenCode Plugin

**Location:** OpenCode plugin system, loaded as a dev plugin or extension.

**Hook points:**
- `onToolResult` → `page.declare`: When a tool result returns, declare the page with `logicalRef = tool:<name>(<args>)`, `contentHash = sha256(result)`, kind = `tool_result`, tokens = token count.
- `onTurnStart` → `turn.render`: Before assembling messages for the model, emit `turn.render` with current resident/evicted token totals.
- `onTurnEnd` → `page.fault`: After model output, scan for identifiers; if an identifier references an evicted page, emit `page.fault` with source `identifier_scan`; if the model re-calls a tool with same args, emit `page.fault` with source `tool_recall`.
- `onSessionStart` → `session.open`: Namespace the trace with agent id, model, provider, budget, tokenizer id.

**CLI commands:**
```
# Start tracing an OpenCode session
opencode ctxvm trace --session my-session --budget 120000

# Export a handoff snapshot at turn N
opencode ctxvm export --session my-session --turn 142 --output handoff/turn-142/

# Resume from a handoff snapshot (same harness)
opencode ctxvm trace --session my-session-b --resume-from handoff/turn-142/
```

**Plugin surface (~50 lines of glue):**
- Wrap `client.callTool(...)` → `vm.call(...)` auto-shim (from `03-tracer-api-ts.md` §Auto-shim): auto-declare pages, `tool_recall` faults by name+args matching.
- Wrap message assembly: intercept before model call, inject stubs for evicted pages, emit `turn.render`.
- Wrap model output scan: `vm.observe(modelOutputText)` after each turn.

### 3. Hermes Plugin

**Location:** Hermes plugin system (`~/.hermes/plugins/`) or managed connector (`manage_connections install`).

**Hook points:**
- Hermes agent loop hooks: `onToolResult`, `onTurnStart`, `onTurnEnd`, `onSessionStart`.
- Hermes session management: persist trace to `~/.hermes/sessions/<session-id>/trace.jsonl`.
- Hermes cron: schedule periodic trace snapshots for CI validation.

**CLI commands (Hermes native):**
```
# Start tracing a Hermes session
hermes ctxvm trace --session my-session --budget 120000

# Export a handoff snapshot at turn N
hermes ctxvm export --session my-session --turn 142 --output handoff/turn-142/

# Resume from a handoff snapshot (same harness)
hermes ctxvm trace --session my-session-b --resume-from handoff/turn-142/
```

**Plugin surface (~50 lines of glue):**
- Same as OpenCode but using Hermes's plugin API for message loop interception.
- Hermes's built-in MCP tool-shim (T6 design note, `design/mcp-shim.md`) can be used for call interception: callTool decorator that verbatim mirrors tool results (v0) or emits RFC-0 §7 stubs (v1).
- Hermes's cron system can schedule periodic `ctxvm replay` checks on the trace to ensure determinism is maintained.

### 4. Cross-Harness Portability (Scope Note)

Because both plugins emit the same xCABI event vocabulary and use the same stub format, a trace recorded by OpenCode can be *read* by Hermes's replay engine — but the harness-specific render is not byte-identical across harnesses. Page identity (`logical_ref`, `content_hash`) transfers; turn-level render bytes do not.

Cross-harness handoff requires either:
1. A shared page-store convention (not yet specified), or
2. Accepting that the receiving harness re-assembles context from its own message format, using the xCABI trace as a fidelity reference rather than a byte-for-byte reconstruction.

### 5. Dependencies

- **T8** (`@ctxvm/node` v0 tracer): The TypeScript binding that implements `trace()`, `vm.page()`, `vm.render()`, `vm.observe()`. Required for both OpenCode and Hermes plugins.
- **T9** (OpenCode adapter spike): The OpenCode plugin hook points and fixture traces. Reference implementation for OpenCode integration.
- **T10** (corpus drop M1 + CI): GitHub Actions gate: `cargo test` + schema validator + hub byte-identity check. Provides CI validation for traces.
- **Rust M0** (`ctxvm-core`, `ctxvm-conformance`): The replay engine and conformance validator. Already complete (28+ tests green; validator PASS qualifies with two-fixture argv).

### 6. Verification

```
# End-to-end within-harness handoff test
opencode ctxvm trace --session handoff-test --budget 120000
# ... run agent for 142 turns ...
opencode ctxvm export --session handoff-test --turn 142 --output /tmp/handoff/
opencode ctxvm trace --session handoff-test-b --resume-from /tmp/handoff/
ctxvm replay /tmp/handoff/trace-142.jsonl --turn 142
# exit 0, divergences: []
ctxvm diff session-a.jsonl /tmp/handoff/trace-142.jsonl
# page-level divergence: only new events after turn 142
```

**Exit criteria:**
- `ctxvm replay` exit 0 (byte-identical re-render at handoff turn, same harness)
- `ctxvm diff` shows only new events after the handoff turn (no divergence in shared prefix)
- `validate_schema.py` passes on the exported trace (108 checks qualify with two-fixture argv: healthy + thrashing fixtures)

**Out of scope for v0:** Cross-harness byte-identical resume. That requires a pager (v1) and a shared page-store convention (not yet specified).