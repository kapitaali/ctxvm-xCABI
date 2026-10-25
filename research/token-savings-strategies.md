# How to Turn ctxvm and/or umpire into Something That Actually Saves Tokens

**Status:** Research synthesis — grounded in web-verified primary sources (2025-2026)
**Date:** 2026-10-25
**Scope:** ctxvm (context virtual memory) and umpire (pinned decision primitive)
**Question:** What must change for these systems to produce measurable token savings?

---

## 1. The Problem in One Sentence

ctxvm observes context usage but never acts on it; umpire records decisions but never reuses them. Both are **telemetry-first** — they measure waste but do not prevent it.

---

## 2. The Core Insight: Inverted Economics

The single most important finding from demand-paging research on LLM context (Pichay, 2026):

> In hardware VM, keeping a page resident costs nothing until touched. In an LLM, every resident token is recomputed through attention on **every turn** — whether or not it is referenced. Keeping is expensive; faulting is cheap.

A 5,000-token file sitting in context for 20 turns costs 100,000 input tokens of processing. Re-reading that file once when actually needed costs 5,000 tokens. The eviction saves 95,000 tokens.

**Break-even rule:** Evict whenever a page will not be referenced for more than one turn. Fault it back if you were wrong.

This is why FIFO — the worst policy in classical VM — works best for agents. When keeping is expensive and faulting is cheap, aggressive eviction is correct by default.

### Empirical results (Pichay)

| Metric | Value |
|--------|-------|
| Context reduction | 93% (5,038KB → 339KB) in a 681-turn session |
| Fault rate | 0.0254% across 1.4M simulated evictions |
| Structural waste in production | 21.8% of tokens (84.4× amplification for stale results) |
| Completion rate improvement | 71.0% → 91.6% |
| Token reduction | ~63% |

Source: Pichay, "The Missing Memory Hierarchy: Demand Paging for LLM Context" (arXiv 2603.09023v1, 2026).

---

## 3. Why ctxvm Doesn't Save Tokens Yet

### 3.1 The telemetry-first wedge

ctxvm's design (RFC-0, UC1) is explicitly observe-only:
- Tracer wraps the agent loop and logs `page.declare`, `page.render`, `page.fault`, `turn.render`
- The tracer **never mutates** `messages`
- Paging control ships in v1 behind an opt-in `policy` flag

This is the right starting point — you cannot evict what you cannot measure. But it means **zero token savings today**.

### 3.2 The inverted NTR finding

ctxvm's own policy simulator and KPI formulas reveal a critical problem: under famine (small budget), NTR (net token reduction) is **reward-inverted**. Evicting pages and then needing them again (double-fetch) costs more tokens than keeping them.

The mechanism:
1. Evict page P → save `tokens(P)` this turn
2. Model references P → fault → re-read → re-declare → re-render
3. Re-materialization cost > eviction savings

This is exactly the "thrashing" failure mode Pichay describes: a 681-turn session hit a 97% fault rate when eviction was too aggressive.

### 3.3 What's missing

| Capability | Status | What's needed |
|------------|--------|---------------|
| `page.evict` events | Schema exists (RFC-0 §events), never emitted | Renderer change: stub replacement |
| Stub replacement | Template exists in RFC-0, never used | Wire into render path |
| Fault-driven pinning | Simulator compares strategies, not wired | Default policy = fault-pin |
| Budget trigger | Accounting exists, no trigger | Degrade ladder |
| Stable prefix for caching | Not addressed | Reorder + `cacheAlignment` |

---

## 4. Five Strategies That Actually Work

### Strategy 1: Turn on the control beat (ctxvm)

**The smallest change with the largest impact.** ctxvm already has:
- Page table (resident/stub state tracking)
- Fault tracking (tool_recall, identifier_scan, explicit_api)
- Policy simulator (LRU, fault-pin, size-based)
- KPI formulas (net_token_reduction, fault_recall, touch_ratio, thrash_index)
- Stub template in RFC-0

**What's missing:** `page.evict` events, stub replacement in renderer, fault-driven re-materialization.

