# ctxvm Use Case #2 — Agent Forensics / Root Cause Analysis

**Status:** Design concept — not yet implemented in code (read-only tracer first)
**Source:** White paper Phase 3 (§4.6 what you can do with a trace); Rust M0 replay engine (T1d); metric simulator (T3); fault taxonomy (§2 of `02-xcabi-events-v0.md`)

## 1. The Problem

An LLM agent makes a wrong decision: it writes buggy code, misses a requirement, or gives incorrect advice. The team needs to know why. Was the model missing critical information that had been evicted from the context window? Or did the model have everything it needed and simply reason poorly?

Today, answering this question is nearly impossible. After the fact, nobody knows exactly what was in the context window at turn N. Was the relevant file stubbed? Was the critical tool result evicted three turns earlier? Was the model prompted with stale or duplicated content? Without a deterministic record of what the model actually saw, root cause analysis becomes speculation.

The result: teams cannot distinguish between **context-management faults** (the pager dropped something the model needed) and **model reasoning faults** (the model had the content but used it wrong). These require completely different fixes — one is a pager configuration problem, the other is a prompt or model problem.

## 2. What ctxvm Provides

ctxvm's deterministic trace and replay engine make agent forensics possible:

- **Append-only JSONL trace.** Every page declaration, render, eviction, and fault is logged. The trace is the complete, authoritative record of what the model saw at every turn.
- **Byte-identical replay.** `ctxvm replay` re-renders any turn exactly. You can reconstruct turn N's message array precisely as the model received it.
- **Fault taxonomy.** xCABI classifies faults by source: `tool_recall` (model re-requested evicted content), `identifier_scan` (scan found an identifier for evicted content), `explicit_api` (harness requested it), `semantic_*` (v1 plugin only, marked non-deterministic).
- **Stub text.** Evicted pages leave inline placeholders showing what the model was told was removed, including recovery instructions.
- **call.meta.** Provider-reported or estimated cache hit/miss per turn, flagged as estimates — cost figures subtract estimated cache misses.

## 3. How Forensic Analysis Works

The analysis proceeds in three phases: reconstruct, measure, diagnose.

### Phase 1 — Reconstruct the Fault Turn

Identify the turn where the bad decision was made (e.g., turn 37, where the agent wrote incorrect code). Replay that turn byte-identically:

```bash
# Replay turn 37 exactly as the model saw it
ctxvm replay session.jsonl --turn 37 --output render-turn-37.jsonl

# Inspect the render
cat render-turn-37.jsonl
```

Output is the exact message array the model received: system prompt, tool definitions, chat history, tool results — resident pages as full content, evicted pages as stub text.

### Phase 2 — Measure Waste and Faults Leading Up to the Turn

Profile the session window around the fault to see the pattern:

```bash
# Waste and fault statistics for turns 30–37
ctxvm profile session.jsonl --window turns 30-37
```

Example output:
```
Pages: 312        Rendered tokens: 41.8k
Never-touched: 65.3% of rendered tokens (27.3k)
Worst page: tool:read_file(src/db/schema.sql) 12.1k tokens — 0 touches
Faults: 19 (all recovered via tool_recall) → eviction mistakes cost 0.4% net tokens
Worst page by faults: tool:read_file(src/auth/session.ts) — 4 faults, 0 touches
```

This tells you whether the model was starved of relevant content (high fault rate on specific pages) or drowning in irrelevant content (high never-touched percentage).

### Phase 3 — Diagnose the Fault

Cross-reference the fault turn with the fault taxonomy:

```bash
# List all faults in the session
ctxvm profile session.jsonl --event page.fault

# Filter to a specific source
ctxvm profile session.jsonl --event page.fault --source tool_recall
```

Example output:
```
Turn 12: page.fault source=tool_recall page=tool:read_file(src/auth/session.ts) — model re-requested evicted content
Turn 23: page.fault source=tool_recall page=tool:read_file(src/auth/session.ts) — model re-requested evicted content
Turn 31: page.fault source=identifier_scan page=file:config/production.yaml — identifier found in model output
Turn 36: page.evict page=tool:read_file(src/auth/session.ts) stub="[Paged out: read src/auth/session.ts (8.2k tok, 187 lines). ...]"
Turn 37: model output — incorrect code (no tool call made)
```

**Diagnosis:** If turn 36 evicted `src/auth/session.ts` just before turn 37's bad decision, and turn 37's output references authentication logic that was in that file, the fault is a **context-management fault**: the pager evicted something the model needed. The fix is a paging policy change (pin `src/auth/session.ts`, increase budget, or change eviction policy).

If `src/auth/session.ts` was resident at turn 37 and the model still got it wrong, the fault is a **model reasoning fault**: the pager is not at fault; the fix is prompt engineering, model selection, or few-shot examples.

### Phase 4 — Verify the Diagnosis (Counterfactual Test)

Because the renderer is deterministic, you can test counterfactuals:

```bash
# Re-render turn 37 with the suspect page forced resident
ctxvm replay session.jsonl --turn 37 --pin page:tool:read_file(src/auth/session.ts) --output render-turn-37-pinned.jsonl

# Diff against the original render
ctxvm diff render-turn-37.jsonl render-turn-37-pinned.jsonl
```

