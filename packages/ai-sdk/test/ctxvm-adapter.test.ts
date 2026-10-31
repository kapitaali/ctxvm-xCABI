/**
 * T15 — Vercel AI SDK adapter tests (T7 Adapter B, pinned `ai` 7.0.154).
 *
 * GLUE units run against a RECORDING TRACER stand-in (no real tracer state —
 * the mapping is what this package proves; the opencode spike's precedent) with
 * the canonical COMMITTED fixture (`fixtures/echo-thrash.parts.json`, recorded
 * by the gen driver through a real `streamText` + `MockLanguageModelV4` loop —
 * `npm run gen`).
 *
 * The INTEGRATION test replays the committed fixture through a REAL
 * `@ctxvm/node` tracer and asserts the finished trace is byte-identical to the
 * committed `fixtures/echo-thrash.trace.jsonl` — the recorded orderings replay
 * deterministically (mirror-mode law: same parts in → same trace out).
 * Provenance (RR-RFC01E1): the TRACE fixture was regenerated 2026-10-31 through
 * the RFC-0.1 emitter (schemaVersion "0.1" on session.open — exactly one line
 * changed); the PARTS fixture is the frozen recorded provenance and was not.
 *
 * Mirror law is asserted byte-level: middleware `transformParams` returns the
 * SAME params object; the tap yields every part untouched (deep equality).
 *
 * Env laws mirrored from the opencode suite: `freshTmp` quarantines leaked
 * CTXVM_* keys (m7 gate-2 regression, RR-UM7CAPTURE), and the unarmed capture
 * is a hard no-op.
 */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { createTrace, type FinishedTrace, type Json, type Tracer } from "../../node/src/index.ts";
import { TurnAgreement } from "../src/contract.ts";
import { createCtxvmCapture } from "../src/index.ts";
import { ctxvmMiddleware, type MiddlewareHandle } from "../src/middleware.ts";
import { ctxvmTap, newTapStats, type TapHandle, type TapStats } from "../src/tap.ts";

const REPO_ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const PARTS_FIXTURE = join(REPO_ROOT, "packages/ai-sdk/fixtures/echo-thrash.parts.json");
const TRACE_FIXTURE = join(REPO_ROOT, "packages/ai-sdk/fixtures/echo-thrash.trace.jsonl");
const VENV_PYTHON = join(REPO_ROOT, "venvs/odps/bin/python");
const V01_VALIDATOR = join(REPO_ROOT, "spec/rfc-0.1/validate_schema_v0_1.py");

function freshTmp(label: string): string {
  // Test isolation (m7 gate-2 regression, RR-UM7CAPTURE): quarantine leaked
  // CTXVM_* keys so captures arm only where a test deliberately sets them.
  for (const key of Object.keys(process.env)) {
    if (key.startsWith("CTXVM_")) delete process.env[key];
  }
  return mkdtempSync(join(tmpdir(), `ctxvm-t15-${label}-`));
}

/** Recording-tracer stand-in: the GLUE proof (opencode spike precedent). */
interface Recorder {
  pages: { tool: string; args: unknown; content: unknown }[];
  recalls: { tool: string; args: unknown }[];
  scans: string[];
  renders: number;
  usages: { inputTokens: number; outputTokens: number; cachedInputTokens?: number }[];
  finished: boolean;
}

function recorder(sameTracer = new Map<string, Recorder>()): Tracer & { record: Recorder } {
  const rec: Recorder = { pages: [], recalls: [], scans: [], renders: 0, usages: [], finished: false };
  return {
    record: rec,
    page(input: { tool?: string; args?: Json; content: unknown }) {
      rec.pages.push({ tool: input.tool ?? "", args: input.args, content: input.content });
      return { logicalRef: `tool:${input.tool}(x)`, contentHash: "sha256:fixture", tokens: 1 };
    },
    recall(input: { tool?: string; args?: unknown }) {
      rec.recalls.push(input as { tool: string; args: unknown });
    },
    render() {
      rec.renders += 1;
    },
    scan(input: { text: string }) {
      rec.scans.push(input.text);
    },
    noteUsage(input: { inputTokens: number; outputTokens: number; cachedInputTokens?: number }) {
      rec.usages.push(input); // mirrors the tracer intake: the stand-in records what real code would wire
    },
    pin() {},
    unpin() {},
    finish(): FinishedTrace {
      rec.finished = true;
      return { jsonl: "", events: [], stats: { turns: rec.renders, pages: rec.pages.length, faults: 0, residentTokens: 0 } };
    },
  } as unknown as Tracer & { record: Recorder };
}

