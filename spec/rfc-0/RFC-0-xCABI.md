# xCABI RFC-0 — Agent Trace/Page/Fault Standard

*Status: **DRAFT** · Version: 0 · Date: 2026-10-22 · Source draft: `02-xcabi-events-v0.md`
· Executive note: `xCABI` and `ctxvm` are working names; renaming is an explicit
orchestrator task, not a free act.*

## 0. Abstract

xCABI defines an append-only JSONL event log that records, per agent session, the
**pages** (addressable content chunks), the **decisions** taken over them
(declare / evict / fault / pin / unpin), and the **facts** of what the model actually
saw each turn (render modes, token totals, cache-cost metadata). Any conforming
consumer can deterministically re-derive each turn's page/stub composition from the
log alone and *prove* a trace internally coherent (replay). The log is telemetry:
it never mutates host messages (telemetry-first wedge, `01-PLAN.md`).

## 1. Scope

- **In:** page identity, event vocabulary, payload shapes, effect timing, ordering
  rules, stub format, invariants, canonical JSONL form, replay/conformance semantics.
- **Out:** eviction *policy* (pluggable, logged as non-deterministic plugin events in
  v1), tokenizer concurrency (token counts are tagged `tokenizer_id` per session),
  provider message mirroring (v1 tracer concern), bindings' FFI details.

## 2. Conformance language

Normative: MUST / SHOULD / MAY (RFC 2119 sense). Conformance = passing the vectors in
§13 (byte-identity) + §12.3 (fact coherence) + §11 (strictness gates).

## 3. Design goals (from 02, unchanged)

Append-only · deterministic replay · cross-harness portability · provider/harness
agnostic · zero ambient intelligence (no LLM/embedding consult inside the standard's
machinery; any smart decision is a marked non-deterministic plugin event class).

## 4. Pages

A page is addressed by the pair (normative):

```
page_id := (logical_ref, content_hash)
kind    := file | tool_result | summary | image_ref
tokens  := declared full-content size in `tokenizer_id` units
```

- `logical_ref` examples: `tool:read_file(path="src/auth.ts")`, `file:sha256:…`,
  `summary:t9`. `content_hash` is a string tag; its hashing scheme is session-scoped.
- **First declaration wins.** An identical `page.declare` re-statement is idempotent;
  a mismatched one never changes the record (a conformance violation is logged).
- Floating-point values are banned anywhere in the trace.

## 5. Events

JSONL: one event object per line, tagged by a literal `"type"` key with the dotted
lowercase tag below. Field names are camelCase. Tag values and enum values are
exact strings (normative). Optional fields are **omitted when unknown — never `null`**.

| # | tag | payload (normative fields) | status |
|---|---|---|---|
| 1 | `session.open` | `agentId` S · `model` S · `provider` S · `budgetTokens` I≥0 · `tokenizerId` S | required |
| 2 | `page.declare` | `page` R{ id R{`logicalRef` S · `contentHash` S} · `kind` K · `tokens` I≥0 } | required |
| 3 | `page.render` | `turn` I≥0 · `page` {logicalRef,contentHash} · `mode` M | required |
| 4 | `page.evict` | `turn` I≥0 · `page` · `stubText` S | required |
| 5 | `page.fault` | `turn` I≥0 · `page` · `source` F · `latencyMs` I? | required; latency optional |
| 6 | `page.pin` | `page` · `reason` S | required |
| 7 | `page.unpin` | `page` · `reason` S | required |
| 8 | `turn.render` | `turn` I≥0 · `residentTokens` I≥0 · `evictedTokens` I≥0 · `headroom` I? | required; headroom optional |
| 9 | `call.meta` | `turn` I≥0 · `provider` S · `cacheEstimate` R{`estHitTokens` I≥0 · `estMissTokens` I≥0 · `providerReported` B} · `latencyMs` I? | required; latency optional |

S=string · I=integer · K=`file|tool_result|summary|image_ref` ·
M=`full|stub` · F=`tool_recall|identifier_scan|explicit_api|semantic` · B=boolean · I? = optional integer.

Resolution notes vs the 02 draft table (recorded here, backward-referenced):

- `call.meta` **gains `turn`** (not in the draft payload list): cache estimates cannot
  be joined to the turn they describe otherwise (invariant 5).
- `page.pin`/`page.unpin` **stay turn-free** in v0: pins are working-set decisions
  whose effective turn is undecidable in the draft; slot pin-flags reflect the latest
  stream state. RFC-1 may add `turn`.
- `page.declare` **stays turn-free**: a page's first eligible turn is decided by its
  first render/fact, not its declaration order.
- Unknown fields MUST be rejected by conforming implementations (see §11); the 02
  draft's silent-drop hazard is neutralized.

## 6. Effect timing and change ordering (the replay kernel)

Normative, locked in the M0 engine (`RR-T1c`):

| Decision | Effect |
|---|---|
| `page.evict @ t` | stub visible **at turn t** (evictions batch at the boundary before the turn they tag) |
| `page.fault @ t` | page full **from turn t+1** (fault discovered observing turn t; re-materialized at the next boundary) |
| `page.pin / unpin` | bookkeeping only; no render-mode effect in v0 |

