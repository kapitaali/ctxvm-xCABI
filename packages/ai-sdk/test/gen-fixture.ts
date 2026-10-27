/**
 * T15 B2 fixture driver — records the echo/thrash session exactly as the
 * design/adapters.md §B test strategy prescribes: drive `streamText` with the
 * SDK's mock language model, record the resulting app-level fullStream
 * orderings as fixtures.
 *
 * CANON MOCK RECIPE (proven live at ai 7.0.154; each rule cost real debugging
 * to find — deviating from ANY of them yields silent misshapes):
 *   1. v7 `streamText` tool loops need `stopWhen: stepCountIs(N)` — the default
 *      loop budget is ONE step (no tool results ever surface).
 *   2. Mock `finish` parts need `finishReason` as an OBJECT `{ unified, raw }` —
 *      a bare string yields finishReason 'other' and the tool never executes.
 *   3. Text needs the `text-start`/`text-delta`/`text-end` fence trio — deltas
 *      without fences abort the text part upstream (`error` part "text part
 *      tN not found"); the pass-through is honest, never a page.
 *   4. Tool calls stream as the `tool-input-start`/`-delta`/`-end` trio plus
 *      the terminal `tool-call` part (JSON-encoded input).
 *   5. App-layer rename (B0 erratum 3): fullStream `text-delta` carries `text`.
 *   6. App-layer `finish-step` carries `performance` timings + `response`
 *      runtime metadata — wall-clock carriers; canonical fixtures strip them
 *      (m2 law), the adapter passes them through untouched.
 *
 * Deterministic by construction: explicit part ids/call ids, fixed usage
 * numbers, stripped wall-clock telemetry. Byte-stable across runs (verified:
 * double-run sha256 equal for both fixtures).
 *
 * Outputs:
 *   fixtures/echo-thrash.parts.json  — recorded app-level part sequence
 *   fixtures/echo-thrash.trace.jsonl — the @ctxvm/node trace generated from it
 *
 * Run: npm run gen (node test/gen-fixture.ts)
 */

// freshTmp law (m7 gate-2 regression, RR-UM7CAPTURE): quarantine leaked
// CTXVM_* keys BEFORE anything arms a capture.
for (const key of Object.keys(process.env)) {
  if (key.startsWith("CTXVM_")) delete process.env[key];
}

import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";

// The driver exercises the REAL env law end to end: arm with a throwaway dir
// (sidecar + witness land there and stay out of git); the committed fixture
// comes from the in-memory FinishedTrace, not the tmp files.
process.env.CTXVM_TRACE_DIR = mkdtempSync(join(tmpdir(), "ctxvm-ai-sdk-gen-"));
process.env.CTXVM_TRACE_NAME = "echo-thrash";

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { jsonSchema, simulateReadableStream, stepCountIs, streamText, tool, wrapLanguageModel } from "ai";
import { MockLanguageModelV4 } from "ai/test";
import type { LanguageModelV4StreamPart } from "@ai-sdk/provider";

import { createCtxvmCapture } from "../src/index.ts";

const here = fileURLToPath(new URL(".", import.meta.url));
const fixtures = join(here, "..", "fixtures");

/** Fixed usage: defined fields only, deterministic bytes. */
const usage = {
  inputTokens: { total: 10, noCache: 10, cacheRead: 0, cacheWrite: 0 },
  outputTokens: { total: 5, text: 5, reasoning: 0 },
};

const streamOf = (chunks: LanguageModelV4StreamPart[]) => ({
  stream: simulateReadableStream({ chunks }),
});

// Echo + thrash in the m2 shape: two identical tool calls (the repeat trips
// the tool_recall fault through the T6 §4 matrix), then terminal text.
const model = new MockLanguageModelV4({
  provider: "ctxvm-mock",
  modelId: "echo-model",
  doStream: [
    streamOf([
      { type: "text-start", id: "t1" },
      { type: "text-delta", id: "t1", delta: "Echo reply for " },
      { type: "text-end", id: "t1" },
      { type: "tool-input-start", id: "call-1", toolName: "echo", inputEncoding: "json" },
      { type: "tool-input-delta", id: "call-1", delta: JSON.stringify({ message: "hello" }) },
      { type: "tool-input-end", id: "call-1" },
      { type: "tool-call", toolCallId: "call-1", toolName: "echo", input: JSON.stringify({ message: "hello" }) },
      { type: "finish", finishReason: { unified: "tool-calls", raw: undefined }, usage },
    ]),
    streamOf([
      { type: "tool-input-start", id: "call-2", toolName: "echo", inputEncoding: "json" },
      { type: "tool-input-delta", id: "call-2", delta: JSON.stringify({ message: "hello" }) },
      { type: "tool-input-end", id: "call-2" },
      { type: "tool-call", toolCallId: "call-2", toolName: "echo", input: JSON.stringify({ message: "hello" }) },
      { type: "finish", finishReason: { unified: "tool-calls", raw: undefined }, usage },
    ]),
    streamOf([
      { type: "text-start", id: "t2" },
      { type: "text-delta", id: "t2", delta: "done" },
      { type: "text-end", id: "t2" },
      { type: "finish", finishReason: { unified: "stop", raw: undefined }, usage },
    ]),
  ],
});

const echoTool = tool({
  description: "echoes its input",
  inputSchema: jsonSchema<{ message: string }>({
    type: "object",
    properties: { message: { type: "string" } },
    required: ["message"],
    additionalProperties: false,
  }),
  execute: async ({ message }) => ({ echo: message }),
});

const capture = createCtxvmCapture({
  agentId: "ctxvm-ai-sdk",
  model: "ctxvm-mock/echo-model",
  provider: "ctxvm-mock",
  budgetTokens: 120000,
});

const result = streamText({
  model: wrapLanguageModel({ model, middleware: capture.middleware }),
  tools: { echo: echoTool },
  prompt: "Echo 'hello' twice, then say done.",
  stopWhen: stepCountIs(10),
});

// Mirror pass-over: record every app-level part EXACTLY as yielded.
const recorded: object[] = [];
for await (const part of capture.tap(result.fullStream)) {
  recorded.push(part);
}

// Canon-fixture normalization (m2 law: byte-deterministic, no wall-clock). The
// adapter itself passes `finish-step`'s `performance` telemetry and the runtime
// `response` metadata (generated id + timestamp) through UNTOUCHED — this strip
// is the recording policy only, so the committed fixture replays byte-stably.
// (Verified: the tracer never maps these fields; the trace fixture is already
// byte-stable across runs.)
const normalized = recorded.map((part) => {
  const p = part as Record<string, unknown>;
  if (!("performance" in p) && !("response" in p)) return part;
  const copy = { ...p };
  delete copy.performance;
  delete copy.response;
  return copy;
});
recorded.length = 0;
recorded.push(...normalized);

const finished = capture.finishAll();
if (finished.length !== 1) throw new Error(`expected 1 finished trace, got ${finished.length}`);

mkdirSync(fixtures, { recursive: true });
writeFileSync(join(fixtures, "echo-thrash.parts.json"), `${JSON.stringify(recorded, null, 2)}\n`);
writeFileSync(join(fixtures, "echo-thrash.trace.jsonl"), finished[0]!.trace.jsonl);

console.log(`recorded ${recorded.length} parts; trace events: ${finished[0].trace.events.length}`);
console.log(`stats: ${JSON.stringify(finished[0].trace.stats)}`);
