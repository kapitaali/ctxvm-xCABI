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

export function apply(ctx: Context, config: CtxvmDshConfig): void {
  if (!config.enabled) return

  const sessions = new Map<string, SessionTracer>()

  ctx.effect(() => {
    // Page table is a projection over the session log — live and replay agree.
    ctx.sessionProjections.register(ctxvmPageTableProjection)

    const offCreated = ctx.on('session/created', (session) => {
      sessions.set(String(session.id), { sessionId: session.id, calls: new Map() })
    })

    const offEvent = ctx.on('session/event', (session, event) => {
      const key = String(session.id)
      let st = sessions.get(key)
      if (!st) {
        st = { sessionId: session.id, calls: new Map() }
        sessions.set(key, st)
      }
      ensureTracer(st, event, config) // no-op once created
      mapEvent(st, event)
    })

    const offDisposed = ctx.on('session/disposed', (session) => {
      const st = sessions.get(String(session.id))
      if (st) {
        sessions.delete(String(session.id))
        if (st.tracer) {
          try { flushTracer(st, config) } catch { /* never raise into the loop */ }
        }
      }
    })

    return () => {
      offCreated(); offEvent(); offDisposed()
      for (const st of sessions.values()) {
        if (st.tracer) {
          try { flushTracer(st, config) } catch { /* ignore */ }
        }
      }
      sessions.clear()
    }
  }, 'ctxvm-tracer')
}
