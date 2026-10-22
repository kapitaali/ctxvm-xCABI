# `@ctxvm/node` — v0 tracer

Telemetry-first tracer for agent loops. Emits **RFC-0 xCABI JSONL** (see
`spec/rfc-0/`) from the harness-facing primitives: page materialization,
pre-execution recall marks, turn rendering, output scanning. **Mirror-only**:
v0 records; it never evicts, never mutates caller data, and never throws on
semantic conditions — RFC-0 makes violations logged values, and a fault against
a resident page is exactly the double-fetch waste ledger row (T6 §4).

Zero runtime dependencies. Requires **Node ≥ 22.6** — the TS sources run
directly via type stripping (`erasableSyntaxOnly`: no enums/namespaces); no
build step is needed in-repo.

## Quick start

```ts
import { createTrace } from "./src/index.ts";

const vm = createTrace({
  agentId: "opencode", model: "openai/gpt-5", provider: "openai", budgetTokens: 120_000,
});

vm.page({ tool: "read_file", args: { path: "src/auth.ts" }, content: "…" }); // tool result → page
vm.render();                                              // turn boundary
vm.recall({ tool: "read_file", args: { path: "src/auth.ts" } }); // pre-execution re-call mark
vm.page({ tool: "read_file", args: { path: "src/auth.ts" }, content: "…" });  // landing on a resident page → page.fault(tool_recall)
vm.scan({ text: modelOutputText });                       // page.fault(identifier_scan)
vm.finish();                                              // → { jsonl, events, stats }
```

## API map (the T6/T7 contract surfaces)

| Method | Harness moment | Emits / does |
|---|---|---|
| `page({tool,args,content,tokens?,ref?,kind?})` | tool success → context | `page.declare`; landing on a resident page with the *same* content hash → `page.fault(tool_recall)` |
| `recall({tool,args})` | `tool.execute.before` (pre-exec) | marks a pending re-call; consumed only by the landing `page()` call |
| `render({latencyMs?})` | request composition | reveals newly declared pages (`page.render` full); buffers the turn facts |
| `scan({text,latencyMs?})` | model output observed | `page.fault(identifier_scan)` for identity matches (deduped per page · source) |
| `pin` / `unpin({ref,reason})` | explicit_api | `page.pin` / `page.unpin` (no turn field in v0, per RFC-0) |
| `finish()` | flush | `turn.render` 0..N then `call.meta` 0..N batch; returns `{jsonl, events, stats}` |

The T6/T7 design sketches referred to these as `page_raw` / `observe_recall` /
`scan_text`; the shipped names are the canonical ones.

## Semantics worth knowing

- **Identity** = `(logicalRef, contentHash)` — same args with a new hash ⇒ a NEW
  page slot (a fresh fetch is never scored as waste). Tool refs mint as
  `tool:<name>(<canonicalArgs>)` with keys-sorted canonical JSON; canonical args
  longer than 120 chars truncate to 120 + `#<sha256.8>`. Hashes are
  `sha256:<8 hex>`.
- **Derived composition**: turn facts flush in `finish()` against the whole-trace
  table, matching the Rust engine's static analysis (`ctxvm-core tally_at`): a
  page declared at any stream point counts resident from turn 0 in v0 (there is
  no evict path). Fresh-fetch versions coexist in the derived tally —
  replacement is eviction-policy work (T6 §5), not tracer work.
- **Estimates**: `call.meta` `estHit/estMiss` are page-layer estimates for that
  turn (tokens unchanged since the previous composition count as hit);
  `tokenizerId` defaults to `apx4-char` (≈ chars/4); `providerReported` stays
  `false` until an adapter wires provider-returned numbers.
- **Fault timing**: a fault records the turn in composition when it was
  observed; pre-first-render hits clamp to turn 0 (`turn` is `I≥0`).

## Fixture regeneration & gates

```sh
npm run gen         # rewrites fixtures/tracer-healthy.jsonl + tracer-recall.jsonl
npm run validate    # repo schema conformance gate over both (venv python + spec/rfc-0/validate_schema.py)
npm run replay      # rust divergence gate: cargo run -p ctxvm-conformance --bin replay <fixture>
npm test            # unit suite (node --test test/, 12 tests)
```

## Status / roadmap

v0 = mirror only (this package). Eviction/pinning-driven control ships with the
policy engine later (`design/mcp-shim.md` §5). Next: T9 — OpenCode adapter spike
wiring these surfaces into real hooks; `design/adapters.md` is the wiring plan
(anchors pinned).
