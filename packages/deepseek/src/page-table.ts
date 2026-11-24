/**
 * W22 §4.2 — page table as a pure fold over the session log, registered as a
 * dsh session projection (ProjectionDefinition) so the live session and any
 * later replay agree.
 *
 *   tool/result       → insert/refresh page (first-declare-wins content hash)
 *   tool/call         → pair callId → (name, args); lookup by logicalRef (a
 *                       resident page re-called is a FaultOfResidentPage ledger
 *                       row — emitted trace-side by event-map's tracer.recall,
 *                       not stored in this projection)
 *   tool/result replace→ original page becomes stub; hash/tokens stay full
 *   tool/result append → full result restores stub to resident
 *   compaction/summary → shadowedSeqs' pages become evicted
 *
 * Page identity reuses @ctxvm/node's minters (toolRef/contentHash/approx4) so
 * the projection's logicalRefs match the trace's exactly. All event reads go
 * through eventData(), which merges DSH's `{type, seq, time, data}` envelope
 * with its surface metadata.
 *
 * schemastery is part of the DSH runtime only. The schema is built by an
 * injected factory (makePageTableStateSchema) that the runtime entry
 * (src/index.ts) calls at load; init()/apply() never touch the schema, so
 * tests load this module without schemastery installed (P15 option ii).
 */
import { approx4, canonicalJson, contentHash, toolRef } from '@ctxvm/node'
import type { ProjectionDefinition } from '@deepseek-ai/dsh-session-projection'
import type { SessionEvent, SessionHeader } from '@deepseek-ai/dsh-session/types'
import type { PageEntry, PageTableState } from './types.ts'
import { eventData, asRecord, asString, asNumberArray } from './event-data.ts'
import { isReplacement, replacementSourceSeq } from './surface.ts'

type Z = typeof import('@deepseek-ai/schemastery').default

/** Build the page-table state schema from the runtime's schemastery `z` (P15 option ii). */
export function makePageTableStateSchema(z: Z) {
  return z.object({
    pages: z.dict(z.object({
      kind: z.string(),
      contentHash: z.string(),
      tokens: z.number(),
      status: z.union([z.const('resident'), z.const('stub'), z.const('evicted')]),
      seq: z.number(),
    })),
    order: z.array(z.string()),
    calls: z.dict(z.object({ name: z.string(), args: z.any() })),
  })
}

let _pageTableStateSchema: unknown

/** Inject the built schema; called by the runtime entry (src/index.ts) at load. */
export function setPageTableStateSchema(schema: unknown): void {
  _pageTableStateSchema = schema
}

function textOfContent(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content.filter(b => asRecord(b)?.type === 'text')
      .map(b => asString(asRecord(b)?.text)).join('')
  }
  // Stored tool/result rows can have no message at all. canonicalJson(undefined)
  // is undefined and contentHash(undefined) throws; absent content stays a fact
  // (empty body hash), never a fabricated token count (RR-DSHPROJ-20261116).
  const canonical = content === undefined || content === null ? undefined : canonicalJson(content as never)
  return typeof canonical === 'string' ? canonical : ''
}

/** Pure: returns a new state, never mutates `state`. */
function markPages(state: PageTableState, seqs: readonly number[], status: PageEntry['status']): PageTableState {
  const set = new Set(seqs)
  let changed = false
  const pages: Record<string, PageEntry> = {}
  for (const [ref, p] of Object.entries(state.pages)) {
    // evicted is terminal: a later stub (surface replace) never regresses it
    if (set.has(p.seq) && p.status !== 'evicted' && p.status !== status) {
      pages[ref] = { ...p, status }
      changed = true
    } else {
      pages[ref] = p
    }
  }
  return changed ? { ...state, pages } : state
}

export const ctxvmPageTableProjection: ProjectionDefinition<'ctxvmPageTable', PageTableState> = {
  key: 'ctxvmPageTable',
  get stateSchema(): any {
    return _pageTableStateSchema
  },
  // stateVersion 3: only single-node tool/result replacements mark pages stub;
  // replacement text no longer refreshes the original hash/token accounting.
  stateVersion: 3,
  init(_header: SessionHeader, _inheritedEventCount: number): PageTableState {
    return { pages: {}, order: [], calls: {} }
  },
  apply(state: PageTableState, event: SessionEvent): PageTableState {
    const ev = eventData(event)
    const seq = typeof ev.seq === 'number' ? ev.seq : 0
    switch (ev.type) {
      case 'tool/call': {
        const raw = asString(ev.arguments)
        let args: unknown
        try { args = JSON.parse(raw) } catch { args = raw }
        const calls = { ...state.calls, [asString(ev.callId)]: { name: asString(ev.name), args } }
        return { ...state, calls }
      }
      case 'tool/result': {
        if (isReplacement(ev)) {
          const originalSeq = replacementSourceSeq(ev)
          return originalSeq === undefined ? state : markPages(state, [originalSeq], 'stub')
        }
        const message = asRecord(ev.message)
        const call = state.calls[asString(message?.toolCallId)]
        const ref = toolRef(undefined, call?.name ?? 'unknown', (call?.args ?? null) as never)
        const text = textOfContent(message?.content)
        const hash = contentHash(text)
        const tokens = approx4(text)
        const pages = { ...state.pages }
        const existing = pages[ref]
        let next: PageTableState
        if (existing) {
          // First-declare-wins hash. A full append restores a stub; evicted is terminal.
          pages[ref] = { ...existing, tokens, status: existing.status === 'evicted' ? 'evicted' : 'resident' }
          next = { ...state, pages }
        } else {
          pages[ref] = { kind: 'tool_result', contentHash: hash, tokens, status: 'resident', seq }
          next = { ...state, pages, order: [...state.order, ref] }
        }
        return next
      }
      case 'compaction/summary': {
        return markPages(state, asNumberArray(ev.shadowedSeqs) ?? [], 'evicted')
      }
      default: {
        // User/system/assistant replacements and pruner replacements are not
        // ctxvm stubs. Only the tool/result branch above may shadow tool pages.
        return state
      }
    }
  },
}
