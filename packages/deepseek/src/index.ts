/**
 * W22 Phase 1 — @ctxvm/dsh: mirror-mode xCABI trace capture for DeepSeek Harness.
 *
 * Cordis plugin. Disabled unless Config.enabled; when enabled it listens to
 * session/event, keeps one @ctxvm/node tracer per session (created lazily on
 * the first event so a leading request/header supplies the real provider/model
 * for session.open), maps events via event-map.ts, registers the page-table
 * projection, and writes the trace on session end. Mirror mode never mutates
 * session state. Opt-in stub mode may append durable tool/result replacements
 * at agent/pre-step; passive tracing records those same replacements.
 *
 * Diagnostics: console.error('[ctxvm] …') — captured in the host log. Mirror
 * mode still never raises into the loop.
 */
import z from '@deepseek-ai/schemastery'
import type { Context } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-agent'
import { makeConfig, type CtxvmDshConfig } from './config.ts'
import { mapEvent } from './event-map.ts'
import { createSessionTracer, ensureTracer, finalizeTracer, flushTracer } from './tracer.ts'
import { ctxvmPageTableProjection, makePageTableStateSchema, setPageTableStateSchema } from './page-table.ts'
import { applyActivePreStep, type ActiveAgent } from './active-runtime.ts'
import { createActiveSessionState, type ActiveSessionState } from './context-engine.ts'
import type { SessionTracer } from './types.ts'

export const name = 'ctxvm-tracer'
export const inject = ['sessionProjections']

// P15 option (ii): inject the DSH runtime's schemastery at plugin load so the
// exported Config schema is real (cordis resolveConfig validates the row config
// and applies defaults) and the projection's stateSchema is set before register().
setPageTableStateSchema(makePageTableStateSchema(z))
export const Config = makeConfig(z)

const log = (...args: unknown[]): void => console.error('[ctxvm]', ...args)

export function apply(ctx: Context, config: CtxvmDshConfig): void {
  log('apply called, enabled =', config.enabled, 'traceDir =', config.traceDir)
  if (!config.enabled) return

  const sessions = new Map<string, SessionTracer>()
  const activeSessions = new Map<string, ActiveSessionState>()

  ctx.effect(() => {
    log('effect running; registering page-table projection')
    ctx.sessionProjections.register(ctxvmPageTableProjection)

    const offCreated = ctx.on('session/created', (session) => {
      log('session/created', String(session.id))
      sessions.set(String(session.id), createSessionTracer(session.id))
      if (config.mode === 'stub') activeSessions.set(String(session.id), createActiveSessionState())
    })

    let eventCount = 0
    const offEvent = ctx.on('session/event', (session, event) => {
      eventCount++
      const key = String(session.id)
      let st = sessions.get(key)
      if (!st) {
        st = createSessionTracer(session.id)
        sessions.set(key, st)
        if (config.mode === 'stub') activeSessions.set(key, createActiveSessionState())
      }
      if (eventCount <= 5 || eventCount % 100 === 0) log('session/event #' + eventCount, key.slice(0, 8), (event as { type?: string }).type)
      ensureTracer(st, event, config) // no-op once created
      mapEvent(st, event)
    })

    const offPreStep = config.mode === 'stub'
      ? ctx.on('agent/pre-step', async ({ agent, signal, messages }, next) => {
        const decision = await next()
        if (decision.kind === 'reject' || signal.aborted) return decision
        const key = String(agent.session.id)
        const st = sessions.get(key)
        if (st === undefined) return decision
        const state = activeSessions.get(key) ?? createActiveSessionState()
        activeSessions.set(key, state)
        const result = await applyActivePreStep(ctx, config, st, state, agent as unknown as ActiveAgent, signal, messages)
        if (result.appended > 0) log('active stub plan', key.slice(0, 8), result.plan.reason, 'appended', result.appended)
        return decision
      }, { prepend: true })
      : undefined

    const offDisposed = ctx.on('session/disposed', (session) => {
      log('session/disposed', String(session.id))
      const st = sessions.get(String(session.id))
      if (st) {
        sessions.delete(String(session.id))
        activeSessions.delete(String(session.id))
        finalizeTracer(st, config)
        if (st.tracer) {
          try {
            const p = flushTracer(st, config)
            log('trace written:', p)
          } catch (err) {
            log('flushTracer FAILED:', err)
          }
        }
      }
    })

    return () => {
      log('effect cleanup; flushing', sessions.size, 'live session(s)')
      offCreated(); offEvent(); offPreStep?.(); offDisposed()
      for (const st of sessions.values()) {
        finalizeTracer(st, config)
        if (st.tracer) {
          try {
            const p = flushTracer(st, config)
            log('trace written:', p)
          } catch (err) {
            log('flushTracer FAILED:', err)
          }
        }
      }
      sessions.clear()
      activeSessions.clear()
    }
  }, 'ctxvm-tracer')
}
