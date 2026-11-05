/** T12 live-adapter tests — env gate, hook registration/mapping, cleanup flush. */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readdirSync, readFileSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import live, { defaultTraceDir, resolveTraceDir } from "../live/ctxvm.ts";
import { rustBinDir } from "../src/uc1-handoff.ts";

const ENV_KEYS = [
  "CTXVM_TRACE_DIR",
  "CTXVM_TRACE_NAME",
  "CTXVM_MODEL",
  "CTXVM_PROVIDER",
  "CTXVM_AGENT_ID",
  "CTXVM_BUDGET_TOKENS",
  "CTXVM_OPENCODE_VERSION",
  "CTXVM_RESUME_FROM",
  "CTXVM_FEATURES",
  "CTXVM_HANDOFF_DIR",
  "CTXVM_HANDOFF_TURN",
  "CTXVM_HANDOFF_STOP",
] as const;

function clearEnv(): void {
  for (const key of ENV_KEYS) delete process.env[key];
}

test("live adapter is inert only when tracing is explicitly disabled", async () => {
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
  // Parity with the hermes adapter (2026-11-01): capture is ON by default, so the
  // old "inert without CTXVM_TRACE_DIR" contract is retired. Explicit opt-out only.
  process.env.CTXVM_TRACE = "0";
  assert.equal(await live.setup(ctx as never), undefined);
  delete process.env.CTXVM_TRACE;
});

test("trace dir expands ~ and defaults to the XDG state dir", () => {
  clearEnv();
  assert.equal(resolveTraceDir(undefined), defaultTraceDir());
  const tilde = resolveTraceDir("~/ctxvm-tilde");
  assert.ok(tilde !== null && isAbsolute(tilde) && !tilde.includes("/~"));
  process.env.CTXVM_TRACE = "off";
  assert.equal(resolveTraceDir("/tmp/x"), null);
  delete process.env.CTXVM_TRACE;
  assert.equal(resolveTraceDir(""), null);
});

test("retention enforces a byte budget on complete captures", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-retain-bytes-"));
  for (let i = 0; i < 4; i += 1) {
    writeFileSync(join(dir, `cap${i}.jsonl`), "x".repeat(1000));
    writeFileSync(join(dir, `cap${i}.meta.json`), "{}");
    const when = new Date(1000 * 1000 + i * 1000);
    utimesSync(join(dir, `cap${i}.jsonl`), when, when);
  }
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "wt";
  process.env.CTXVM_TRACE_RETAIN_MAX = "100";
  process.env.CTXVM_TRACE_RETAIN_DAYS = "9999";
  process.env.CTXVM_TRACE_RETAIN_BYTES = "2500";

  const ctx = { session: { hook: async () => ({ dispose() {} }) }, tool: { hook: async () => ({ dispose() {} }) } };
  const cleanup = await live.setup(ctx as never);
  await cleanup?.();

  const remaining = readdirSync(dir).filter((n) => n.endsWith(".jsonl"));
  const total = remaining.reduce((sum, n) => sum + readFileSync(join(dir, n)).length, 0);
  assert.ok(remaining.length < 4, "byte budget must prune older captures");
  assert.ok(total <= 3500, "budget is enforced (2500 plus the kept file allowance)");
});

test("write-through persists a partial snapshot and cleanup clears it", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-wt-"));
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "wt";
  process.env.CTXVM_TRACE_WRITETHROUGH_EVERY = "1";

  let beforeCb: (input: unknown) => void = () => {};
  const ctx = {
    session: { hook: async () => ({ dispose() {} }) },
    tool: {
      hook: async (name: string, cb: (input: unknown) => void) => {
        if (name === "execute.before") beforeCb = cb;
        return { dispose() {} };
      },
    },
  };
  const cleanup = await live.setup(ctx as never);
  beforeCb({ sessionID: "ses_wt", tool: "read", input: { path: "notes.txt" } });

  const partials = readdirSync(dir).filter((n) => n.endsWith(".partial.jsonl"));
  assert.equal(partials.length, 1, "write-through must persist a partial snapshot");

  await cleanup?.();
  assert.equal(readdirSync(dir).filter((n) => n.endsWith(".partial.jsonl")).length, 0);
  assert.ok(existsSync(join(dir, "wt.jsonl")), "the complete capture must exist after cleanup");
});