**What this proves:** If the pinned render shows the previously-evicted content present where the stub was, the model *could* have seen it — the fault was visibility, not absence. If the pinned render still produces the same wrong output, the model had the information and used it wrong — the fault is model reasoning, not context management.

**Honest limit:** A pinned render proves **visibility** (the content was in the window), not **correctness** (that the model would have used it correctly). To prove correctness, you would need to re-run the model on the pinned render — which is only deterministic under a pinned model + seed, and even then measures what the model *would* do, not what it *did* do.

## 4. What Makes This Possible

| xCABI feature | Forensic value |
|---------------|----------------|
| Append-only JSONL | Complete, tamper-evident record of every page decision |
| Deterministic renderer | Byte-identical re-render of any turn — no approximation |
| Fault taxonomy | Faults classified by source (`tool_recall`, `identifier_scan`, etc.) |
| Stub text | Visible record of what the model was told was removed |
| `call.meta` | Cache hit/miss estimates per turn for cost accounting |
| Turn = determinism unit | Any turn can be isolated and re-rendered independently |

## 5. What ctxvm Does Not Do

- **v0 observes only.** ctxvm records faults but does not prevent them. Paging control (eviction, pinning) ships in v1 behind an opt-in `policy` flag.
- **No automatic root cause attribution.** ctxvm provides the data (what was evicted, what was faulted, what was resident) but does not automatically classify faults as "context-management" vs "model reasoning." That analysis is manual or plugin-driven.
- **Semantic faults excluded.** `semantic_*` faults (embedding/LLM guesses about what the model wants) are v1 plugins, marked non-deterministic, and excluded from the core. ctxvm does not consult an LLM to decide what to page.
- **No correctness attribution.** A pinned render proves visibility, not correctness. Correctness requires re-running the model, which is only deterministic under pinned model+seed.

## 6. Verification

All claims are backed by committed repo artifacts:

```bash
# Rust M0 replay (T1d complete)
cd rust && cargo test --package ctxvm-conformance
# 28+ tests green, 0 warnings, replay determinism byte-identical

# Replay CLI exit code
ctxvm replay session.jsonl --turn 37
# exit 0 = byte-identical re-render

# Schema validation
python spec/rfc-0/validate_schema.py session.jsonl
# SCHEMA CONFORMANCE: PASS (108 checks qualify with two-fixture argv: healthy + thrashing fixtures)

# Metric simulator
python benchmarks/metrics/metrics.py benchmarks/metrics/fixtures/session-thrashing.jsonl
# 18/18 pytest green
```

## 7. Related Work in Repo

- `02-xcabi-events-v0.md` — xCABI event vocabulary and fault taxonomy (`tool_recall`, `identifier_scan`, `explicit_api`, `semantic_*`)
- `03-tracer-api-ts.md` — Tracer API (`vm.observe()` records faults via `identifier_scan`)
- `benchmarks/metrics/` — Metric simulator with four formulas (net_token_reduction, fault_recall, touch_ratio, thrash_index)
- `07-benchmarks-go-no-go.md` — Benchmark suites and M0 go/no-go gates
- `rust/crates/ctxvm-conformance/` — Golden vectors and replay conformance checks
- `reports/RR-M1-20261022.md` — M1 report with P4 (re-decide pricing) and P5 (validator) results
- `reports/RR-M1AB-20261022.md` — M1b A/B pin completeness with live divergent-hash demo

---

**Next step:** This use case is ready to implement once the tracer (T8) is built. The replay engine and conformance validator (M0) are already complete. The missing piece is the live tracer that produces traces from real agent sessions. Without recorded traces, there is nothing to forensically analyze.

---

## Implementation Plan: Agent Forensics via ctxvm

This section describes how to implement agent forensics (root cause analysis of agent decisions) as plugins for two harnesses: OpenCode and Hermes Agent. Both use the same xCABI trace format and replay engine, so forensic analysis is harness-agnostic.

### 1. Shared Forensic Surface

Both harness plugins implement the same forensic data collection:

| Forensic artifact | Source event | What it reveals |
|-------------------|--------------|-----------------|
| Full render at turn N | `turn.render` + `page.render` | Exact message array the model saw at turn N |
| Resident pages at turn N | `page.declare` up to turn N | What content was in context |
| Evicted pages at turn N | `page.evict` + stub text | What was removed and what the model was told |
| Faults before turn N | `page.fault` (source: `tool_recall`/`identifier_scan`/`explicit_api`) | What the model tried to recover |
| Cache estimates at turn N | `call.meta` | Estimated cache hit/miss per turn |

### 2. OpenCode Plugin

**Location:** OpenCode plugin system.

**Hook points:**
- `onTurnRender` → Capture `turn.render` event with resident/evicted token totals.
- `onPageEvict` → Capture `page.evict` with stub text and page identity.
- `onModelOutput` → Scan for identifiers; emit `page.fault` with source `identifier_scan` if an evicted page reference is found; emit `page.fault` with source `tool_recall` if the model re-calls a tool.
- `onSessionEnd` → Export full trace to JSONL.

