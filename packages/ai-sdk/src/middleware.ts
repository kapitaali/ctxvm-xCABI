/**
 * T15 — the render anchor: `wrapLanguageModel` middleware whose
 * `transformParams` is the one-fire-one-turn boundary (design/adapters.md §B).
 * THE MIRROR LAW IS THE POINT: params are returned unchanged — the middleware
 * exists to be a recording witness, never a control surface (design risk 5,
 * "mutability temptation"; the design explicitly forbids mutation).
 */

import type { LanguageModelMiddleware } from "ai";
import type { Tracer } from "../../node/src/index.ts";
import type { TurnAgreement } from "./contract.ts";

export interface MiddlewareHandle {
  /** Tracer for the capture session (caller owns keying; default "local"). */
  vmFor(sessionKey: string): Tracer;
  /** Session key the middleware records turns for (default "local"). */
  sessionKey: string;
  /** The risk-1 counter (middleware renders vs tap step-ends). */
  counts: TurnAgreement;
  /** Best-effort hooks-witness line (no dir set → swallowed no-op). */
  witness(message: string): void;
  /** Whether the capture is armed (CTXVM_TRACE_DIR set). False = pure no-op. */
  armed: boolean;
}

export function ctxvmMiddleware(handle: MiddlewareHandle): LanguageModelMiddleware {
  const { vmFor, sessionKey, counts, witness, armed } = handle;
  return {
    // No `specificationVersion` — ai 7.0.154 relaxes it to optional (V3/V4 both
    // accepted; the B0 erratum records the V4 base type).
    transformParams: async ({ type, params }) => {
      if (!armed) return params; // env-gated no-op: pass-through, unmetered

      const turn = counts.middlewareRenders; // pre-increment value = the turn id
      counts.middlewareRenders += 1;
      witness(`transformParams type=${type} turn=${turn}`);
      // 1 fire = 1 xCABI turn (design §B): the outbound request window IS the
      // turn boundary. Record params.prompt depth in the witness for the
      // flush-diagnosis story T12 won (silent-loss diagnosis).
      const prompt = (params as { prompt?: unknown }).prompt;
      const depth = Array.isArray(prompt) ? prompt.length : 0;
      witness(`transformParams done turn=${turn} promptMessages=${depth}`);

      vmFor(sessionKey).render();
      return params; // byte-unchanged — mirror law, witnessed by test
    },
  };
}