test("W21: a reused trace name never replaces another session's bytes", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-collide-"));
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "collide";
  const sentinel = '{"sentinel": true}\n';
  writeFileSync(join(dir, "collide.jsonl"), sentinel);
  writeFileSync(join(dir, "collide.meta.json"), JSON.stringify({ sessionID: "someone-else" }));

  let sessionCb: (input: unknown) => void = () => {};
  const ctx = {
    session: {
      hook: async (_name: string, cb: (input: unknown) => void) => {
        sessionCb = cb;
        return { dispose() {} };
      },
    },
    tool: { hook: async () => ({ dispose() {} }) },
  };
  const cleanup = await live.setup(ctx as never);
  sessionCb({
    sessionID: "ses_collide",
    messages: [{ role: "user", content: [{ type: "text", text: "hello" }] }],
  });
  await (cleanup as () => Promise<void>)();

  const suffix = createHash("sha256").update("ses_collide").digest("hex").slice(0, 8);
  assert.ok(existsSync(join(dir, `collide-${suffix}.jsonl`)), "the second session needs its own path");
  assert.ok(existsSync(join(dir, `collide-${suffix}.coverage.json`)));
  assert.equal(
    readFileSync(join(dir, "collide.jsonl"), "utf8"),
    sentinel,
    "the other session's bytes must be untouched",
  );
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
    "model", "pluginVersion", "provider", "resumeFrom", "sessionID", "traceStats",
  ]);
  assert.equal(meta.resumeFrom, null); // not resuming in this run
  assert.equal(meta.harness, "opencode-v2-promise-plugin");
  assert.equal(meta.harnessVersion, null); // CTXVM_OPENCODE_VERSION not exported in this test
  assert.equal(typeof meta.pluginVersion, "string"); // resolved from the adapter package
  assert.ok((meta.capturedAt as string).endsWith("Z"));
  assert.deepEqual(Object.keys(meta.hookStats).sort(), [
    "after", "before", "completed", "contexts", "errored", "extraHookStats", "sessions",
  ]);
  assert.deepEqual(meta.hookStats.extraHookStats, {});

  // W17 (09-plugin-parity.md §3): the coverage sidecar rides every FULL flush,
  // and its digest ties it to the jsonl bytes physically at the flushed path.
  const coverage = JSON.parse(
    readFileSync(join(dir, "live-test.coverage.json"), "utf8"),
  ) as Record<string, never>;
  const cov: any = coverage;
  assert.deepEqual(Object.keys(cov).sort(), [
    "captures", "instrumentation", "plugin", "session", "toolTable",
    "traceDigest", "traceFile", "xcabiCoverage",
  ]);
  assert.equal(cov.xcabiCoverage, "0.1");
  assert.equal(cov.traceFile, "live-test.jsonl");
  assert.equal(
    cov.traceDigest,
    createHash("sha256").update(readFileSync(join(dir, "live-test.jsonl"))).digest("hex"),
  );
  assert.equal(cov.session.sessionID, "ses_live_test");
  assert.deepEqual(cov.toolTable, {
    readOnlyRegistered: ["glob", "grep", "list", "read", "webfetch"].sort(),
    default: "MUTATING",
  });
  assert.deepEqual(cov.instrumentation, { ts: true, toolEffect: true, identifierScan: true });
  assert.equal(cov.plugin.harness, "opencode-v2-promise-plugin");
  assert.equal(cov.plugin.version, meta.pluginVersion); // same version source as the meta
  // captures equal observation (declared class computed, fault rows echoed)
  assert.equal(cov.captures.declares, 1);
  assert.deepEqual(cov.captures.declaresByClass, { READ_ONLY: 1, MUTATING: 0 });
  const byFault: Record<string, number> = {
    tool_recall: 0, identifier_scan: 0, explicit_api: 0, semantic: 0,
  };
  for (const e of events) {
    if (e.type === "page.fault") byFault[String(e.source)] += 1;
  }
  assert.deepEqual(cov.captures.faultsBySource, byFault);
  assert.equal(cov.captures.faults, events.filter((e) => e.type === "page.fault").length);

  clearEnv();
});