async function* streamOf<T>(parts: T[]): AsyncGenerator<T, void, void> {
  yield* parts;
}

function handleFor(harness: Tracer & { record: Recorder }, opts?: { armed?: boolean; renders?: number }): TapHandle {
  const counts = new TurnAgreement();
  counts.middlewareRenders = opts?.renders ?? 0;
  return {
    vmFor: () => harness as unknown as Tracer,
    sessionKey: "local",
    counts,
    witness: () => {},
    armed: opts?.armed ?? true,
  };
}

type AnyPart = Record<string, unknown>;

test("middleware mirror law: params returned UNCHANGED (same object), armed and unarmed", async () => {
  for (const armed of [true, false]) {
    const vm = recorder();
    const counts = new TurnAgreement();
    const mw = ctxvmMiddleware({
      vmFor: () => vm as unknown as Tracer,
      sessionKey: "local",
      counts,
      witness: () => {},
      armed,
    });
    const params = { prompt: [{ role: "user", content: "hello" }], temperature: 0.5 };
    const returned = await mw.transformParams!({
      type: "stream",
      params: params as never,
      model: {} as never,
    });
    assert.ok(Object.is(returned, params), "middleware must return the SAME params object (mirror law)");
    if (armed) {
      assert.equal(counts.middlewareRenders, 1);
      assert.equal(vm.record.renders, 1); // one fire = one xCABI turn
    } else {
      assert.equal(counts.middlewareRenders, 0);
      assert.equal(vm.record.renders, 0); // unarmed: no metering at all
    }
  }
});

test("tap pass-through law: every part yields UNTOUCHED, unarmed capture records nothing", async () => {
  const parts = [
    { type: "start-step" },
    { type: "text-delta", id: "1", delta: "hi" },
    { type: "tool-call", toolCallId: "c1", toolName: "echo", input: { message: "hi" } },
    { type: "finish-step" },
  ];
  const vm = recorder();
  const stats = newTapStats();
  const out: AnyPart[] = [];
  for await (const part of ctxvmTap(streamOf(parts), handleFor(vm, { armed: false }), stats)) {
    out.push(part as AnyPart);
  }
  assert.deepEqual(out, parts);
  assert.equal(vm.record.recalls.length, 0);
  assert.equal(vm.record.pages.length, 0);
  assert.equal(stats.toolCalls, 0);
});

test("tap mapping (recording tracer): the canonical echo/thrash fixture maps exactly", async () => {
  const parts = JSON.parse(readFileSync(PARTS_FIXTURE, "utf8")) as AnyPart[];
  const vm = recorder();
  const stats = newTapStats();
  const counts = new TurnAgreement();
  counts.middlewareRenders = 3; // canonical run: 3 model calls (witnessed by gen)
  const handle = handleFor(vm);
  handle.counts = counts;

  const out: AnyPart[] = [];
  for await (const part of ctxvmTap(streamOf(parts), handle, stats)) {
    out.push(part as AnyPart);
  }

  // Mirror: identical passthrough.
  assert.deepEqual(out, parts);

  // Pichay keys: 2 recalls of echo, canonical args.
  assert.equal(vm.record.recalls.length, 2);
  for (const recall of vm.record.recalls) {
    assert.equal(recall.tool, "echo");
    assert.deepEqual(recall.args, { message: "hello" });
  }

  // Pages: 2 final tool-results (no preliminary parts in this fixture).
  assert.equal(stats.toolResults, 2);
  assert.equal(stats.preliminarySkipped, 0);
  assert.equal(vm.record.pages.length, 2);
  for (const page of vm.record.pages) {
    assert.equal(page.tool, "echo");
    assert.deepEqual(page.content, { echo: "hello" });
  }

  // Scans: one per text-bearing step (step 1 and step 3 texts).
  assert.deepEqual(vm.record.scans, ["Echo reply for ", "done"]);
  assert.equal(stats.scannedBytes, "Echo reply for ".length + "done".length);

  // Risk-1 witness: renders == steps (3 == 3, same run).
  assert.equal(counts.tapStepEnds, 3);
  assert.equal(stats.steps, 3);
  assert.equal(counts.agree(), true);

  // W2b glue: the canonical parts' 3 finish-step receipts relay into the
  // tracer interface exactly (10/5/cached 0 each — the provider's own facts).
  assert.deepEqual(vm.record.usages, [
    { inputTokens: 10, outputTokens: 5, cachedInputTokens: 0 },
    { inputTokens: 10, outputTokens: 5, cachedInputTokens: 0 },
    { inputTokens: 10, outputTokens: 5, cachedInputTokens: 0 },
  ]);
});

