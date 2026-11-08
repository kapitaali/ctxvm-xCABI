#!/usr/bin/env node
/**
 * otel-export.mjs — project an xCABI (RFC-0 / RFC-0.1) JSONL trace onto OTLP/JSON.
 *
 * W4.5/W6 prototype (see design/otel-mapping.md), PROMOTED to the supported
 * path by the D3-c card (reports/RR-D3COTEL-20261108.md; decision D3-c
 * "layered" in reports/RR-DECISIONS-20261030.md §3): conformance fixtures +
 * field-set drift guard now live in tools/otel-export.test.mjs and run in
 * the TS gate. This is still a ONE-WAY, LOSSY projection emitted to stdout;
 * the JSONL remains the replayable source of truth, and the projection is a
 * pure function of the trace. Run:
 *
 *   node tools/otel-export.mjs corpus/m1/session-thrashing.jsonl
 *   node tools/otel-export.mjs corpus/m7/hermes-pause-session-a.jsonl --conversation local-cbeac4fb
 *
 * Encoding rules applied (OTLP 1.11.1, "JSON Protobuf Encoding"):
 *   - traceId/spanId: hex strings, not base64
 *   - enum fields (`kind`, `status.code`): INTEGER values only
 *   - 64-bit integers (intValue, *TimeUnixNano): decimal strings
 *   - object keys: lowerCamelCase field names
 *
 * What the projection deliberately does NOT do, because the trace cannot
 * support it (design/otel-mapping.md §4):
 *   - emit startTimeUnixNano / endTimeUnixNano — xCABI events carry no clock
 *     (R4 `ts` is declared-dropped, preserved in the source of truth)
 *   - fill gen_ai.usage.input_tokens — `residentTokens` is the declared page
 *     table, not provider usage; it ships as ctxvm.resident_tokens instead
 *   - read providerUsage — D12 (RR-DECISIONS-20261031 §3) keeps the est*
 *     attributes keyed on cacheEstimate.providerReported; the W6 OTel gate
 *     is untouched (declared dropped in EXPORT_SPEC below)
 *   - send anything over the network — stdout only, no deps
 */
import { readFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { basename } from "node:path"
import { pathToFileURL } from "node:url"

const KIND_INTERNAL = 1
const KIND_CLIENT = 3

export const EXPORT_SPEC = {
  /* The declared surface of the lossy projection. tools/otel-export.test.mjs
   * keeps these tables mechanically in sync with the RFC-0.1 schema's field
   * set: per event type, consumed ∪ dropped ∪ {type} == that type's flattened
   * schema fields, with no overlap and no phantom entries (D3-c drift-guard
   * rider; RR-DECISIONS-20261030 §3.6). Field paths are dotted and resolved
   * through the schema's $defs (page.declare nests id/logicalRef, other
   * page-carrying types are flat pageId). Sub-object fields are declared one
   * level at a time, exactly as the projection reads them. */
  schema: "spec/rfc-0.1/x-cabi.schema-v0.1.json",
  note:
    "one-way lossy projection: consumed fields are mapped below; every other schema field is declared dropped with a reason — two lists per type, nothing silent",
  globalDropped: {
    ts: "R4 clock: OTLP times are omitted by design (mapping note §4) so the projection stays deterministic and v0 corpus traces carry none; the stamp stays in the JSONL source of truth",
  },
  events: {
    "session.open": {
      consumed: {
        agentId: "root span name + gen_ai.agent.name",
        model: "gen_ai.request.model",
        provider: "gen_ai.provider.name",
        budgetTokens: "ctxvm.budget.tokens (only when the trace carries it)",
        tokenizerId: "ctxvm.trace.tokenizer (default apx4-char)",
      },
      dropped: {
        schemaVersion: "version boundary belongs to the JSONL source of truth",
        environmentId: "W14 stream key is not in the audited attribute set",
      },
    },
    "page.declare": {
      consumed: {
        "page.id.logicalRef": "tool span name + span identity + page identity",
        "page.id.contentHash": "ctxvm.page.content_hash",
        "page.kind": "span fallback name (page.<kind>) + ctxvm.page.kind",
        "page.tokens": "ctxvm.page.tokens",
      },
      dropped: {
        turn: "R5: tool spans hang off the root and name their first RENDERING turn (derived), not the declare-side stamp (mapping note §4.3)",
        latencyMs: "no declare-side latency in the audited mapping",
        toolEffect: "W15 side-effect class stays a wire fact; no OTel attribute in the audited mapping",
      },
    },
    "page.render": {
      consumed: {
        turn: "parent turn span",
        "page.logicalRef": "event identity + first_rendered_turn key",
        mode: "ctxvm.render.mode",
      },
      dropped: {
        "page.contentHash": "after the first hash-bearing event the projection keys on logicalRef",
      },
    },
    "page.evict": {
      consumed: {
        turn: "parent turn span",
        "page.logicalRef": "event identity",
        stubText: "length only, as ctxvm.evict.stub_chars — the stub body stays in the source of truth",
      },
      dropped: {
        "page.contentHash": "after the first hash-bearing event the projection keys on logicalRef",
      },
    },
    "page.fault": {
      consumed: {
        turn: "parent turn span",
        "page.logicalRef": "event identity",
        source: "ctxvm.fault.source",
      },
      dropped: {
        latencyMs: "no fault-time latency in the audited mapping",
        "page.contentHash": "after the first hash-bearing event the projection keys on logicalRef",
      },
    },
    "page.pin": {
      consumed: {
        "page.logicalRef": "event identity",
        reason: "ctxvm.pin.reason (default empty string)",
      },
      dropped: {
        "page.contentHash": "after the first hash-bearing event the projection keys on logicalRef",
      },
    },
    "page.unpin": {
      consumed: {
        "page.logicalRef": "event identity",
        reason: "ctxvm.pin.reason (default empty string)",
      },
      dropped: {
        "page.contentHash": "after the first hash-bearing event the projection keys on logicalRef",
      },
    },
    "turn.render": {
      consumed: {
        turn: "span identity + ctxvm.turn",
        residentTokens: "ctxvm.resident_tokens (declared page table, not usage)",
        evictedTokens: "ctxvm.evicted_tokens ?? 0",
        headroom: "ctxvm.headroom_tokens (when the trace carries it)",
      },
      dropped: {
        "prefix.toolSchemas": "W13 static prefix cost stays a wire fact; no OTel attribute in the audited mapping",
        "prefix.messageCount": "W13 static prefix cost stays a wire fact; no OTel attribute in the audited mapping",
        "prefix.requestChars": "W13 static prefix cost stays a wire fact; no OTel attribute in the audited mapping",
        "prefix.systemPromptBytes": "W13 static prefix cost stays a wire fact; no OTel attribute in the audited mapping",
        "prefix.approxInputTokens": "W13 static prefix cost stays a wire fact; no OTel attribute in the audited mapping",
        "prefix.source": "W13 static prefix cost stays a wire fact; no OTel attribute in the audited mapping",
      },
    },
    "call.meta": {
      consumed: {
        turn: "parent turn span",
        "cacheEstimate.estHitTokens": "gen_ai.usage.cache_read.input_tokens or ctxvm.cache.est_hit_tokens, keyed on providerReported",
        "cacheEstimate.estMissTokens": "gen_ai.usage.input_tokens or ctxvm.cache.est_miss_tokens, keyed on providerReported",
        "cacheEstimate.providerReported": "branch key of the cache gate (D12: est* keep page-table semantics)",
        latencyMs: "ctxvm.call.latency_ms (when the trace carries it)",
      },
      dropped: {
        provider: "the session.open provider name is authoritative for the span",
        "providerUsage.inputTokens": "R3 provider receipt stays out of the projection (D12: the W6 OTel gate is untouched; the est→truth decision lives in the W8 capture design)",
        "providerUsage.outputTokens": "R3 provider receipt stays out of the projection (D12: the W6 OTel gate is untouched; the est→truth decision lives in the W8 capture design)",
        "providerUsage.cachedInputTokens": "R3 provider receipt stays out of the projection (D12: the W6 OTel gate is untouched; the est→truth decision lives in the W8 capture design)",
      },
    },
  },
}

const hex = (s, n) => createHash("sha256").update(s).digest("hex").slice(0, n)

const str = (key, v) => ({ key, value: { stringValue: String(v) } })
const int = (key, v) => ({ key, value: { intValue: String(v) } })
const bool = (key, v) => ({ key, value: { boolValue: Boolean(v) } })

export function parseArgs(argv) {
  const out = { file: null, conversation: null, service: "ctxvm" }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === "--conversation") out.conversation = argv[++i]
    else if (a === "--service") out.service = argv[++i]
    else if (a === "-h" || a === "--help") {
      process.stderr.write("usage: otel-export.mjs <trace.jsonl> [--conversation ID] [--service NAME]\n")
      process.exit(2)
    } else if (a.startsWith("--")) {
      process.stderr.write(`unknown flag: ${a}\n`)
      process.exit(2)
    } else out.file = a
  }
  if (!out.file) {
    process.stderr.write("usage: otel-export.mjs <trace.jsonl> [--conversation ID] [--service NAME]\n")
    process.exit(2)
  }
  return out
}

