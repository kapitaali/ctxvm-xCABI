/**
 * T8 unit tests — `@ctxvm/node` v0 tracer, run by `node --test` (Node ≥22.6 type stripping).
 */

import assert from "node:assert/strict";
import { test } from "node:test";

import { canonicalJson, contentHash, toolRef } from "../src/ident.ts";
import { createTrace, type FinishedTrace } from "../src/tracer.ts";

const INIT = {
  agentId: "opencode",
  model: "openai/gpt-5",
  provider: "openai",
  budgetTokens: 120000,
};

/** Healthy flow, structured exactly like benchmarks/metrics/fixtures/session-healthy.jsonl. */
function runHealthy(): FinishedTrace {
  const vm = createTrace(INIT);
  vm.page({ ref: "file:src/auth.ts", kind: "file", content: "export const S = 1;\n" });
  vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: "SESSION = configured\n" });
  vm.page({ ref: "summary:t0", kind: "summary", content: "turn-0 micro-summary" });
  vm.render();
  vm.render();
  vm.render();
  vm.scan({ text: "opening src/auth/session.ts to verify the change", latencyMs: 12 });
  vm.render({ latencyMs: 1240 });
  return vm.finish();
}

type List = Record<string, unknown>[];

const of = (events: readonly object[], type: string): List =>
  events.filter((e) => (e as Record<string, unknown>).type === type) as List;

test("finish() idempotent (T17.7 parity): tail computed per call, never appended", () => {
  // Mirror of the hermes TracerTests idempotency pin (landed same card —
  // plugin.py's finish docstring was never test-enforced before): repeated
  // flushes produce the same JSONL; lifecycle recorded after a first flush
  // joins the next transcript exactly once with a regenerated tail.
  const vm = createTrace(INIT);
  vm.page({ ref: "file:src/a.ts", kind: "file", content: "A" });
  vm.render();
  vm.render({ latencyMs: 100 });
  const first = vm.finish();
  const again = vm.finish();
  assert.equal(again.jsonl, first.jsonl);
  // Mid-session flush continues: new lifecycle, then the second finish.
  vm.page({ ref: "file:src/b.ts", kind: "file", content: "B" });
  vm.render({ latencyMs: 200 });
  const second = vm.finish();
  assert.deepEqual(
    of(second.events, "turn.render").map((e) => e.turn),
    [0, 1, 2],
  );
  assert.equal(of(second.events, "call.meta").length, 3);
  assert.equal(of(second.events, "page.declare").length, 2);
  // The first flushed transcript was never mutated by the later flush.
  assert.deepEqual(
    of(first.events, "turn.render").map((e) => e.turn),
    [0, 1],
  );
  assert.equal(of(first.events, "page.declare").length, 1);
});

test("event types + field order match the RFC-0 §6 payload shapes", () => {
  const { events } = runHealthy();
  assert.equal((events[0] as List[number]).type, "session.open");
  assert.equal(
    Object.keys(events[0]).join(","),
    "type,agentId,model,provider,budgetTokens,tokenizerId",
  );
  const declare = of(events, "page.declare")[0];
  assert.equal(Object.keys(declare.page as object).join(","), "id,kind,tokens"); // spec table order
  const tr = of(events, "turn.render");
  assert.deepEqual(tr.map((e) => e.turn), [0, 1, 2, 3]);
  assert.equal(tr[0].evictedTokens, 0); // mirror: nothing evicted
  assert.equal(tr[0].headroom, INIT.budgetTokens - Number(tr[0].residentTokens));
  const f = of(events, "page.fault")[0];
  assert.equal(f.source, "identifier_scan");
  assert.equal(f.turn, 2); // fault@t, effect scope is turn t (RFC-0 §5)
  assert.equal(f.latencyMs, 12);
  const cm = of(events, "call.meta");
  assert.equal(cm.length, 4);
  assert.equal(cm[3].turn, 3);
  const cache = cm[3].cacheEstimate as Record<string, unknown>;
  assert.equal(cache.providerReported, false);
  const order = events.map((e) => (e as { type: string }).type);
  assert.ok(
    order.lastIndexOf("turn.render") < order.indexOf("call.meta"),
    "turn.render facts flush before call.meta facts",
  );
});

test("resident render sums match declared pages", () => {
  const { events, stats } = runHealthy();
  const tr0 = of(events, "turn.render")[0];
  const sum = of(events, "page.declare").reduce((acc, e) => acc + Number((e.page as { tokens: number }).tokens), 0);
  assert.equal(tr0.residentTokens, sum);
  assert.ok(stats.pages === 3 && stats.turns === 4 && stats.faults === 1);
});

