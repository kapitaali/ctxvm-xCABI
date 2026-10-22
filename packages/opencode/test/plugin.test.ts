/** T9 glue tests — plugin wiring is exercised by replaying recorded hook payloads. */

import assert from "node:assert/strict";
import { test } from "node:test";

import { contentToPageBody, createCtxvmPlugin } from "../src/plugin.ts";
import type { HookEvent } from "../src/opencode-contract.ts";
import { loadEchoFixture, replayHooks } from "./replay-registry.ts";

const INIT = {
  agentId: "opencode",
  model: "anthropic/claude-sonnet-4-5",
  provider: "anthropic",
  budgetTokens: 200_000,
};

type List = Record<string, unknown>[];
const of = (events: readonly object[], type: string): List =>
  events.filter((e) => (e as Record<string, unknown>).type === type) as List;

interface Run {
  jsonl: string;
  events: Record<string, unknown>[];
  hooks: HookEvent[];
}

function runOnce(): Run {
  const hooks = loadEchoFixture();
  const plugin = createCtxvmPlugin(INIT);
  replayHooks(plugin, hooks);
  const [record] = plugin.finishAll();
  const events = record.trace.jsonl
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as Record<string, unknown>);
  return { jsonl: record.trace.jsonl, events, hooks };
}

test("one echoed session replays to the expected event shape (17 events)", () => {
  const run = runOnce();
  assert.equal(of(run.events, "session.open").length, 1);
  assert.equal(of(run.events, "page.declare").length, 2); // A-v1 + fresh A-v2
  assert.equal(of(run.events, "page.fault").length, 2); // identifier_scan + tool_recall
  assert.equal(of(run.events, "page.render").length, 2); // reveal@1 + reveal@3
  assert.equal(of(run.events, "turn.render").length, 5); // turns 0..4 (5 session.context fires)
  assert.equal(of(run.events, "call.meta").length, 5);
  assert.equal(run.events.length, 17);
});

test("fault rows attribute per RFC-0 §5 (scan@0 from turn-0 output; recall@1 mid turn-1)", () => {
  const run = runOnce();
  assert.deepEqual(
    of(run.events, "page.fault").map((e) => [e.source, e.turn]),
    [
      ["identifier_scan", 0],
      ["tool_recall", 1],
    ],
  );
  // the resident re-call (call_02) faulted exactly once; the fresh fetch (call_03) never faulted
  const declares = of(run.events, "page.declare");
  const recallFault = of(run.events, "page.fault")[1];
  assert.equal(recallFault.page.contentHash, declares[0].page.id.contentHash);
});

test("errored call (call_04, status:error) produces no page events (T6 §2)", () => {
  const run = runOnce();
  const text = run.jsonl;
  assert.ok(!text.includes("missing.json"), "no page declared for the errored call");
  assert.equal(of(run.events, "page.declare").length, 2);
});

test("mirror purity: replay never mutates recorded payloads", () => {
  const hooks = loadEchoFixture();
  const frozen = JSON.stringify(hooks);
  const plugin = createCtxvmPlugin(INIT);
  replayHooks(plugin, hooks);
  assert.equal(JSON.stringify(hooks), frozen);
});

test("determinism: two replayed sessions are byte-identical", () => {
  assert.equal(runOnce().jsonl, runOnce().jsonl);
});

test("contentToPageBody: text items verbatim, non-text items as type markers", () => {
  assert.equal(contentToPageBody([{ type: "text", text: "a\n" }, { type: "text", text: "b" }]), "a\n\nb");
  assert.equal(contentToPageBody([{ type: "file", name: "report.pdf" }]), "<file:report.pdf>");
  assert.equal(contentToPageBody([]), "");
});
