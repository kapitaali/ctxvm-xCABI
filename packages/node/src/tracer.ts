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

/**
 * W15 / RFC-0.1 §R7: side-effect class tagged at tool REGISTRATION by the harness
 * adapter. Never inferred from model text or result content; an unregistered tool
 * is MUTATING (fail safe), and an absent class means the adapter could not tell.
 */
export type ToolEffect = "READ_ONLY" | "MUTATING";

/**
 * RFC-0.1 W13: the static cost billed on every turn whether or not any page is touched.
 * Every counter is optional so a harness that cannot see its request reports
 * `source: "unknown"` instead of a zero it did not measure.
 */
export interface PrefixCost {
  toolSchemas?: number;
  messageCount?: number;
  requestChars?: number;
  systemPromptBytes?: number;
  approxInputTokens?: number;
  source: "measured" | "estimated" | "unknown";
}

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
  /**
   * RFC-0.1 §R4 (R5-turn card): the page's own acquisition latency in whole
   * milliseconds — ACCEPTED-BUT-UNEMITTED. The declared turn (below) is always
   * stamped; this slot exists so a harness that measures a tool call can hand
   * the fact in, and it is emitted only when it is a safe integer ≥ 0. Absent
   * or invalid ⇒ the key is omitted, never null/float-coerced.
   */
  latencyMs?: number;
  /** W15 §R7: registration-time class supplied by the adapter, never inferred. */
  toolEffect?: ToolEffect;
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
  /**
   * RFC-0.1 W13: record the static per-turn cost (tool schemas, prefix bytes).
   * Harnesses that cannot see the request simply never call this; the render row
   * then carries `source: "unknown"`.
   */
  onApiRequest(payload: {
    tool_count?: number;
    message_count?: number;
    request_char_count?: number;
    approx_input_tokens?: number;
    system_prompt?: string;
  }): void;
  /** `identifier_scan` over produced model text (deduped per page per source, T3 v0). */
  scan(input: ScanInput): void;
  pin(input: PinInput): void;
  unpin(input: PinInput): void;
  /**
   * Attach the provider's own usage receipt (RFC-0.1 R3) to a turn's `call.meta`.
   * W2b: the ai-sdk tap relays each step's `finish-step` usage; the fact rides
   * the exact turn it was billed on. Omitted when the provider did not report —
   * never null, never coerced (float law: integers only, all-or-nothing).
   */
  noteUsage(input: ProviderUsageInput): void;
  finish(): FinishedTrace;
}

/** Provider-reported usage shape (RFC-0.1 §R3 validator law in mirror form). */
export interface ProviderUsageInput {
  inputTokens: number;
  outputTokens: number;
  /** Present only when the provider itself reported a cache-read receipt. */
  cachedInputTokens?: number;
}

/** RFC-0.1 §R3 strict intake: integers ≥ 0, both required fields present
 * (cached optional). Invalid intake returns null → the fact is omitted at the
 * wire, never null-coerced and never float-encoded (the schema would reject it). */