export function readTrace(file) {
  return readFileSync(file, "utf8")
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line))
}

export function project(events, opts) {
  const open = events.find((e) => e.type === "session.open") || {}
  const model = open.model || "unknown"
  const agentId = open.agentId || "unknown"
  const conversationId = opts.conversation || basename(opts.file, ".jsonl")
  const traceId = hex(conversationId, 32)
  const rootSpanId = hex(`${conversationId}:root`, 16)

  // Per-turn buckets. `turn.render` is the only event that defines a turn;
  // faults/renders/evicts carry a turn index; page.declare carries none.
  const turns = new Map()
  const ensureTurn = (t) => {
    if (!turns.has(t)) turns.set(t, { renders: [], faults: [], evicts: [], pins: [], meta: null })
    return turns.get(t)
  }
  const pages = []
  for (const e of events) {
    if (e.type === "page.declare") pages.push(e.page)
    else if (e.type === "turn.render") ensureTurn(e.turn).turn = e
    else if (e.type === "call.meta") ensureTurn(e.turn).meta = e
    else if (e.type === "page.render") ensureTurn(e.turn).renders.push(e)
    else if (e.type === "page.fault") ensureTurn(e.turn).faults.push(e)
    else if (e.type === "page.evict") ensureTurn(e.turn).evicts.push(e)
    else if (e.type === "page.pin" || e.type === "page.unpin") ensureTurn(e.turn ?? 0).pins.push(e)
  }

  const event = (name, attrs) => ({ name, attributes: attrs })

  const rootSpan = {
    traceId,
    spanId: rootSpanId,
    name: `invoke_agent ${agentId}`,
    kind: KIND_INTERNAL,
    attributes: [
      str("gen_ai.operation.name", "invoke_agent"),
      str("gen_ai.agent.name", agentId),
      str("gen_ai.conversation.id", conversationId),
      str("gen_ai.request.model", model),
      str("gen_ai.provider.name", open.provider || "unknown"),
      str("ctxvm.trace.xcabi_version", "0"),
      str("ctxvm.trace.tokenizer", open.tokenizerId || "apx4-char"),
      int("ctxvm.trace.pages", pages.length),
    ],
    events: [],
  }
  if (open.budgetTokens != null) {
    rootSpan.attributes.push(int("ctxvm.budget.tokens", open.budgetTokens))
  }

  const spans = [rootSpan]
  for (const t of [...turns.keys()].sort((a, b) => a - b)) {
    const bucket = turns.get(t)
    const render = bucket.turn
    const span = {
      traceId,
      spanId: hex(`${conversationId}:turn:${t}`, 16),
      parentSpanId: rootSpanId,
      name: `chat ${model}`,
      kind: KIND_CLIENT,
      attributes: [
        str("gen_ai.operation.name", "chat"),
        str("gen_ai.request.model", model),
        int("ctxvm.turn", t),
      ],
      events: [],
    }
    if (render) {
      span.attributes.push(int("ctxvm.resident_tokens", render.residentTokens))
      span.attributes.push(int("ctxvm.evicted_tokens", render.evictedTokens ?? 0))
      if (render.headroom != null) span.attributes.push(int("ctxvm.headroom_tokens", render.headroom))
    }
    // Provider usage is only ever filled when the emitter recorded it as
    // provider-reported; the v0 emitters never do (W3 prices.json law).
    const est = bucket.meta && bucket.meta.cacheEstimate
    if (est) {
      const key = est.providerReported ? "gen_ai.usage.cache_read.input_tokens" : "ctxvm.cache.est_hit_tokens"
      span.attributes.push(int(key, est.estHitTokens))
      span.attributes.push(
        int(est.providerReported ? "gen_ai.usage.input_tokens" : "ctxvm.cache.est_miss_tokens", est.estMissTokens),
      )
      span.attributes.push(bool("ctxvm.cache.provider_reported", Boolean(est.providerReported)))
    }
    if (bucket.meta && bucket.meta.latencyMs != null) {
      span.attributes.push(int("ctxvm.call.latency_ms", bucket.meta.latencyMs))
    }

    for (const r of bucket.renders) {
      span.events.push(
        event("ctxvm.page.render", [str("ctxvm.page.ref", r.page.logicalRef), str("ctxvm.render.mode", r.mode)]),
      )
    }
    for (const f of bucket.faults) {
      span.events.push(
        event("ctxvm.page.fault", [
          str("ctxvm.page.ref", f.page.logicalRef),
          str("ctxvm.fault.source", f.source),
        ]),
      )
    }
    for (const v of bucket.evicts) {
      const attrs = [str("ctxvm.page.ref", v.page.logicalRef)]
      if (v.stubText) attrs.push(str("ctxvm.evict.stub_chars", String(v.stubText.length)))
      span.events.push(event("ctxvm.page.evict", attrs))
    }
    for (const p of bucket.pins) {
      span.events.push(
        event(p.type === "page.pin" ? "ctxvm.page.pin" : "ctxvm.page.unpin", [
          str("ctxvm.page.ref", p.page.logicalRef),
          str("ctxvm.pin.reason", p.reason || ""),
        ]),
      )
    }
    spans.push(span)
  }

  // Tool spans: page.declare carries no turn (mapping note §4.3), so
  // they hang off the root and name their first rendering turn when one exists.
  const firstRenderTurn = new Map()
  for (const t of [...turns.keys()].sort((a, b) => a - b)) {
    for (const r of turns.get(t).renders) {
      if (!firstRenderTurn.has(r.page.logicalRef)) firstRenderTurn.set(r.page.logicalRef, t)
    }
  }
  for (const p of pages) {
    const ref = p.id.logicalRef
    const toolName = ref.startsWith("tool:") ? ref.slice(5).split("(")[0] : `page.${p.kind}`
    const attrs = [
      str("gen_ai.operation.name", "execute_tool"),
      str("gen_ai.tool.name", toolName),
      str("ctxvm.page.ref", ref),
      str("ctxvm.page.content_hash", p.id.contentHash),
      str("ctxvm.page.kind", p.kind),
      int("ctxvm.page.tokens", p.tokens),
    ]
    if (firstRenderTurn.has(ref)) attrs.push(int("ctxvm.page.first_rendered_turn", firstRenderTurn.get(ref)))
    spans.push({
      traceId,
      spanId: hex(`${conversationId}:page:${ref}`, 16),
      parentSpanId: rootSpanId,
      name: `execute_tool ${toolName}`,
      kind: KIND_INTERNAL,
      attributes: attrs,
      events: [],
    })
  }

  return {
    resourceSpans: [
      {
        resource: {
          attributes: [
            str("service.name", opts.service),
            str("ctxvm.export.schema", "otlp-json/1.11.1"),
            str("ctxvm.export.version", "0.1.0-prototype"),
          ],
        },
        scopeSpans: [
          {
            scope: { name: "ctxvm.otel-export", version: "0.1.0-prototype" },
            spans,
          },
        ],
      },
    ],
  }
}

// CLI runs only when executed directly; importing (the drift-guard tests) never
// executes the CLI path, so `node --test tools/otel-export.test.mjs` is safe.
const here = import.meta.url
const invoked = process.argv[1] ? pathToFileURL(process.argv[1]).href : null
if (here === invoked) {
  const opts = parseArgs(process.argv.slice(2))
  const events = readTrace(opts.file)
  process.stdout.write(JSON.stringify(project(events, opts), null, 2) + "\n")
}
