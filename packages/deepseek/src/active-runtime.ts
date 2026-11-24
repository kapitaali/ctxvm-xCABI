/** DSH pre-step integration for the opt-in active context engine. */
import type { Context } from '@deepseek-ai/cordis'
import type { SessionEvent, SessionId } from '@deepseek-ai/dsh-session/types'
import type { CtxvmDshConfig } from './config.ts'
import type { SessionTracer } from './types.ts'
import {
  buildStubText,
  estimateEngineMessage,
  pageKey,
  planActiveStub,
  textOfContent,
  type ActivePlan,
  type ActiveSessionState,
  type EngineMessage,
  type PageCandidate,
} from './context-engine.ts'

interface ActiveSession {
  id: SessionId
  seq: number
  surface: { nodes: readonly number[] }
  deriveMessages(): readonly EngineMessage[]
  append(type: 'tool/result', data: Record<string, unknown>, options: {
    surfaceOp: { op: 'replace'; startSeq: number; endSeq: number }
    sourceEventSeqs: number[]
  }): unknown
}

export interface ActiveAgent {
  id: SessionId
  session: ActiveSession
}

interface SurfaceSnapshot {
  capturedThroughSeq: number | null
  events: readonly SessionEvent[]
}

interface SessionQueryLike {
  readSurface(sessionId: SessionId): Promise<SurfaceSnapshot>
}

interface TokenMeterLike {
  measure(session: unknown): { totalTokens?: number; surfaceTokens?: number }
}

interface SessionStoreLike {
  flush(session: unknown): Promise<boolean>
}

export interface ActiveRuntimeResult {
  plan: ActivePlan
  appended: number
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : undefined
}

function diagnostic(state: ActiveSessionState, message: string): void {
  state.diagnostics.push(message)
  if (state.diagnostics.length > 100) state.diagnostics.shift()
}

function emptyResult(): ActiveRuntimeResult {
  return {
    plan: { selected: [], reason: 'fits', floorTokens: 0, residentTokens: 0, droppedTokens: 0 },
    appended: 0,
  }
}

/** Build current append-origin tool-result candidates from the nondeprecated surface query. */
export async function buildActiveCandidates(
  ctx: Context,
  agent: ActiveAgent,
  tracer: SessionTracer,
  state: ActiveSessionState,
  signal: AbortSignal,
): Promise<{ messages: EngineMessage[]; candidates: PageCandidate[]; surfaceEvents: Map<number, SessionEvent> }> {
  const query = ctx.get('sessionQuery') as SessionQueryLike | undefined
  if (query === undefined) {
    diagnostic(state, 'sessionQuery is unavailable; active selection skipped')
    return { messages: [], candidates: [], surfaceEvents: new Map() }
  }
  const surface = await query.readSurface(agent.id)
  signal.throwIfAborted()
  const capturedOffset = surface.capturedThroughSeq === null ? 0 : surface.capturedThroughSeq + 1
  if (capturedOffset !== Number(agent.session.seq)) {
    diagnostic(state, `surface snapshot stale: ${capturedOffset} != ${agent.session.seq}`)
    return { messages: [], candidates: [], surfaceEvents: new Map() }
  }

  const messages = [...agent.session.deriveMessages()]
  const indexByMessageId = new Map(messages.map((message, index) => [(message as { id?: unknown }).id, index]))
  const projectedById = new Map(messages.map(message => [(message as { id?: unknown }).id, message]))
  const surfaceEvents = new Map(surface.events.map(event => [Number(event.seq), event]))
  const candidates: PageCandidate[] = []
  for (const event of surface.events) {
    if (event.type !== 'tool/result' || event.surfaceOp !== 'append') continue
    const seq = Number(event.seq)
    const identity = tracer.pagesBySeq.get(seq)
    if (identity === undefined) {
      diagnostic(state, `active candidate ${seq} has no original PageId`)
      continue
    }
    const data = asRecord(event.data)
    const rawMessage = asRecord(data?.message)
    const messageId = rawMessage?.id
    const message = projectedById.get(messageId)
    const messageIndex = indexByMessageId.get(messageId)
    if (message === undefined || message.role !== 'tool' || messageIndex === undefined) {
      diagnostic(state, `active candidate ${seq} has no projected tool message`)
      continue
    }
    const callId = message.toolCallId
    if (typeof callId !== 'string') {
      diagnostic(state, `active candidate ${seq} has no tool-call id`)
      continue
    }
    const call = tracer.calls.get(callId)
    if (call === undefined) {
      diagnostic(state, `active candidate ${seq} has no tool-call identity`)
      continue
    }
    candidates.push({
      seq,
      ref: identity.logicalRef,
      contentHash: identity.contentHash,
      tokens: estimateEngineMessage(message),
      name: call.name,
      args: call.rawArgs ?? call.args,
      callId,
      messageIndex,
      text: textOfContent(message.content),
    })
  }
  return { messages, candidates, surfaceEvents }
}

