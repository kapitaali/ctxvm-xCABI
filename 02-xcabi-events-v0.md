# xCABI Events — Draft v0

*The trace format is the product (telemetry-first wedge). This file is the open draft;
attack list at bottom.*

## Design goals

1. **Append-only.** Logs are the only artifact, not a debugging afterthought.
2. **Deterministic replay.** Same trace → byte-identical re-render of every turn.
3. **Cross-harness portability.** A consumer reconstructs turn 37 without knowing the
   originating harness.
4. **Provider/harness agnostic.** Talks raw messages; no vendor semantics in the format.
5. **Zero ambient intelligence.** Core never consults an LLM; any "smart" decision is a
   plugin logged as a marked non-deterministic event class.

## Pages (nouns)

Stable identity, always:

```
page_id := (logical_ref, content_hash)
  logical_ref  e.g. "tool:read_file(path=src/auth.ts)" | "file:sha256:…" | "summary:t9"
  kind         file | tool_result | summary | image_ref
  tokens       tokenizer-tagged count
```

## Events (verbs) — draft vocabulary

| Event | Payload | Why it matters |
|---|---|---|
| `session.open` | agent id, model, provider, budget, tokenizer id | namespaces a trace |
| `page.declare` | page desc | entered the pager |
| `page.render` | turn #, mode (full \| stub) | ground truth for "waste" measurements |
| `page.evict` | turn #, stub text used | paging decision + what the model was told |
| `page.fault` | turn #, source, latency | **the economics event** — a fault is a measured eviction mistake |
| `page.pin` / `page.unpin` | reason | working-set decisions auditable |
| `turn.render` | turn #, resident/evicted token totals, headroom | the render set for that call |
| `call.meta` | provider, est. cache hit/miss, latency | cache-cost honesty (estimates flagged as such) |

**Resolved:** derived events (`trace.gc`, waste stats) stay **out** of the log — the
profiler-computes them from `page.render` × `page.fault` at read time. Log stays a pure
determinism surface.

## Fault taxonomy (sources)

| Source | Mechanism | Default |
|---|---|---|
| `tool_recall` | model re-calls same tool/args → fault-in (Pichay-proven) | on |
| `identifier_scan` | scan model output for paths/keys/URLs/symbols → fault-in | on |
| `explicit_api` | harness or plugin calls `vm.fault(h)` | on |
| `semantic_*` | embedding/LLM "it probably wants this" | **v1 plugin only**, marked non-deterministic |

## Stub format (what the model sees after page-out)

Inline identity + self-service recovery, zero added system prompt:

```
[Paged out: read src/auth/session.ts (8.2k tok, 187 lines).
 Re-call read_file(path="src/auth/session.ts") to re-materialize.]
```

Three functions (per Pichay): identify what left, how to recover it, cost less than the page.

## Log invariants (the standard-making part)

1. Append-only; turns are the determinism unit.
2. Every re-render of the same trace yields the identical message array.
3. Evictions batch at turn boundaries (never mid-turn); transcript shape kept stable via stubs.
4. Different-harness consumers replay any turn exactly.
5. Every cost figure in derived analytics must subtract estimated cache misses
   (`call.meta.cacheEstimate`) — "net cost" is the only honest number.

## Open questions

- `call.meta` cache-hit accuracy: provider-reported where available; otherwise estimated and
  *flagged* — build the flag into consumers, not wish it away.
- `page.pinned_content` mid-flight protection semantics (kill window between fault and render).
- Relationship to compaction/summary pages (`summary:` ref kind) — does summarization produce
  a new page at lower fidelity, or replace? (Lean: new page; original stays addressable.)
