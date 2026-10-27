/**
 * T15 — Vercel AI SDK part→tracer contract (`design/adapters.md` §B), re-pinned
 * at `ai` 7.0.154 (latest stable tag; B0 survey: hook points intact, errata in
 * the design doc).
 *
 * Anchored to the harness's OWN exported types per the design's law ("the
 * payload types are the contract — they are the fixture schema"): the tap types
 * against the exported `TextStreamPart`, and the middleware against the
 * exported `LanguageModelMiddleware`. These types are also every fixture's
 * schema.
 *
 * The mapping (design §B table, at 7.0.154):
 *
 *   fullStream part           → @ctxvm/node call
 *   -------------------------  ----------------------------------------------
 *   (middleware transformParams) → vm.render()   — 1 fire = 1 xCABI turn
 *   tool-call                  → vm.recall({ tool, args: input })   (Pichay key)
 *   tool-result                → vm.page({ tool, args, content: output })
 *     .preliminary === true    → SKIPPED (partial stream slice, not the
 *                                transcript result — B0 erratum 2)
 *   tool-error / tool-output-denied → nothing (errors are not pages, T6 §2)
 *   text-delta                 → buffered per step; scanned ONCE at finish-step
 *                                (design table) — faults attribute to the
 *                                producing turn (RFC-0 §5, T15 note: no T3
 *                                one-turn-lag artifact, unlike the opencode
 *                                window re-walk)
 *   start-step                 → resets the step text buffer
 *   finish-step                → vm.scan(stepText) + the design-risk-1 count
 *                                witness (renders vs steps must agree)
 *   any other part kind        → pass-through, unmapped (mirror law)
 *
 * Two glue invariants, both witnessed by tests:
 *   MIRROR  — middleware returns `params` unchanged; tap yields every part
 *             untouched (mirror mode never mutates anything received).
 *   COUNTS  — one turn counter per `transformParams` fire + one per
 *             `finish-step`; they must agree (design risk 1). Divergence ⇒
 *             witness warning lines + `mirrorCountsAgree: false` in the
 *             sidecar; the tracer is never mis-scored.
 */

/** Part kinds the tap owns (everything else passes through unmapped). */
export const mappedPartKinds = [
  "tool-call",
  "tool-result",
  "tool-error",
  "tool-output-denied",
  "text-delta",
  "start-step",
  "finish-step",
] as const;

/**
 * The design-risk-1 witness: middleware-side render count vs tap-side step-end
 * count, asserted equal per step. A mismatch never throws into the model loop —
 * it taints the sidecar (`mirrorCountsAgre: false`) and witnesses loudly.
 */
export class TurnAgreement {
  middlewareRenders = 0;
  tapStepEnds = 0;
  mismatches = 0;

  /** Agree after the current step end? Called at each finish-step. */
  agree(): boolean {
    return this.middlewareRenders === this.tapStepEnds;
  }

  inspect(): { middlewareRenders: number; tapStepEnds: number; mismatches: number } {
    return {
      middlewareRenders: this.middlewareRenders,
      tapStepEnds: this.tapStepEnds,
      mismatches: this.mismatches,
    };
  }
}