test("B3 boot check: CTXVM_RESUME_FROM stamps resumeFrom evidence + verified=True witness", async () => {
  clearEnv();
  const repoRoot = fileURLToPath(new URL("../../..", import.meta.url));
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-live-resume-"));
  const snap = join(dir, "handoff");
  // Same fixture discipline as uc1-resume.test.ts: relative argv + cwd=repo
  // root (artifact bytes stay host-independent).
  const bin = rustBinDir();
  assert.ok(bin, "release binaries not built — run the cargo build gate");
  const proc = spawnSync(
    join(bin, "export"),
    ["corpus/m1/session-healthy.jsonl", "--turn", "0", "--output", snap, "--odps"],
    { cwd: repoRoot, encoding: "utf8" },
  );
  assert.equal(proc.status, 0, proc.stderr);

  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "boot-test";
  process.env.CTXVM_RESUME_FROM = snap;

  let sessionCb: (input: unknown) => void = () => {};
  const ctx = {
    session: {
      hook: async (_name: string, cb: (input: unknown) => void) => {
        sessionCb = cb;
        return { dispose() {} };
      },
    },
    tool: {
      hook: async () => ({ dispose() {} }),
    },
  };

  const cleanup = await live.setup(ctx as never);
  sessionCb({
    sessionID: "ses_boot",
    messages: [{ role: "user", content: [{ type: "text", text: "after resume" }] }],
  });
  await (cleanup as () => Promise<void>)();

  const meta = JSON.parse(readFileSync(join(dir, "boot-test.meta.json"), "utf8")) as {
    resumeFrom?: Record<string, unknown>;
  };
  const rf = meta.resumeFrom;
  assert.ok(rf, "boot check must stamp resumeFrom");
  assert.equal(rf.turn, 0);
  assert.equal(rf.snapTurn, 0);
  assert.equal(rf.snapshot, snap);
  assert.ok(String(rf.snapshotDigest).startsWith("sha256:"));
  // Artifact set deep-equal to the shared golden fixture (§4 cross-file pin).
  const golden = JSON.parse(
    readFileSync(join(repoRoot, "packages/opencode/test/fixtures/uc1-resume-golden.json"), "utf8"),
  ) as { artifactNames: string[] };
  assert.deepEqual(
    ((rf.artifacts as string[]) ?? []).map((p) => p.split("/").pop()).sort(),
    golden.artifactNames,
  );

  const witness = readFileSync(join(dir, "hooks-witness.log"), "utf8");
  assert.match(
    witness,
    /resume_from=\S+ verified=True reason=snapshot verified: replay exit 0 at turn 0/,
  );

  clearEnv();
});

test("B2 flush-time handoff: CTXVM_HANDOFF_DIR packages the flushed capture", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-live-handoff-"));
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "hand-test";
  // Env recipe: CTXVM_HANDOFF_DIR equals the trace dir (reference law: the
  // handoff dir resolves env-first; design §2's flush target). CTXVM_HANDOFF_
  // TURN unset → the "package at flush" path: no --turn.
  process.env.CTXVM_HANDOFF_DIR = dir;

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
  const base = { sessionID: "ses_hand", agent: "build", id: "call_1" };
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
  await (cleanup as () => Promise<void>)();

  // Era copies exist next to the flushed files (cp -n law).
  assert.ok(existsSync(join(dir, "hand-test-flush.jsonl")));
  assert.ok(existsSync(join(dir, "hand-test-flush.meta.json")));

  // The package directory carries the full artifact set.
  const snapshotDir = join(dir, "handoff");
  assert.ok(existsSync(snapshotDir));
  const packaged = readdirSync(snapshotDir).sort();
  assert.ok(packaged.includes("manifest.yaml"));
  assert.ok(packaged.includes("checksums.sha256"));
  assert.ok(packaged.includes("llms.txt"));
  assert.ok(packaged.some((name) => /^trace-\d+\.jsonl\.zst$/.test(name)));
  assert.ok(packaged.some((name) => /^page-table-\d+\.json$/.test(name)));

  // Witness line mirrors their /ctxvm-handoff rendering (dead-path law keeps
  // verified True; empty divergences list renders as []).
  const witnessFile = readFileSync(join(dir, "hooks-witness.log"), "utf8");
  assert.match(witnessFile, /ctxvm-handoff: exit_code=0 verified=True divergences=\[\]/);

  clearEnv();
});

