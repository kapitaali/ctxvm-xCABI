/**
 * W22 — page table fold unit tests.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ctxvmPageTableProjection } from '../src/page-table.ts'

test('init yields an empty page table', () => {
  const state = ctxvmPageTableProjection.init({} as never, 0)
  assert.deepEqual(state, { pages: {}, order: [] })
})

test('apply is pure and does not mutate input state', () => {
  const state = ctxvmPageTableProjection.init({} as never, 0)
  const next = ctxvmPageTableProjection.apply(state, { type: 'turn/start', turn: 0 } as never)
  assert.deepEqual(state, { pages: {}, order: [] })
  assert.ok(next)
})
