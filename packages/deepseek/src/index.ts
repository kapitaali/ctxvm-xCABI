/**
 * W22 Phase 1 — @ctxvm/dsh: mirror-mode xCABI trace capture for DeepSeek Harness.
 *
 * Cordis plugin. Disabled unless Config.enabled; when enabled it listens to
 * session/event, keeps one @ctxvm/node tracer per session (created lazily on
 * the first event so a leading request/header supplies the real provider/model
 * for session.open), maps events via event-map.ts, registers the page-table
 * projection, and writes the trace on session end. It never mutates session
 * state and never appends to the session log (acceptance: log identical
 * with/without the plugin).
 *
 * Diagnostics: console.error('[ctxvm] …') — captured in the host log. Mirror
 * mode still never raises into the loop.
 */
import type { Context } from '@deepseek-ai/cordis'
import { Config, type CtxvmDshConfig } from './config.ts'
import { mapEvent } from './event-map.ts'
import { ensureTracer, flushTracer } from './tracer.ts'
import { ctxvmPageTableProjection } from './page-table.ts'
import type { SessionTracer } from './types.ts'

export const name = 'ctxvm-tracer'
export const inject = ['sessionProjections']
export { Config }

const log = (...args: unknown[]): void => console.error('[ctxvm]', ...args)

export function apply(ctx: Context, config: CtxvmDshConfig): void {
  log('apply called, enabled =', config.enabled, 'traceDir =', config.traceDir)
  if (!config.enabled) return

  const sessions = new Map<string, SessionTracer>()

  ctx.effect(() => {
    log('effect running; registering page-table projection')
    ctx.sessionProjections.register(ctxvmPageTableProjection)

    const offCreated = ctx.on('session/created', (session) => {
      log('session/created', String(session.id))
      sessions.set(String(session.id), { sessionId: session.id, calls: new Map() })
    })

    let eventCount = 0
    const offEvent = ctx.on('session/event', (session, event) => {
      eventCount++
      const key = String(session.id)
      let st = sessions.get(key)
      if (!st) {
        st = { sessionId: session.id, calls: new Map() }
        sessions.set(key, st)
      }
      if (eventCount <= 5 || eventCount % 100 === 0) log('session/event #' + eventCount, key.slice(0, 8), (event as { type?: string }).type)
      ensureTracer(st, event, config) // no-op once created
      mapEvent(st, event)
    })

    const offDisposed = ctx.on('session/disposed', (session) => {
      log('session/disposed', String(session.id))
      const st = sessions.get(String(session.id))
      if (st) {
        sessions.delete(String(session.id))
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
      offCreated(); offEvent(); offDisposed()
      for (const st of sessions.values()) {
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
    }
  }, 'ctxvm-tracer')
}
