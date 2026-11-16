/**
 * W22 — page table fold unit tests (§4.2). Run: node --test test/
 * No schemastery needed: page-table.ts keeps only a type-only import of it
 * (P15 option ii, landed 254fa7c); init()/apply() never touch the schema.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { toolRef, contentHash } from '@ctxvm/node'
import { ctxvmPageTableProjection } from '../src/page-table.ts'

const apply = (s: never, e: never) => ctxvmPageTableProjection.apply(s, e) as never as import('../src/types.ts').PageTableState
const init = () => ctxvmPageTableProjection.init({} as never, 0)

test('init yields an empty page table', () => {
  assert.deepEqual(init(), { pages: {}, order: [], calls: {} })
})

test('apply is pure and does not mutate input state', () => {
  const state = init()
  const next = apply(state, { type: 'turn/start', turn: 0 })
  assert.deepEqual(state, { pages: {}, order: [], calls: {} })
  assert.ok(next)
})

test('tool/call then tool/result declares a resident page with the toolRef identity', () => {
  let s = init()
  s = apply(s, { type: 'tool/call', seq: 1, callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' })
  s = apply(s, { type: 'tool/result', seq: 2, message: { toolCallId: 'c1', content: 'file.txt' }, surfaceOp: 'append' })
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
  s = apply(s, { type: 'tool/call', seq: 1, callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' })
  // Stored dsh sessions can carry tool/result with message undefined; the
  // projection must still fold so session resume does not fail.
  s = apply(s, { type: 'tool/result', seq: 2, surfaceOp: 'append' })
  // With no message there is no toolCallId to pair, so identity falls back to
  // the fail-safe 'unknown' name rather than the preceding call's name.
  const refs = Object.keys(s.pages)
  assert.equal(refs.length, 1, `expected one page; have ${refs}`)
  assert.equal(s.pages[refs[0]].contentHash, contentHash(''))
  assert.equal(s.pages[refs[0]].status, 'resident')
})

test('re-declared page keeps first-declare-wins content hash but refreshes tokens/status', () => {
  let s = init()
  s = apply(s, { type: 'tool/call', seq: 1, callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' })
  s = apply(s, { type: 'tool/result', seq: 2, message: { toolCallId: 'c1', content: 'aaa' }, surfaceOp: 'append' })
  const ref = toolRef(undefined, 'bash', { cmd: 'ls' } as never)
  const firstHash = s.pages[ref].contentHash
  s = apply(s, { type: 'tool/result', seq: 3, message: { toolCallId: 'c1', content: 'a much longer result body' }, surfaceOp: 'append' })
  assert.equal(s.pages[ref].contentHash, firstHash)
  assert.ok(s.pages[ref].tokens > 1)
  assert.equal(s.pages[ref].status, 'resident')
  assert.deepEqual(s.order, [ref], 'no duplicate order entry')
})

test('surface replace op marks shadowed pages stub, never regresses evicted', () => {
  let s = init()
  s = apply(s, { type: 'tool/call', seq: 1, callId: 'c1', name: 'bash', arguments: '{"cmd":"ls"}' })
  s = apply(s, { type: 'tool/result', seq: 2, message: { toolCallId: 'c1', content: 'x' }, surfaceOp: 'append' })
  const ref = toolRef(undefined, 'bash', { cmd: 'ls' } as never)
  // user/message replacing surface node 2 (the tool/result) shadows it
  s = apply(s, { type: 'user/message', seq: 5, surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2] })
  assert.equal(s.pages[ref].status, 'stub')
  // compaction/summary evicts the shadowed seqs
  s = apply(s, { type: 'compaction/summary', seq: 6, shadowedSeqs: [2] })
  assert.equal(s.pages[ref].status, 'evicted')
  // a later replace must not regress evicted → stub
  s = apply(s, { type: 'user/message', seq: 7, surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2] })
  assert.equal(s.pages[ref].status, 'evicted')
})

test('unmapped events leave state untouched (same reference)', () => {
  const s = init()
  assert.equal(apply(s, { type: 'request/header', seq: 1 }), s)
})
