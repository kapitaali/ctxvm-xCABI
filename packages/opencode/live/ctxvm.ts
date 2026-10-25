/**
 * T12 live adapter — OpenCode v2 promise-plugin surface → `@ctxvm/node` (T7 Adapter A).
 *
 * OpenCode v2 loads local plugins from `<project>/.opencode/plugins/*` as modules that
 * `export default { id, setup }`. `setup(ctx)` receives promise-style hook domains; the
 * three hooks this adapter needs are exactly the T9-mapped trigger sites:
 *
 *   ctx.session.hook("context", ...)          → SessionContext (primary model request only)
 *   ctx.tool.hook("execute.before", ...)      → ToolExecuteBefore
 *   ctx.tool.hook("execute.after", ...)       → ToolExecuteAfter
 *
 * This is the "dev-build wiring" the T9 spike deferred: no `packages/core` patch is
 * needed because v2 exposes the same domains to external plugins (see README.md here).
 *
 * Lifecycle: `setup` returns a cleanup function; OpenCode runs it on plugin unload /
 * server shutdown. The cleanup flushes every session tracer to `CTXVM_TRACE_DIR`
 * (`<name>.jsonl` + `<name>.meta.json`). The plugin is INERT unless `CTXVM_TRACE_DIR`
 * is set — loading it in a normal session has no effect.
 *
 * Payload deviation from the T9 pin (v2.1.3 `e965774f`) observed on the shipped v2.1.2
 * binary: `SessionContext.model` is `{ id, providerID, variant }` (no `modelID`). Only
 * metadata is affected; the mapping reads `sessionID` + `messages`, whose shapes match.
 */

import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { createCtxvmPlugin, type CtxvmPlugin } from "../src/plugin.ts";

interface HookRegistration {
  dispose?: () => Promise<void> | void;
}

/** Minimal structural view of the v2 plugin context (typed payloads live in the spike). */
export interface LiveContext {
  session: {
    hook(name: "context", callback: (input: any) => void | Promise<void>): Promise<HookRegistration>;
  };
  tool: {
    hook(
      name: "execute.before" | "execute.after",
      callback: (input: any) => void | Promise<void>,
    ): Promise<HookRegistration>;
  };
}

export interface CaptureStats {
  contexts: number;
  before: number;
  after: number;
  completed: number;
  errored: number;
  sessions: string[];
}

function budgetFromEnv(): number {
  const raw = Number(process.env.CTXVM_BUDGET_TOKENS ?? "200000");
  return Number.isFinite(raw) && raw > 0 ? raw : 200000;
}

export default {
  id: "ctxvm-live",
  async setup(ctx: LiveContext) {
    const traceDir = process.env.CTXVM_TRACE_DIR;
    if (!traceDir) return;

    // 2026-10-25 diagnostic witness: hooks are silent by design, so a missing
    // flush was previously undiagnosable (TUI-quit loss incident of 2026-10-25).
    // Every hook fire and every flush attempt is now appended to
    // hooks-witness.log. The witness must NEVER break capture — best effort.
    mkdirSync(traceDir, { recursive: true });
    const witnessLog = join(traceDir, "hooks-witness.log");
    const wit = (msg: string) => {
      try {
        appendFileSync(witnessLog, `${new Date().toISOString()} ${msg}\n`);
      } catch {
        /* witness failures are swallowed by design */
      }
    };
    wit(`init name=${process.env.CTXVM_TRACE_NAME ?? "<sessionID>"}`);


    const model = process.env.CTXVM_MODEL ?? "unknown/unknown";
    const provider = process.env.CTXVM_PROVIDER ?? "unknown";
    const vm: CtxvmPlugin = createCtxvmPlugin({
      agentId: process.env.CTXVM_AGENT_ID ?? "opencode",
      model,
      provider,
      budgetTokens: budgetFromEnv(),
    });

    const stats: CaptureStats = { contexts: 0, before: 0, after: 0, completed: 0, errored: 0, sessions: [] };
    const regs: HookRegistration[] = [];
    regs.push(
      await ctx.session.hook("context", (input) => {
        stats.contexts += 1;
        wit(`context session=${input?.sessionID ?? "?"}`);
        vm.onSessionContext(input);
      }),
    );
    regs.push(
      await ctx.tool.hook("execute.before", (input) => {
        stats.before += 1;
        wit(`before session=${input?.sessionID ?? "?"} tool=${input?.tool ?? "?"}`);
        vm.onToolExecuteBefore(input);
      }),
    );
    regs.push(
      await ctx.tool.hook("execute.after", (input) => {
        stats.after += 1;
        if (input?.status === "completed") stats.completed += 1;
        else stats.errored += 1;
        wit(`after session=${input?.sessionID ?? "?"} tool=${input?.tool ?? "?"} status=${input?.status ?? "?"}`);
        vm.onToolExecuteAfter(input);
      }),
    );

    return async () => {
      wit("cleanup entered (plugin unload)");
      const flushed = vm.finishAll();
      wit(`cleanup finishAll -> ${flushed.length} tracer(s)`);
      mkdirSync(traceDir, { recursive: true });
      const base = process.env.CTXVM_TRACE_NAME;
      for (const { sessionID, trace } of flushed) {
        const file = base || sessionID;
        writeFileSync(join(traceDir, `${file}.jsonl`), trace.jsonl);
        wit(`flush ${file}.jsonl bytes=${trace.jsonl.length} session=${sessionID}`);
        writeFileSync(
          join(traceDir, `${file}.meta.json`),
          `${JSON.stringify(
            {
              sessionID,
              harness: "opencode-v2-promise-plugin",
              opencodeVersion: process.env.CTXVM_OPENCODE_VERSION ?? null,
              model,
              provider,
              budgetTokens: budgetFromEnv(),
              capturedAt: new Date().toISOString(),
              hookStats: { ...stats, sessions: [sessionID] },
              traceStats: trace.stats,
            },
            null,
            2,
          )}\n`,
        );
        stats.sessions.push(sessionID);
      }
      for (const reg of regs) await reg.dispose?.();
      wit("cleanup exit");
    };
  },
};
