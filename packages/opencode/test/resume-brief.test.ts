/** T25 handoff-inject tests — the per-harness beat resolved as gated mutation
 * (§7 rulings 2026-10-28, all recommendations accepted). Mirror-module tests +
 * live-adapter wiring tests through the ctx-stub shape (live-adapter.test.ts
 * pattern). Provider-key-free: committed corpus + release binaries (T22
 * precedent); packages built by the m1-thrash @2 export (the only corpus
 * anchor whose projection carries BOTH modes at one turn — 1 full + 1 stub). */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import live from "../live/ctxvm.ts";
import { assembleResumeBrief } from "../src/resume-brief.ts";
import { rustBinDir, snapshotDigest } from "../src/uc1-handoff.ts";

const REPO_ROOT = fileURLToPath(new URL("../../..", import.meta.url));

function buildThrashSnapshot(dir: string, turn: number): void {
  const bin = rustBinDir();
  assert.ok(bin, "release binaries not built — run the cargo build gate");
  const proc = spawnSync(
    join(bin, "export"),
    ["corpus/m1/session-thrashing.jsonl", "--turn", String(turn), "--output", dir, "--odps"],
    { cwd: REPO_ROOT, encoding: "utf8" },
  );
  assert.equal(proc.status, 0, `export failed: ${proc.stderr}`);
}

/** The package's events (the verified boot / a prior read already leaves the
 * plain slice beside the zst). */
function packageEvents(dir: string): Record<string, unknown>[] {
  const zsts = readdirSync(dir).filter((n) => /^trace-.*\.jsonl\.zst$/.test(n)).sort();
  assert.ok(zsts.length > 0, "no package slice");
  const turn = parseInt(zsts[0]!.replace(/\.zst$/, "").split("-")[1]!.split(".")[0]!, 10);
  const plain = join(dir, `trace-${turn}.jsonl`);
  if (!existsSync(plain)) {
    const proc = spawnSync("zstd", ["-d", join(dir, zsts[0]!), "-o", plain, "-f"], {
      encoding: "utf8",
    });
    assert.equal(proc.status, 0, proc.stderr);
  }
  return readFileSync(plain, "utf8")
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l) as Record<string, unknown>);
}

function pageTableOf(dir: string): {
  slots: Array<{
    mode: string;
    reference: { id: { logicalRef: string; contentHash: string }; kind: string; tokens: number };
  }>;
  tally: Record<string, unknown>;
  turn: number;
} {
  const zsts = readdirSync(dir).filter((n) => /^trace-.*\.jsonl\.zst$/.test(n)).sort();
  const turn = parseInt(zsts[0]!.replace(/\.zst$/, "").split("-")[1]!.split(".")[0]!, 10);
  return JSON.parse(readFileSync(join(dir, `page-table-${turn}.json`), "utf8"));
}

function wipeCtxvmEnv(): void {
  for (const key of Object.keys(process.env)) {
    if (key.startsWith("CTXVM_")) delete process.env[key];
  }
}

type HookCb = (input: unknown) => void | Promise<void>;

function ctxStub() {
  const sessionCbs: HookCb[] = [];
  const beforeCbs: HookCb[] = [];
  const afterCbs: HookCb[] = [];
  const ctx = {
    session: {
      hook: async (_name: string, cb: HookCb) => {
        sessionCbs.push(cb);
        return { dispose() {} };
      },
    },
    tool: {
      hook: async (name: string, cb: HookCb) => {
        if (name === "execute.before") beforeCbs.push(cb);
        else afterCbs.push(cb);
        return { dispose() {} };
      },
    },
  };
  return { ctx, sessionCbs, beforeCbs, afterCbs };
}

/** Synthetic SessionContext (shim shape — messages use the `parts` law). */
function payload(system: string[] = ["base prompt"]): Record<string, unknown> {
  return {
    sessionID: "ses_t25",
    agent: "build",
    model: { providerID: "p", modelID: "m" },
    system,
    messages: [{ role: "user", parts: [{ text: "hello" }] }],
    options: {},
    tools: {},
  };
}

function witnessOf(traceDir: string): string {
  return readFileSync(join(traceDir, "hooks-witness.log"), "utf8");
}

// ---------------------------------------------------------------------------
// Mirror module (resolver-less v0 — §7 Q5 ruling)
// ---------------------------------------------------------------------------