**CLI commands:**
```
# Record a session for forensic analysis
opencode ctxvm trace --session forensic-session --budget 120000
# ... run agent normally ...

# Replay a specific turn to see what the model saw
opencode ctxvm replay --session forensic-session --turn 37 --output render-turn-37.jsonl

# Profile waste and faults around the fault turn
opencode ctxvm profile --session forensic-session --window turns 30-37
# Shows: touch ratio, never-touched pages, fault rate, worst pages

# List all faults in the session
opencode ctxvm profile --session forensic-session --event page.fault
```

**Plugin surface (~40 lines of glue):**
- Wrap message assembly: capture `turn.render` events with resident/evicted totals.
- Wrap eviction decisions: capture `page.evict` events with stub text.
- Wrap model output: scan for identifiers, emit `page.fault` events.
- Export trace to JSONL on session end.

### 3. Hermes Plugin

**Location:** Hermes plugin system (`~/.hermes/plugins/`) or managed connector.

**Hook points:**
- Hermes agent loop hooks: `onTurnRender`, `onPageEvict`, `onModelOutput`, `onSessionEnd`.
- Hermes session management: persist trace to `~/.hermes/sessions/<session-id>/trace.jsonl`.
- Hermes CLI: `hermes ctxvm replay`, `hermes ctxvm profile`.

**CLI commands (Hermes native):**
```
# Record a Hermes session for forensics
hermes ctxvm trace --session forensic-session --budget 120000
# ... run agent normally ...

# Replay a specific turn
hermes ctxvm replay --session forensic-session --turn 37 --output render-turn-37.jsonl

# Profile waste and faults
hermes ctxvm profile --session forensic-session --window turns 30-37
```

**Plugin surface (~40 lines of glue):**
- Same hook points as OpenCode but using Hermes's plugin API.
- Hermes's MCP tool-shim (T6 design note) provides verbatim mirror of tool results (v0) which makes fault detection more accurate: the model sees exactly what was declared, and faults are accurately attributed.
- Hermes's cron system can schedule periodic `ctxvm replay` checks on recorded traces to ensure determinism is maintained over time.

### 4. Forensic Analysis Workflow

**Step 1 — Identify the fault turn:**
Find the turn where the agent made the wrong decision (e.g., turn 37 where it wrote incorrect code or gave wrong advice).

**Step 2 — Reconstruct the render:**
```bash
ctxvm replay session.jsonl --turn 37 --output render-turn-37.jsonl
cat render-turn-37.jsonl
```
Examine: Was the critical file resident? Was it stubbed? Was the system prompt correct? Were tool results present?

**Step 3 — Check faults leading up to the turn:**
```bash
ctxvm profile session.jsonl --event page.fault --window turns 25-37
```
Look for: Did the model re-request an evicted page (`tool_recall`)? Did an identifier scan find an evicted page reference (`identifier_scan`)? Was a page evicted right before the fault turn?

**Step 4 — Counterfactual test:**
```bash
# Re-render turn 37 with the suspect page pinned resident
ctxvm replay session.jsonl --turn 37 --pin page:tool:read_file(src/auth/session.ts) --output render-turn-37-pinned.jsonl
ctxvm diff render-turn-37.jsonl render-turn-37-pinned.jsonl
```
If the pinned render shows the previously-evicted content where the stub was, the model *could* have seen it — visibility was the issue, not correctness. If the pinned render still produces the same wrong output, the fault is model reasoning.

### 5. Dependencies

- **Rust M0** (`ctxvm-core`, `ctxvm-conformance`): Replay engine and conformance validator. Already complete (28+ tests green).
- **T8** (`@ctxvm/node` v0 tracer): The tracer that produces traces. Required for live session recording.
- **T9** (OpenCode adapter spike): Provides the OpenCode plugin hook points and fixture traces for forensic testing.
- **Metric simulator** (`benchmarks/metrics/`): Provides `touch_ratio`, `fault_recall`, `thrash_index` for quantifying waste around fault turns.

### 6. Verification

```
# End-to-end forensic test
opencode ctxvm trace --session forensic-test --budget 120000
# ... run agent, induce a bad decision at turn 37 ...

# Replay the fault turn
ctxvm replay session.jsonl --turn 37
# exit 0, divergences: []

# Check faults
ctxvm profile session.jsonl --event page.fault --window turns 30-37
# Should show: page.evict at turn 36, page.fault at turn 37 (tool_recall or identifier_scan)

# Counterfactual: pin the suspect page
ctxvm replay session.jsonl --turn 37 --pin page:tool:read_file(src/auth/session.ts) --output pinned.jsonl
ctxvm diff render-turn-37.jsonl pinned.jsonl
# If diff shows the previously-evicted content restored, visibility was the issue
```

**Exit criteria:**
- `ctxvm replay` exit 0 (byte-identical re-render of fault turn)
- `ctxvm profile` shows fault events with correct sources (`tool_recall`, `identifier_scan`)
- Counterfactual render differs from original render (proving visibility was the issue, not reasoning)
- `validate_schema.py` passes on the trace (108 checks qualify with two-fixture argv: healthy + thrashing fixtures)
