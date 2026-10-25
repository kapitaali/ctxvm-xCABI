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

import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { createCtxvmPlugin, type CtxvmPlugin } from "../src/plugin.ts";
import { resumeVerify, uc1Pause } from "../src/uc1-handoff.ts";

interface HookRegistration {
  dispose?: () => Promise<void> | void;
}

/** Sidecar contract (09-plugin-parity.md §3): the adapter's own semver,
 * best-effort resolve from the adapter package's package.json via the module
 * URL — null if the module lives somewhere unexpected (shim copies carry the
 * same file, so the URL is the module's own). */
function adapterVersion(): string | null {
  try {
    // live/ -> ../package.json is packages/opencode/package.json (the adapter
    // package itself; import.meta.url is the module's own location even when a
    // shim re-exports it from a project plugin directory).
    const url = new URL("../package.json", import.meta.url);
    const pkg = JSON.parse(readFileSync(fileURLToPath(url), "utf8")) as {
      version?: string;
    };
    return pkg.version ?? null;
  } catch {
    return null;
  }
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

    // --- B3 resume: CTXVM_RESUME_FROM boot check (UC1-RESUME-MIRROR) --------
    // Mirror of the hermes register() block (live/__init__.py): verify the
    // paused snapshot BEFORE the first hook work; failures are loud witness
    // lines and the tracer continues UNVERIFIED (never blocks the agent
    // loop). `verified` renders Python-style True/False so the witness logs
    // byte-match across harnesses. Runs only while capture is active — the
    // adapter is inert without CTXVM_TRACE_DIR by contract (§1 09-plugin-
    // parity.md); hermes has no capture-independent boot witness either.
    let resumeFrom: Record<string, unknown> | null = null;
    const resumeFromEnv = process.env.CTXVM_RESUME_FROM;
    if (resumeFromEnv) {
      const resumeResult = resumeVerify(resumeFromEnv);
      // Hermes law mirrored: the evidence dict ALWAYS replaces the slot ({}
      // on early failures) — null stays reserved for "not resuming".
      resumeFrom = resumeResult.evidence;
      wit(
        `resume_from=${resumeFromEnv} verified=${resumeResult.verified ? "True" : "False"} reason=${resumeResult.reason}`,
      );
      if (!resumeResult.verified) {
        wit(
          `resume_from=${resumeFromEnv} UNVERIFIED — tracer continues, snapshot not trusted`,
        );
      }
    }


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
              harnessVersion: process.env.CTXVM_OPENCODE_VERSION ?? null,
              pluginVersion: adapterVersion(),
              model,
              provider,
              budgetTokens: budgetFromEnv(),
              capturedAt: new Date().toISOString(),
              hookStats: { ...stats, extraHookStats: {}, sessions: [sessionID] },
              traceStats: trace.stats,
              // B3 (§3 contract): resumeFrom stamped LAST — null when the
              // session is not resuming, the evidence dict (incl. {} on
              // failed boot checks) otherwise.
              resumeFrom,
            },
            null,
            2,
          )}\n`,
        );
        stats.sessions.push(sessionID);
      }

      // UC1-PAUSE-MIRROR: design §2 "package at flush" — with the handoff
      // envelope set (CTXVM_HANDOFF_DIR and/or CTXVM_HANDOFF_TURN), package
      // the just-flushed capture (era copy + export --odps). The flush above
      // already wrote the files; pause() itself maps hermes UC1Handoff.pause()
      // (the flush is deferred to the caller by reference design). handoff
      // dir resolves env-first (reference law) — the env recipe keeps
      // CTXVM_HANDOFF_DIR equal to CTXVM_TRACE_DIR so the flushed files are
      // found. Witness line mirrors their /ctxvm-handoff output rendering
      // (Python-style True/False/None). Mid-session CTXVM_HANDOFF_TURN
      // triggers need TS finish() idempotency — follow-up card.
      if (process.env.CTXVM_HANDOFF_DIR || process.env.CTXVM_HANDOFF_TURN) {
        const pauseResult = uc1Pause({
          traceDir,
          handoffName: process.env.CTXVM_TRACE_NAME ?? undefined,
        });
        const verified =
          pauseResult.verified === undefined
            ? "None"
            : pauseResult.verified
              ? "True"
              : "False";
        const divergences =
          pauseResult.divergences === undefined
            ? "None"
            : JSON.stringify(pauseResult.divergences);
        wit(
          `ctxvm-handoff: exit_code=${pauseResult.exit_code} verified=${verified} divergences=${divergences}`,
        );
        if (pauseResult.stderr) wit(`ctxvm-handoff stderr: ${pauseResult.stderr}`);
      }

      for (const reg of regs) await reg.dispose?.();
      wit("cleanup exit");
    };
  },
};
