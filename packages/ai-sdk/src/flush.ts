/**
 * T15 — env-gated flush: `<name>.jsonl` + `<name>.meta.json` +
 * `<name>.coverage.json` (W17) + hooks-witness sidecar, mirroring the T12
 * opencode live adapter's flush contract (the
 * `.meta.json` sidecar shape follows the same fields where the concepts map;
 * UC layer fields are absent — T15 is trace-only by ruling).
 *
 * Env law (T12 mirror): the capture is armed by `CTXVM_TRACE_DIR` (else the
 * middleware/tap are pass-through no-ops); traces accumulate by
 * `CTXVM_TRACE_NAME` (default: the session key); model identity comes from
 * `CTXVM_MODEL`/`CTXVM_PROVIDER`/`CTXVM_AGENT_ID`/`CTXVM_BUDGET_TOKENS`.
 */

import { createHash } from "node:crypto";
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import type { FinishedTrace } from "../../node/src/index.ts";
import type { TurnAgreement } from "./contract.ts";
import { READ_ONLY_TOOLS } from "./tap.ts";
import type { TapStats } from "./tap.ts";
import type { ResumeEvidence } from "./uc1-handoff.ts";

/** Version of the pinned `ai` SDK, resolved best-effort at flush time. */
function aiVersion(): string | null {
  try {
    // src/ -> ../node_modules/ai/package.json is THIS package's installed pin.
    const url = new URL("../node_modules/ai/package.json", import.meta.url);
    const pkg = JSON.parse(readFileSync(fileURLToPath(url), "utf8")) as { version?: string };
    return pkg.version ?? null;
  } catch {
    return null;
  }
}

/** Version of THIS adapter package, resolved best-effort (packages/ai-sdk/package.json). */
function adapterVersion(): string | null {
  try {
    // src/ -> ../package.json is the package's own manifest.
    const url = new URL("../package.json", import.meta.url);
    const pkg = JSON.parse(readFileSync(fileURLToPath(url), "utf8")) as { version?: string };
    return pkg.version ?? null;
  } catch {
    return null;
  }
}

export interface FlushInput {
  traceDir: string;
  name: string;
  sessionKey: string;
  trace: FinishedTrace;
  counts: TurnAgreement;
  stats: TapStats;
  init: {
    agentId: string;
    model: string;
    provider: string;
    budgetTokens: number;
  };
  /** T22 UC1: whole-resumeVerify evidence dict when the capture was booted
   * with `resumeFrom` (09-plugin-parity §3 — the WHOLE dict flows through as
   * a nested opt-in field; the canon top-level sidecar keys are untouched). */
  resumeFrom?: ResumeEvidence;
}

/**
 * W17 coverage manifest body (sidecar `<file>.coverage.json`, NOT a tenth event).
 *
 * Session facts come from the trace's own `session.open` row, never from env, so
 * the claims are byte-true by construction and the checker verifies them against
 * the same bytes it digests. `instrumentation.ts` is read at FLUSH time to mirror
 * the tracer's per-trace `CTXVM_TRACE_TS=0` opt-out (D9 captures are ts-less and
 * must still pass the checker with `ts: false`).
 */
