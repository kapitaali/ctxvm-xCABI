/**
 * T15 — env-gated flush: `<name>.jsonl` + `<name>.meta.json` + hooks-witness
 * sidecar, mirroring the T12 opencode live adapter's flush contract (the
 * `.meta.json` sidecar shape follows the same fields where the concepts map;
 * UC layer fields are absent — T15 is trace-only by ruling).
 *
 * Env law (T12 mirror): the capture is armed by `CTXVM_TRACE_DIR` (else the
 * middleware/tap are pass-through no-ops); traces accumulate by
 * `CTXVM_TRACE_NAME` (default: the session key); model identity comes from
 * `CTXVM_MODEL`/`CTXVM_PROVIDER`/`CTXVM_AGENT_ID`/`CTXVM_BUDGET_TOKENS`.
 */

import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import type { FinishedTrace } from "../../node/src/index.ts";
import type { TurnAgreement } from "./contract.ts";
import type { TapStats } from "./tap.ts";

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
}

export function writeCapture(input: FlushInput): { jsonlPath: string; metaPath: string } {
  const { traceDir, name } = input;
  mkdirSync(traceDir, { recursive: true });
  const jsonlPath = join(traceDir, `${name}.jsonl`);
  const metaPath = join(traceDir, `${name}.meta.json`);

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
  };
  writeFileSync(metaPath, `${JSON.stringify(meta, null, 2)}\n`);
  return { jsonlPath, metaPath };
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
