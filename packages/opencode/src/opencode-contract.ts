/**
 * T9 spike — pinned-snapshot payload contracts for the OpenCode adapter.
 *
 * SOURCE OF TRUTH (not this file): `anomalyco/opencode` branch `dev`
 * @ e965774fa0e2a8ffb27bf02827a2c3c6a8c0f45b (v2.1.3):
 *   - packages/plugin/src/effect/tool.ts    → ToolHooks (verbatim fields below)
 *   - packages/plugin/src/effect/session.ts → SessionHooks / SessionContext
 * These local copies exist only so the spike runs without an npm workspace;
 * field names are verbatim. Replace with `@opencode/plugin` imports at dev-build
 * wiring time (T7 risk 6: anchor to their packages, never to our copies).
 */

/** `@opencode/schema/session` `Session.ID` (string brand). */
export type SessionID = string;

export interface ToolExecuteBefore {
  readonly tool: string;
  readonly sessionID: SessionID;
  readonly agent: string;
  readonly messageID: string;
  readonly id: string;
  /** Mutable in OpenCode; this adapter is mirror-only — we never write it. */
  input: unknown;
}

/**
 * `Tool.Result` — `{ output?, content, metadata? }` per the T7 trigger-site survey
 * (`packages/core/src/tool.ts executeTool`, success path). `content` is the
 * transcript material; `output` is structured side-data; `metadata` is call.meta
 * material (design/mcp-shim.md §6) — v0 does not consume it.
 */
export interface ToolResult {
  output?: unknown;
  readonly content: readonly { readonly type: string; readonly text?: string; readonly [k: string]: unknown }[];
  metadata?: Record<string, unknown>;
}

export type ToolExecuteAfter = {
  readonly tool: string;
  readonly sessionID: SessionID;
  readonly agent: string;
  readonly messageID: string;
  readonly id: string;
  readonly input: unknown;
} & (
  | { readonly status: "completed"; readonly result: ToolResult }
  | { readonly status: "error"; readonly error: Record<string, unknown> }
);

/** Tolerant member of the `@opencode/ai` `Message` family (parts/text/content). */
export interface LooseMessage {
  readonly role: string;
  readonly parts?: readonly { readonly type?: string; readonly text?: string }[];
  readonly content?: readonly { readonly type?: string; readonly text?: string }[];
  readonly text?: string;
}

/**
 * `SessionContext` — fired ONLY for `kind: "primary"` by construction
 * (model-request.ts wires compaction/generate/title to their own hooks),
 * so no kind-filtering is needed in the adapter (T7 §Adapter A, fact 2).
 */
export interface SessionContextPayload {
  readonly sessionID: SessionID;
  readonly agent: string;
  /** `@opencode/schema/model` `Model.Ref` — fields not read by this adapter. */
  readonly model: { readonly providerID: string; readonly modelID: string };
  readonly system: readonly unknown[];
  readonly messages: readonly LooseMessage[];
  readonly options: Record<string, unknown>;
  readonly tools: Record<string, { description: string }>;
}

/** Chronological hook recording for fixture replay (all hooks serialize as JSON). */
export type HookEvent =
  | { readonly hook: "session.context"; readonly payload: SessionContextPayload }
  | { readonly hook: "tool.execute.before"; readonly payload: ToolExecuteBefore }
  | { readonly hook: "tool.execute.after"; readonly payload: ToolExecuteAfter };
