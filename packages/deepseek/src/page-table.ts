/**
 * W22 §4.2 — page table as a pure fold over the session log, registered as a
 * dsh session projection (ProjectionDefinition) so the live session and any
 * later replay agree.
 *
 *   tool/result      → insert/refresh page (first-declare-wins content hash)
 *   tool/call        → lookup by logicalRef; resident page ⇒ fault ledger row
 *   surface          → mark pages resident/stub
 *   compaction       → mark shadowed pages evicted
 */
import type { ProjectionDefinition } from '@deepseek-ai/dsh-session-projection'
import type { SessionEvent, SessionHeader } from '@deepseek-ai/dsh-session/types'
import type { PageTableState } from './types.ts'

// @deepseek-ai/schemastery is part of the DSH runtime and may not be
// available when this module is loaded outside DSH (e.g. in tests).
// The schema is loaded lazily on first access; init()/apply() do not require it.
let _pageTableStateSchema: any = null

/** Inject the schemastery schema (called by the DSH runtime at load time). */
export function setPageTableStateSchema(schema: any): void {
  _pageTableStateSchema = schema
}

/** Read the lazily-loaded schema (null until the DSH runtime has set it). */
export function getPageTableStateSchema(): any {
  return _pageTableStateSchema
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
