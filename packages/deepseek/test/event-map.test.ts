/**
 * W22 — event mapping unit tests: DSH SessionEvent envelopes → tracer verbs.
 * Run from packages/deepseek with node_modules/@ctxvm/node linked:
 *   node --test test/
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mapEvent } from '../src/event-map.ts'
import { openTracer, ensureTracer, createSessionTracer } from '../src/tracer.ts'

const config = {
  enabled: true,
  traceDir: '/tmp/ctxvm-test',
  tokenizerId: 'apx4-char',
  budgetTokens: 200_000,
  agentIdPrefix: 'dsh',
} as const

/** DSH publishes {type, seq, time, data}; payload fields live under data. */
function env(type: string, data: Record<string, unknown> = {}, seq = 0, extra: Record<string, unknown> = {}): never {
  return { type, seq, time: 1794841561000, data, ...extra } as never
}

function makeTracer() {
  return openTracer('session-test-0001' as never, { model: 'm', provider: 'p' }, config as never)
}

/** v0.1.0: finish() → { jsonl, events, stats }; parse jsonl for verbs. */
function verbsOf(st: { tracer?: import('@ctxvm/node').Tracer }): string[] {
  const finished = st.tracer!.finish()
  return finished.jsonl.trim().split('\n').map(l => JSON.parse(l).type as string)
}

