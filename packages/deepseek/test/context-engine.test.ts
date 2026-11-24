/** Active stub-mode pure engine tests. */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  buildStubText,
  createActiveSessionState,
  estimateEngineMessage,
  hardKeepIndices,
  pageKey,
  planActiveStub,
  type ActiveEngineConfig,
  type EngineMessage,
  type PageCandidate,
} from '../src/context-engine.ts'

const config: ActiveEngineConfig = {
  budgetTokens: 100,
  protectFirstN: 0,
  protectLastN: 0,
  stubDropped: 'recoverable',
  selectionMode: 'fresh',
  stableEvery: 4,
}

const message = (role: string, text: string, extra: Partial<EngineMessage> = {}): EngineMessage => ({
  role,
  content: [{ type: 'text', text }],
  ...extra,
})

const candidate = (
  seq: number,
  messageIndex: number,
  ref: string,
  contentHash: string,
  tokens: number,
  name = 'read_file',
  args: unknown = { path: 'a.ts' },
  callId = `call-${seq}`,
): PageCandidate => ({ seq, messageIndex, ref, contentHash, tokens, name, args, callId, text: 'full body' })

test('protected floor at or above budget is a no-op', () => {
  const state = createActiveSessionState()
  const messages = [message('system', 's'), message('user', 'u')]
  const plan = planActiveStub(messages, [], { ...config, budgetTokens: 10 }, state)
  assert.equal(plan.reason, 'floor_bust')
  assert.deepEqual(plan.selected, [])
  assert.equal(plan.floorTokens, 10)
})

test('hard keeps include system, head, tail, last user, and open tool calls', () => {
  const messages: EngineMessage[] = [
    message('system', 's'),
    message('user', 'head'),
    { role: 'assistant', content: [{ type: 'tool-call', id: 'open', name: 'bash', arguments: '{}' }] },
    message('tool', 'answered', { toolCallId: 'answered' }),
    message('user', 'last'),
    message('assistant', 'tail'),
  ]
  const candidates = [candidate(1, 3, 'tool:read({})', 'sha256:1', 10, 'read_file', {}, 'answered')]
  const keep = hardKeepIndices(messages, candidates, { ...config, protectFirstN: 1, protectLastN: 1 })
  assert.deepEqual([...keep].sort((a, b) => a - b), [0, 1, 2, 4, 5])
})

test('fresh selection keeps a newest-first contiguous recency run', () => {
  const state = createActiveSessionState()
  const messages = [message('system', 's'), message('user', 'u'), message('tool', 'one'), message('tool', 'two'), message('tool', 'three')]
  const candidates = [
    candidate(1, 2, 'tool:one', 'sha256:1', 20),
    candidate(2, 3, 'tool:two', 'sha256:2', 20),
    candidate(3, 4, 'tool:three', 'sha256:3', 20),
  ]
  const plan = planActiveStub(messages, candidates, { ...config, budgetTokens: 50 }, state)
  assert.deepEqual(plan.selected.map(item => item.seq), [1])
  assert.equal(plan.reason, 'evicted')
})

test('second result demand pins and a new content hash releases the pin', () => {
  const state = createActiveSessionState()
  const first = candidate(1, 1, 'tool:read', 'sha256:old', 10)
  planActiveStub([message('tool', 'old')], [first], config, state)
  const second = candidate(2, 1, 'tool:read', 'sha256:old', 10)
  planActiveStub([message('tool', 'old')], [second], config, state)
  assert.equal(state.pages.get(pageKey(first))?.pinned, true)
  const changed = candidate(3, 1, 'tool:read', 'sha256:new', 10)
  planActiveStub([message('tool', 'new')], [changed], config, state)
  assert.equal(state.pages.get(pageKey(first))?.pinned, false)
  assert.equal(state.pinOrder.includes(pageKey(first)), false)
})

test('stable selection holds, ignores its own stubs, and replans on every-B', () => {
  const state = createActiveSessionState()
  const stable = { ...config, selectionMode: 'stable' as const, stableEvery: 2, budgetTokens: 44 }
  const first = candidate(1, 1, 'tool:old', 'sha256:old', 40)
  const messages = [message('user', 'u'), message('tool', 'old')]
  assert.deepEqual(planActiveStub(messages, [first], stable, state).selected.map(item => item.seq), [1])
  state.stubbedKeys.add(pageKey(first))
  const held = planActiveStub([messages[0]!], [], stable, state)
  assert.equal(held.trigger, 'held')
  assert.deepEqual(held.selected, [])
  const every = planActiveStub([messages[0]!], [], stable, state)
  assert.equal(every.trigger, 'every-B')
})

test('stable selection triggers on a genuinely new page', () => {
  const state = createActiveSessionState()
  const stable = { ...config, selectionMode: 'stable' as const }
  const first = candidate(1, 1, 'tool:one', 'sha256:1', 10)
  planActiveStub([message('tool', 'one')], [first], stable, state)
  const second = candidate(2, 2, 'tool:two', 'sha256:2', 10)
  const plan = planActiveStub([message('tool', 'one'), message('tool', 'two')], [first, second], stable, state)
  assert.equal(plan.trigger, 'new-page')
})

test('duplicate current PageIds fail closed instead of partially stubbing', () => {
  const state = createActiveSessionState()
  const duplicate = candidate(1, 1, 'tool:same', 'sha256:same', 10)
  const plan = planActiveStub([message('tool', 'one'), message('tool', 'two')], [
    duplicate,
    candidate(2, 2, 'tool:same', 'sha256:same', 10),
  ], config, state)
  assert.deepEqual(plan.selected, [])
  assert.ok(state.diagnostics.some(item => item.includes('duplicate current PageId')))
})

test('estimator uses Unicode code points and Hermes message overhead', () => {
  assert.equal(estimateEngineMessage(message('user', '😀😀😀😀')), 5)
  assert.equal(estimateEngineMessage({
    role: 'assistant',
    content: [{ type: 'tool-call', id: 'c', name: 'read', arguments: '{"path":"a"}' }],
  }), 9)
})

test('stub template, read-only excerpt, escaping, cap, and mutating fallback are exact', () => {
  assert.equal(buildStubText({ name: 'read_file', args: '{"path":"notes/f2.md"}' }),
    '[ctxvm: dropped result for read_file({"path":"notes/f2.md"}); re-run to restore.]')
  assert.equal(buildStubText({ name: 'bash', args: '{"command":"rm -rf /"}' }),
    '[ctxvm: dropped result for bash(see the call above); re-run to restore.]')
  const escaped = buildStubText({ name: 'search_files', args: '[a]\n\tb' })
  assert.equal(escaped, '[ctxvm: dropped result for search_files(\\[a\\]  b); re-run to restore.]')
  const capped = buildStubText({ name: 'read_file', args: 'x'.repeat(201) })
  assert.ok(capped.includes(`${'x'.repeat(200)}...[truncated]`))
})
