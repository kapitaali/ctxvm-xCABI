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

function range(start: number, end: number): number[] {
  const out: number[] = []
  for (let s = start; s <= end; s++) out.push(s)
  return out
}

function applySurfaceOp(state: PageTableState, ev: Record<string, unknown>): PageTableState {
  const op = asRecord(ev.surfaceOp)
  if (!op || op.op !== 'replace') return state
  const start = op.startSeq
  const end = op.endSeq
  const shadowed = asNumberArray(ev.sourceEventSeqs)?.length
    ? asNumberArray(ev.sourceEventSeqs)!
    : (typeof start === 'number' && typeof end === 'number' ? range(start, end) : [])
  return markPages(state, shadowed, 'stub')
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
          // first-declare-wins content hash; refresh tokens and residency
          pages[ref] = { ...existing, tokens, status: 'resident' }
          next = { ...state, pages }
        } else {
          pages[ref] = { kind: 'tool_result', contentHash: hash, tokens, status: 'resident', seq }
          next = { ...state, pages, order: [...state.order, ref] }
        }
        return applySurfaceOp(next, ev)
      }
      case 'compaction/summary': {
        return markPages(state, asNumberArray(ev.shadowedSeqs) ?? [], 'evicted')
      }
      default: {
        // other surface events (user/system/assistant/developer messages): only
        // a replace op can shadow tool pages; append touches nothing
        return applySurfaceOp(state, ev)
      }
    }
  },
}
