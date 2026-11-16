/**
 * W22 — shared types for the dsh → xCABI adapter.
 */
import type { SessionId } from '@deepseek-ai/dsh-session/types'

/** One live tracer per session. */
export interface SessionTracer {
  sessionId: SessionId
  /** @ctxvm/node Tracer instance (created lazily on the first event). */
  tracer?: import('@ctxvm/node').Tracer
  /** callId → (name, parsed arguments) built from tool/call events. */
  calls: Map<string, { name: string; args: unknown }>
  /** Trace file path once written. */
  tracePath?: string
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
