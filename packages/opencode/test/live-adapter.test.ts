/** T12 live-adapter tests — env gate, hook registration/mapping, cleanup flush. */

import assert from "node:assert/strict";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import live from "../live/ctxvm.ts";

const ENV_KEYS = [
  "CTXVM_TRACE_DIR",
  "CTXVM_TRACE_NAME",
  "CTXVM_MODEL",
  "CTXVM_PROVIDER",
  "CTXVM_AGENT_ID",
  "CTXVM_BUDGET_TOKENS",
  "CTXVM_OPENCODE_VERSION",
] as const;

function clearEnv(): void {
  for (const key of ENV_KEYS) delete process.env[key];
}

test("live adapter is inert without CTXVM_TRACE_DIR", async () => {
  clearEnv();
  const ctx = {
    session: {
      hook: async () => {
        throw new Error("must not register");
      },
    },
    tool: {
      hook: async () => {
        throw new Error("must not register");
      },
    },
  };
  assert.equal(await live.setup(ctx as never), undefined);
});

test("live adapter maps the three hooks and flushes a trace on cleanup", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-live-"));
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "live-test";
  process.env.CTXVM_MODEL = "opencode/deepseek-v4.1-flash-free";
  process.env.CTXVM_PROVIDER = "opencode";

  let sessionCb: (input: unknown) => void = () => {};
  let beforeCb: (input: unknown) => void = () => {};
  let afterCb: (input: unknown) => void = () => {};
  const ctx = {
    session: {
      hook: async (_name: string, cb: (input: unknown) => void) => {
        sessionCb = cb;
        return { dispose() {} };
      },
    },
    tool: {
      hook: async (name: string, cb: (input: unknown) => void) => {
        if (name === "execute.before") beforeCb = cb;
        else afterCb = cb;
        return { dispose() {} };
      },
    },
  };

  const cleanup = await live.setup(ctx as never);
  assert.equal(typeof cleanup, "function");

  const base = { sessionID: "ses_live_test", agent: "build", id: "call_1" };
  sessionCb({
    sessionID: base.sessionID,
    model: { id: "deepseek-v4.1-flash-free", providerID: "opencode", variant: "default" },
    messages: [{ role: "user", content: [{ type: "text", text: "Read notes.txt" }] }],
  });
  beforeCb({ ...base, tool: "read", input: { path: "notes.txt" } });
  afterCb({
    ...base,
    tool: "read",
    input: { path: "notes.txt" },
    status: "completed",
    result: { content: [{ type: "text", text: "hello" }] },
  });
  sessionCb({
    sessionID: base.sessionID,
    messages: [
      { role: "user", content: [{ type: "text", text: "Read notes.txt" }] },
      { role: "assistant", content: [{ type: "text", text: "It says hello." }] },
    ],
  });
  await (cleanup as () => Promise<void>)();

  const events = readFileSync(join(dir, "live-test.jsonl"), "utf8")
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as Record<string, unknown>);
  const types = events.map((e) => e.type);
  assert.equal(events[0]?.type, "session.open");
  assert.equal(events[0]?.model, "opencode/deepseek-v4.1-flash-free");
  assert.ok(types.includes("page.declare"));
  assert.ok(types.includes("turn.render"));
  assert.ok(types.includes("call.meta"));
  assert.ok(types.includes("page.fault"));

  const meta = JSON.parse(readFileSync(join(dir, "live-test.meta.json"), "utf8")) as {
    sessionID: string;
    [key: string]: unknown;
    hookStats: Record<string, unknown>;
    traceStats: { turns: number; pages: number; faults: number };
  };
  assert.equal(meta.sessionID, "ses_live_test");
  assert.deepEqual(meta.hookStats.contexts, 2);
  assert.deepEqual(meta.hookStats.before, 1);
  assert.deepEqual(meta.hookStats.after, 1);
  assert.deepEqual(meta.hookStats.completed, 1);
  assert.deepEqual(meta.traceStats, { turns: 2, pages: 1, faults: 1, residentTokens: 2 });

  // KIT-1 (09-plugin-parity.md §3): canonical sidecar shape — identical to the
  // hermes `_canon_meta` shape asserted in packages/hermes/test/test_plugin.py.
  assert.deepEqual(Object.keys(meta).sort(), [
    "budgetTokens", "capturedAt", "harness", "harnessVersion", "hookStats",
    "model", "pluginVersion", "provider", "sessionID", "traceStats",
  ]);
  assert.equal(meta.harness, "opencode-v2-promise-plugin");
  assert.equal(meta.harnessVersion, null); // CTXVM_OPENCODE_VERSION not exported in this test
  assert.equal(typeof meta.pluginVersion, "string"); // resolved from the adapter package
  assert.ok((meta.capturedAt as string).endsWith("Z"));
  assert.deepEqual(Object.keys(meta.hookStats).sort(), [
    "after", "before", "completed", "contexts", "errored", "extraHookStats", "sessions",
  ]);
  assert.deepEqual(meta.hookStats.extraHookStats, {});

  clearEnv();
});