function coverageManifest(input: FlushInput, traceJsonl: string): Record<string, unknown> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any — trace bytes are whatever the codec emitted
  const rows: any[] = traceJsonl
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const open: any = rows.find((r) => r.type === "session.open") ?? {};
  const declares = rows.filter((r) => r.type === "page.declare");
  const toolResults = declares.filter((r: any) => r?.page?.kind === "tool_result");
  const faults = rows.filter((r) => r.type === "page.fault");
  const declaresByClass: Record<string, number> = { READ_ONLY: 0, MUTATING: 0 };
  for (const r of toolResults) {
    if (r.toolEffect in declaresByClass) declaresByClass[r.toolEffect] += 1;
  }
  const faultsBySource: Record<string, number> = {
    tool_recall: 0,
    identifier_scan: 0,
    explicit_api: 0,
    semantic: 0,
  };
  for (const r of faults) {
    if (r.source in faultsBySource) faultsBySource[r.source] += 1;
  }
  const turns = new Set<number>(
    rows.filter((r) => r.type === "turn.render" && Number.isInteger(r.turn)).map((r) => r.turn),
  );
  const pageKeys = new Set<string>();
  for (const r of declares) {
    const id = (r as any)?.page?.id;
    if (id?.logicalRef != null && id?.contentHash != null) {
      pageKeys.add(`${id.logicalRef}\u0000${id.contentHash}`);
    }
  }
  return {
    xcabiCoverage: "0.1",
    traceFile: `${input.name}.jsonl`,
    traceDigest: createHash("sha256").update(traceJsonl, "utf8").digest("hex"),
    session: {
      sessionID: input.sessionKey,
      environmentId: open.environmentId ?? null,
      model: open.model ?? null,
      provider: open.provider ?? null,
    },
    toolTable: {
      readOnlyRegistered: [...READ_ONLY_TOOLS].sort(),
      default: "MUTATING", // the W15 fail-safe law, restated byte-verifiably
    },
    instrumentation: {
      ts: process.env.CTXVM_TRACE_TS !== "0", // tracer's per-trace opt-out, re-read at flush
      toolEffect: true,
      identifierScan: true,
    },
    plugin: {
      version: adapterVersion(),
      harness: "ai-sdk-middleware",
      harnessVersion: process.env.CTXVM_AI_SDK_VERSION ?? null,
    },
    captures: {
      turns: turns.size,
      pages: pageKeys.size,
      declares: declares.length,
      declaresByClass,
      faults: faults.length,
      faultsBySource,
    },
  };
}

export function writeCapture(input: FlushInput): {
  jsonlPath: string;
  metaPath: string;
  coveragePath: string;
} {
  const { traceDir, name } = input;
  mkdirSync(traceDir, { recursive: true });
  const jsonlPath = join(traceDir, `${name}.jsonl`);
  const metaPath = join(traceDir, `${name}.meta.json`);
  const coveragePath = join(traceDir, `${name}.coverage.json`);

  writeFileSync(jsonlPath, input.trace.jsonl); // FinishedTrace.jsonl carries the trailing newline

  const meta = {
    sessionID: input.sessionKey,
    harness: "ai-sdk",
    aiSdkVersion: aiVersion(),
    captureVersion: "0.1",
    model: input.init.model,
    provider: input.init.provider,
    agentId: input.init.agentId,
    budgetTokens: input.init.budgetTokens,
    capturedAt: new Date().toISOString(),
    hookStats: {
      middlewareRenders: input.counts.middlewareRenders,
      tapStepEnds: input.counts.tapStepEnds,
      ...input.stats,
    },
    mirrorCountsAgree: input.counts.agree(),
    traceStats: input.trace.stats,
    ...(input.resumeFrom ? { resumeFrom: input.resumeFrom } : {}),
  };
  writeFileSync(metaPath, `${JSON.stringify(meta, null, 2)}\n`);
  // W17: the coverage sidecar describes the bytes just written — flush-only, never
  // at write-through partials (a pruned partial would leave coverage describing
  // bytes that no longer exist).
  writeFileSync(coveragePath, `${JSON.stringify(coverageManifest(input, input.trace.jsonl), null, 2)}\n`);
  return { jsonlPath, metaPath, coveragePath };
}

export function witnessLine(traceDir: string | undefined, message: string): void {
  if (!traceDir) return; // unarmed capture: the witness is a no-op, by contract
  try {
    mkdirSync(traceDir, { recursive: true });
    appendFileSync(join(traceDir, "hooks-witness.log"), `${new Date().toISOString()} ${message}\n`);
  } catch {
    /* witness failures are swallowed by design (T12 law) */
  }
}
