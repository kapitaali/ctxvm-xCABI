/**
 * W22 §4.1 — DSH SessionEvent → @ctxvm/node tracer calls.
 *
 * Append-origin tool results declare pages. A single-node tool/result replacement
 * is passive stub provenance: it resolves the original PageId and emits one
 * eviction/stub-render pair with the replacement's exact text. Other replacement
 * types never become ctxvm stubs.
 */
import type { SessionEvent } from '@deepseek-ai/dsh-session/types'
import type { SessionTracer } from './types.ts'
import { eventData, asRecord, asString } from './event-data.ts'
import { isReplacement, replacementSourceSeq } from './surface.ts'

function diagnostic(st: SessionTracer, message: string): void {
  st.diagnostics.push(message)
  if (st.diagnostics.length > 100) st.diagnostics.shift()
}

/** Feed one committed DSH event into the session tracer. Never throws. */
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
        tracer.recall({ tool: asString(data.name), args: args as never })
        break
      }
      case 'tool/result': {
        if (isReplacement(data)) {
          const originalSeq = replacementSourceSeq(data)
          if (originalSeq === undefined) {
            diagnostic(st, 'tool/result replacement has invalid single-node provenance')
            break
          }
          const original = st.pagesBySeq.get(originalSeq)
          if (original === undefined) {
            diagnostic(st, `tool/result replacement origin ${originalSeq} has no declared PageId`)
            break
          }
          const message = asRecord(data.message)
          const stubText = textOf(message?.content)
          if (stubText.length === 0) {
            diagnostic(st, `tool/result replacement origin ${originalSeq} has no text stub`)
            break
          }
          const turn = Math.max(0, st.turn)
          const emitted = tracer.stub({
            ref: original.logicalRef,
            contentHash: original.contentHash,
            stubText,
            turn,
          })
          if (!emitted) {
            diagnostic(st, `tool/result replacement origin ${originalSeq} was refused by the tracer`)
            break
          }
          st.stubbedRefs.push({ ref: original.logicalRef, contentHash: original.contentHash, stubText, turn })
          st.evictedTokens += original.tokens
          break
        }

        const message = asRecord(data.message)
        const call = st.calls.get(asString(message?.toolCallId))
        const page = tracer.page({
          kind: 'tool_result',
          tool: call?.name ?? 'unknown',
          args: call?.args as never,
          content: textOf(message?.content),
        })
        if (typeof data.seq === 'number' && Number.isSafeInteger(data.seq) && data.seq >= 0) {
          st.pagesBySeq.set(data.seq, page)
        }
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
        st.turn++
        tracer.render()
        break
      default:
        break
    }
  } catch (error) {
    diagnostic(st, `event mapping failed: ${error instanceof Error ? error.message : String(error)}`)
  }
}

function textOf(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content.filter(block => asRecord(block)?.type === 'text')
      .map(block => asString(asRecord(block)?.text)).join('')
  }
  return content === undefined || content === null ? '' : JSON.stringify(content)
}