function providerUsageOf(
  input: ProviderUsageInput,
): { inputTokens: number; outputTokens: number; cachedInputTokens?: number } | null {
  const isTok = (n: unknown): n is number => typeof n === "number" && Number.isSafeInteger(n) && n >= 0;
  if (!isTok(input.inputTokens) || !isTok(input.outputTokens)) return null;
  if (input.cachedInputTokens !== undefined && !isTok(input.cachedInputTokens)) return null;
  const out: { inputTokens: number; outputTokens: number; cachedInputTokens?: number } = {
    inputTokens: input.inputTokens,
    outputTokens: input.outputTokens,
  };
  if (input.cachedInputTokens !== undefined)
    out.cachedInputTokens = input.cachedInputTokens; // a reported 0 is a fact, not an absence
  return out;
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

/**
 * W15 §R7 strict intake: the class is registration-owned, so a value outside the
 * union is a caller bug — throw rather than coerce, or a typo becomes a policy.
 */
function toolEffectOf(value: unknown): ToolEffect | undefined {
  if (value === undefined || value === null) return undefined;
  if (value === "READ_ONLY" || value === "MUTATING") return value;
  throw new Error(`toolEffect must be READ_ONLY or MUTATING (registration-time tag), got ${JSON.stringify(value)}`);
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
  /** RFC-0.1 §R4 (D9 policy): every event gains `ts` — RFC 3339 UTC ms. Default
   * ON; the per-trace opt-out `CTXVM_TRACE_TS=0` covers byte-stability needs
   * (canon-derived fixtures, determinism pins, drop minting). Stamps are minted
   * at the moment the event happens: front-stream events in push(), tail facts
   * (turn.render + call.meta) at their turn's render() snapshot time — so
   * repeated finish() flushes re-derive the SAME stamps (idempotency law). */
  const tsEnabled: boolean = process.env.CTXVM_TRACE_TS !== "0";
  const stamp = (): string => new Date().toISOString();
  /**
   * RFC-0.1 §R4: the canonical v0.1 wire order the rust writer minted puts `ts`
   * LAST on every line (events-v0-1.jsonl: …, providerUsage, ts). Optional per
   * the §R4 law — under the opt-out the key is simply absent, never null.
   */
  const turnStamps: (string | undefined)[] = [];
  // W13: prefix snapshots keyed by turn; last attempt of a turn wins.
  const turnPrefixes = new Map<number, PrefixCost>();
  /** Per-turn `call.meta` snapshots — flushed at finish() in turn order (see render). */
  type PendingMeta = { turn: number; hit: number; residentAtTurn: number; latencyMs?: number; providerUsage?: { inputTokens: number; outputTokens: number; cachedInputTokens?: number }; ts?: string };
  const pendingMeta: PendingMeta[] = [];
  /** A usage fact handed in before its turn is buffered — claimed by the next render, exactly once. */
  let orphanUsage: PendingMeta["providerUsage"] = undefined;

  /**
   * RFC-0 §6 payload field ORDER is the spec table order; object insertion order carries
   * it through JSON.stringify. Optional integer fields are omitted when unknown
   * ("optional fields are omitted when unknown — never `null`", RFC-0 preamble).
   */
  const push = (e: object): void => {
    if (tsEnabled) (e as { ts?: string }).ts = stamp(); // R4-ts: rides LAST (assignment order)
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

  /**
   * RFC-0.1 §R5 + §R4 (R5-turn card): every `page.declare` carries the tracer's
   * turn counter AT DECLARATION TIME. Declarations made before the first render
   * carry the pre-first-render counter (-1) and stamp as 0 — the standing RFC-0
   * §5 convention `page.fault` already uses. `latencyMs` rides between `turn`
   * and `ts` when (and only when) the caller supplied a valid one, so the wire
   * order is type,page,turn,latencyMs?,ts (`ts` lands LAST via push).
   */
  const declarePage = (
    ref: string,
    hash: string,
    kind: PageKind,
    tokens: number,
    latencyMs: number | undefined,
    toolEffect: ToolEffect | undefined,
  ): void => {
    const t = turn < 0 ? 0 : turn;
    const e: Record<string, unknown> = {
      type: "page.declare",
      page: { id: { logicalRef: ref, contentHash: hash }, kind, tokens },
      turn: t,
    };
    if (latencyMs !== undefined) e.latencyMs = latencyMs;
    // W15 §R7: the class rides between latencyMs and ts (ts must land last).
    if (toolEffect !== undefined) e.toolEffect = toolEffect;
    push(e);
  };

  /** RFC-0.1 §R4 strict intake (mirrors providerUsageOf / noteUsage): whole
   * milliseconds ≥ 0 only. Anything else is an ABSENCE, not a zero. */
  const declareLatencyOf = (input: PageInput): number | undefined =>
    typeof input.latencyMs === "number" && Number.isSafeInteger(input.latencyMs) && input.latencyMs >= 0
      ? input.latencyMs
      : undefined;

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
      const declareLatency = declareLatencyOf(input);
      const toolEffect = toolEffectOf(input.toolEffect);

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
        declarePage(ref, hash, kind, tokens, declareLatency, toolEffect);
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
        declarePage(ref, hash, kind, tokens, declareLatency, toolEffect);
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
      // W2b: a usage role opened before its turn is buffered rides THIS turn.
      const orphan = orphanUsage;
      orphanUsage = undefined;
      // R4-ts: the turn's tail facts mint their timestamp at snapshot time;
      // finish() flushes re-derive these exact stamps (idempotency law).
      const now = tsEnabled ? stamp() : undefined;
      turnStamps.push(now);
      pendingMeta.push({ turn, hit, residentAtTurn, latencyMs: input.latencyMs, providerUsage: orphan, ts: now });
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

    noteUsage(input: ProviderUsageInput) {
      // All-or-nothing validation upstream (R3 law): invalid intake is omitted,
      // never coerced. Attaches to the newest buffered turn snapshot; a fact
      // arriving before any render is claimed by the next one (orphan slot).
      const shaped = providerUsageOf(input);
      if (shaped === null) return;
      if (pendingMeta.length > 0) {
        pendingMeta[pendingMeta.length - 1].providerUsage = shaped;
      } else {
        orphanUsage = shaped;
      }
    },

    onApiRequest(payload) {
      const atTurn = turn >= 0 ? turn : 0;
      const snapshot: PrefixCost = { source: "unknown" };
      const has = (v: unknown): v is number =>
        typeof v === "number" && Number.isFinite(v) && v >= 0;
      if (has(payload.tool_count)) snapshot.toolSchemas = Math.trunc(payload.tool_count);
      if (has(payload.message_count)) snapshot.messageCount = Math.trunc(payload.message_count);
      if (has(payload.request_char_count)) snapshot.requestChars = Math.trunc(payload.request_char_count);
      if (has(payload.approx_input_tokens))
        snapshot.approxInputTokens = Math.trunc(payload.approx_input_tokens);
      if (typeof payload.system_prompt === "string" && payload.system_prompt.length > 0)
        snapshot.systemPromptBytes = Buffer.byteLength(payload.system_prompt, "utf8");
      if (snapshot.toolSchemas !== undefined || snapshot.messageCount !== undefined ||
          snapshot.requestChars !== undefined || snapshot.approxInputTokens !== undefined ||
          snapshot.systemPromptBytes !== undefined) {
        snapshot.source = "measured";
      }
      turnPrefixes.set(atTurn, snapshot);
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
        // R4-ts: cached from snapshot time — repeated flushes stay byte-stable.
        // W13: the render row carries the static cost. A harness with no request
        // visibility says "unknown" — absence of a measurement, never a zero.
        // Assigned BEFORE ts: ts must ride last on every event (R4 key order).
        tr.prefix = turnPrefixes.get(t) ?? { source: "unknown" };
        if (turnStamps[t] !== undefined) tr.ts = turnStamps[t];
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
        // RFC-0.1 §R3: providerUsage rides after cacheEstimate/latencyMs — the
        // canonical v0.1 wire order the rust writer minted. cacheEstimate's
        // providerReported stays false: the upgrade of est* to provider truth
        // is its own decisive card (open question, RR-RFC01E2).
        if (m.providerUsage !== undefined) meta.providerUsage = m.providerUsage;
        // R4-ts rides LAST (after providerUsage) — canonical v0.1 wire order.
        if (m.ts !== undefined) meta.ts = m.ts;
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
