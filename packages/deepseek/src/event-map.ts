/**
 * W22 §4.1 — dsh SessionEvent → @ctxvm/node tracer calls (v0.1.0 API).
 *
 * Reads go through eventData(), which merges DSH's `{type, seq, time, data}`
 * envelope with its surface metadata. Mapping (mirror mode; page.evict/pin/
 * unpin deferred to Phase 3):
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
import { eventData, asRecord, asString } from './event-data.ts'

/** Feed one committed dsh event into the session's tracer. Never throws. */
export function mapEvent(st: SessionTracer, event: SessionEvent): void {
  try {
    const tracer = st.tracer
    if (!tracer) return
    const data = eventData(event)
    switch (data.type) {
      case 'tool/call': {
        const raw = asString(data.arguments)
        let args: unknown
        try { args = JSON.parse(raw) } catch { args = raw }
        st.calls.set(asString(data.callId), { name: asString(data.name), args })
        // A re-call of a declared page is the FaultOfResidentPage ledger row.
        tracer.recall({ tool: asString(data.name), args })
        break
      }
      case 'tool/result': {
        const message = asRecord(data.message)
        const call = st.calls.get(asString(message?.toolCallId))
        tracer.page({
          kind: 'tool_result',
          tool: call?.name ?? 'unknown',
          args: call?.args,
          // A stored tool/result may have no message; the empty body is a fact,
          // never a fabricated token count. Keeps the tracer total.
          content: textOf(message?.content),
        })
        break
      }
      case 'user/message': {
        const message = asRecord(data.message)
        tracer.page({ kind: 'file', content: textOf(message?.content) })
        break
      }
      case 'system/message': {
        const message = asRecord(data.message)
        tracer.page({ kind: 'summary', content: textOf(message?.content) })
        break
      }
      case 'assistant/message': {
        const message = asRecord(data.message)
        tracer.scan({ text: textOf(message?.content) })
        const usage = asRecord(data.usage)
        if (usage) {
          const input = usage.inputTokens
          const output = usage.outputTokens
          if (typeof input === 'number' && typeof output === 'number') {
            const cached = usage.cacheReadTokens
            tracer.noteUsage({
              inputTokens: input,
              outputTokens: output,
              cachedInputTokens: typeof cached === 'number' ? cached : undefined,
            })
          }
        }
        break
      }
      case 'request/header': {
        const header = asRecord(data.header)
        tracer.onApiRequest({
          tool_count: Array.isArray(header?.tools) ? header.tools.length : undefined,
          request_char_count: header ? Buffer.byteLength(JSON.stringify(header)) : undefined,
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
  if (Array.isArray(content)) {
    return content.filter(b => asRecord(b)?.type === 'text')
      .map(b => asString(asRecord(b)?.text)).join('')
  }
  return content === undefined || content === null ? '' : JSON.stringify(content)
}
