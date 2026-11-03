# Causal edges — what the ledger can prove, and what it cannot

**Status:** design note only (W16). No implementation, and no promise of fault localization in any
README or pitch until an owner decision. **Gate:** implementation waits on W13–W15 (landed) and on
the owner's approval of the question it is meant to answer.

## 1. The question

The Trace Engineering essay (@marfinxx, 30 Aug 2026) describes causal fault localization: identify
the failing span, walk backwards **only along data-dependency edges**, and stop at the origin span —
noting that the origin often reported `status: OK`, because a syntactically valid call can be
semantically wrong. The essay asserts this; it measures nothing.

The useful question for this repo is narrower: **which dependency edges can xCABI already prove, and
which would need new fields?**

## 2. What the ledger derives today, at zero bytes

The nine v0 verbs give, per session:

| Edge | Derived from | Strength |
|---|---|---|
| `page p became visible at turn t` | `page.declare` (+ `turn`, R5) and `page.render` | proven |
| `p was resident at turn t` | declares up to `t`; from v0.1, adjusted by `page.evict`/`page.pin`/`page.unpin` | proven |
| `the call at turn t re-fetched p` | `page.fault{source: "tool_recall", turn, page}` | proven |
| `t1 precedes t2` | `turn` index, `ts` | proven |
| `resident/evicted token totals at t` | `turn.render` | proven (aggregate only) |

That is a DAG over **pages and turns**. It answers: which pages were resident when a fault fired,
which turn introduced a page, what a bad declare reached afterwards. It cannot answer: which *call
instance* did it.

Two boundaries are worth stating plainly:

1. **`identifier_scan` is a heuristic touch, not causality.** We infer that a page was "used" because
   its identifiers appear in model output. The essay's phrase would be a data-dependency edge; ours
   is a correlation with a known false-positive class (the page's own stub text, a shared filename).
   Any graph that draws it as an edge must mark it inferred.
2. **The page ref is content-derived.** `tool:read_file({"path":"a"})` identifies a page by name and
   hash, so two identical calls collapse into one node. Instance identity is not available by
   construction — no amount of replay recovers it.

## 3. What the hosts already expose — all three lanes, verified

| Lane | Instance id | Locator |
|---|---|---|
| hermes | `tool_call_id` (and `task_id`) on tool hooks | `hermes_cli/hooks.py` `_DEFAULT_PAYLOADS`; the same keys are in the production payloads |
| opencode | `id` (call) and `messageID` on `ToolExecuteAfter` | `packages/opencode/src/opencode-contract.ts:38-48` |
| ai-sdk | `toolCallId` on `tool-call` / `tool-result` parts | `packages/ai-sdk/src/tap.ts:66`; exercised in `test/ctxvm-adapter.test.ts` |

So option B needs **no new host support** — only a decision to trust the id and a field to carry it.
What is genuinely missing is the cross-session link (§4 C), not the per-call one.

## 4. Three designs, cheapest first

### A. A view, not a record (recommended first)

New binary `causality` (siblings: `replay`, `diff`, `profile`, `export`) that derives §2's page/turn
DAG from an existing trace and prints it, or emits DOT/JSON.

- **Bytes:** zero. No schema change, no version gate, no fixture regeneration.
- **Determinism:** unaffected — the DAG is a pure function of events already proven byte-identical.
  Ordering must be fixed explicitly (turn, then event index, then content hash) or the output is
  non-deterministic even though the input is.
- **Answers:** residency at a fault, introduction turn of a page, blast radius of a declare, the
  re-fetch chain of one page.
- **Refuses:** instance-level attribution ("this call, not that one") and anything crossing sessions.

### B. Store instances (only if an owner question needs it)

`page.declare.callId` (the host's `tool_call_id`), additive, version-gated, allowlisted, with a
validator negative for a non-opaque value.

- **Bytes:** ~30–40 per declare (`"callId":"call_…"`). On the 6-event sample (1,530 B) that is ~2%;
  on a 300-event session it is ~9–12 KB, which matters only if traces are shipped in bulk.
- **Determinism:** the id must be **recorded, never regenerated** — a content hash cannot separate
  two identical calls, which is exactly the case the field exists for. That makes the field a claim
  about the host, and a replay can only check that the id is present and well-formed, not that it is
  the right one.
- **Answers:** which call instance introduced a page; per-call blast radius.
- **Costs:** a new field on the busiest event in the stream, and a spec that now depends on host id
  stability.

### C. Cross-session and sub-agent links (deferred)

A fan-out (one orchestrator delegating to N sub-agents) needs a parent/child session edge: the
delegation tool call in the parent would carry `childSessionId`. Nothing in the current hooks
provides it, and `environmentId` (W14) only groups siblings — it cannot say which parent spawned
which child. Deferred: the graph is still a forest of trees without it, which is enough for a single
agent and not enough for a cluster.

## 5. Recommendation

Build **A**, and only A, until someone needs to answer a question A cannot. It is the cheapest honest
step: it uses data we already prove is deterministic, it adds no field to the wire, and it prevents
the failure mode of shipping a graph shaped like causality but built from heuristics.

If B is ever built, the edge must be labelled with its provenance the way `prefix.source` and
`toolEffect` are: `derived` (from turn/page structure) versus `recorded` (host-supplied id) versus
`inferred` (`identifier_scan`). A single unlabelled edge type is how a dependency graph becomes a
blame graph.

## 6. What this note refuses to claim

- No fault **localization** — the graph shows dependency, not blame, and there is no ground truth in
  this repo about which span was "the cause".
- No cross-session causality.
- No claim that `status: OK` implies correctness; that observation is the essay's, and the W15
  classification is the counter-measure we actually ship.
- The essay's own numbers (step-count MAD > 3.5, entropy variance < 0.02) are asserted, not measured;
  this note does not adopt them.

## 7. If implementation is approved

1. `causality` binary + tests: two traces (hermes live-echo, ai-sdk canon) produce stable graphs;
   red-before: dropping a `page.render` row must change the graph, not the exit code silently.
2. Determinism: run under `PYTHONHASHSEED`-equivalent conditions in Rust (BTreeMap, no HashMap
   iteration) and compare output across two runs and two machines.
3. Docs: `design/` note moves to `docs/` only after the owner approves the question; README gains a
   sentence only if the graph is shipped.
