# Tracer API Sketch (TypeScript, telemetry-first v0)

## The only thing a harness integrator writes (~10 lines)

```ts
import { trace } from "@ctxvm/node"

const vm = trace({
  agent: "my-agent",
  model: "openai/gpt-5",
  budgetTokens: 120_000,
})

// When tool results materialize, declare pages (auto-tokenized)
const h = vm.page({ kind: "tool_result", ref: "tool:read_file(sha:abc123)", tokens: n })

// Per turn: mirror what the model will actually see
vm.render(messages)                          // emits turn.render

// After the turn: scan model output for identifiers → record faults
vm.observe(modelOutputText)                  // source: identifier_scan
```

No behavior change. The pager never touches anything — it mirrors. Adoption is a config step.

## Auto-shim (optional, zero-code)

Wraps MCP tool calls: results are auto-declared as pages (`tool_recall` faults by
name+args matching, per Pichay). One-line swap from `client.callTool(...)` → `vm.call(...)`.

## CLI surface

```
ctxvm profile ./session.jsonl     # the demo moment:
#   Pages: 312        Rendered tokens: 41.8k
#   Never-touched: 65.3% of rendered tokens (27.3k)
#   Worst page: tool:read_file(src/db/schema.sql) 12.1k tokens — 0 touches
#   Faults: 19 (all recovered via tool_recall)  → eviction mistakes cost 0.4% net tokens

ctxvm replay ./session.jsonl      # byte-identical re-render; exit 1 on divergence
ctxvm diff a.jsonl b.jsonl        # page-level divergence of two runs
ctxvm export --odps ./session.jsonl   # dataproduct.yaml + llms.txt (telemetry → packaging)
```

## Type/impl notes

- Binding layer: napi-rs over `ctxvm-core`. Parser/renderer in Rust; JS sees the API above.
- Tracer NEVER mutates `messages`; it derives and logs only.
- `vm.page()` accepts raw string or structured chunks; tokenizer pluggable
  (tiktoken default; HF behind feature flag).
- Errors are events too: a dangling pin, unclaimed fault, or divergent replay is logged,
  never thrown — telemetry-first means the tracer can't harm the host agent.