test("tap mapping: preliminary tool-results are NOT pages (B0 erratum 2)", async () => {
  const parts: AnyPart[] = [
    { type: "start-step" },
    { type: "tool-call", toolCallId: "c1", toolName: "echo", input: { message: "hi" } },
    { type: "tool-result", toolCallId: "c1", toolName: "echo", input: { message: "hi" }, output: { echo: "hi" }, preliminary: true },
    { type: "tool-result", toolCallId: "c1", toolName: "echo", input: { message: "hi" }, output: { echo: "hi" } },
    { type: "finish-step" },
  ];
  const vm = recorder();
  const stats = newTapStats();
  for await (const _ of ctxvmTap(streamOf(parts), handleFor(vm), stats)) {} // mirror pass-over
  assert.equal(stats.preliminarySkipped, 1);
  assert.equal(vm.record.pages.length, 1); // only the FINAL result pages
});

test("tap mapping: tool-error and tool-output-denied are NOT pages (T6 §2)", async () => {
  const parts: AnyPart[] = [
    { type: "tool-error", toolCallId: "c1", toolName: "boom", input: { x: 1 }, error: "nope" },
    { type: "tool-output-denied", toolCallId: "c2", toolName: "vault", input: { x: 2 } },
  ];
  const vm = recorder();
  const stats = newTapStats();
  for await (const _ of ctxvmTap(streamOf(parts), handleFor(vm), stats)) {}
  assert.equal(stats.deniedOrErrors, 2);
  assert.equal(vm.record.pages.length, 0);
});

