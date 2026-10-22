# T6 — MCP tool-shim design note (v0)

**Status:** Draft (markdown only; no code this card) · Source cards: `03` (Auto-shim),
`02` (fault taxonomy + invariants), RFC-0 §5/§7/§8 (timing/stub/fault rules).

The shim is a **loader-side decorator over MCP `callTool`**: same wire syntax, same
semantics — it only DERIVES AND LOGS. Zero behavior change (telemetry-first): the model
always receives the real tool result in v0.

## 1. Interception point

Wrap the MCP **client SDK's `callTool(name, args)`** — the smallest surface that sees
every tool result exactly once (`03`'s one-line swap: `client.callTool(...)` → `vm.call(...)`).
Not the transport (misses higher-level caching spans) and not the server (breaks
provenance: a server may be remote; the client call is where attribution is unambiguous).

```
agent tool-call loop                     shim (this doc)
──────────────────────────               ─────────────────────────────────
harness picks tool+args      ──────────→ vm.call(tool, args)
  → MCP request                            → wire callTool (verbatim, unmodified)
  ← result R                               ← sha256 R · tokenize · mint page id
model sees R next turn                    → declare / render / fault bookkeeping
model replies                             ← vm.observe(output) — identifier_scan,
                                            NOT shim scope (03)
```

## 2. Page identity & what the model sees

Minted per call, RFC-0-conformant, stable across identical re-calls (§4 needs stability):

```
logicalRef   := tool:<server>.<name>(<canonicalArgs>)   # >120 chars ⇒ truncate + "#<sha256.8>"
contentHash  := sha256(serialized result)               # first-declare-wins content (RFC-0 §4)
kind         := tool_result (text) · image_ref (image blocks) · isError ⇒ not a page
tokens       := token count of the full content         # pluggable tokenizer, tiktoken default
```

**Handle shape (v0, mirror):** the JSON the model sees is the tool result itself —
**verbatim**. There is no model-visible handle object in v0; the "handle" is the tracer's
internal record (page id + hash + tokens). The trace records exactly what `02`/RFC-0 pin:
`page.declare` at call time (turn-free), `page.render` mode=full at the turn the result
is first visible (same-turn, stream order per RFC-0 §5).

**Handle shape (v1, paged):** an evicted slot carries the shim-written `stubText`,
mechanically derived with the RFC-0 §7 three functions (identify · how-to-recover · cost):

```
[Paged out: MCP tool github.create_issue (3.1k tok).
 Re-call create_issue(repo="acme/x") (server github) to re-materialize.]
```

`stubText` is recorded in `page.evict` exactly as written; renderers never rewrite it
(RFC-0 §7 normative: renderers never invent or rewrite stub text). **No JSON surface
beyond the verbatim result (v0) or this prose stub (v1) is ever exposed to the model.**

## 3. `tool_recall` matching (Pichay method)

Rule: a model re-call `(name, args)` matches a prior page iff
`canonical(name, canonicalArgs) == that page's logicalRef`.

- **canonicalArgs** = JSON with sorted keys, minimal separators, insignificant
  whitespace dropped — stable across transport serialization quirks.
- Nondeterministic argument values (cursor, timestamp, draft-edits) intentionally
  distinguish calls → distinct logicalRefs → correctly NOT counted as re-calls.
- The match lands at the re-call's turn `t`; per RFC-0 §5 the evicted page renders
  full at `t+1` — the harness's next `vm.render` pass simply records the fact.

## 4. What the shim records (per call)

| Situation | Event(s) | Conformance note |
|---|---|---|
| first call, result R | `page.declare` · `page.render` full@t | clean |
| repeat call, page **evicted** (stub) | `page.fault(tool_recall)@t` | real fault-in; full render fact at t+1 |
| repeat call, page **resident** | `page.fault(tool_recall)@t` → ledger logs `FaultOfResidentPage`, state untouched (RFC-0 §8; T1c rules) | divergence-free; **the violation ledger IS the double-fetch metric** |
| repeat call, content changed | same tool+args, new `contentHash` ⇒ new page declared | a legitimate fresh fetch is never mis-measured as waste |
| call raises / `isError` | no page events; error surfaced verbatim | pages are content only |

`identifier_scan` is NOT shim scope — it fires in `vm.observe(modelOutputText)` per
`03`; the shim only supplies the declarations that make those scans matchable.

## 5. Zero-config flag surface (complete list)

| Flag | Default | Meaning |
|---|---|---|
| `--ctxvm <off\|mirror\|page>` | `mirror` once the shim is installed | `mirror` = v0 telemetry-only; `page` = v1 control mode (stub slots carry the §2 stub; policy external, inert in v0 planner) |
| `--tokenizer <id>` | `tiktoken-o200k_base` | declared-token unit |
| (v1 only) `--budget-tokens N`, `--policy <id>` | — | accepted, inert in v0 |

Nothing else. No MCP protocol extension, no server-side changes, no per-tool config.

## 6. Risks — double-fetch elimination vs cost of gathering

- **Gathering is bounded and local:** tokenize + sha256 over result bytes — microseconds
  per kTok, orders below the tool latency being measured. No extra network I/O.
- **Elimination is a v1 policy, not a format concern:** the ledger already prices every
  avoidable re-call (evicted ⇒ fault-in was measured; resident ⇒ violation row measures
  the double-fetch). Policies can be evaluated OFFLINE against the same traces — the
  elimination decision never has to be made online at zero-config level.
- **Fresh fetch honesty:** hash-before-count (§4) prevents conflating a changed
  underlying resource with waste — the biggest correctness risk of naive re-call
  counting.
- **Non-MCP/adjacent cost surfaces** (prompt cache, provider-side reuse) are invisible
  to the shim — they belong to `call.meta` estimates, which the tracer already records.

## 7. Pseudocode (the whole shim)

```ts
const vm = trace({ agent, model, tokenizer: opts.tokenizer })

async function vmCall(name: string, args: Json, invoke: MCPInvoke): Promise<McpResult> {
  const res = await invoke(name, args)              // MCP wire call, unmodified
  if (res.isError) return res                       // errors are not pages
  const content = serialize(res)                    // deterministic serialization
  const hash = sha256(content)
  const ref = logicalRef(serverOf(name), name, canonicalArgs(args))
  if (!vm.knows(ref, hash)) {
    vm.declare({ kind: kindOf(res), tokens: vm.count(content) })   // turn-free
    vm.render(ref, vm.turn())                       // full at t (internal call-through)
  } else if (vm.residentAt(ref, vm.turn())) {
    vm.fault({ ref, source: "tool_recall" })        // ledger: FaultOfResidentPage,
  } else {                                          // state untouched (RFC-0 §8)
    vm.fault({ ref, source: "tool_recall" })        // real fault-in ⇒ full at t+1
  }
  return res                                        // model sees res verbatim in v0
}
```

(Names like `vm.turn()`/`vm.knows()` are internal call-throughs of `@ctxvm/node`, not
new public API — adapters in T7 need only `trace()`, `vm.call`, `vm.render`,
`vm.observe`.)

## 8. Consistency with `02` / RFC-0 (checklist)

- Uses only `tool_recall` (shim scope) · `identifier_scan` lives in `trace()`/`observe()`
  per `03` · `explicit_api` unaffected · `semantic_*` untouched (v1 plugin class) ✓
- Stub text = RFC-0 §7 template facts (identify / recover / cost), no invention ✓
- Effect timing honored: fault@t → full@t+1; `page.declare` stays turn-free ✓
- No new event kinds proposed; resident re-calls surface via the EXISTING
  `FaultOfResidentPage` violation ledger ✓
- The standard stays pure — this design requires zero xCABI changes ✓

**RFC-1 candidate (discovered here, parked):** a `page.touch` receipt distinct from
`page.fault` (same tension RR-T3 note 3 recorded) would let mirror-mode resident
re-calls count without ledger noise. Not proposed into v0.