test('tool/result yields at least one page.declare', () => {
  const st = makeTracer()
  mapEvent(st, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' }, 1))
  mapEvent(st, env('tool/result', { message: { toolCallId: 'c1', content: 'file.txt' } }, 2))
  assert.ok(verbsOf(st).includes('page.declare'))
})

test('turn/start renders a turn', () => {
  const st = makeTracer()
  mapEvent(st, env('turn/start', { turn: 0 }, 3))
  assert.ok(verbsOf(st).includes('turn.render'))
})

test('request/header feeds onApiRequest without throwing', () => {
  const st = makeTracer()
  mapEvent(st, env('request/header', { header: { config: { provider: 'p', model: 'm' }, tools: [] } }, 4))
  assert.ok(verbsOf(st).length > 0)
})

test('request/header yields real provider/model in session.open', () => {
  const st = createSessionTracer('s' as never)
  ensureTracer(st, env('request/header', {
    header: { config: { provider: 'opencode', model: 'hy4-flash-free' }, tools: [] },
  }, 5), config as never)
  const first = JSON.parse(st.tracer!.finish().jsonl.trim().split('\n')[0])
  assert.equal(first.type, 'session.open')
  assert.equal(first.provider, 'opencode')
  assert.equal(first.model, 'hy4-flash-free')
})

test('assistant/message usage is carried into providerUsage', () => {
  const st = makeTracer()
  mapEvent(st, env('request/header', { header: { config: { provider: 'opencode', model: 'hy4-flash-free' }, tools: [] } }, 4))
  mapEvent(st, env('turn/start', { turn: 0 }, 5))
  mapEvent(st, env('assistant/message', {
    message: { content: 'ok' },
    usage: { inputTokens: 10, outputTokens: 3, cacheReadTokens: 2 },
  }, 6))
  const lines = st.tracer!.finish().jsonl.trim().split('\n').map(l => JSON.parse(l))
  const callMeta = lines.find(l => l.type === 'call.meta')
  assert.ok(callMeta, 'expected call.meta')
  assert.deepEqual(callMeta.providerUsage, { inputTokens: 10, outputTokens: 3, cachedInputTokens: 2 })
})

test('a later request/header supplies identity and replays buffered pages', () => {
  const st = createSessionTracer('s' as never)
  const header = env('request/header', { header: { config: { provider: 'opencode', model: 'hy4-flash-free' }, tools: [] } }, 3)
  ensureTracer(st, env('turn/start', { turn: 0 }, 1), config as never)
  const systemEvent = env('system/message', { message: { content: 'buffered system page' } }, 2)
  ensureTracer(st, systemEvent, config as never) // index.ts calls this for every event
  mapEvent(st, systemEvent)
  ensureTracer(st, header, config as never)
  mapEvent(st, header)
  const lines = st.tracer!.finish().jsonl.trim().split('\n').map(l => JSON.parse(l))
  assert.equal(lines[0].type, 'session.open')
  assert.equal(lines[0].provider, 'opencode')
  assert.equal(lines[0].model, 'hy4-flash-free')
  assert.ok(lines.some(l => l.type === 'page.declare'), 'buffered system page must be replayed')
})

test('mapEvent never throws on unknown events', () => {
  const st = makeTracer()
  mapEvent(st, env('something/else', {}, 6))
  mapEvent(st, env('tool/call', { arguments: '{not json' }, 7))
})

test('append result plus single-node replacement emits one declaration and one exact stub pair', () => {
  const st = makeTracer()
  mapEvent(st, env('turn/start', { turn: 1 }, 0))
  mapEvent(st, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' }, 1))
  mapEvent(st, env('tool/result', { message: { toolCallId: 'c1', content: 'full result' } }, 2, {
    surfaceOp: 'append', sourceEventSeqs: [1],
  }))
  const original = st.pagesBySeq.get(2)!
  const stubText = '  [ctxvm: exact]\nbody  '
  mapEvent(st, env('tool/result', { message: { toolCallId: 'c1', content: [{ type: 'text', text: stubText }] } }, 3, {
    surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [1, 2],
  }))
  const events = st.tracer!.finish().events as Record<string, unknown>[]
  assert.equal(events.filter(e => e.type === 'page.declare').length, 1)
  const evicts = events.filter(e => e.type === 'page.evict')
  const stubRenders = events.filter(e => e.type === 'page.render' && e.mode === 'stub')
  assert.equal(evicts.length, 1)
  assert.equal(stubRenders.length, 1)
  assert.deepEqual(evicts[0].page, { logicalRef: original.logicalRef, contentHash: original.contentHash })
  assert.deepEqual(stubRenders[0].page, evicts[0].page)
  assert.equal(evicts[0].stubText, stubText)
  assert.equal(evicts[0].turn, 0)
  assert.equal(stubRenders[0].turn, 0)
  assert.ok(events.indexOf(evicts[0]) < events.indexOf(stubRenders[0]))
  assert.deepEqual(st.stubbedRefs, [{ ref: original.logicalRef, contentHash: original.contentHash, stubText, turn: 0 }])
  assert.equal(st.evictedTokens, original.tokens)
})

test('append sourceEventSeqs and user replacements are not stubs', () => {
  const st = makeTracer()
  mapEvent(st, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{}' }, 1))
  mapEvent(st, env('tool/result', { message: { toolCallId: 'c1', content: 'full' } }, 2, {
    surfaceOp: 'append', sourceEventSeqs: [1],
  }))
  mapEvent(st, env('user/message', { message: { content: 'replacement' } }, 3, {
    surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2],
  }))
  const events = st.tracer!.finish().events as Record<string, unknown>[]
  const toolDeclares = events.filter(event => event.type === 'page.declare'
    && (event.page as { kind?: string }).kind === 'tool_result')
  assert.equal(toolDeclares.length, 1)
  assert.equal(events.some(event => event.type === 'page.evict'), false)
  assert.equal(st.stubbedRefs.length, 0)
})

test('unknown or malformed replacement origin is diagnostic-only', () => {
  const st = makeTracer()
  mapEvent(st, env('tool/result', { message: { content: 'stub' } }, 3, {
    surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2],
  }))
  mapEvent(st, env('tool/result', { message: { content: 'stub' } }, 4, {
    surfaceOp: { op: 'replace', startSeq: 2, endSeq: 3 }, sourceEventSeqs: [2, 3],
  }))
  assert.equal(verbsOf(st).includes('page.evict'), false)
  assert.equal(st.stubbedRefs.length, 0)
  assert.equal(st.diagnostics.length, 2)
})

test('multi-step DSH turn shares one visibility turn and the next turn advances', () => {
  const st = makeTracer()
  mapEvent(st, env('turn/start', { turn: 1 }, 0))
  for (const [seq, text] of [[1, 'one'], [2, 'two']] as const) {
    mapEvent(st, env('tool/call', { callId: `c${seq}`, name: 'read', arguments: '{}' }, seq * 2))
    mapEvent(st, env('tool/result', { message: { toolCallId: `c${seq}`, content: `full-${text}` } }, seq * 2 + 1, {
      surfaceOp: 'append', sourceEventSeqs: [seq * 2],
    }))
    mapEvent(st, env('tool/result', { message: { toolCallId: `c${seq}`, content: `stub-${text}` } }, seq * 2 + 2, {
      surfaceOp: { op: 'replace', startSeq: seq * 2 + 1, endSeq: seq * 2 + 1 }, sourceEventSeqs: [seq * 2 + 1],
    }))
  }
  assert.deepEqual(st.stubbedRefs.map(record => record.turn), [0, 0])
  mapEvent(st, env('turn/start', { turn: 2 }, 10))
  mapEvent(st, env('tool/call', { callId: 'c3', name: 'read', arguments: '{}' }, 11))
  mapEvent(st, env('tool/result', { message: { toolCallId: 'c3', content: 'full-three' } }, 12, { surfaceOp: 'append' }))
  mapEvent(st, env('tool/result', { message: { toolCallId: 'c3', content: 'stub-three' } }, 13, {
    surfaceOp: { op: 'replace', startSeq: 12, endSeq: 12 }, sourceEventSeqs: [12],
  }))
  assert.deepEqual(st.stubbedRefs.map(record => record.turn), [0, 0, 1])
})

test('two sessions with identical seqs do not share stub state', () => {
  const a = makeTracer()
  const b = makeTracer()
  for (const [st, body] of [[a, 'A'], [b, 'B']] as const) {
    mapEvent(st, env('tool/call', { callId: 'same', name: 'read', arguments: '{}' }, 1))
    mapEvent(st, env('tool/result', { message: { toolCallId: 'same', content: body } }, 2, { surfaceOp: 'append' }))
  }
  mapEvent(a, env('tool/result', { message: { toolCallId: 'same', content: 'stub-A' } }, 3, {
    surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2],
  }))
  assert.equal(a.stubbedRefs.length, 1)
  assert.equal(b.stubbedRefs.length, 0)
  assert.notEqual(a.pagesBySeq.get(2)!.contentHash, b.pagesBySeq.get(2)!.contentHash)
})
