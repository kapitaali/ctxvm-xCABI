/**
 * T15 — the app-level tap: an async generator pass-over the `fullStream` that
 * mirrors tool lifecycle and model text into `@ctxvm/node` (design/adapters.md
 * §B). Every part YIELDS UNTOUCHED (mirror law); page/observe/scan mapping per
 * the §B table in contract.ts, with the 7.0.154 `preliminary` exclusion.
 */

import type { TextStreamPart, ToolSet } from "ai";
import type { Json, Tracer } from "../../node/src/index.ts";
import type { TurnAgreement } from "./contract.ts";

export interface TapHandle {
  vmFor(sessionKey: string): Tracer;
  sessionKey: string;
  counts: TurnAgreement;
  witness(message: string): void;
  armed: boolean;
}

/** Tap counter bumps for the sidecar's hookStats (opencode CaptureStats role). */
export interface TapStats {
  toolCalls: number;
  toolResults: number;
  preliminarySkipped: number;
  deniedOrErrors: number;
  textDeltas: number;
  scannedBytes: number;
  steps: number;
}

export function newTapStats(): TapStats {
  return {
    toolCalls: 0,
    toolResults: 0,
    preliminarySkipped: 0,
    deniedOrErrors: 0,
    textDeltas: 0,
    scannedBytes: 0,
    steps: 0,
  };
}

interface WindowPart {
  type: string;
  toolName?: unknown;
  toolCallId?: unknown;
  input?: unknown;
  output?: unknown;
  preliminary?: unknown;
  /** App-layer text-delta payload (provider layer calls it `delta`). */
  text?: unknown;
  /** Per-step provider receipt (`finish-step` in ai 7.0.154, RFC-0.1 §R3). */
  usage?: {
    inputTokens?: unknown;
    outputTokens?: unknown;
    inputTokenDetails?: { cacheReadTokens?: unknown } | null;
  } | null;
}

/**
 * Passthrough tap. `TextStreamPart` returns through unmodified; the tracer
 * never sees anything the app did not also get, byte-for-byte.
 */
export async function* ctxvmTap<TPart extends object>(
  stream: AsyncIterable<TPart>,
  handle: TapHandle,
  stats: TapStats = newTapStats(),
): AsyncGenerator<TPart, void, void> {
  const { vmFor, sessionKey, counts, witness, armed } = handle;
  const vm = armed ? vmFor(sessionKey) : null;

  let stepText = "";
  let stepBytes = 0;

  for await (const part of stream) {
    if (vm) {
      const p = part as WindowPart;
      switch (p.type) {
        case "start-step":
          stepText = "";
          stepBytes = 0;
          witness("start-step");
          break;
        case "text-delta": {
          // ai 7.0.154 app-layer rename (B0 erratum 3): TextStreamPart's
          // text-delta carries `text` — the provider-layer `delta` field is
          // renamed during projection into the fullStream union.
          const delta = typeof p.text === "string" ? p.text : "";
          stepText += delta;
          stepBytes += delta.length;
          stats.textDeltas += 1;
          break;
        }
        case "tool-call":
          stats.toolCalls += 1;
          // Pichay key = (tool, canonical(input)) exactly like T6 §3 /
          // opencode's execute.before mirror — pre-execution, no history walk.
          vm.recall({ tool: str(p.toolName), args: p.input as Json });
          witness(`tool-call tool=${str(p.toolName)}`);
          break;
        case "tool-result":
          if (p.preliminary === true) {
            // B0 erratum 2: partial stream slices are not the final transcript
            // result; the final `tool-result` part follows in the stream.
            stats.preliminarySkipped += 1;
            witness(`tool-result preliminary tool=${str(p.toolName)} — not a page`);
            break;
          }
          stats.toolResults += 1;
          vm.page({ tool: str(p.toolName), args: p.input as Json, content: p.output as Json });
          witness(`tool-result tool=${str(p.toolName)} — page`);
          break;
        case "tool-error":
        case "tool-output-denied":
          // Errors are not pages (T6 §2): mirrored read-only, no declaration.
          stats.deniedOrErrors += 1;
          witness(`${p.type} tool=${str(p.toolName)} — no page (T6 §2)`);
          break;
        case "error":
          // Upstream stream error surfacing (seen while pinning the mock
          // recipe: malformed mock fences yield an `error` part) — validated
          // read-only here: witness + pass-through, never a page.
          witness("error part on fullStream (upstream)");
          break;
        case "finish-step":
          // Scan AFTER the step's text is complete — one vm.scan per step
          // (design table), faults attributed to the producing turn (RFC-0 §5;
          // T15 note: no T3 one-turn-lag artifact here — the deltas ARE this
          // turn's output, unlike opencode's next-window re-walk).
          if (stepText.length > 0) {
            vm.scan({ text: stepText });
            stats.scannedBytes += stepBytes;
            witness(`finish-step scan bytes=${stepBytes}`);
          }
          counts.tapStepEnds += 1;
          stats.steps += 1;
          witness(
            `finish-step step=${counts.tapStepEnds} renders=${counts.middlewareRenders} agree=${counts.agree() ? "True" : "False"}`,
          );
          // W2b: relay the provider's own receipt to the turn it belongs to
          // (RFC-0.1 §R3). Pass-through law untouched — the shell part yields
          // to the app exactly as it arrived; the tracer gets a copy of the
          // numeric facts. Absent/invalid shapes → omitted, with a witness
          // line so the omission is observable, never silent.
          const u = p.usage;
          const details = u?.inputTokenDetails ?? null;
          const cached = details && typeof details.cacheReadTokens === "number" ? details.cacheReadTokens : undefined;
          if (u && typeof u.inputTokens === "number" && typeof u.outputTokens === "number") {
            vm.noteUsage({
              inputTokens: u.inputTokens,
              outputTokens: u.outputTokens,
              ...(cached !== undefined ? { cachedInputTokens: cached } : {}),
            });
            witness(`finish-step usage wired in=${u.inputTokens} out=${u.outputTokens}${cached !== undefined ? ` cached=${cached}` : ""}`);
          } else {
            witness("finish-step usage absent/invalid — providerUsage omitted (RFC-0 law)");
          }
          break;
        default:
          break; // unknown kinds pass through unmapped (mirror law)
      }
    }
    yield part; // pass-through, untouched — the app gets its exact stream
  }
}

function str(v: unknown): string {
  return typeof v === "string" ? v : String(v);
}
