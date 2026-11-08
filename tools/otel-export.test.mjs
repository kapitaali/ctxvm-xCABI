/**
 * tools/otel-export.test.mjs — the D3-c drift guard for the promoted OTLP/JSON
 * projection (RR-DECISIONS-20261030 §3.6; D3-c decided "layered": JSONL stays
 * canonical, the exporter is a declared lossy projection; card
 * reports/RR-D3COTEL-20261108.md).
 *
 * Four properties, all mechanical, no network, no deps:
 *
 * 1. SYNC — EXPORT_SPEC's consumed/dropped tables exactly cover the RFC-0.1
 *    schema's field set per event type (dotted paths, $defs resolved). When an
 *    additive RFC-0.1 field lands, this test goes red until the projection
 *    declares the field consumed or dropped — nothing silent.
 * 2. GOLDEN — the projection of five frozen byte-inputs equals the committed
 *    golden bytes (tools/fixtures/otel/). A mapping change trips here.
 * 3. STRUCTURE — the OTLP/JSON encoding rules the prototype was audited
 *    against design/otel-mapping.md §6 (no *TimeUnixNano anywhere, integer
 *    `kind`, decimal-string `intValue`, hex ids, per-file span counts).
 * 4. DETERMINISM + CLI — repeat calls are byte-identical, and the CLI path
 *    emits exactly the same bytes the module does; an unknown flag exits 2.
 */
