/**
 * W22 — shared types for the dsh → xCABI adapter.
 */
import type { SessionId } from '@deepseek-ai/dsh-session/types'
import type { Tracer } from '@ctxvm/node'

/** One live tracer per session (created lazily on the first session event). */
export interface SessionTracer {
  sessionId: SessionId
  /** @ctxvm/node Tracer; undefined until the first event arrives. */
  tracer?: Tracer
  /** callId → (name, parsed arguments) built from tool/call events. */
  calls: Map<string, { name: string; args: unknown }>
  /** Trace file path once written. */
  tracePath?: string
}

/** Page table fold state (pure; registered as a session projection). */
export interface PageTableState {
  pages: Record<string, PageEntry>
  order: string[]
}

export interface PageEntry {
  kind: string
  contentHash: string
  tokens: number
  status: 'resident' | 'stub' | 'evicted'
}
