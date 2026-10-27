/**
 * T15 — Vercel AI SDK ↔ `@ctxvm/node` capture context (T7 Adapter B,
 * mirror-only). Composes the middleware render-anchor (`middleware.ts`) and the
 * fullStream tap (`tap.ts`) over shared per-session tracers, and owns the
 * env-gated flush (`flush.ts`).
 *
 * Entry point for an app author:
 *
 * ```ts
 * import { createCtxvmCapture, wrapLanguageModel, streamText, tool } from "ai"-land
 * const capture = createCtxvmCapture({
 *   agentId: "my-app", model: "vendor/foo", provider: "vendor", budgetTokens: 120000,
 * });
 * const result = streamText({
 *   model: wrapLanguageModel({ model: baseModel, middleware: capture.middleware }),
 *   tools, prompt,
 * });
 * for await (const _ of capture.tap(result.fullStream)) {} // mirror pass-over
 * capture.finishAll(); // env-gated: no CTXVM_TRACE_DIR → returns []
 * ```
 *
 * Without `CTXVM_TRACE_DIR` nothing is recorded, nothing is metered, nothing is
 * written — the middleware is an identity, the tap is a pass-through, the
 * witness and tracers are never created. Mirror mode opens no control path.
 */

import { createTrace, type FinishedTrace, type TraceInit, type Tracer } from "../../node/src/index.ts";
import { TurnAgreement } from "./contract.ts";
import { witnessLine, writeCapture } from "./flush.ts";
import { ctxvmMiddleware } from "./middleware.ts";
import { ctxvmTap, newTapStats, type TapHandle, type TapStats } from "./tap.ts";

export interface CtxvmCaptureInit extends TraceInit {
  /** Session key the middleware records turns for (default "local"). */
  sessionKey?: string;
}

export interface FinishedCapture {
  sessionKey: string;
  trace: FinishedTrace;
  jsonlPath?: string;
  metaPath?: string;
}

export interface CtxvmCapture {
  /** `wrapLanguageModel({ model, middleware: capture.middleware })`. */
  middleware: ReturnType<typeof ctxvmMiddleware>;
  /**
   * Mirror pass-over the app's `fullStream`:
   * `for await (const part of capture.tap(result.fullStream)) {}`.
   * Every part yields untouched.
   */
  tap<TPart extends object>(stream: AsyncIterable<TPart>): AsyncGenerator<TPart, void, void>;
  /** Flush every session tracer. Env-gated: `[]`/no writes without CTXVM_TRACE_DIR. */
  finishAll(): FinishedCapture[];
}

export function createCtxvmCapture(init: CtxvmCaptureInit): CtxvmCapture {
  const traceDir = process.env.CTXVM_TRACE_DIR;
  const armed = Boolean(traceDir);
  const sessionKey = init.sessionKey ?? "local";

  const tracers = new Map<string, Tracer>();
  const vmFor = (key: string): Tracer => {
    const existing = tracers.get(key);
    if (existing) return existing;
    const created = createTrace({
      agentId: init.agentId,
      model: init.model,
      provider: init.provider,
      budgetTokens: init.budgetTokens,
    });
    tracers.set(key, created);
    return created;
  };

  const counts = new TurnAgreement();
  const stats: TapStats = newTapStats();
  const witness = (message: string): void => witnessLine(traceDir, message);

  if (armed) {
    witness(`init name=${process.env.CTXVM_TRACE_NAME ?? "<sessionKey>"}`);
  }

  const middleware = ctxvmMiddleware({ vmFor, sessionKey, counts, witness, armed });
  const handle: TapHandle = { vmFor, sessionKey, counts, witness, armed };

  return {
    middleware,
    tap(stream) {
      return ctxvmTap(stream, handle, stats);
    },
    finishAll() {
      if (!armed || tracers.size === 0) {
        witness("finishAll — nothing to flush (unarmed or no tracers)");
        return [];
      }
      const name = process.env.CTXVM_TRACE_NAME ?? sessionKey;
      const out: FinishedCapture[] = [];
      for (const [key, vm] of tracers) {
        const trace = vm.finish();
        witness(`flush ${key} bytes=${trace.jsonl.length}`);
        const written = writeCapture({
          // The write goes to the env dir even for non-default session keys;
          // the NAME is env-owned, so non-root keys never accumulate over it
          // (documented: multiple sessions → pass distinct CTXVM_TRACE_NAME or
          // use capture.name per finish — v0 ships the single-session law).
          traceDir: traceDir!,
          name: key === sessionKey ? name : `${name}.${key}`,
          sessionKey: key,
          trace,
          counts,
          stats,
          init: { agentId: init.agentId, model: init.model, provider: init.provider, budgetTokens: init.budgetTokens },
        });
        witness(
          `flush ${key} wrote=${written.jsonlPath} renders=${counts.middlewareRenders} steps=${counts.tapStepEnds}`,
        );
        out.push({ sessionKey: key, trace, jsonlPath: written.jsonlPath, metaPath: written.metaPath });
      }
      // Deterministic flush order (opencode finishAll precedent).
      return out.sort((a, b) => (a.sessionKey < b.sessionKey ? -1 : 1));
    },
  };
}