import test from "node:test"
import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { execFileSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import { join } from "node:path"

import { EXPORT_SPEC, project, readTrace } from "./otel-export.mjs"

const repo = (p) => fileURLToPath(new URL("../" + p, import.meta.url))
const schemaPath = repo(EXPORT_SPEC.schema)
const schema = JSON.parse(readFileSync(schemaPath, "utf8"))

// --- flatten the per-type field set: dotted paths, $defs resolved to leaves ---
const resolveField = (def, prefix, out) => {
  if (def.$ref) {
    resolveField(schema.$defs[def.$ref.split("/").pop()], prefix, out)
    return
  }
  if (def.type === "object" && def.properties) {
    for (const [name, sub] of Object.entries(def.properties)) {
      resolveField(sub, `${prefix}.${name}`, out)
    }
    return
  }
  out.add(prefix) // leaf (string/integer/boolean/enum/leaf $ref chain)
}

const schemaTypes = new Map() // "session.open" -> Set<dotted field paths>
for (const branch of schema.oneOf) {
  const typeName = branch.properties.type.const
  const fields = new Set()
  resolveField(branch.properties.type, "type", fields)
  for (const [name, def] of Object.entries(branch.properties)) {
    if (name === "type") continue
    resolveField(def, name, fields)
  }
  schemaTypes.set(typeName, fields)
}

function declared(typeName) {
  const ev = EXPORT_SPEC.events[typeName]
  assert.ok(ev, `EXPORT_SPEC must declare event type ${typeName}`)
  const consumed = new Set(Object.keys(ev.consumed ?? {}))
  const dropped = new Set(Object.keys(ev.dropped ?? {}))
  for (const g of Object.keys(EXPORT_SPEC.globalDropped ?? {})) dropped.add(g)
  for (const name of schemaTypes.get(typeName)) {
    const top = name.split(".")[0]
    if (top === "type") continue // the routing key is consumed by the bucket loop
    if (!consumed.has(name) && !dropped.has(name)) {
      return `undeclared field ${typeName}.${name}`
    }
  }
  return null
}

const GLOBES = [
  { trace: "corpus/m1/session-thrashing.jsonl", opts: { conversation: "m1-thrash", service: "ctxvm" }, golden: "tools/fixtures/otel/m1-session-thrashing.otlp.json", spans: 13 },
  { trace: "corpus/m6/opencode-pause-session-a.jsonl", opts: null, golden: "tools/fixtures/otel/m6-opencode-pause-a.otlp.json", spans: 14 },
  { trace: "corpus/m7/hermes-pause-session-a.jsonl", opts: null, golden: "tools/fixtures/otel/m7-hermes-pause-a.otlp.json", spans: 17 },
  { trace: "corpus/m8/live-thrash.jsonl", opts: null, golden: "tools/fixtures/otel/m8-live-thrash.otlp.json", spans: 10 },
  { trace: "packages/ai-sdk/fixtures/echo-thrash.trace.jsonl", opts: null, golden: "tools/fixtures/otel/ai-sdk-echo-thrash.otlp.json", spans: 5 },
]

const projected = (g) => {
  const events = readTrace(repo(g.trace))
  const opts = { file: repo(g.trace), conversation: g.opts?.conversation ?? null, service: "ctxvm" }
  return JSON.stringify(project(events, opts), null, 2) + "\n"
}

test("SYNC: EXPORT_SPEC covers the RFC-0.1 field set exactly, nothing silent", () => {
  // the exporter declares exactly the schema's event types
  assert.deepEqual(
    [...Object.keys(EXPORT_SPEC.events)].sort(),
    [...schemaTypes.keys()].sort(),
    "EXPORT_SPEC.events and the schema oneOf must name the same event types",
  )
  for (const typeName of schemaTypes.keys()) {
    const missing = declared(typeName)
    assert.equal(missing, null, missing ?? "")
    const ev = EXPORT_SPEC.events[typeName]
    const schemaFields = schemaTypes.get(typeName)
    const consumed = new Set(Object.keys(ev.consumed))
    const dropped = new Set(Object.keys(ev.dropped))
    for (const name of [...consumed, ...dropped]) {
      assert.ok(
        schemaFields.has(name),
        `phantom declaration ${typeName}.${name} is not a schema field`,
      )
    }
    for (const name of consumed) assert.equal(dropped.has(name), false, `${typeName}.${name} both consumed and dropped`)
    for (const [k, v] of [...Object.entries(ev.consumed), ...Object.entries(ev.dropped)]) {
      assert.equal(typeof v, "string", `${typeName}.${k} declaration must carry a reason`)
      assert.ok(v.length > 0, `${typeName}.${k} reason must be non-empty`)
    }
  }
  for (const [k, v] of Object.entries(EXPORT_SPEC.globalDropped)) {
    assert.equal(typeof v, "string", "global drop must carry a reason")
    assert.ok(v.length > 0, "global drop reason must be non-empty")
    for (const fields of schemaTypes.values()) {
      assert.ok(fields.has(k), `global dropped field ${k} must exist in the schema`)
    }
  }
})

test("GOLDEN: the projection of five frozen inputs is byte-stable", () => {
  for (const g of GLOBES) {
    const golden = readFileSync(repo(g.golden), "utf8")
    const fresh = projected(g)
    assert.equal(fresh, golden, `golden drift on ${g.golden}`)
  }
})

test("STRUCTURE: the OTLP/JSON encoding rules, as audited at design/otel-mapping.md §6", () => {
  for (const g of GLOBES) {
    const doc = JSON.parse(readFileSync(repo(g.golden), "utf8"))
    const raw = readFileSync(repo(g.golden), "utf8")
    const text = raw
    assert.ok(!text.includes("startTimeUnixNano") && !text.includes("endTimeUnixNano"), "no clock fields (§4 gap 1)")
    const scope = doc.resourceSpans[0].scopeSpans[0]
    const spans = scope.spans
    assert.equal(spans.length, g.spans, `span count for ${g.golden} (design doc §6 pins 13/14/17/10)`)
    for (const span of spans) {
      assert.match(span.traceId, /^[0-9a-f]{32}$/, "traceId: 32 hex chars, not base64")
      assert.match(span.spanId, /^[0-9a-f]{16}$/, "spanId: 16 hex chars")
      if (span.parentSpanId !== undefined) assert.match(span.parentSpanId, /^[0-9a-f]{16}$/)
      assert.equal(typeof span.kind, "number", "kind: integer (OTLP JSON forbids enum names)")
      assert.ok([1, 3].includes(span.kind), "kind is INTERNAL or CLIENT as mapped")
      for (const attr of span.attributes ?? []) {
        for (const [sub, val] of Object.entries(attr.value)) {
          if (sub === "intValue") assert.match(val, /^-?[0-9]+$/, "intValue: decimal string (64-bit rule)")
          else if (sub === "stringValue") assert.equal(typeof val, "string")
          else if (sub === "boolValue") assert.equal(typeof val, "boolean")
        }
      }
      for (const ev of span.events ?? []) {
        assert.ok(typeof ev.name === "string" && ev.name.length > 0)
        assert.ok(Array.isArray(ev.attributes))
      }
    }
  }
})

test("DETERMINISM + CLI: repeated projection and the CLI path agree byte-for-byte", () => {
  const g = GLOBES[0]
  const once = projected(g)
  const twice = projected(g)
  assert.equal(once, twice, "repeat calls are byte-identical")
  const golden = readFileSync(repo(g.golden), "utf8")
  const out = execFileSync("node", [repo("tools/otel-export.mjs"), repo(g.trace), "--conversation", "m1-thrash"], {
    encoding: "utf8",
  })
  assert.equal(out, golden, "the CLI emits exactly the golden bytes")
  try {
    execFileSync("node", [repo("tools/otel-export.mjs"), "--not-a-flag"], { encoding: "utf8", stdio: "pipe" })
    assert.fail("unknown flag must exit non-zero")
  } catch (err) {
    assert.equal(err.status, 2, "unknown flag exits 2")
  }
})
