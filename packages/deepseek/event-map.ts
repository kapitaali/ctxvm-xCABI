/**
 * W22 §4.1 — dsh SessionEvent → @ctxvm/node tracer calls (v0.1.0 API).
 *
 * Mapping (mirror mode; page.evict/pin/unpin deferred to Phase 3):
 *
 *   session.open  ← tracer creation (first event; provider/model from the
 *                   first request/header when available)
 *   page.declare  ← tool/result | user/message | system/message
 *   page.render   ← turn/start (tracer.render reveals newly declared pages)
 *   page.fault    ← tool/call matching a declared page (tracer.recall)
 *   turn.render   ← tracer.render() at each turn boundary
 *   call.meta     ← request/header → onApiRequest({ tool_count, request_char_count })
 *                   + assistant/message usage → noteUsage
 *   scan          ← assistant/message text (identifier_scan)
 *
 * Note: tool/result carries no top-level callId; pair via
 * message.toolCallId → tool/call.callId (dsh llm message.ts).
 */
import type { SessionEvent } from '@deepseek-ai/dsh-session/types'
import type { SessionTracer } from './types.ts'

/** Feed one committed dsh event into the session's tracer. Never throws. */
export function mapEvent(st: SessionTracer, event: SessionEvent): void {
  try {
    const tracer = st.tracer
    if (!tracer) return
    switch (event.type) {
      case 'tool/call': {
        // Remember callId → (name, args) so a later tool/result can declare a page.
        let args: unknown
        try { args = JSON.parse(event.arguments) } catch { args = event.arguments }
        st.calls.set(event.callId, { name: event.name, args })
        // If this (name, args) matches an already-declared page → page.fault (tool_recall).
        tracer.recall({ tool: event.name, args })
        break
      }
      case 'tool/result': {
        const call = st.calls.get(event.message.toolCallId)
        tracer.page({
          kind: 'tool_result',
          tool: call?.name ?? 'unknown',
          args: call?.args,
          content: event.message.content,
        })
        break
      }
      case 'user/message':
        tracer.page({ kind: 'file', content: event.message.content })
        break
      case 'system/message':
        tracer.page({ kind: 'summary', content: event.message.content })
        break
      case 'assistant/message':
        tracer.scan({ text: textOf(event.message.content) })
        if (event.message.usage) {
          tracer.noteUsage({
            inputTokens: event.message.usage.inputTokens,
            outputTokens: event.message.usage.outputTokens,
            cachedInputTokens: event.message.usage.cacheReadTokens,
          })
        }
        break
      case 'request/header': {
        // v0.1.0 onApiRequest records per-turn static cost, not provider/model
        // (those went into createTrace at session.open).
        const header = event.header as { tools?: unknown[]; config?: unknown }
        tracer.onApiRequest({
          tool_count: Array.isArray(header.tools) ? header.tools.length : undefined,
          request_char_count: Buffer.byteLength(JSON.stringify(event.header)),
        })
        break
      }
      case 'turn/start':
        tracer.render()
        break
      default:
        break // mirror mode: unmapped events are ignored, never fatal
    }
  } catch {
    // W22 §4.3: a throwing listener would break the loop — swallow and continue.
  }
}

function textOf(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) return content.filter(b => b && b.type === 'text').map(b => (b as { text: string }).text).join('')
  return String(content ?? '')
}
