/**
 * W22 — per-session @ctxvm/node tracer lifecycle.
 *
 * One tracer per sessionId; created lazily on the first session event (using
 * the real provider/model when the first event is a request/header), fed from
 * event-map.ts, finished (trace written) on session/disposed or plugin unload.
 * Never throws into the event loop.
 *
 * API note (verified against packages/node v0.1.0):
 *   - finish() returns { jsonl, events, stats } — jsonl has a trailing newline.
 *   - onApiRequest takes { tool_count?, message_count?, request_char_count?,
 *     approx_input_tokens?, system_prompt? } — provider/model are NOT accepted
 *     here; they belong in createTrace(init).
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { createTrace, type Tracer } from '@ctxvm/node'
import type { SessionId } from '@deepseek-ai/dsh-session/types'
import type { CtxvmDshConfig } from './config.ts'
import { eventData, asRecord, asString } from './event-data.ts'
import { mapEvent } from './event-map.ts'
import type { SessionEvent } from '@deepseek-ai/dsh-session/types'
import type { SessionTracer } from './types.ts'

/**
 * Expand `~` and `${VAR}` / `${VAR:-default}` in the configured trace dir.
 * schemastery defaults are static strings, so env expansion happens here.
 */
export function resolveTraceDir(traceDir: string): string {
  // Env expansion FIRST: the ${VAR:-default} default can itself contain `~`
  // (e.g. ${XDG_STATE_HOME:-~/.local/state}), so tilde expansion must run after.
  const withEnv = traceDir.replace(/\$\{([A-Z_][A-Z0-9_]*)(?::-([^}]*))?\}/g, (m, name: string, dflt?: string) => {
    const v = process.env[name]
    return v !== undefined && v !== '' ? v : (dflt ?? m)
  })
  return withEnv.replace(/^~(?=$|\/)/, homedir())
}

export function openTracer(
  sessionId: SessionId,
  init: { model: string; provider: string },
  config: CtxvmDshConfig,
): SessionTracer {
  const tracer: Tracer = createTrace({
    agentId: `${config.agentIdPrefix}:${String(sessionId).slice(0, 12)}`,
    model: init.model,
    provider: init.provider,
    budgetTokens: config.budgetTokens,
    tokenizerId: config.tokenizerId,
  })
  return { sessionId, tracer, calls: new Map() }
}

/**
 * Create the session's tracer once DSH commits a request/header with real
 * provider/model. Earlier events are buffered and replayed in order, since
 * @ctxvm/node fixes session.open identity at createTrace time. A session that
 * ends without a header is finalized with the fail-safe placeholders.
 */
export function ensureTracer(st: SessionTracer, firstEvent: unknown, config: CtxvmDshConfig): void {
  if (st.tracer) return
  const ev = eventData(firstEvent as never)
  if (ev.type !== 'request/header') {
    st.pending ??= []
    if (st.pending.length < 2048) st.pending.push(firstEvent)
    return
  }
  let model = 'unknown'
  let provider = 'dsh'
  const header = asRecord(ev.header)
  const headerConfig = asRecord(header?.config)
  if (headerConfig) {
    provider = asString(headerConfig.provider) || provider
    model = asString(headerConfig.model) || model
  }
  st.tracer = openTracer(st.sessionId, { model, provider }, config).tracer
  replayPending(st)
}

/** Flush a session that never committed a request/header, keeping the trace total. */
export function finalizeTracer(st: SessionTracer, config: CtxvmDshConfig): void {
  if (st.tracer) return
  st.tracer = openTracer(st.sessionId, { model: 'unknown', provider: 'dsh' }, config).tracer
  replayPending(st)
}

function replayPending(st: SessionTracer): void {
  const pending = st.pending ?? []
  st.pending = []
  for (const event of pending) mapEvent(st, event as SessionEvent)
}

/** Write the finished trace to <traceDir>/<sessionId>-<ts>.jsonl. Returns the path. */
export function flushTracer(st: SessionTracer, config: CtxvmDshConfig): string {
  if (!st.tracer) throw new Error('flushTracer: no tracer for session ' + String(st.sessionId))
  const finished = st.tracer.finish()
  const dir = resolveTraceDir(config.traceDir)
  mkdirSync(dir, { recursive: true, mode: 0o700 })
  const path = join(dir, `${String(st.sessionId)}-${Date.now()}.jsonl`)
  // v0.1.0: finish().jsonl is the full RFC-0 JSONL document, trailing newline included.
  writeFileSync(path, finished.jsonl, { mode: 0o600 })
  st.tracePath = path
  return path
}