test("late-declared pages join the derived composition from turn 0 (tally_at parity)", () => {
  const vm = createTrace(INIT);
  vm.page({ ref: "file:a.ts", kind: "file", content: "0".repeat(40) }); // 10 tokens
  vm.render(); // turn 0: only A revealed so far
  vm.page({ ref: "file:b.ts", kind: "file", content: "1".repeat(40) }); // declared mid-stream
  vm.render(); // turn 1: B revealed
  const { events, stats } = vm.finish();
  const tr = of(events, "turn.render");
  // whole-table sum at BOTH turns — replay derives resident tokens statically, a page
  // declared at any stream point counts from turn 0 (ctxvm-core `tally_at`)
  assert.deepEqual(tr.map((e) => e.residentTokens), [20, 20]);
  assert.deepEqual(tr.map((e) => e.turn), [0, 1]);
  assert.equal(stats.pages, 2);
});

test("tool_recall resident re-call → page.fault row, state untouched (T6 §4)", () => {
  const vm = createTrace(INIT);
  vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: "A" });
  vm.render();
  vm.recall({ tool: "read_file", args: { path: "src/auth/session.ts" } });
  const landing = vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: "A" });
  vm.render();
  const { events } = vm.finish();
  const faults = of(events, "page.fault");
  assert.deepEqual(faults.map((e) => [e.source, e.turn]), [["tool_recall", 0]]);
  assert.equal(faults[0].page.contentHash, landing.contentHash);
  // no mode flips beyond the t0 reveal — re-call of a resident page changed nothing
  assert.deepEqual(of(events, "page.render").map((e) => e.mode), ["full"]);
});

test("recall landing before any render clamps to turn 0 (schema: turn I≥0)", () => {
  const vm = createTrace(INIT);
  vm.page({ tool: "read_file", args: { path: "a.ts" }, content: "hello" });
  vm.recall({ tool: "read_file", args: { path: "a.ts" } });
  vm.page({ tool: "read_file", args: { path: "a.ts" }, content: "hello" }); // same-hash landing, no render yet
  const { events } = vm.finish();
  assert.equal(of(events, "page.fault")[0].turn, 0);
});

test("fresh fetch (same ref, new contentHash) → new declare, never scored as waste (T6 §4)", () => {
  const vm = createTrace(INIT);
  vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: "v1" });
  vm.render();
  vm.recall({ tool: "read_file", args: { path: "src/auth/session.ts" } });
  const fresh = vm.page({
    tool: "read_file",
    args: { path: "src/auth/session.ts" },
    content: "v2 (resource changed)",
  });
  vm.render();
  const { events } = vm.finish();
  const declares = of(events, "page.declare");
  assert.equal(declares.length, 2);
  assert.equal((declares[1].page as { id: { contentHash: string } }).id.contentHash, fresh.contentHash);
  assert.equal(of(events, "page.fault").length, 0);
  const reveal = of(events, "page.render").filter((e) => e.turn === 1);
  assert.deepEqual(reveal.map((e) => e.mode), ["full"]);
  assert.equal(reveal[0].page.contentHash, fresh.contentHash);
});

test("canonicalArgs: key order is irrelevant to identity; ref is stable + readable", () => {
  const a = toolRef(undefined, "read_file", { path: "src/a.ts", mode: "r" });
  const b = toolRef(undefined, "read_file", { mode: "r", path: "src/a.ts" });
  assert.equal(a, b);
  assert.equal(a, 'tool:read_file({"mode":"r","path":"src/a.ts"})');
});

test(">120-char args truncate deterministically with a #sha suffix (T6 §2)", () => {
  const payload = { blob: "x".repeat(400) };
  const r1 = toolRef("github", "create_issue", payload);
  const r2 = toolRef("github", "create_issue", payload);
  assert.equal(r1, r2);
  assert.ok(r1.startsWith("tool:github.create_issue("));
  assert.ok(r1.length < 200);
  const different = toolRef("github", "create_issue", { blob: "_".repeat(400) });
  assert.notEqual(r1, different);
});

test("identifier_scan is deduped per page per source (T3 v0 touch proxy)", () => {
  const vm = createTrace(INIT);
  vm.page({ ref: "file:src/auth/session.ts", kind: "file", content: "s" });
  vm.render();
  vm.scan({ text: "mentions src/auth/session.ts twice: src/auth/session.ts" });
  vm.scan({ text: "mentions src/auth/session.ts again" });
  vm.render();
  const { events } = vm.finish();
  assert.equal(of(events, "page.fault").length, 1);
});

test("determinism: identical sessions → byte-identical JSONL", () => {
  assert.equal(runHealthy().jsonl, runHealthy().jsonl);
});

test("contentHash form is sha256:<8 hex>; canonicalJson sorts keys recursively", () => {
  assert.match(contentHash("anything"), /^sha256:[0-9a-f]{8}$/);
  assert.equal(canonicalJson({ b: 1, a: [2, { d: 1, c: 2 }] }), '{"a":[2,{"c":2,"d":1}],"b":1}');
});

test("session.open is the first line; JSONL is newline-terminated; every line parses", () => {
  const { jsonl } = runHealthy();
  const first = JSON.parse(jsonl.split("\n")[0] as string) as { type: string };
  assert.equal(first.type, "session.open");
  assert.ok(jsonl.endsWith("\n"));
  for (const line of jsonl.trim().split("\n")) JSON.parse(line);
});