test("B2 mid-session trigger: CTXVM_HANDOFF_TURN packages at the turn boundary, tracing continues", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-live-trigger-"));
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "hand-test";
  process.env.CTXVM_HANDOFF_DIR = dir;
  process.env.CTXVM_HANDOFF_TURN = "1";

  let sessionCb: (input: unknown) => void | Promise<void> = () => {};
  let beforeCb: (input: unknown) => void = () => {};
  let afterCb: (input: unknown) => void = () => {};
  const ctx = {
    session: {
      hook: async (_name: string, cb: (input: unknown) => void | Promise<void>) => {
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
  const base = { sessionID: "ses_trig", agent: "build", id: "call_1" };
  const fire = (text: string) =>
    sessionCb({
      sessionID: base.sessionID,
      model: { id: "deepseek-v4.1-flash-free", providerID: "opencode", variant: "default" },
      messages: [{ role: "user", content: [{ type: "text", text }] }],
    });

  // Turn 0: no trigger (HANDOFF_TURN=1 arms the turn-1 boundary); the turn-N
  // probe is the idempotent finish() (T17.7 parity) — events untouched.
  await fire("Read notes.txt");
  beforeCb({ ...base, tool: "read", input: { path: "notes.txt" } });
  afterCb({
    ...base,
    tool: "read",
    input: { path: "notes.txt" },
    status: "completed",
    result: { content: [{ type: "text", text: "hello" }] },
  });
  assert.ok(!existsSync(join(dir, "handoff")), "no package before the boundary turn");

  // Turn 1 fires the trigger: flush → era copy → package (--turn 1 via the
  // env law, uc1Pause re-reads).
  await fire("Read again.txt");
  const witness = readFileSync(join(dir, "hooks-witness.log"), "utf8");
  assert.match(witness, /handoff trigger turn=1 session=ses_trig/);
  assert.match(witness, /ctxvm-handoff: exit_code=0 verified=True divergences=\[\]/);
  assert.ok(existsSync(join(dir, "hand-test-turn-1.jsonl")), "era copy with the turn label");
  assert.ok(existsSync(join(dir, "hand-test-turn-1.meta.json")));
  const packaged = readdirSync(join(dir, "handoff")).sort();
  assert.ok(packaged.includes("manifest.yaml"));
  assert.ok(packaged.some((name) => /^trace-\d+\.jsonl\.zst$/.test(name)));
  assert.ok(packaged.includes("checksums.sha256"));

  // Tracing CONTINUES (design §2: pause is not teardown by default): turn 2
  // fires and the trigger does NOT re-fire.
  await fire("Read third.txt");
  const witness2 = readFileSync(join(dir, "hooks-witness.log"), "utf8");
  assert.equal(
    witness2.split("handoff trigger turn=1").length - 1,
    1,
    "trigger fires exactly once per session",
  );

  // Cleanup: the flush-time package was the fallback only — the trigger
  // already packaged, so no second ctxvm-handoff line and no flush era.
  await (cleanup as () => Promise<void>)();
  const witness3 = readFileSync(join(dir, "hooks-witness.log"), "utf8");
  assert.equal(
    witness3.split("ctxvm-handoff: exit_code=").length - 1,
    1,
    "no second package at cleanup after a fired trigger",
  );
  assert.ok(
    !existsSync(join(dir, "hand-test-flush.jsonl")),
    "no flush-era copy when the trigger already packaged",
  );
  // the continued tracing is not lost: the final flush still landed
  assert.ok(existsSync(join(dir, "hand-test.jsonl")));

  clearEnv();
});

test("B2 mid-session trigger + CTXVM_HANDOFF_STOP=1: package, then hook disposal", async () => {
  clearEnv();
  const dir = mkdtempSync(join(tmpdir(), "ctxvm-live-triggerstop-"));
  process.env.CTXVM_TRACE_DIR = dir;
  process.env.CTXVM_TRACE_NAME = "hand-test";
  process.env.CTXVM_HANDOFF_DIR = dir;
  process.env.CTXVM_HANDOFF_TURN = "1";
  process.env.CTXVM_HANDOFF_STOP = "1";

  let sessionCb: (input: unknown) => void | Promise<void> = () => {};
  let beforeCb: (input: unknown) => void = () => {};
  let afterCb: (input: unknown) => void = () => {};
  let sessionDisposed = false;
  let toolDisposed = false;
  const ctx = {
    session: {
      hook: async (_name: string, cb: (input: unknown) => void | Promise<void>) => {
        sessionCb = cb;
        return {
          dispose() {
            sessionDisposed = true;
          },
        };
      },
    },
    tool: {
      hook: async (name: string, cb: (input: unknown) => void) => {
        if (name === "execute.before") beforeCb = cb;
        else afterCb = cb;
        return {
          dispose() {
            toolDisposed = true;
          },
        };
      },
    },
  };
  const cleanup = await live.setup(ctx as never);
  const base = { sessionID: "ses_stop", agent: "build", id: "call_1" };
  const fire = (text: string) =>
    sessionCb({
      sessionID: base.sessionID,
      model: { id: "deepseek-v4.1-flash-free", providerID: "opencode", variant: "default" },
      messages: [{ role: "user", content: [{ type: "text", text }] }],
    });

  await fire("Read notes.txt");
  await fire("Read again.txt"); // the boundary turn: package + STOP disposal

  const witness = readFileSync(join(dir, "hooks-witness.log"), "utf8");
  assert.match(witness, /handoff trigger turn=1 session=ses_stop/);
  assert.match(witness, /ctxvm-handoff: exit_code=0 verified=True divergences=\[\]/);
  assert.match(witness, /handoff stop: hook registrations disposed/);
  assert.ok(sessionDisposed, "the stop law disposes the hook registrations");
  assert.ok(toolDisposed);
  assert.ok(existsSync(join(dir, "hand-test-turn-1.jsonl")));

  await (cleanup as () => Promise<void>)();
  // re-dispose is idempotent-safe and cleanup still flushes the final trace
  assert.ok(existsSync(join(dir, "hand-test.jsonl")));

  clearEnv();
});
