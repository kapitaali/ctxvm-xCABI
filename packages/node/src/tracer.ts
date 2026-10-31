/**
 * `@ctxvm/node` v0 tracer — telemetry-first, mirror-only (RFC-0 §6 event grammar).
 *
 * The tracer never mutates anything it is given, never throws on semantic conditions
 * (RFC-0 §13: violations are logged values, state untouched), and never evicts — v0 has
 * no paging/eviction logic (control ships later per `design/mcp-shim.md` §5). Faults
 * against resident pages are legal xCABI facts that replay records as
 * `FaultOfResidentPage` ledger rows — that row IS the double-fetch waste metric (T6 §4).
 *
 * Turn-level facts (`turn.render`, `call.meta`) flush at `finish()`: replay's static
 * analysis derives resident tokens from the WHOLE declared table (a page declared at
 * any point counts from turn 0), so turn facts are countersigned against the final
 * derived composition, not against a mid-stream view.
 */

import {
  approx4,
  canonicalJson,
  contentHash,
  fileRef,
  identityTokens,
  imageRef,
  type Json,
  summaryRef,
  toolRef,
} from "./ident.ts";

export type PageKind = "file" | "tool_result" | "summary" | "image_ref";
export type FaultSource = "tool_recall" | "identifier_scan" | "explicit_api" | "semantic";

export interface TraceInit {
  /** Stable across sessions of the same agent class (RFC-0 `agentId: S`). */
  agentId: string;
  /** e.g. `openai/gpt-5`. */
  model: string;
  /** e.g. `openai`. */
  provider: string;
  /** Declared page-budget units (inert bookkeeping in v0; drives `turn.render.headroom`). */
  budgetTokens: number;
  /** Declared-token unit id; default `apx4-char` (see `approx4`). */
  tokenizerId?: string;
}

export interface PageInput {
  kind?: PageKind;
  /** Tool provenance → `tool:<name>(<canonicalArgs>)` via the T6 §2 identity minting. */
  tool?: string;
  server?: string;
  args?: Json;
  /** Pre-built ref override (`fileRef`/`summaryRef`/`imageRef`; beats tool+args). */
  ref?: string;
  /** Full content, string or value (values are canonically serialized for hashing). */
  content: Json | string;
  /** Override the `apx4-char` estimate when a real tokenizer is wired. */
  tokens?: number;
}

export interface RecallInput {
  tool?: string;
  server?: string;
  args?: Json;
  /** Pre-built ref override. */
  ref?: string;
}

export interface RenderInput {
  /** Optional wall-clock of the provider call this turn renders (emitted on `call.meta`). */
  latencyMs?: number;
}

export interface ScanInput {
  text: string;
  latencyMs?: number;
}

export interface PinInput {
  ref: string;
  reason: string;
}

export interface TraceStats {
  turns: number;
  pages: number;
  faults: number;
  residentTokens: number;
}

export interface FinishedTrace {
  /** RFC-0 JSONL, trailing newline included. */
  jsonl: string;
  events: readonly object[];
  stats: TraceStats;
}

export interface Tracer {
  page(input: PageInput): { logicalRef: string; contentHash: string; tokens: number };
  /** Mark a pre-execution re-call (`tool.execute.before` in the OpenCode adapter). */
  recall(input: RecallInput): void;
  /** Turn boundary: reveals newly declared pages; turn-level facts flush at finish(). */
  render(input?: RenderInput): void;
  /** `identifier_scan` over produced model text (deduped per page per source, T3 v0). */
  scan(input: ScanInput): void;
  pin(input: PinInput): void;
  unpin(input: PinInput): void;
  finish(): FinishedTrace;
}

/** Kind inference for convenience callers (error results are callers' responsibility, T6 §2). */
export function inferKind(content: Json | string): PageKind {
  const s = typeof content === "string" ? content : canonicalJson(content);
  return /^https?:\/\//.test(s) ? "image_ref" : "tool_result";
}

interface Page {
  logicalRef: string;
  contentHash: string;
  kind: PageKind;
  tokens: number;
  revealed: boolean;
  revealedAtPrev: boolean;
  identities: readonly string[];
}