**Recommended first policy:** Fault-pin (ctxvm's own simulator winner on live-thrash: 100% recall vs 50% for LRU). Pin by reference, not recency — a file read during planning matters for the rest of the session.

**Key design constraint from Pichay:** Leave a stub anchor when evicting. `[Paged out: Read file.py (8,192 bytes). Re-read if needed.]` costs ~20 tokens but prevents the model from hallucinating that the content never existed. Without the stub, the model re-requests the full content every time it suspects the page might be relevant.

**Expected savings:** 20-60% token reduction (Pichay: 93%, TRC: 29%)

Source: Pichay (arXiv 2603.09023v1); ctxvm policy simulator results (UC3 capacity planning research).

### Strategy 2: Stable prefix for prompt caching (ctxvm)

**Zero quality loss, provider-side savings.** Prompt caching (Anthropic, OpenAI, Google) provides 41-80% cost reduction and 13-31% TTFT improvement by reusing KV cache for identical prefixes.

ctxvm's page table produces deterministic renders — same page content always renders the same way. If ctxvm reorders context so stable (pinned) pages come first (cacheable prefix) and volatile (recent, evictable) pages come last, prompt caching kicks in automatically.

**ctxvm action:** Add a `cacheAlignment` field to the sidecar — the byte offset where the stable prefix ends. The renderer already knows which pages are pinned vs. volatile.

**Expected savings:** 41-80% cost reduction (provider-side, no quality loss)

Sources: "Cache Engineering for Agents" (arXiv 2610.28577v1); "Agent Cost" (neelmishra.github.io, 2026).

### Strategy 3: Tool-result clearing (TRC)

**Highest-ROI compression from systematic study.** A study of 35,000 agent runs on SWE-bench Verified and Terminal-Bench 1.0 found:

| Method | Billed cost | Latency | Resolve rate |
|--------|-------------|---------|-------------|
| Full context | 1.0× | 1.0× | baseline |
| Tool-result clearing (TRC) | 0.71× | 0.79× | highest (53.7%) |
| Compaction (summarization) | 0.85× | 0.90-1.8× | varies by model |
| TRC + summarization | 0.71× | 0.90× | 57.0% (Devstral) |

TRC replaces older tool outputs with `[output cleared]` while retaining surrounding agent interactions and recent tool results. It is cheap (no LLM call), semantically aware (only clears outputs the model has already processed), and achieves the best cost-latency-quality tradeoff.

ctxvm already tracks page age and fault history — perfect inputs for TRC decisions. The eviction threshold from Pichay ("evict if not referenced for >1 turn") translates directly to "clear tool results older than 1 turn."

**Expected savings:** 0.71× billed cost, 0.79× latency

Source: "A Systematic Study of Context Compression in LLM Agents" (arXiv 2609.32961v1, 2026).

### Strategy 4: Semantic deduplication (ctxvm already detects this)

ctxvm already flags `faultOfResidentPage` violations when the same tool call returns identical content. This is a double-fetch — the model re-requested something it already has. ctxvm could prevent this by returning a stub: "already read at turn N, unchanged."

**Estimated savings:** Pichay found 21.8% structural waste in production sessions. ctxvm's own corpus shows tool_recall faults on every live capture (m2: 3 faults, m4: 1 fault, m5: 17 faults).

### Strategy 5: Budget enforcement with a degrade ladder

ctxvm has `budgetTokens` and `turn.render` token accounting. The gap: no trigger when the budget is exceeded.

**Degrade ladder (from context engineering research):**
1. **Evict** obviously-dead items (TRC, age-based)
2. **Truncate** over-long single results
3. **Compact** (summarize) the conversation periodically
4. **Hard-truncate** as backstop

The UC3 policy simulator already models the three-regime law (starvation wall → pressure band → plateau) which maps directly to these four levels.

**Expected savings:** Prevents runaway sessions (no upper bound on token usage today)

---

## 5. Where umpire Fits

umpire is a decision primitive (typed decisions via a pinned local model). It saves tokens through four mechanisms:

### 5.1 Decision caching

Repeated similar decisions can reuse prior calibrated decisions. umpire's append-only ledger is already designed for this — a decision cache layer on top would skip LLM calls for high-confidence repeats.

### 5.2 Confidence-based routing

umpire's calibration corpus provides confidence scores. High-confidence decisions → use a smaller/cheaper model or skip the model entirely. Research: "Use a large model for planning only, then hand off execution to a small model." umpire's pinned local model is already the "small model" — the question is when to escalate.

### 5.3 Decision reuse across sessions

umpire's ledger persists across sessions. Similar decisions in future sessions can reuse prior decisions. The `resumeFrom` provenance mechanism (UC1-B3) already supports session continuity.

### 5.4 Token accounting per decision

umpire can track token usage per decision type, identifying which decisions are expensive. The `call.meta` event already carries estimated cache cost.

**Expected savings:** 30-50% decision-call reduction (estimated from calibration corpus size)

---

## 6. The Recommended Roadmap

| Phase | System | What | Expected savings | Effort |
|-------|--------|------|-----------------|--------|
| 1 | ctxvm | Enable eviction: `page.evict` + stub replacement + fault-pin default | 20-60% tokens | Schema + renderer + policy wiring |
| 2 | ctxvm | Prompt-cache alignment: stable prefix first, `cacheAlignment` in sidecar | 41-80% cost | Renderer reorder |
| 3 | ctxvm | Tool-result clearing (TRC) with age threshold | 0.71× billed cost | Policy config |
| 4 | umpire | Decision caching: skip LLM for high-confidence repeats | 30-50% calls | Cache layer on ledger |
| 5 | ctxvm | Budget enforcement: degrade ladder (evict → compact → truncate → hard-truncate) | Prevents runaway | Budget trigger |

### Phase 1 is the critical path

Everything else depends on Phase 1. Without actual eviction, there is no token savings — only measurement of waste. Phase 1 is the thinnest possible change:
- Add `page.evict` to the schema (RFC-0 revision — the event already exists in the vocabulary)
- Implement stub replacement in the renderer (the stub template already exists in RFC-0)
- Wire fault-pin policy as default (the simulator already compares strategies)

### The key risk

The SWE-bench systematic study (35,000 runs) found: **saving tokens does not reliably reduce latency or cost.** The same compression policy helps on some tasks and hurts on others. Token savings and quality are not monotonically linked.

ctxvm's own finding (NTR reward-inverted under famine) is an instance of this. The path forward is not "evict more" but "evict smarter" — fault-driven pinning, stub anchors, and measuring the fault rate as the key health metric (Pichay's 0.0254% fault rate is the target).