test("integration: the committed fixture replays through a REAL tracer byte-identically", async () => {
  const tmp = freshTmp("replay");
  try {
    process.env.CTXVM_TRACE_DIR = tmp;
    process.env.CTXVM_TRACE_NAME = "replay-echo";
    // D9 (RFC-0.1 §R4-ts): this pin compares REPLAYED bytes against the frozen
    // canon fixture — a byte-stability need, so the whole capture runs under
    // the named per-trace opt-out. Fresh captures stamp ts by default.
    process.env.CTXVM_TRACE_TS = "0";
    const capture = createCtxvmCapture({
      agentId: "ctxvm-ai-sdk",
      model: "ctxvm-mock/echo-model",
      provider: "ctxvm-mock",
      budgetTokens: 120000,
    });

    // Replay the recorded orderings with the same middleware/tap interleaving
    // the gen run had: transformParams fires ONCE PER STEP (the model call
    // precedes the fullStream projection), so turn.render/call.meta events land
    // on the same turns. The stream's leading `start` part belongs to step 1's
    // stream — already preceded by its transformParams — so it rides the first
    // group WITHOUT a render of its own (same for the trailing `finish`).
    const parts = JSON.parse(readFileSync(PARTS_FIXTURE, "utf8")) as AnyPart[];
    const groups: AnyPart[][] = [[]];
    for (const part of parts) {
      if (part.type === "start-step") groups.push([part]);
      else (groups[groups.length - 1] as AnyPart[]).push(part);
    }
    // Step 1's transformParams preceded the whole first stream: fold the head
    // group (`start`) in front of step 1 so the fed order matches the run.
    const stepGroups = groups.filter((group) => group[0]?.type === "start-step");
    assert.equal(stepGroups.length, 3); // canonical run: exactly 3 steps
    if (groups[0]!.length > 0) stepGroups[0]!.unshift(...groups[0]!);
    for (const group of stepGroups) {
      await capture.middleware.transformParams!({
        type: "stream",
        params: { prompt: [] } as never,
        model: {} as never,
      });
      for await (const _ of capture.tap(streamOf(group))) {} // mirror pass-over
    }

    const finished = capture.finishAll();
    assert.equal(finished.length, 1);
    const replayed = finished[0]!.trace.jsonl;
    const committed = readFileSync(TRACE_FIXTURE, "utf8");
    // RFC-0.1 R0: the adapter lane negotiates the version on session.open.
    assert.equal(
      (JSON.parse(replayed.split("\n")[0] as string) as { schemaVersion?: string }).schemaVersion,
      "0.1",
      "session.open must declare schemaVersion \"0.1\" (RFC-0.1 R0)",
    );
    // W2b: the recorded parts' finish-step usage receipts (10/5/cached 0, all
    // three steps) must land on their own turns' call.meta — the faucet is the
    // provider's own account, not an estimate.
    const metas = replayed
      .split("\n")
      .filter((l) => l.includes("\"providerUsage\""))
      .map((l) => {
        const m = JSON.parse(l) as { turn: number; providerUsage: object };
        return { turn: m.turn, providerUsage: m.providerUsage };
      });
    assert.deepEqual(metas, [
      { turn: 0, providerUsage: { inputTokens: 10, outputTokens: 5, cachedInputTokens: 0 } },
      { turn: 1, providerUsage: { inputTokens: 10, outputTokens: 5, cachedInputTokens: 0 } },
      { turn: 2, providerUsage: { inputTokens: 10, outputTokens: 5, cachedInputTokens: 0 } },
    ]);
    assert.equal(replayed, committed, "recorded orderings must replay deterministically");

    const metaPath = finished[0]!.metaPath!;
    const meta = JSON.parse(readFileSync(metaPath, "utf8")) as { mirrorCountsAgree: boolean; hookStats: Record<string, number> };
    assert.equal(meta.mirrorCountsAgree, true);
    assert.equal(meta.hookStats.middlewareRenders, 3); // gen had 3 model calls
    assert.equal(meta.hookStats.tapStepEnds, 3);
    assert.equal(statSync(join(tmp, "replay-echo.jsonl")).isFile(), true);
  } finally {
    delete process.env.CTXVM_TRACE_DIR;
    delete process.env.CTXVM_TRACE_NAME;
    delete process.env.CTXVM_TRACE_TS; // D9 opt-out ran only for this capture
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("unarmed capture: finishAll is an empty no-op with no files", async () => {
  const tmp = freshTmp("unarmed");
  try {
    const capture = createCtxvmCapture({
      agentId: "ctxvm-ai-sdk",
      model: "ctxvm-mock/echo-model",
      provider: "ctxvm-mock",
      budgetTokens: 120000,
    });
    assert.deepEqual(capture.finishAll(), []);
    // No sidecar, no jsonl, no witness log — the env dir was never touched.
    const entries = readdirSync(tmp);
    assert.deepEqual(entries, []);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("schema conformance: the committed fixture trace passes the RFC-0.1 validator", () => {
  // gate-2 shape: run the validator ONLY when the workspace venv exists —
  // their published CI gate 2 has no venvs (schema job rebuilds them).
  // Since the RR-RFC01E1 version switch, the regenerated trace fixture is a
  // v0.1 trace (schemaVersion on session.open; the sealed v0 validator would
  // REJECT that unknown field, which is the R0 boundary working) — so the
  // fixture's standing validator is RFC-0.1. The v0 corpus fixtures keep
  // their sealed-v0 gate in run-ci gate 3.
  if (!statSafe(VENV_PYTHON)) return;
  const res = spawnSync(VENV_PYTHON, [V01_VALIDATOR, TRACE_FIXTURE], { encoding: "utf8", timeout: 120000 });
  if (res.error || res.status === undefined) assert.fail(`validator spawn failed: ${res.error}`);
  assert.equal(res.status, 0, res.stdout + res.stderr);
  assert.match(res.stdout, /OK: all checks passed/);
});

function statSafe(path: string): boolean {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}