/** Apply one active plan before the proposed step opens. Never throws into the loop. */
export async function applyActivePreStep(
  ctx: Context,
  config: CtxvmDshConfig,
  tracer: SessionTracer,
  state: ActiveSessionState,
  agent: ActiveAgent,
  signal: AbortSignal,
  prospectiveMessages: readonly EngineMessage[] = [],
): Promise<ActiveRuntimeResult> {
  if (signal.aborted) return emptyResult()
  try {
    const { messages, candidates, surfaceEvents } = await buildActiveCandidates(ctx, agent, tracer, state, signal)
    if (candidates.length === 0) return emptyResult()
    let measuredTokens: number | undefined
    try {
      const meter = ctx.get('tokenMeter') as TokenMeterLike | undefined
      measuredTokens = meter?.measure(agent.session).totalTokens
    } catch {
      // Pre-step precedes the first step/start; the engine-owned apx4 estimator
      // remains authoritative for selection when the meter has no anchor yet.
    }
    const plan = planActiveStub([...messages, ...prospectiveMessages], candidates, config, state, measuredTokens)
    if (plan.selected.length === 0 || config.stubDropped === 'off') return { plan, appended: 0 }
    let appended = 0
    for (const candidate of plan.selected) {
      if (signal.aborted) break
      if (!agent.session.surface.nodes.includes(candidate.seq)) continue
      const event = surfaceEvents.get(candidate.seq)
      if (event?.type !== 'tool/result') continue
      const data = structuredClone(event.data) as Record<string, unknown>
      const message = asRecord(data.message)
      if (message === undefined) {
        diagnostic(state, `active replacement ${candidate.seq} has no message`)
        continue
      }
      data.message = { ...message, content: [{ type: 'text', text: buildStubText(candidate) }] }
      try {
        agent.session.append('tool/result', data, {
          surfaceOp: { op: 'replace', startSeq: candidate.seq, endSeq: candidate.seq },
          sourceEventSeqs: [candidate.seq],
        })
        state.stubbedKeys.add(pageKey(candidate))
        appended++
      } catch (error) {
        diagnostic(state, `active replacement ${candidate.seq} failed: ${error instanceof Error ? error.message : String(error)}`)
      }
    }
    if (appended > 0) {
      try {
        const store = ctx.get('sessions') as SessionStoreLike | undefined
        if (store !== undefined && !await store.flush(agent.session)) {
          diagnostic(state, 'active replacement flush had no persistence listener')
        }
      } catch (error) {
        diagnostic(state, `active replacement flush failed: ${error instanceof Error ? error.message : String(error)}`)
      }
    }
    return { plan, appended }
  } catch (error) {
    diagnostic(state, `active pre-step failed: ${error instanceof Error ? error.message : String(error)}`)
    return emptyResult()
  }
}
