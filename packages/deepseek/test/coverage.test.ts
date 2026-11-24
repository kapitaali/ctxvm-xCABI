/** Passive stub trace + exact-byte DSH coverage sidecar. */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { mkdtempSync, readFileSync, rmSync, statSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { mapEvent } from '../src/event-map.ts'
import { flushTracer, openTracer } from '../src/tracer.ts'

const config = {
  enabled: true,
  traceDir: '',
  tokenizerId: 'apx4-char',
  budgetTokens: 200_000,
  agentIdPrefix: 'dsh',
} as const

function env(type: string, data: Record<string, unknown> = {}, seq = 0, extra: Record<string, unknown> = {}): never {
  return { type, seq, time: 1794841561000, data, ...extra } as never
}

test('flush writes a private sidecar bound to the exact stub trace bytes', () => {
  const dir = mkdtempSync(join(tmpdir(), 'ctxvm-dsh-coverage-'))
  try {
    const st = openTracer('session-coverage-0001' as never, { model: 'm', provider: 'p' }, { ...config, traceDir: dir })
    mapEvent(st, env('turn/start', { turn: 1 }, 0))
    mapEvent(st, env('tool/call', { callId: 'c1', name: 'read', arguments: '{}' }, 1))
    mapEvent(st, env('tool/result', { message: { toolCallId: 'c1', content: 'full body' } }, 2, { surfaceOp: 'append' }))
    const original = st.pagesBySeq.get(2)!
    mapEvent(st, env('tool/result', { message: { toolCallId: 'c1', content: 'exact stub' } }, 3, {
      surfaceOp: { op: 'replace', startSeq: 2, endSeq: 2 }, sourceEventSeqs: [2],
    }))
    const tracePath = flushTracer(st, { ...config, traceDir: dir })
    const coveragePath = `${tracePath}.coverage.json`
    const bytes = readFileSync(tracePath)
    const sidecar = JSON.parse(readFileSync(coveragePath, 'utf8')) as Record<string, any>
    assert.equal(sidecar.traceFile, tracePath.split('/').at(-1))
    assert.equal(sidecar.traceDigest, createHash('sha256').update(bytes).digest('hex'))
    assert.equal(sidecar.plugin.adapter, 'dsh')
    assert.deepEqual(sidecar.plugin.capabilities, { stubWire: 1 })
    assert.equal(sidecar.plugin.stubDropped, 'recoverable')
    assert.equal(sidecar.plugin.stubCount, 1)
    assert.equal(sidecar.plugin.evictedTokens, original.tokens)
    assert.deepEqual(sidecar.plugin.stubbedRefs, [{
      ref: original.logicalRef,
      contentHash: original.contentHash,
      stubText: 'exact stub',
      turn: 0,
    }])
    assert.deepEqual(sidecar.captures.declaresByClass, { READ_ONLY: 0, MUTATING: 0 })
    assert.equal(sidecar.captures.declares, 1)
    assert.equal(sidecar.captures.turns, 1)
    assert.equal(statSync(tracePath).mode & 0o777, 0o600)
    assert.equal(statSync(coveragePath).mode & 0o777, 0o600)
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
})