test("T25 brief assembly mirror: stubs package-complete verbatim, full slots degrade loudly (resolver-less v0), provenance header/footer — the ai-sdk module mirrored", () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const pkg = join(tmp, "pkg");
    buildThrashSnapshot(pkg, 2);
    const table = pageTableOf(pkg);
    assert.equal(table.slots.length, 2);
    assert.deepEqual(table.slots.map((s) => s.mode), ["full", "stub"]);

    const brief = assembleResumeBrief(pkg);
    assert.equal(brief.turn, 2);
    assert.equal(brief.slots, 2);
    assert.equal(brief.full, 1);
    assert.equal(brief.stub, 1);
    assert.ok(brief.text.startsWith("# ctxvm resume brief — turn 2\n"), brief.text.slice(0, 80));
    assert.ok(brief.text.includes(snapshotDigest(pkg)), "header carries the provenance digest");
    // full slot: the loud unresolved marker (resolver-less v0 — content-blind
    // law: the package never carries full-page text, the plugin never invents it)
    const fullRef = table.slots[0]!.reference.id.logicalRef;
    assert.ok(brief.text.includes(`- ${fullRef} (file, 1000 tok,`), "reference line shape");
    assert.ok(brief.text.includes(`  [unresolved: ${fullRef} — content not provided]`));
    // stub slot: the slice's stubText bytes verbatim (package-complete)
    const stubRef = table.slots[1]!.reference.id.logicalRef;
    const evict = packageEvents(pkg)
      .filter((e) => e.type === "page.evict" && (e.page as { logicalRef: string }).logicalRef === stubRef)
      .at(-1) as { stubText: string };
    assert.ok(evict, "the stub slot has an evict row in the slice");
    assert.ok(
      brief.text.includes(evict.stubText.split("\n").map((l) => `  ${l}`).join("\n")),
      "stubText rendered verbatim (indented)",
    );
    // section order + footer
    const residentAt = brief.text.indexOf("## Resident pages (1)");
    const stubAt = brief.text.indexOf("## Stubbed pages (1)");
    assert.ok(residentAt !== -1 && stubAt !== -1 && residentAt < stubAt);
    assert.ok(brief.text.includes("- slots: 2 (1 full, 1 stub)"));
    assert.ok(brief.text.includes(`- tally: ${JSON.stringify(table.tally)}`));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("T25 module law: structural package problems THROW — the live adapter's arm catch disarms loudly (never-breaks-capture lives there)", () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const empty = join(tmp, "empty");
    mkdirSync(empty, { recursive: true });
    assert.throws(() => assembleResumeBrief(empty), /no trace-\*\.jsonl\.zst/);
    const pkg = join(tmp, "pkg");
    buildThrashSnapshot(pkg, 2);
    const tableNames = readdirSync(pkg).filter((n) => n.startsWith("page-table-"));
    rmSync(join(pkg, tableNames[0]!), { force: true });
    assert.throws(() => assembleResumeBrief(pkg), /page-table-2\.json missing/);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// ---------------------------------------------------------------------------
// Live adapter wiring (ctx-stub replays)
// ---------------------------------------------------------------------------

test("T25 disarm red-pin: verified resume WITHOUT the gate → payload byte-untouched, no injection witness (the frozen-payload law, T24 mirror)", async () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const pkg = join(tmp, "pkg");
    buildThrashSnapshot(pkg, 2);
    const traceDir = join(tmp, "trace");
    process.env.CTXVM_TRACE_DIR = traceDir;
    process.env.CTXVM_RESUME_FROM = pkg;
    // NO CTXVM_FEATURES → the gate is off even though the boot verifies.
    const { ctx, sessionCbs } = ctxStub();
    const cleanup = await live.setup(ctx as never);
    assert.equal(typeof cleanup, "function");
    const p = payload();
    const frozen = JSON.stringify(p);
    await sessionCbs[0]!(p);
    await sessionCbs[0]!(p);
    assert.equal(JSON.stringify(p), frozen, "disarmed: the payload is byte-untouched");
    const wit = witnessOf(traceDir);
    assert.ok(wit.includes("verified=True"), "the boot verified (law ran, loud)");
    assert.ok(!wit.includes("resumeBrief"), "no injection lines when disarmed");
    await cleanup();
  } finally {
    wipeCtxvmEnv();
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("T25 armed: first fire prepends the brief into system ONCE, messages untouched, witness order pins inject-before-capture (Q4)", async () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const pkg = join(tmp, "pkg");
    buildThrashSnapshot(pkg, 2);
    const traceDir = join(tmp, "trace");
    process.env.CTXVM_TRACE_DIR = traceDir;
    process.env.CTXVM_TRACE_NAME = "t25";
    process.env.CTXVM_RESUME_FROM = pkg;
    process.env.CTXVM_FEATURES = "trace,handoff-inject";
    const { ctx, sessionCbs } = ctxStub();
    const cleanup = await live.setup(ctx as never);
    const p = payload();
    const messagesFrozen = JSON.stringify(p.messages);
    await sessionCbs[0]!(p);
    const system = p.system as unknown[];
    assert.equal(system.length, 2, "exactly one prepend");
    assert.ok(String(system[0]).startsWith("# ctxvm resume brief — turn 2"), "the brief leads");
    assert.ok(String(system[0]).includes(snapshotDigest(pkg)), "brief provenance == boot digest");
    assert.ok(String(system[0]).includes("[unresolved:"), "full slots ride as loud markers");
    assert.equal(String(system[1]), "base prompt", "the native system survives unshifted");
    assert.equal(JSON.stringify(p.messages), messagesFrozen, "messages untouched (Q2: system surface)");
    const wit = witnessOf(traceDir);
    assert.ok(wit.includes("resumeBrief assembled: slots=2 full=1 stub=1"), "arm witness");
    assert.ok(
      wit.includes("resumeBrief injected turn=2 session=ses_t25 surface=system"),
      "inject witness",
    );
    // Q4 order pin: the injected line precedes the capture's context line
    const injectedAt = wit.indexOf("resumeBrief injected");
    const contextAt = wit.indexOf("context session=ses_t25");
    assert.ok(injectedAt !== -1 && contextAt !== -1 && injectedAt < contextAt);
    // second fire: no duplicate (once per session — boot semantics)
    await sessionCbs[0]!(p);
    assert.equal((p.system as unknown[]).length, 2, "no re-prepend on later fires");
    assert.equal(wit.split("resumeBrief injected").length - 1, 1, "exactly one injection");
    await cleanup();
  } finally {
    wipeCtxvmEnv();
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("T25 unverified boot + gate → never arms: the T22 boot law runs first, verify-only continues", async () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const traceDir = join(tmp, "trace");
    process.env.CTXVM_TRACE_DIR = traceDir;
    process.env.CTXVM_RESUME_FROM = join(tmp, "no-such-snapshot");
    process.env.CTXVM_FEATURES = "handoff-inject";
    const { ctx, sessionCbs } = ctxStub();
    const cleanup = await live.setup(ctx as never);
    const p = payload();
    const frozen = JSON.stringify(p);
    await sessionCbs[0]!(p);
    assert.equal(JSON.stringify(p), frozen, "unverified boot: nothing injected");
    const wit = witnessOf(traceDir);
    assert.ok(wit.includes("verified=False"), "loud boot failure");
    assert.ok(wit.includes("UNVERIFIED — tracer continues"), "the T22 law line");
    assert.ok(!wit.includes("resumeBrief assembled"), "never armed");
    await cleanup();
  } finally {
    wipeCtxvmEnv();
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("T25 never-breaks-capture: a hostile (frozen) system array throws at unshift → loud FAILED witness, capture continues, no retry", async () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const pkg = join(tmp, "pkg");
    buildThrashSnapshot(pkg, 2);
    const traceDir = join(tmp, "trace");
    process.env.CTXVM_TRACE_DIR = traceDir;
    process.env.CTXVM_TRACE_NAME = "t25frozen";
    process.env.CTXVM_RESUME_FROM = pkg;
    process.env.CTXVM_FEATURES = "handoff-inject";
    const { ctx, sessionCbs } = ctxStub();
    const cleanup = await live.setup(ctx as never);
    const p = payload(Object.freeze(["frozen prompt"]) as unknown as string[]);
    await sessionCbs[0]!(p);
    const wit = witnessOf(traceDir);
    assert.ok(wit.includes("resumeBrief assembled:"), "armed (the boot verified)");
    assert.ok(
      wit.includes("resumeBrief inject FAILED (capture continues):"),
      "the unshift failure is loud",
    );
    // capture continued: the fire registered a turn → cleanup flushes a trace
    await cleanup();
    const flushed = readFileSync(join(traceDir, "t25frozen.jsonl"), "utf8");
    assert.ok(flushed.includes("turn.render"), "the tracer metered the fire despite the failed injection");
    assert.equal(wit.split("resumeBrief inject FAILED").length - 1, 1, "never retried");
  } finally {
    wipeCtxvmEnv();
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("T25 sidecar canon untouched: the brief is derived data — resumeFrom evidence intact, NO new keys (the T24 law mirrored)", async () => {
  const tmp = mkdtempSync(join(tmpdir(), "ctxvm-t25-"));
  try {
    const pkg = join(tmp, "pkg");
    buildThrashSnapshot(pkg, 2);
    const traceDir = join(tmp, "trace");
    process.env.CTXVM_TRACE_DIR = traceDir;
    process.env.CTXVM_TRACE_NAME = "t25canon";
    process.env.CTXVM_RESUME_FROM = pkg;
    process.env.CTXVM_FEATURES = "handoff-inject";
    const { ctx, sessionCbs } = ctxStub();
    const cleanup = await live.setup(ctx as never);
    await sessionCbs[0]!(payload());
    await cleanup();
    const meta = JSON.parse(readFileSync(join(traceDir, "t25canon.meta.json"), "utf8")) as {
      resumeFrom?: Record<string, unknown>;
    };
    assert.ok(meta.resumeFrom, "resumeFrom evidence still stamped (§3 canon)");
    assert.equal(meta.resumeFrom!.snapshotDigest, snapshotDigest(pkg));
    assert.ok(!("brief" in meta), "no brief key in the sidecar canon");
    assert.ok(!("injected" in meta), "no injected key in the sidecar canon");
    assert.ok(!("resumeBrief" in (meta.resumeFrom as Record<string, unknown>)));
  } finally {
    wipeCtxvmEnv();
    rmSync(tmp, { recursive: true, force: true });
  }
});
