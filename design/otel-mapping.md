# W6 — OpenTelemetry mapping: what xCABI can be on the wire, and what it cannot

**Status:** Draft / analysis (owner decision **D3** open — "native format vs OTel
semantic-convention layer"). This note supplies the evidence; it does not choose.
**Date:** 2026-10-29. **Card:** W6 of `08.1-UPDATE-PROMPT.md`.
**Prototype:** `tools/otel-export.mjs` (runs; output in §6).

**Sources (all fetched 2026-10-29):**

| Claim area | Locator |
|---|---|
| GenAI semantic conventions: status, span names, attributes | `github.com/open-telemetry/semantic-conventions-genai` → `docs/gen-ai/gen-ai-spans.md`, `gen-ai-agent-spans.md`, `gen-ai-events.md`, `client-inference.md` (repo pushed 2026-10-29; the OTel site now redirects: "GenAI semantic conventions have moved to the OpenTelemetry GenAI semantic conventions repository" — `opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/`) |
| OTLP JSON encoding rules | `opentelemetry.io/docs/specs/otlp/` §"JSON Protobuf Encoding" (OTLP 1.11.1: stable for traces/metrics/logs) |
| Langfuse OTel ingestion + default span filter | `langfuse.com/docs/observability/sdk/advanced-features#opentelemetry-setup` |
| LangSmith OTel tracing | `docs.langchain.com/langsmith/trace-with-opentelemetry` |
| OpenInference (Phoenix/Arize) conventions | `arize.com/docs/ax/concepts/otel-openinference/semantic-conventions` |
| Hermes' own observability path | `hermes-agent.nousresearch.com/docs/developer-guide/observer-hooks` ("existing consumers": the Langfuse catalog plugin, the native NeMo Relay integration) |

**Everything in the GenAI semconv is `Development`, not `Stable`.** Every `gen_ai.*`
attribute quoted below carries the blue development badge, and the events document
says events "are in-development and not yet available in some languages". A mapping
built today is a mapping onto a moving target — that is a fact about the ecosystem,
not a defect of this note.

---

## 1. The semconv vocabulary xCABI would map onto

Verified names (no paraphrasing):

| Signal | Normative statement | Locator |
|---|---|---|
| Inference span | `gen_ai.operation.name` = `chat`; span name `{gen_ai.operation.name} {gen_ai.request.model}` | client-inference.md |
| Agent span (in-process) | `gen_ai.operation.name` = `invoke_agent`; name `invoke_agent {gen_ai.agent.name}`; kind `INTERNAL` | gen-ai-agent-spans.md §"Invoke agent internal span" |
| Tool span | `gen_ai.operation.name` = `execute_tool`; name `execute_tool {gen_ai.tool.name}`; kind `INTERNAL`; `gen_ai.tool.name` Required, `gen_ai.tool.call.id` Conditionally Required | gen-ai-agent-spans.md §"Execute tool span" |
| Conversation join | `gen_ai.conversation.id` — "unique identifier for a conversation (session, thread)" | client-inference.md |
| Provider | `gen_ai.provider.name` — Required on inference, **enum** with well-known values (`openai`, `gcp.gen_ai`, …) | client-inference.md |
| Token usage | `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.cache_read.input_tokens`, `gen_ai.usage.cache_write.input_tokens` — "as reported by the provider" | client-inference.md |
| Content capture | `OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT`; governed attributes include `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`; "may contain sensitive information" | gen-ai-spans.md §"Content capture configuration" |

Two consequences before any mapping is written:

1. **The vocabulary is request/span-shaped.** There is no eviction, no page
   residency, no stub, no fault, and no "context" object anywhere in the
   conventions. The nearest thing to xCABI's central noun is a tool call.
2. **The content attributes are the ones we deliberately never produce.** RFC-0
   records references and hashes, not bodies. That aligns with the conventions'
   own opt-in posture (`CAPTURE_CONTENT`, "may contain sensitive information") —
   a rare case where xCABI's privacy default *is* the semconv default.

---

## 2. Mapping table (xCABI event → OTel signal)

Implemented in `tools/otel-export.mjs`; every row below is emitted by the prototype.

| xCABI event | OTel signal | Attributes |
|---|---|---|
| `session.open` | resource attrs + root span `invoke_agent {agentId}` (INTERNAL) | `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.conversation.id`, `gen_ai.request.model`, `gen_ai.provider.name`; `ctxvm.trace.xcabi_version`, `ctxvm.trace.tokenizer`, `ctxvm.trace.pages`, `ctxvm.budget.tokens` |
| `turn.render` | span `chat {model}` (CLIENT), child of the agent span | `gen_ai.operation.name=chat`, `gen_ai.request.model`, `ctxvm.turn`, `ctxvm.resident_tokens`, `ctxvm.evicted_tokens`, `ctxvm.headroom_tokens` |
| `call.meta.cacheEstimate` | attributes on the turn span | `gen_ai.usage.cache_read.input_tokens` **only when `providerReported`**; otherwise `ctxvm.cache.est_hit_tokens` / `ctxvm.cache.est_miss_tokens` + `ctxvm.cache.provider_reported=false` |
| `call.meta.latencyMs` | attribute | `ctxvm.call.latency_ms` |
| `page.declare` | span `execute_tool {tool}` (INTERNAL) | `gen_ai.operation.name=execute_tool`, `gen_ai.tool.name`, `ctxvm.page.ref`, `ctxvm.page.content_hash`, `ctxvm.page.kind`, `ctxvm.page.tokens`, `ctxvm.page.first_rendered_turn` |
| `page.render` | span event `ctxvm.page.render` | `ctxvm.page.ref`, `ctxvm.render.mode` |
| `page.fault` | span event `ctxvm.page.fault` | `ctxvm.page.ref`, `ctxvm.fault.source` |
| `page.evict` | span event `ctxvm.page.evict` | `ctxvm.page.ref`, `ctxvm.evict.stub_chars` |
| `page.pin` / `page.unpin` | span event | `ctxvm.page.ref`, `ctxvm.pin.reason` |

Naming discipline: **standard attributes carry only values the semconv actually
defines.** Anything xCABI means that OTel has no word for ships under `ctxvm.*`,
so a backend that understands only `gen_ai.*` shows a clean agent and cannot
mistake an estimate for a provider count.

---

## 3. What survives, what is lost

| xCABI concept | On the OTel wire |
|---|---|
| turn order | `ctxvm.turn` on each turn span, plus child order — **order survives** |
| page identity | `ctxvm.page.ref` + `ctxvm.page.content_hash` — survives as attributes |
| fault source taxonomy (4 values) | `ctxvm.fault.source` on an event — survives as a string, loses the RFC-0 invariant (`faultOfResidentPage` is not expressible) |
| eviction + stub text | `ctxvm.page.evict` + `stub_chars`; the stub **text** is not exported (content) |
| residency / headroom | `ctxvm.resident_tokens` / `ctxvm.headroom_tokens` — survives as an attribute, loses its definition |
| replay determinism | **lost** — nothing in OTel replays a page table |
| derived KPIs (touch_ratio, net token cost, thrash_index) | **lost** — they are corpus-level computations, not signals |

### The three hard gaps

1. **xCABI has no clock.** The RFC-0 schema contains no timestamp field of any
   kind (verified: `grep -o '"[a-zA-Z]*[Tt]ime[a-zA-Z]*"' spec/rfc-0/x-cabi.schema-v0.json`
   → no matches; the only temporal field is the optional `latencyMs`). OTel spans
   are *defined* by `startTimeUnixNano`/`endTimeUnixNano`. The prototype therefore
   emits spans **without** time — structurally valid OTLP, but many backends key
   span rendering on time and will either drop or degenerate them. Any honest
   exporter needs a capture-time clock, which is an RFC-0.1 candidate (→ W7).
2. **Residency is not usage.** `turn.render.residentTokens` is the declared page
   table, not what the provider billed. Filling `gen_ai.usage.input_tokens` from
   it would be the exact dishonesty W3 removed from the metrics. The prototype
   leaves `gen_ai.usage.*` empty unless `providerReported` (which no v0 emitter
   sets) and ships the number under `ctxvm.resident_tokens`.
3. **`page.declare` carries no turn.** The event is `{type, page}` — so a tool
   span cannot be parented to the turn in which it happened. The prototype parents
   all tool spans to the agent span and records `ctxvm.page.first_rendered_turn`
   instead. This is an RFC-0.1 candidate too (a `turn` field on `page.declare`).

---

## 4. Coexistence: what Langfuse / Phoenix / LangSmith already own

Facts, each with its locator:

- **Langfuse** ingests OTLP and applies a default span filter — a span is exported
  if it "has at least one `gen_ai.*` attribute", or comes from a known
  instrumentation scope (`openinference.*`, `langsmith`, `litellm`, …). The
  prototype's spans all carry `gen_ai.*` on the agent/turn/tool spans, so a ctxvm
  trace **would be ingested by Langfuse without a custom filter or an SDK.**
- **LangSmith** documents OTel-based tracing for any OTel-compatible agent and
  explicitly supports fan-out of one span stream to several backends.
- **Phoenix/Arize** standardise on **OpenInference** (`llm.*`, `tool.*`, `agent.*`,
  `retriever.*`). Arize publishes the comparison directly: OpenInference is
  "Stable… breaking changes are versioned"; the GenAI conventions are "still in
  development; not on a stable release" and "subject to change at any time".
  Phoenix's reading of `gen_ai.*`: "Spans tagged with `gen_ai.*` attributes still
  arrive at Phoenix, but won't get the same UI treatment as
  OpenInference-tagged spans." Arize's own advice for new instrumentation today:
  "use OpenInference". So the second projection is not a nicety — the largest
  OSS OTel-native AI backend treats `gen_ai.*` as second class.
- **Hermes already ships both paths** (observer-hooks, "Existing consumers"): the
  official Langfuse catalog plugin and the native NeMo Relay integration (ATOF/
  ATIF/OTEL exporters). So on the harness where ctxvm is most developed, an OTel
  view of the session *already exists* upstream of us.

**The differentiator, stated precisely.** Those systems answer "what happened,
in what order, with what cost". None of them can answer: *was this tool result
still resident when the model asked for it again, and what did re-materializing it
cost?* That question needs the page table, the eviction record and a deterministic
replay — i.e. the JSONL. OTel is a **projection of an execution**; xCABI is a
**replayable model of the context**, of which the execution is one instance.

---

## 5. D3 options (analysis, not a decision)

| Option | What it means | Cost | What it buys | What it cannot do |
|---|---|---|---|---|
| **D3-a Native format** (status quo) | JSONL stays the only format; OTel is out of scope | 0 | replay, page-table semantics, differential testing | no OTel-native dashboards; outsiders must adopt a new format |
| **D3-b Semantic-convention layer** | Publish `ctxvm.*` as an *extension profile* of the GenAI semconv; ship the exporter as the supported path | one exporter per language + attribute registry + conformance fixtures | reach into OTel backends at zero integration cost (Langfuse first-class by its filter rule; LangSmith; Phoenix accepts `gen_ai.*` with reduced UI treatment per Arize) | paging semantics degrade to custom events; no replay; the semconv is `Development` and will move |
| **D3-c Both, layered** | JSONL canonical + exporter as a **lossy view**; the exporter declares which fields it drops | 1 (exporter) + docs | reach without giving up replay; two independent consumers of one capture | two things to keep honest (a drift risk, mitigated by making the exporter a pure projection with no independent logic) |

The prototype is an existence proof for **D3-c**: it is 235 lines, dependency-free,
reads only the JSONL, and produces valid OTLP/JSON for all four harnesses
(§6). The recommendation *as an input to D3* is D3-c, with two preconditions
recorded above: a capture-time clock and a `turn` on `page.declare` (both W7/RFC-0.1
candidates), because without them the OTel view is legitimately time-less and
turn-partial.

---

## 6. Prototype — measured, not described

```
$ node tools/otel-export.mjs corpus/m1/session-thrashing.jsonl --conversation m1-thrash
  spans=13 gen_ai.attrs=29 violations=none
$ node tools/otel-export.mjs corpus/m6/opencode-pause-session-a.jsonl
  spans=14 gen_ai.attrs=31 violations=none
$ node tools/otel-export.mjs corpus/m7/hermes-pause-session-a.jsonl
  spans=17 gen_ai.attrs=37 violations=none
$ node tools/otel-export.mjs corpus/m8/live-thrash.jsonl
  spans=10 gen_ai.attrs=23 violations=none
```

`violations` is the structural check the prototype is held to (asserted inline in
the run above): no `startTimeUnixNano`/`endTimeUnixNano` (the clock gap), `kind`
always an integer (OTLP JSON forbids enum name strings), every `intValue` a
decimal string (protobuf 64-bit rule). The m1 trace projects to 1 agent span +
10 turn spans + 2 tool spans, with 20 render / 4 evict / 3 fault events — i.e. the
whole paging story is on the wire as events.

No network call, no dependency, no state: `otel-export.mjs` is a pure function of
the trace. It is **not** wired into `tools/run-ci.sh` — it is a prototype for D3,
not a supported surface, and wiring it before D3 is answered would freeze a
mapping onto a `Development` spec.

---

## 7. Open questions for the owner

1. **D3**: native / semconv layer / layered? (This note recommends layered, with
   the two RFC-0.1 preconditions as the price.)
2. Should the clock gap be fixed in RFC-0.1 (a `ts` on `session.open` and
   `turn.render`), or accepted as "xCABI is deliberately time-free and the
   exporter stamps time at export"? The former is honest at capture; the latter
   is honest at export but makes replay timing irreproducible.
3. Is an OpenInference flavour (Phoenix) worth a second projection, or is
   `gen_ai.*` enough for v0?
