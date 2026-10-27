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
 *
 * // T22 UC1: flush-first typed pause + boot-verified resume.
 * const packaged = capture.pauseAll({ turn: 3 }); // flush → pause (m7 name law)
 * const resumed = createCtxvmCapture({ ..., resumeFrom: { dir: "/…/handoff" } });
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
import {
  resumeVerify,
  uc1Pause,
  type PauseResult,
  type ResumeEvidence,
} from "./uc1-handoff.ts";

export {
  pauseTurnFromEnv,
  resumeVerify,
  rustBinDir,
  snapshotDigest,
  uc1Pause,
} from "./uc1-handoff.ts";
export type {
  PauseOptions,
  PauseResult,
  ResumeEvidence,
  ResumeResult,
} from "./uc1-handoff.ts";

export interface CtxvmCaptureInit extends TraceInit {
  /** Session key the middleware records turns for (default "local"). */
  sessionKey?: string;
  /**
   * T22 UC1: boot-verify a packaged snapshot BEFORE any hook work (the m7
   * law: verified boot precedes capture). Unverified → the constructor
   * THROWS (aborting at the boundary beats silently recording an unverified
   * boot — ruled 2026-10-27). When verified, the whole resumeVerify evidence
   * dict is stamped into every flushed sidecar's `resumeFrom` key
   * (09-plugin-parity §3 nesting; canon top-level keys untouched). The
   * resumed capture continues as a FRESH trace (its own era) — no trace
   * splice in mirror v0; the evidence, not a splice, is the provenance.
   */
  resumeFrom?: { dir: string };
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
  /**
   * T22 UC1 pause: flush-first convenience — runs the same finishAll flush,
   * then the mirrored `uc1Pause` on the FLUSHED name (m7 run-1 law: the
   * handoff name is the flush base `CTXVM_TRACE_NAME ?? sessionKey`, never a
   * fresh "handoff" default; ARG name › flush base; the raw exported
   * `uc1Pause` keeps the reference env chain power-user law). Options:
   * `turn` (default: env CTXVM_HANDOFF_TURN, junk = arm-but-degrade),
   * `dir` (default env CTXVM_TRACE_DIR — ARG beats env, arg-first law),
   * `name` (default flush base). Pause results never throw into the app
   * (exit-code shapes, capture never breaks). For the flush-is-the-caller's
   * -duty reference law, use the raw exported `uc1Pause` instead.
   */
  pauseAll(options?: { turn?: number | null; dir?: string; name?: string }): PauseResult;
}

export function createCtxvmCapture(init: CtxvmCaptureInit): CtxvmCapture {
  // T22 UC1: boot-verification BEFORE any hook work (m7 law). Unverified →
  // throw at init (ruled 2026-10-27: aborting at the boundary beats silently
  // recording an unverified boot).
  let resumeEvidence: ResumeEvidence | undefined;
  if (init.resumeFrom) {
    const rv = resumeVerify(init.resumeFrom.dir);
    if (!rv.verified) {
      throw new Error(
        `createCtxvmCapture: resumeFrom boot verification FAILED: ${rv.reason}`,
      );
    }
    resumeEvidence = rv.evidence;
  }
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
  if (resumeEvidence) {
    // The witness line is the call-side §3(4) surfacing the reference
    // resume kept (projection likewise flows through the evidence dict).
    witness(`resumeFrom verified digest=${resumeEvidence.snapshotDigest} turn=${resumeEvidence.snapTurn}`);
  }

  const middleware = ctxvmMiddleware({ vmFor, sessionKey, counts, witness, armed });
  const handle: TapHandle = { vmFor, sessionKey, counts, witness, armed };

  const flushAll = (): FinishedCapture[] => {
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
        // T22 UC1: whole-evidence nesting when the capture booted from a
        // verified package (canon keys untouched).
        resumeFrom: resumeEvidence,
      });
      witness(
        `flush ${key} wrote=${written.jsonlPath} renders=${counts.middlewareRenders} steps=${counts.tapStepEnds}`,
      );
      out.push({ sessionKey: key, trace, jsonlPath: written.jsonlPath, metaPath: written.metaPath });
    }
    // Deterministic flush order (opencode finishAll precedent).
    return out.sort((a, b) => (a.sessionKey < b.sessionKey ? -1 : 1));
  };

  const pauseAll = (
    options?: { turn?: number | null; dir?: string; name?: string },
  ): PauseResult => {
    flushAll();
    // The m7 run-1 law, library edition: pause the FLUSHED name — arg, else
    // the flush base (CTXVM_TRACE_NAME ?? sessionKey); never a fresh
    // "handoff" default. The reference env chain (CTXVM_HANDOFF_NAME) stays
    // visible only in the raw exported uc1Pause.
    const name = options?.name ?? process.env.CTXVM_TRACE_NAME ?? sessionKey;
    // Dir chain ARG-FIRST (options.dir beats env CTXVM_TRACE_DIR).
    const dir = options?.dir ?? process.env.CTXVM_TRACE_DIR;
    const result = uc1Pause({
      traceDir: dir ?? "",
      turn: options?.turn ?? null,
      handoffName: name,
    });
    // Call-side §3(4)/§4 witness rendering — library analogue of the hermes
    // `/ctxvm-handoff` line and the opencode cleanup rendering.
    witness(
      `pauseAll: exit_code=${result.exit_code} verified=${result.verified === true ? "True" : "False"}` +
        ` divergences=[${(result.divergences ?? []).join(",")}]` +
        ` diff_relation=${result.diff_relation === undefined ? "None" : result.diff_relation}`,
    );
    return result;
  };

  return {
    middleware,
    tap(stream) {
      return ctxvmTap(stream, handle, stats);
    },
    finishAll: flushAll,
    pauseAll,
  };
}
