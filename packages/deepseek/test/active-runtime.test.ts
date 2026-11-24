/** Active pre-step runtime tests with a nondeprecated surface-query stub. */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { applyActivePreStep } from '../src/active-runtime.ts'
import { createActiveSessionState, type EngineMessage } from '../src/context-engine.ts'
import { createSessionTracer } from '../src/tracer.ts'
import type { CtxvmDshConfig } from '../src/config.ts'

const config: CtxvmDshConfig = {
  enabled: true,
  traceDir: '/tmp/unused',
  tokenizerId: 'apx4-char',
  budgetTokens: 5,
  mode: 'stub',
  protectFirstN: 0,
  protectLastN: 0,
  stubDropped: 'recoverable',
  selectionMode: 'fresh',
  stableEvery: 4,
  agentIdPrefix: 'dsh',
}

function fixture() {
  const tracer = createSessionTracer('session-active-runtime' as never)
  tracer.pagesBySeq.set(1, { logicalRef: 'tool:bash({})', contentHash: 'sha256:abc', tokens: 100 })
  tracer.calls.set('call-1', { name: 'bash', args: { command: 'x' }, rawArgs: '{"command":"x"}' })
  const messages: EngineMessage[] = [{ id: 'm1', role: 'tool', toolCallId: 'call-1', content: [{ type: 'text', text: 'full body' }] }]
  const appends: unknown[] = []
  const session = {
    id: tracer.sessionId,
    seq: 2,
    surface: { nodes: [0, 1] },
    deriveMessages: () => messages,
    append: (...args: unknown[]) => { appends.push(args); return {} },
  }
  const surface = {
    capturedThroughSeq: 1,
    events: [
      { type: 'system/message', seq: 0, time: 0, surfaceOp: 'append', data: { message: { id: 'empty', role: 'system', content: [] } } },
      { type: 'tool/result', seq: 1, time: 1, surfaceOp: 'append', sourceEventSeqs: [0], data: {
        turn: 1,
        step: 1,
        message: { id: 'm1', role: 'tool', toolCallId: 'call-1', content: [{ type: 'text', text: 'full body' }] },
        meta: { keep: true },
      } },
    ],
  }
  let queries = 0
  const ctx = {
    get(name: string) {
      if (name === 'sessionQuery') return { readSurface: async () => { queries++; return surface } }
      if (name === 'tokenMeter') return { measure: () => ({ totalTokens: 100 }) }
      if (name === 'sessions') return { flush: async () => true }
      return undefined
    },
  }
  return { tracer, session, appends, ctx, queries: () => queries }
}

test('active runtime maps by message identity even when an empty system node derives no message', async () => {
  const f = fixture()
  const state = createActiveSessionState()
  const agent = { id: f.tracer.sessionId, session: f.session }
  const result = await applyActivePreStep(
    f.ctx as never, config, f.tracer, state, agent as never, new AbortController().signal,
  )
  assert.equal(result.appended, 1)
  assert.equal(f.appends.length, 1)
  type Replacement = [
    string,
    { meta: { keep: boolean }; message: { id: string; toolCallId: string; content: { text: string }[] } },
    { surfaceOp: { op: string; startSeq: number; endSeq: number }; sourceEventSeqs: number[] },
  ]
  const [type, data, options] = f.appends[0] as Replacement
  assert.equal(type, 'tool/result')
  assert.equal(data.meta.keep, true)
  assert.equal(data.message.id, 'm1')
  assert.equal(data.message.toolCallId, 'call-1')
  assert.equal(data.message.content[0].text, '[ctxvm: dropped result for bash(see the call above); re-run to restore.]')
  assert.deepEqual(options, { surfaceOp: { op: 'replace', startSeq: 1, endSeq: 1 }, sourceEventSeqs: [1] })
})

test('off mode plans but appends no replacement', async () => {
  const f = fixture()
  const agent = { id: f.tracer.sessionId, session: f.session }
  const result = await applyActivePreStep(
    f.ctx as never, { ...config, stubDropped: 'off' }, f.tracer, createActiveSessionState(), agent as never,
    new AbortController().signal,
  )
  assert.equal(result.plan.selected.length, 1)
  assert.equal(result.appended, 0)
  assert.equal(f.appends.length, 0)
})

test('cancelled pre-step does not query or append', async () => {
  const f = fixture()
  const controller = new AbortController()
  controller.abort()
  const agent = { id: f.tracer.sessionId, session: f.session }
  const result = await applyActivePreStep(
    f.ctx as never, config, f.tracer, createActiveSessionState(), agent as never, controller.signal,
  )
  assert.equal(result.appended, 0)
  assert.equal(f.queries(), 0)
})

test('unknown original provenance is diagnostic-only', async () => {
  const f = fixture()
  f.tracer.pagesBySeq.delete(1)
  const state = createActiveSessionState()
  const agent = { id: f.tracer.sessionId, session: f.session }
  const result = await applyActivePreStep(
    f.ctx as never, config, f.tracer, state, agent as never, new AbortController().signal,
  )
  assert.equal(result.appended, 0)
  assert.equal(f.appends.length, 0)
  assert.ok(state.diagnostics.some(item => item.includes('no original PageId')))
})
