/**
 * W22 §4.2 — page table as a pure fold over the session log, registered as a
 * dsh session projection (ProjectionDefinition) so the live session and any
 * later replay agree.
 *
 *   tool/result      → insert/refresh page (first-declare-wins content hash)
 *   tool/call        → lookup by logicalRef; resident page ⇒ fault ledger row
 *   surface          → mark pages resident/stub
 *   compaction       → mark shadowed pages evicted
 *
 * schemastery is part of the DSH runtime only. The schema is built by an
 * injected factory (makePageTableStateSchema) that the runtime entry
 * (src/index.ts) calls at load; init()/apply() never touch the schema, so
 * tests load this module without schemastery installed (P15 option ii).
 */
import type { ProjectionDefinition } from '@deepseek-ai/dsh-session-projection'
import type { SessionEvent, SessionHeader } from '@deepseek-ai/dsh-session/types'
import type { PageTableState } from './types.ts'

type Z = typeof import('@deepseek-ai/schemastery').default

/** Build the page-table state schema from the runtime's schemastery `z` (P15 option ii). */
export function makePageTableStateSchema(z: Z) {
  return z.object({
    pages: z.dict(z.object({
      kind: z.string(),
      contentHash: z.string(),
      tokens: z.number(),
      status: z.union([z.const('resident'), z.const('stub'), z.const('evicted')]),
    })),
    order: z.array(z.string()),
  })
}

let _pageTableStateSchema: unknown

/** Inject the built schema; called by the runtime entry (src/index.ts) at load. */
export function setPageTableStateSchema(schema: unknown): void {
  _pageTableStateSchema = schema
}

export const ctxvmPageTableProjection: ProjectionDefinition<'ctxvmPageTable', PageTableState> = {
  key: 'ctxvmPageTable',
  get stateSchema(): any {
    return _pageTableStateSchema
  },
  stateVersion: 1,
  init(_header: SessionHeader, _inheritedEventCount: number): PageTableState {
    return { pages: {}, order: [] }
  },
  apply(state: PageTableState, event: SessionEvent): PageTableState {
    // TODO(Phase 1): fold tool/result, tool/call, surface, compaction/summary
    // exactly as W22 §4.2 specifies. Pure: never mutate `state` in place.
    return state
  },
}
