/**
 * W22 — event mapping unit tests: DSH SessionEvent envelopes → tracer verbs.
 * Run from packages/deepseek with node_modules/@ctxvm/node linked:
 *   node --test test/
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mapEvent } from '../src/event-map.ts'
import { openTracer, ensureTracer } from '../src/tracer.ts'

const config = {
  enabled: true,
  traceDir: '/tmp/ctxvm-test',
  tokenizerId: 'apx4-char',
  budgetTokens: 200_000,
  agentIdPrefix: 'dsh',
} as const

/** DSH publishes {type, seq, time, data}; payload fields live under data. */
function env(type: string, data: Record<string, unknown> = {}, seq = 0): never {
  return { type, seq, time: 1794841561000, data } as never
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
  const st = { sessionId: 's' as never, calls: new Map() }
  ensureTracer(st, env('request/header', { header: { config: { provider: 'opencode', model: 'hy4-flash-free' }, tools: [] } }, 5), config as never)
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
  const st = { sessionId: 's' as never, calls: new Map() }
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
