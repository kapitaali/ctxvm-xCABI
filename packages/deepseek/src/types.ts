/**
 * W22 — shared types for the dsh → xCABI adapter.
 */
import type { SessionId } from '@deepseek-ai/dsh-session/types'

/** One successful passive stub observation. */
export interface StubRecord {
  ref: string
  contentHash: string
  stubText: string
  turn: number
}

/** Original append-origin tool result identity. */
export interface ResultPageIdentity {
  logicalRef: string
  contentHash: string
  tokens: number
}

/** One live tracer per session. */
export interface SessionTracer {
  sessionId: SessionId
  /** @ctxvm/node Tracer instance (created lazily on the first event). */
  tracer?: import('@ctxvm/node').Tracer
  /** callId → (name, parsed arguments) built from tool/call events. */
  calls: Map<string, { name: string; args: unknown }>
  /** Original result seq → exact PageId, used by replacement provenance. */
  pagesBySeq: Map<number, ResultPageIdentity>
  /** Zero-based xCABI turn; only turn/start advances it. */
  turn: number
  /** Successful stub pairs observed in this session. */
  stubbedRefs: StubRecord[]
  /** Original full-page tokens replaced by stubs. */
  evictedTokens: number
  /** Bounded non-fatal diagnostics; never raised into the session loop. */
  diagnostics: string[]
  /** Trace file path once written. */
  tracePath?: string
  /** Coverage sidecar path once written. */
  coveragePath?: string
  /** Events seen before request/header, replayed once the identity is known. */
  pending?: unknown[]
}

/** Page table fold state (pure; registered as a session projection). */
export interface PageTableState {
  pages: Record<string, PageEntry>
  order: string[]
  /** callId → (name, parsed arguments) from tool/call events; pairs a tool/result. */
  calls: Record<string, { name: string; args: unknown }>
}

export interface PageEntry {
  kind: string
  contentHash: string
  tokens: number
  status: 'resident' | 'stub' | 'evicted'
  /** seq of the event that declared the page — its surface-node identity. */
  seq: number
}
