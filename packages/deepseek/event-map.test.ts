/**
 * W22 — event mapping unit tests: mock SessionEvent → tracer → expected verbs.
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

function makeTracer() {
  return openTracer('session-test-0001' as never, { model: 'm', provider: 'p' }, config as never)
}

/** v0.1.0: finish() → { jsonl, events, stats }; parse jsonl for verbs. */
function verbsOf(st: { tracer?: import('@ctxvm/node').Tracer }): string[] {
  const finished = st.tracer!.finish()
  return finished.jsonl.trim().split('\n').map(l => JSON.parse(l).type as string)
}

test('tool/call then tool/result declares a page', () => {
  const st = makeTracer()
  mapEvent(st, { type: 'tool/call', turn: 0, step: 0, callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' } as never)
  mapEvent(st, { type: 'tool/result', message: { toolCallId: 'c1', content: 'file.txt' } } as never)
  assert.ok(verbsOf(st).includes('page.declare'))
})

test('turn/start renders a turn', () => {
  const st = makeTracer()
  mapEvent(st, { type: 'turn/start', turn: 0 } as never)
  assert.ok(verbsOf(st).includes('turn.render'))
})

test('request/header feeds onApiRequest without throwing', () => {
  const st = makeTracer()
  mapEvent(st, { type: 'request/header', header: { config: { provider: 'p', model: 'm' }, tools: [] } } as never)
  assert.ok(verbsOf(st).length > 0)
})

test('ensureTracer uses request/header provider/model for session.open', () => {
  const st = { sessionId: 's' as never, calls: new Map() }
  ensureTracer(st, { type: 'request/header', header: { config: { provider: 'nous', model: 'm1' } } }, config as never)
  const first = JSON.parse(st.tracer!.finish().jsonl.trim().split('\n')[0])
  assert.equal(first.type, 'session.open')
  assert.equal(first.provider, 'nous')
  assert.equal(first.model, 'm1')
})

test('mapEvent never throws on unknown events', () => {
  const st = makeTracer()
  mapEvent(st, { type: 'something/else' } as never)
  mapEvent(st, { type: 'tool/call', arguments: '{not json' } as never)
})
