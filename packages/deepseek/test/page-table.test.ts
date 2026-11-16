/**
 * W22 — page table fold unit tests (§4.2). Run: node --test test/
 * Fixtures use DSH's {type, seq, time, data} envelope; no schemastery needed
 * since 254fa7c (type-only import in page-table.ts).
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { toolRef, contentHash } from '@ctxvm/node'
import { ctxvmPageTableProjection } from '../src/page-table.ts'

function env(type: string, data: Record<string, unknown> = {}, seq = 0, extra: Record<string, unknown> = {}): never {
  return { type, seq, time: 1794841561000, data, ...extra } as never
}

const apply = (s: never, e: never) => ctxvmPageTableProjection.apply(s, e) as never as import('../src/types.ts').PageTableState
const init = () => ctxvmPageTableProjection.init({} as never, 0)

test('init yields an empty page table', () => {
  assert.deepEqual(init(), { pages: {}, order: [], calls: {} })
})

test('apply is pure and does not mutate input state', () => {
  const state = init()
  const next = apply(state, env('turn/start', { turn: 0 }, 1))
  assert.deepEqual(state, { pages: {}, order: [], calls: {} })
  assert.ok(next)
})

test('tool/call then tool/result declares a resident page with the toolRef identity', () => {
  let s = init()
  s = apply(s, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' }, 1))
  s = apply(s, env('tool/result', { message: { toolCallId: 'c1', content: 'file.txt' } }, 2))
  const ref = toolRef(undefined, 'bash', { cmd: 'ls' } as never)
  const page = s.pages[ref]
  assert.ok(page, `expected page at ${ref}; have ${Object.keys(s.pages)}`)
  assert.equal(page.kind, 'tool_result')
  assert.equal(page.contentHash, contentHash('file.txt'))
  assert.ok(page.tokens > 0)
  assert.equal(page.status, 'resident')
  assert.equal(page.seq, 2)
  assert.deepEqual(s.order, [ref])
})

test('tool/result with no message does not throw (session resume regression)', () => {
  let s = init()
  s = apply(s, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' }, 1))
  s = apply(s, env('tool/result', {}, 2))
  const refs = Object.keys(s.pages)
  assert.equal(refs.length, 1, `expected one page; have ${refs}`)
  assert.equal(s.pages[refs[0]].contentHash, contentHash(''))
  assert.equal(s.pages[refs[0]].status, 'resident')
})

test('re-declared page keeps first-declare-wins content hash but refreshes tokens/status', () => {
  let s = init()
  s = apply(s, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' }, 1))
  s = apply(s, env('tool/result', { message: { toolCallId: 'c1', content: 'aaa' } }, 2))
  const ref = toolRef(undefined, 'bash', { cmd: 'ls' } as never)
  const firstHash = s.pages[ref].contentHash
  s = apply(s, env('tool/result', { message: { toolCallId: 'c1', content: 'a much longer result body' } }, 3))
  assert.equal(s.pages[ref].contentHash, firstHash)
  assert.ok(s.pages[ref].tokens > 1)
  assert.equal(s.pages[ref].status, 'resident')
  assert.deepEqual(s.order, [ref], 'no duplicate order entry')
})

test('surface replace op marks shadowed pages stub, never regresses evicted', () => {
  let s = init()
  s = apply(s, env('tool/call', { callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' }, 1))
  s = apply(s, env('tool/result', { message: { toolCallId: 'c1', content: 'x' } }, 2))
  const ref = toolRef(undefined, 'bash', { cmd: 'ls' } as never)
  s = apply(s, env('user/message', {}, 5, { surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2] }))
  assert.equal(s.pages[ref].status, 'stub')
  s = apply(s, env('compaction/summary', { shadowedSeqs: [2] }, 6))
  assert.equal(s.pages[ref].status, 'evicted')
  s = apply(s, env('user/message', {}, 7, { surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2] }))
  assert.equal(s.pages[ref].status, 'evicted')
})

test('unmapped events leave state untouched (same reference)', () => {
  const s = init()
  assert.equal(apply(s, env('request/header', { header: {} }, 1)), s)
})