---

## 7. What's Already Built (No Work Needed)

ctxvm already has: page table, fault tracking (tool_recall, identifier_scan, explicit_api), policy simulator (LRU/fault-pin/size-based), KPI formulas (net_token_reduction, fault_recall, touch_ratio, thrash_index), budget accounting, stub template in RFC-0, export manifest with DQ/KPIs, and the corpus to measure against.

umpire already has: append-only decision ledger, pinned local model, calibration corpus, resume-from-snapshot provenance, and the validator.

The gap is purely the **control beat** — turning observation into action.

---

## 8. Source Index

| Source | Type | Key claim |
|--------|------|-----------|
| Pichay, "Demand Paging for LLM Context" (arXiv 2603.09023v1, 2026) | Primary paper | 93% context reduction, 0.0254% fault rate, inverted economics |
| "A Systematic Study of Context Compression in LLM Agents" (arXiv 2609.32961v1, 2026) | Primary paper | TRC: 0.71× cost, 0.79× latency, highest resolve rate; 35,000 agent runs |
| "Cache Engineering for Agents" (arXiv 2610.28577v1, 2026) | Primary paper | Tool-response rolling-drop: 27.7% cost reduction, 1.7pt score improvement |
| "SWE-Pruner" (arXiv 2601.16746, 2026) | Primary paper | 23-54% token reduction on agent tasks |
| "Context Compaction" (morphllm.com, 2026) | Technical guide | FlashCompact: 3-4× fewer tokens per session; 72.8% median compaction removal |
| "Agent Cost" (neelmishra.github.io, 2026) | Blog | Prompt caching: 41-80% cost reduction; 75-85% total from full optimization stack |
| "LLM Cost Optimization for Agents" (viralruparel.com, 2026) | Guide | Anchored summarization, per-tenant budget ledger, reserve-then-settle |
| ctxvm UC3 capacity planning research | Repo artifact | Three-regime law, policy simulator, KPI formulas |
| ctxvm RFC-0 (spec/rfc-0/) | Repo spec | Event vocabulary, stub template, schema, validator |

---

## 9. The One-Line Answer

ctxvm saves tokens when it stops being a flight recorder and starts being a **pager**: evict by default (fault-driven pinning), stub the eviction (20 tokens, not silence), and let prompt caching handle the rest. The telemetry foundation is already there — the control beat is the next card.
