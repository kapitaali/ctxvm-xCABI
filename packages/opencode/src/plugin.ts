/**
 * T9 spike — OpenCode ↔ `@ctxvm/node` adapter (T7 design "Adapter A", mirror-only).
 *
 * Handlers accept the exact hook payload contracts pinned at
 * `anomalyco/opencode` e965774f (see `./opencode-contract.ts`). In a dev OpenCode
 * build the wiring is one line per hook against `packages/core/src/plugin`
 * (`hooks.register("session", "context", …)` etc.); the registry test-double in
 * `test/replay-registry.ts` is the spike's stand-in — payload→tracer MAPPING is
 * what this package proves.
 *
 * Read-only guarantee (T7 risk 5): the scan channel uses the HISTORY-fallback
 * (assistant/user texts entering the window at each `session.context` fire) rather
 * than the mutable `aisdk.language` tap, so every wire surface is read-only. The
 * tap remains an explicit enablement for later.
 *
 * Timing (RFC-0 §5, per T7's "one fire = one turn" fact):
 *   - `session.context` fire = one model request = one xCABI turn.
 *   - Tool hooks fire DURING turn t's lifecycle → page declares land and render at
 *     t+1; faults attributed to t (scan runs BEFORE the render call inside the
 *     handler, so the tracer's current-turn is t).
 *   - `status !== "completed"` → no page (T6 §2). `execute.before` mirrors only.
 */

import { createTrace, contentHash, type FinishedTrace, type Json, type TraceInit, type Tracer } from "../../node/src/index.ts";

import type {
  HookEvent,
  LooseMessage,
  SessionContextPayload,
  ToolExecuteAfter,
  ToolExecuteBefore,
} from "./opencode-contract.ts";

/** Text leaves of a message, across the common `@opencode/ai` Message shapes. */
function messageTexts(message: LooseMessage): string[] {
  const zone = message.parts ?? message.content;
  if (zone) return zone.map((part) => part.text ?? "").filter((t) => t.length > 0);
  return message.text ? [message.text] : [];
}

/** All text entering the compose window this turn (user + assistant + tool summaries). */
export function transcriptTexts(messages: readonly LooseMessage[]): string {
  return messages.flatMap(messageTexts).join("\n");
}

/**
 * Page body from `Tool.Result.content`: text items verbatim (joined by `\n` —
 * the transcript material); non-text items contribute a deterministic type marker.
 */
export function contentToPageBody(content: ToolExecuteAfter["result"]["content"]): string {
  const kept = content.map((item) =>
    item.type === "text" || item.type === undefined
      ? (item.text ?? "")
      : `<${item.type}${typeof item.name === "string" ? `:${item.name}` : ""}>`,
  );
  return kept.join("\n");
}

export interface PluginInit extends TraceInit {}

export interface CtxvmPlugin {
  /** `hooks.register("session", "context", …)` — model-request.ts:399–404 (primary only). */
  onSessionContext(payload: SessionContextPayload): void;
  /** `hooks.register("tool", "execute.before", …)` — Pichay key `(tool, canonical(input))`. */
  onToolExecuteBefore(payload: ToolExecuteBefore): void;
  /** `hooks.register("tool", "execute.after", …)` — page only on `status:"completed"`. */
  onToolExecuteAfter(payload: ToolExecuteAfter): void;
  /** Flush every session tracer (dev-build wiring: session-end/process-exit hook). */
  finishAll(): { sessionID: string; trace: FinishedTrace }[];
  /** Tracer access for tests. */
  tracerFor(sessionID: string): Tracer;
}

export function createCtxvmPlugin(init: PluginInit): CtxvmPlugin {
  const tracers = new Map<string, Tracer>();
  const vmFor = (sessionID: string): Tracer => {
    const existing = tracers.get(sessionID);
    if (existing) return existing;
    const created = createTrace(init);
    tracers.set(sessionID, created);
    return created;
  };

  return {
    onSessionContext(payload) {
      const vm = vmFor(payload.sessionID);
      // Scan BEFORE render: the texts entering this window were produced during the
      // PREVIOUS turn's lifecycle → faults attribute to that turn (RFC-0 §5). The
      // tracer's per-page·source dedupe absorbs the window re-walk across later turns.
      vm.scan({ text: transcriptTexts(payload.messages) });
      vm.render();
    },

    onToolExecuteBefore(payload) {
      // Mirror-only read of the mutable input; recall keys on (tool, canonicalArgs)
      // exactly like the T6 Pichay matcher — no history re-walk needed.
      vmFor(payload.sessionID).recall({ tool: payload.tool, args: payload.input as Json });
    },

    onToolExecuteAfter(payload) {
      if (payload.status !== "completed") return; // errors are not pages (T6 §2)
      const body = contentToPageBody(payload.result.content);
      void contentHash(body); // identity is computed inside page(); kept explicit for parity with the T6 §2 doc
      vmFor(payload.sessionID).page({ tool: payload.tool, args: payload.input as Json, content: body });
      // result.metadata (incl. toolOutput.truncate marks) is call.meta material — parked
      // (design/mcp-shim.md §6); see README for the truncation-approximation note.
    },

    finishAll() {
      const out: { sessionID: string; trace: FinishedTrace }[] = [];
      for (const [sessionID, vm] of tracers) out.push({ sessionID, trace: vm.finish() });
      return out.sort((a, b) => (a.sessionID < b.sessionID ? -1 : 1));
    },

    tracerFor(sessionID) {
      return vmFor(sessionID);
    },
  };
}