Ordering: the change with the latest `(effective_turn, stream_seq)` with
`effective_turn ≤ t` applies; none ⇒ full. Stream order breaks same-turn ties; a
scheduled re-materialization at t+1 is NOT cancelled by an earlier-effective
later-seq evict. Determinism holds even for malformed timelines.

**Shape stability (invariant 3, concretely):** every declared page keeps its turn slot
for every turn; paging swaps full-content ↔ stub — the transcript's page-layer shape
never changes.

## 7. Stub format

The one prose template the standard allows, verbatim from 02 (the stub MUST be the
`stubText` recorded in `page.evict` — renderers never invent or rewrite stub text;
a repeat evict refreshes it in stream order):

```
[Paged out: read src/auth/session.ts (8.2k tok, 187 lines).
 Re-call read_file(path="src/auth/session.ts") to re-materialize.]
```

Three functions (per Pichay, arXiv 2603.09023): identify what left · how to recover it · cost < page.

## 8. Fault taxonomy

`tool_recall` (default on) · `identifier_scan` (default on) · `explicit_api`
(default on) · `semantic_*` — v1 plugin class only, always marked non-deterministic.
A fault MUST target a stubbed page; faulting a resident page is a conformance
violation (logged, state untouched).

## 9. Log invariants (normative; from 02 + M0 refinements)

1. Append-only; turns are the determinism unit.
2. Every re-render of the same trace yields the identical page/stub composition
   (byte-identical conforming serialization).
3. Evictions batch at turn boundaries (§6); shape stability via stubs.
4. Different-harness consumers replay any turn exactly.
5. Every cost figure in derived analytics MUST subtract estimated cache misses
   (`call.meta.cacheEstimate`); `providerReported=false` figures stay labeled.
6. *(new)* Corpus-level fact coherence MUST be checkable mechanically (§12).

## 10. Determinism boundary

The render *structure* (which pages, which modes, which stub bytes, declared token
counts) is a pure function of `(events, turn index)`. Full-content *bytes* are
environment-attached; the trace stores only `content_hash`. Two replays with the
same trace and the same attached content serialize identically.

## 11. Canonical form and strictness (normative)

One compact JSON object per line · field order = schema declaration order · trailing
newline · blank lines tolerated on read, never emitted · no floats — unknown tag ⇒
hard error · unknown field ⇒ hard error · float-encoded integer field ⇒ hard error ·
`latencyMs`/`headroom` omitted (not null) when unknown.

## 12. Replay and conformance

12.1 **Replay** = static analysis: apply all decisions (final schedule), then verify
every `page.render` and `turn.render.residentTokens` against derived state.
Divergence kinds (normative):
`RenderModeMismatch{turn,page,inferred,recorded}` · `RenderOfUnknownPage{turn,page}` ·
`ResidentTokensMismatch{turn,inferred,recorded}`.
`turn.render.evictedTokens` is recorded but unchecked in v0 (stub tokens need a
tokenizer; OPEN T-OVICT). Violations (§13 ledger kinds) are telemetry, not failures —
only divergences trip the conformance gate.

12.2 **Exit contract** for a `replay` CLI: `0` = divergences-free · `1` = divergences ·
`2` = usage/IO/parse error.

12.3 **Fixture taxonomy:** *codec vectors* prove byte-identity (`events-v0.jsonl`);
*replay fixtures* prove fact coherence (`session-clean.jsonl` green; 
`session-divergent.jsonl` = exactly two engineered divergences). Both live in
`rust/crates/ctxvm-conformance/vectors/` and are release-blocking.

## 13. Violations ledger (telemetry, informative)

Types (each logged with its stream index): duplicate-declare · unknown-page decision ·
evict-while-stubbed (repeat evicts rewrite stub text, latest evict wins) ·
evict-while-pinned · fault-resident · duplicate-fault · unpin-unpinned ·
content-attach guard. State takes the logged decision anyway — the tracer cannot harm
its host (03).

## 14. Open questions (carried into next revisions)

- **Version field:** RFC-1 MUST introduce a format tag (`session.open.xcabiVersion`)
  before schema evolution (T1b discovery; deliberate non-inclusion in v0).
- **Declare turn** (should `page.declare` gain one?), **pin turn** (§5 note).
- **Evicted-token verification** (T-OVICT, §12.1).
- `call.meta` accuracy flag: provider-reported vs estimated — currently honest by
  boolean; dashboards must not average them together (invariant 5).
- `page.pinned_content` mid-flight kill-window semantics (02 open).
- Compaction/summary relationship: new page vs replacement (02 open; v0 leans: new
  page, original stays addressable).
- `semantic_*` plugin taxonomy naming (v1).

## 15. References

- `02-xcabi-events-v0.md` — the source draft this RFC consolidates (tables/invariants
  quoted exactly).
- `01-PLAN.md` §arch, §Decisions · `03-tracer-api-ts.md` (CLI exit note) ·
  `07-benchmarks-go-no-go.md` (M0 gate).
- Engine: `rust/crates/ctxvm-core` (semantics), `rust/crates/ctxvm-codec` (wire),
  `rust/crates/ctxvm-conformance/vectors/` (artifacts), `x-cabi.schema-v0.json` (adjacent).
- Reports: `reports/RR-T1b/T1c/T1d-20261022.md`.
