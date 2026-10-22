# ctxvm-core

Deterministic context VM engine — pages, decisions, render projections. Pure Rust,
no FFI, no LLM calls, no embeddings (locked decision: semantic policy lives in plugins
outside this crate).

## Page table (`page_table.rs`)

- **Identity.** A page is keyed by `(logical_ref, content_hash)` — the xCABI page key.
  First `page.declare` wins: an identical re-declaration is idempotent; a mismatched
  one is logged, not applied (`DuplicateDeclare`).
- **Streaming state machine.** `Playback::feed(event)` applies *decision* events
  (`page.declare / evict / fault / pin / unpin`) and schedules per-page render-mode
  changes. Fact and metadata events (`page.render`, `turn.render`, `session.open`,
  `call.meta`) are ignored here — they are T1d's comparison surface.
- **Effect timing (locked for v0 — RFC-0 must record):**
  - `page.evict @ t` → stub visible **at turn t** (evictions batch at the boundary
    before the turn they tag)
  - `page.fault @ t` → full **from turn t+1** (a fault is discovered observing turn
    t's output; the page returns at the next boundary)
  - pins: no turn in v0 — the flag in slots reflects the latest stream state
- **Change ordering.** Mode at turn t = the change with the latest
  `(effective_turn, stream_seq)` among those with `effective_turn ≤ t`; none ⇒ full.
  Stream order breaks same-turn ties; a scheduled re-materialization at t+1 is not
  cancelled by an earlier-effective later-seq evict.
- **Violations, never throws.** Anomalies (evict of unknown/already-stubbed page,
  evict while pinned, fault of resident page, duplicate fault, unpin of unpinned,
  duplicate content attach) become `Violation{seq, kind}` ledger entries; state
  takes the logged decision anyway (telemetry-first: the tracer cannot harm the host).
- **Content.** Host-attached out-of-band (`attach_content`) — the trace stores only
  `content_hash`; content never influences decisions. First attach wins.

## Deterministic rendering (`render.rs`)

- `Playback::slots_at(turn)` — every declared page in first-declaration order, as
  full content or the verbatim logged stub (`page.evict.stub_text` — the only prose
  template v0 allows). Stub slots keep the declared full-size token count for waste
  accounting.
- `tally_at(turn)` — resident tokens (full pages) / stubbed tokens (pending-return
  debt) / slot counts.
- `derive_projection(events, turn)` — pure function trace → projection, in one call.
- **Determinism boundary:** slot *structure* is a pure function of the trace;
  full-content *bytes* are environment-supplied and never affect decisions or order.
  Two derives of the same trace serialize to identical bytes (BTreeMap + seq
  tiebreaks + canonical serde emission; proven in test).

## Known limits (v0)

- Rough O(changes) per page lookup; fine for spike corpora.
- `turn.render` totals are not cross-checked here — that is T1d (replay + divergence).
