# CtxVM Consolidated Plan

*Working names: library `ctxvm`; standard **xCABI** ("eXchangeable Context ABI").*

## 1. Thesis

The LLM context window is not memory — it is L1 cache. In 2026 the field reached the same
independent conclusion (demand paging for context) and sprinted on it: **Pichay** (SOSP-style
preprint, system "Pichay", T. Mason · arXiv 2603.09023), **IBM's agent session manager**
(`IBM/chuk-ai-session-manager` — session/context management with summarization, not
demand paging), **`l1-pager`** (indie LangGraph context GC, sarath-m-s — LRU/IMPORTANCE/
HYBRID eviction + a sentinel `fetch_evicted_page` tool; small traction: ~5★, ~200
weekly downloads), the **virtual-context line** (MemGPT/Letta, arXiv 2310.08560), and a
formalization of the learned-policing problem ("**Neural Paging**", arXiv 2603.02228,
"Semantic Belady's Optimality").

But everyone is building house-of-cards: **private page formats, private fault protocols,
private logs, private policies.** Like the pre-MCP tool era or the pre-SQL data era.
The mechanism is proven; the layer that turns it into an ecosystem does not exist.

**The leap:** not another pager — the *gauge, the dyno, and the SQL* for the context layer.

> **Prior-art verification note (2026-10-22, repo-agent):** all five pointers above were
> web-verified with locators after an audit found the paragraph had been written without
> captured sources. Anchors: Pichay = system name in arXiv 2603.09023 ("…It is L1 cache…",
> 857-session measurement, 21.8% structural waste, §3.5 fault-driven pinning incl.
> unpin-on-content-change — all quoted faithfully downstream in this repo);
> `github.com/IBM/chuk-ai-session-manager` (IBM org OSS); `pypi.org/project/l1-pager` +
> `github.com/sarath-m-s/l1-pager`; arXiv 2310.08560 (MemGPT coined "virtual context
> management"); arXiv 2603.02228 (CPP + Semantic Belady). Repo rule (08-HANDOFF §4):
> prior-art claims must carry locators at first mention — no unsourced prose.
>
> **Independent re-check (2026-10-29, adoption-intake):** all three arXiv pointers
> re-verified fresh from the papers (abs pages ×3 + 2603.09023 full text v1):
> Pichay system name ✓, "It is L1 cache" ✓, 857 sessions ✓, 21.8% ✓, 84.4× median
> amplification (§1 + §5.1, full-text only) ✓, §3.5 fault-driven pinning incl.
> unpin-on-content-change (step 4) ✓, 2603.02228 CPP + Semantic Belady ✓,
> 2310.08560 "virtual context management" ✓ — ALL CONFIRMED. Paper-internal note:
> the 2603.09023 abs landing page says "4.45 million" tokens where the full text
> says "4.45 billion" (self-consistent at billion; this repo never quotes the 4.45
> figure). See reports/RR-ADOPTIONINTAKE-20261029.md §1.

## 2. The three pillars (and what's missing in each)

1. **xCABI — a portable, deterministic page/fault/trace standard.**
   Missing everywhere: every implementation owns a bespoke mutation log; none is
   cross-harness replayable, diffable, or conformance-testable. ("What MCP did for tools,
   SQLite for storage — xCABI does for agent memory.")
2. **Lazy handles at the tool boundary (mmap ABI).**
   All found systems intercept waste *after* tools return bytes. No one returns typed page
   handles instead of payloads. Fixes the measured 84.4× re-mention amplification *before*
   it enters the stream. (Pichay's data: stale tool results reprocessed at a median
   amplification of 84.4× — arXiv 2603.09023.)
3. **The measure — trace corpus + simulator + conformance + policy leaderboard.**
   Neural Paging (arXiv 2603.02228) proposes learned page controllers; no public corpus,
   replay simulator, or benchmark exists to train/eval them. We make the policy space
   researchable.

## 3. Strategy: telemetry-first, control-later

The crowded field is all control-plane pagers fighting for defaults. We escape via the
OpenTelemetry playbook: **v0 is a read-only flight recorder.** Wrap any agent loop; nothing
changes; you get the trace, touch stats, waste measurement ("your agent pays for 65% of
context it never reads"). This:

- generates the corpus organically (every install contributes traces),
- wins the format *before* anyone must trust us with their context,
- makes adoption a config step, not a rewrite.

Paging control ships in v1 behind an opt-in `policy` flag.

## 4. Locked decisions

- **Rust core + TS/Py bindings.** Crates: `ctxvm-core` (page table, budget, policy traits,
  replay engine), `ctxvm-codec` (xCABI serde), `ctxvm-tokenizer` (tiktoken/HF behind
  features), `ctxvm-conformance` (golden vectors = executable truth; every binding must pass).
  FFI: napi-rs (npm prebuilds, SWC/Biome-proven), PyO3/maturin (wheels).
  Adapters (OpenCode, Vercel AI SDK, LangGraph, MCP shim) live *above* bindings as thin TS/Py.
- **Determinism boundary.** Core = pure replayable engine. Semantic/embedding faulting,
  LLM-based compression: policy plugins, logged as marked non-deterministic event classes.
- **Zero prompt pollution in v0.** Stubs carry identity + recovery instructions inline
  ("[Paged out: read src/auth.ts, 8.2k tok — re-call to re-materialize]"); Pichay shows
  models understand this untaught. Escalate to hints only if fault recall suffers.
- **Cache-cost honesty.** Evictions batch at turn boundaries; `call.meta` records estimated
  cache misses so benchmarks report *net* cost — which no competitor's eval does.
- **ODPS integration stays at the edge.** CLI/binding-layer concern (YAML emission);
  Rust core never knows what a manifest is.

## 5. API sketches

Tracer (v0), TypeScript:

```ts
import { trace } from "@ctxvm/node"

const vm = trace({ agent: "my-agent", model: "claude-...", budgetTokens: 120_000 })

const h = vm.page({ kind: "tool_result", ref: awaitArgsHash, tokens: tok(result) })
vm.render(messages)          // emits turn.render as a mirror of what the model sees
vm.observe(modelOutputText)  // scans for identifiers → records faults (source: identifier_scan)
```

Pager (v1): `mmap(path, { advise: "sequential" })`, `pin(h, reason)`, policies
(`FaultPinPolicy` per Pichay: one fault pins for the session; unpin on content change).

CLI: `ctxvm trace`, `ctxvm profile`, `ctxvm replay`, `ctxvm diff a.jsonl b.jsonl`,
`ctxvm export --odps`.

## 6. Milestones

| M | Weeks | Gate |
|---|---|---|
| M0 spike | 2 | Pure Rust: page table + event log + deterministic renderer + golden vectors. No FFI. |
| M1 alpha | 3–4 | napi-rs binding + tracer API + identifier-scanning faults + `ctxvm profile`. Demo: waste numbers on a real agent. |
| M2 beta | 3–4 | Two harness adapters (OpenCode + Vercel AI SDK) emitting identical traces. **xCABI RFC-0** + JSON schema + conformance vectors + ODPS corpus 0.1 shipped. |
| M3 1.0 | 6+ | Control-plane pager behind `policy` flag (FaultPinPolicy), PyO3 binding, semantic-fault plugin interface, trace corpus → policy leaderboard (ODPS-derived rankings). |

## 7. Risks & positions

- **Standards need adoption →** telemetry wedge makes integration value immediate; adapters
  contributed upstream; LF/ODPS governance borrowed rather than cold-started.
- **Silent-reference faults are the hard 20% →** layering: tool_recall (works per Pichay) +
  identifier_scan + explicit API; profiler makes misses visible; semantic plugins later.
- **Pager vendors could standardize →** unlikely — each profits from lock-in; our edge is
  being the Switzerland (LF-governed, Apache-licensed, no product to sell).
- **Prompt-cache rewrite costs →** boundary-aligned eviction + cache-cost accounting in every
  benchmark claim.

## 8. ODPS integration (summary; details in `06-odps-integration.md`)

- Corpus, benchmarks, conformance vectors, enterprise traces, and (later) trained policies
  are packaged as **ODPS 4.1 data products**; hub = **ODPC v1.0** Git-based catalog.
- `productStrategy.productKPIs` carries machine-readable benchmark claims (fault recall,
  net-token reduction) — leaderboard scrapes manifests.
- `x-cabi` sidecar extension pins the trace format version inside every manifest.
- Upstream engagement is line-itemed: JSONL/Parquet format enum PR, template-drift issues.
