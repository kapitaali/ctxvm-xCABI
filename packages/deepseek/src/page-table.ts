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
 *   surface op        → append: declaring page resident; replace: shadowed
 *                       pages (sourceEventSeqs / startSeq..endSeq) become stub
 *   compaction/summary → shadowedSeqs' pages become evicted
 *
 * Page identity reuses @ctxvm/node's minters (toolRef/contentHash/approx4) so
 * the projection's logicalRefs match the trace's exactly.
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

/** Minimal structural view of the flattened event the session/event boundary passes. */
interface FlatEvent {
  type: string
  seq?: number
  callId?: string
  name?: string
  arguments?: string
  message?: { toolCallId?: string; content?: unknown }
  surfaceOp?: 'append' | { op: 'replace'; startSeq: number; endSeq: number }
  sourceEventSeqs?: number[]
  shadowedSeqs?: number[]
}

function textOfContent(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content.filter(b => b && (b as { type?: string }).type === 'text')
      .map(b => (b as { text: string }).text).join('')
  }
  // A tool/result in a stored dsh session can carry no message at all (all 154
  // in the failing session did). canonicalJson(undefined) is undefined, which
  // made contentHash(undefined) throw and broke session projection on resume.
  // Absent content is a fact, not a zero or a guess: hash the empty body so the
  // fold stays total and the page is still declared with its tool identity.
  const canonical = canonicalJson(content as never)
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

function applySurfaceOp(state: PageTableState, ev: FlatEvent): PageTableState {
  const op = ev.surfaceOp
  if (!op || op === 'append') return state
  if (op.op !== 'replace') return state
  const shadowed = ev.sourceEventSeqs?.length
    ? ev.sourceEventSeqs
    : range(op.startSeq, op.endSeq)
  return markPages(state, shadowed, 'stub')
}

function range(start: number, end: number): number[] {
  const out: number[] = []
  for (let s = start; s <= end; s++) out.push(s)
  return out
}

export const ctxvmPageTableProjection: ProjectionDefinition<'ctxvmPageTable', PageTableState> = {
  key: 'ctxvmPageTable',
  get stateSchema(): any {
    return _pageTableStateSchema
  },
  // stateVersion 2: state gained `calls` and PageEntry gained `seq` (Phase 1 task 5 fold).
  stateVersion: 2,
  init(_header: SessionHeader, _inheritedEventCount: number): PageTableState {
    return { pages: {}, order: [], calls: {} }
  },
  apply(state: PageTableState, event: SessionEvent): PageTableState {
    const ev = event as unknown as FlatEvent
    switch (ev.type) {
      case 'tool/call': {
        let args: unknown
        try { args = JSON.parse(ev.arguments ?? '') } catch { args = ev.arguments }
        const calls = { ...state.calls, [String(ev.callId)]: { name: String(ev.name), args } }
        return { ...state, calls }
      }
      case 'tool/result': {
        const call = state.calls[String(ev.message?.toolCallId)]
        const ref = toolRef(undefined, call?.name ?? 'unknown', (call?.args ?? null) as never)
        const text = textOfContent(ev.message?.content)
        const hash = contentHash(text)
        const tokens = approx4(text)
        const pages = { ...state.pages }
        const existing = pages[ref]
        let next: PageTableState
        if (existing) {
          // first-declare-wins content hash; refresh tokens and residency
          pages[ref] = { ...existing, tokens, status: 'resident' }
          next = { ...state, pages }
        } else {
          pages[ref] = { kind: 'tool_result', contentHash: hash, tokens, status: 'resident', seq: ev.seq ?? 0 }
          next = { ...state, pages, order: [...state.order, ref] }
        }
        return applySurfaceOp(next, ev)
      }
      case 'compaction/summary': {
        return markPages(state, ev.shadowedSeqs ?? [], 'evicted')
      }
      default: {
        // other surface events (user/system/assistant/developer messages): only
        // a replace op can shadow tool pages; append touches nothing
        return applySurfaceOp(state, ev)
      }
    }
  },
}