export function createTrace(init: TraceInit): Tracer {
  const events: object[] = [];
  const tokenizerId = init.tokenizerId ?? "apx4-char";
  const declared = new Map<string, Page>(); // key = logicalRef (identity = ref+hash pair in facts)
  const pendingRecall = new Set<string>();
  const touched = new Set<string>(); // T3 v0 touch proxy: one fault per page per source
  let turn = -1;
  let faultCount = 0;
  /** Every declared page key (ref|hash → tokens) — the derived-composition table. */
  const allDeclared = new Map<string, number>();
  /** Per-turn `call.meta` snapshots — flushed at finish() in turn order (see render). */
  const pendingMeta: { turn: number; hit: number; residentAtTurn: number; latencyMs?: number }[] = [];

  /**
   * RFC-0 §6 payload field ORDER is the spec table order; object insertion order carries
   * it through JSON.stringify. Optional integer fields are omitted when unknown
   * ("optional fields are omitted when unknown — never `null`", RFC-0 preamble).
   */
  const push = (e: object): void => {
    events.push(e);
  };

  push({
    type: "session.open",
    agentId: init.agentId,
    model: init.model,
    provider: init.provider,
    budgetTokens: init.budgetTokens,
    tokenizerId,
    // RFC-0.1 R0 (D4 approved; D8 = emitter version switch first): every trace
    // this build emits declares schemaVersion "0.1" — the version boundary.
    // Traces BEFORE this line (frozen corpus drops m1–m8, package fixtures)
    // stay v0: they are committed golden bytes, never regenerated.
    schemaVersion: "0.1",
  });

  const emitFault = (p: Page, source: FaultSource, latencyMs: number | undefined): void => {
    const dedupeKey = `${p.logicalRef}|${source}`;
    if (touched.has(dedupeKey)) return;
    touched.add(dedupeKey);
    faultCount += 1;
    const t = turn < 0 ? 0 : turn; // recalls during the pre-first-render lifecycles belong to turn 0
    const e: Record<string, unknown> = {
      type: "page.fault",
      turn: t,
      page: { logicalRef: p.logicalRef, contentHash: p.contentHash },
      source,
      latencyMs,
    };
    if (latencyMs === undefined) delete e.latencyMs;
    push(e);
  };

  const reveal = (p: Page, t: number): void => {
    push({ type: "page.render", turn: t, page: { logicalRef: p.logicalRef, contentHash: p.contentHash }, mode: "full" });
    p.revealed = true;
  };

  const tracer: Tracer = {
    page(input) {
      const content = typeof input.content === "string" ? input.content : canonicalJson(input.content);
      const hash = contentHash(content);
      const ref = input.ref ?? toolRef(input.server, input.tool ?? "unknown", input.args ?? null);
      const tokens = input.tokens ?? approx4(content);
      const kind = input.kind ?? inferKind(content);

      const existing = declared.get(ref);
      if (existing === undefined) {
        const p: Page = {
          logicalRef: ref,
          contentHash: hash,
          kind,
          tokens,
          revealed: false,
          revealedAtPrev: false,
          identities: identityTokens(ref),
        };
        declared.set(ref, p);
        allDeclared.set(`${ref}|${hash}`, tokens);
        push({ type: "page.declare", page: { id: { logicalRef: ref, contentHash: hash }, kind, tokens } });
        // A page can only be a double fetch if it pre-existed; a first call's own landing
        // is not waste (T6 §4 hash-before-count honesty).
        pendingRecall.delete(ref);
        return { logicalRef: ref, contentHash: hash, tokens };
      }

      if (existing.contentHash === hash) {
        if (pendingRecall.delete(ref)) emitFault(existing, "tool_recall", undefined);
      } else {
        // Fresh fetch: same logicalRef, new content ⇒ new page identity (T6 §4); the
        // changed-underlying-resource case is never scored as waste.
        existing.contentHash = hash;
        existing.tokens = tokens;
        existing.kind = kind;
        existing.revealed = false;
        existing.revealedAtPrev = false;
        allDeclared.set(`${ref}|${hash}`, tokens); // fresh fetch ⇒ a second page key (ref, hash-v2)
        push({ type: "page.declare", page: { id: { logicalRef: ref, contentHash: hash }, kind, tokens } });
        pendingRecall.delete(ref);
      }
      return { logicalRef: ref, contentHash: hash, tokens: existing.tokens };
    },

    recall(input) {
      const ref = input.ref ?? toolRef(input.server, input.tool ?? "unknown", input.args ?? null);
      // Only pre-existing pages can be re-calls; a first call marks nothing (its own
      // landing declares the page instead).
      if (declared.has(ref)) pendingRecall.add(ref);
    },

    render(input: RenderInput = {}) {
      turn += 1;
      for (const p of declared.values()) {
        if (!p.revealed) reveal(p, turn);
      }
      // Page-layer estimate for `call.meta` (v0 approximation: non-page prompt text is
      // not tokenized; providerReported stays false until adapters wire it).
      let hit = 0;
      let residentAtTurn = 0;
      for (const p of declared.values()) {
        if (p.revealedAtPrev) hit += p.tokens;
        residentAtTurn += p.tokens;
        p.revealedAtPrev = p.revealed;
      }
      pendingMeta.push({ turn, hit, residentAtTurn, latencyMs: input.latencyMs });
    },

    scan(input) {
      for (const p of declared.values()) {
        if (p.identities.some((tok) => input.text.includes(tok))) {
          emitFault(p, "identifier_scan", input.latencyMs);
        }
      }
    },

    pin(input) {
      const p = declared.get(input.ref);
      if (p === undefined) return;
      push({ type: "page.pin", page: { logicalRef: p.logicalRef, contentHash: p.contentHash }, reason: input.reason });
    },

    unpin(input) {
      const p = declared.get(input.ref);
      if (p === undefined) return;
      push({ type: "page.unpin", page: { logicalRef: p.logicalRef, contentHash: p.contentHash }, reason: input.reason });
    },

    finish() {
      // Derived-composition arithmetic (RFC-0 replay's static analysis): every declared
      // page key is resident at every turn in v0 — there is no evict path, and
      // ctxvm-core `tally_at` sums the WHOLE table. Turn facts therefore flush here,
      // after all content is known, instead of eagerly mid-session.
      //
      // T17.7 parity (hermes plugin.py finish, docstring mirrored): "Flush:
      // turn.render × (turn+1) then call.meta × len(pending_meta). Idempotent:
      // the tail is computed per call and never appended to the event stream,
      // so repeated flushes (mid-session handoff, session end, unload) produce
      // the same JSONL instead of duplicating turn/meta records." pendingMeta
      // is never cleared — the tail re-renders from live state each call, so
      // lifecycle recorded AFTER a first flush joins the next transcript.
      let resident = 0;
      for (const tokens of allDeclared.values()) resident += tokens;
      const tail: object[] = [];
      for (let t = 0; t <= turn; t++) {
        const tr: Record<string, unknown> = {
          type: "turn.render",
          turn: t,
          residentTokens: resident,
          evictedTokens: 0,
        };
        if (init.budgetTokens > 0) tr.headroom = init.budgetTokens - resident;
        tail.push(tr);
      }
      for (const m of pendingMeta) {
        const meta: Record<string, unknown> = {
          type: "call.meta",
          turn: m.turn,
          provider: init.provider,
          cacheEstimate: {
            estHitTokens: m.hit,
            estMissTokens: m.residentAtTurn - m.hit,
            providerReported: false,
          },
        };
        if (m.latencyMs !== undefined) meta.latencyMs = m.latencyMs;
        tail.push(meta);
      }
      const merged = [...events, ...tail];
      return {
        jsonl: `${merged.map((e) => JSON.stringify(e)).join("\n")}\n`,
        events: merged,
        stats: { turns: turn + 1, pages: allDeclared.size, faults: faultCount, residentTokens: resident },
      };
    },
  };
  return tracer;
}

export { approx4, canonicalJson, contentHash, fileRef, imageRef, summaryRef, toolRef };
