/**
 * W22 — per-session @ctxvm/node tracer lifecycle and coverage sidecar.
 *
 * One tracer per sessionId; created lazily on the first request/header, fed from
 * event-map.ts, finished on session/disposed or plugin unload. Never throws into
 * the event loop.
 */
import { createHash } from 'node:crypto'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { basename, join } from 'node:path'
import { createTrace, type Tracer } from '@ctxvm/node'
import type { SessionId } from '@deepseek-ai/dsh-session/types'
import type { CtxvmDshConfig } from './config.ts'
import { eventData, asRecord, asString } from './event-data.ts'
import { mapEvent } from './event-map.ts'
import type { SessionEvent } from '@deepseek-ai/dsh-session/types'
import type { SessionTracer, StubRecord } from './types.ts'

const packageVersion = (JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')) as { version: string }).version

/** Expand `~` and `${VAR}` / `${VAR:-default}` in the configured trace dir. */
export function resolveTraceDir(traceDir: string): string {
  const withEnv = traceDir.replace(/\$\{([A-Z_][A-Z0-9_]*)(?::-([^}]*))?\}/g, (_match, name: string, dflt?: string) => {
    const value = process.env[name]
    return value !== undefined && value !== '' ? value : (dflt ?? _match)
  })
  return withEnv.replace(/^~(?=$|\/)/, homedir())
}

/** Create empty per-session state; all stub/provenance state is session-local. */
export function createSessionTracer(sessionId: SessionId): SessionTracer {
  return {
    sessionId,
    calls: new Map(),
    pagesBySeq: new Map(),
    turn: -1,
    stubbedRefs: [],
    evictedTokens: 0,
    diagnostics: [],
  }
}

/** Normalize state from older/resumed callers without sharing module globals. */
function normalize(st: SessionTracer): void {
  st.pagesBySeq ??= new Map()
  st.stubbedRefs ??= []
  st.diagnostics ??= []
  st.evictedTokens ??= 0
  if (typeof st.turn !== 'number') st.turn = -1
}

export function openTracer(
  sessionId: SessionId,
  init: { model: string; provider: string },
  config: CtxvmDshConfig,
): SessionTracer {
  const st = createSessionTracer(sessionId)
  st.tracer = createTrace({
    agentId: `${config.agentIdPrefix}:${String(sessionId).slice(0, 12)}`,
    model: init.model,
    provider: init.provider,
    budgetTokens: config.budgetTokens,
    tokenizerId: config.tokenizerId,
  })
  return st
}

/** Create the tracer once a request/header supplies real provider/model identity. */
export function ensureTracer(st: SessionTracer, firstEvent: unknown, config: CtxvmDshConfig): void {
  normalize(st)
  if (st.tracer) return
  const ev = eventData(firstEvent as never)
  if (ev.type !== 'request/header') {
    st.pending ??= []
    if (st.pending.length < 2048) st.pending.push(firstEvent)
    return
  }
  let model = 'unknown'
  let provider = 'dsh'
  const header = asRecord(ev.header)
  const headerConfig = asRecord(header?.config)
  if (headerConfig) {
    provider = asString(headerConfig.provider) || provider
    model = asString(headerConfig.model) || model
  }
  st.tracer = openTracer(st.sessionId, { model, provider }, config).tracer
  replayPending(st)
}

/** Flush a session that never committed a request/header, keeping the trace total. */
export function finalizeTracer(st: SessionTracer, config: CtxvmDshConfig): void {
  normalize(st)
  if (st.tracer) return
  st.tracer = openTracer(st.sessionId, { model: 'unknown', provider: 'dsh' }, config).tracer
  replayPending(st)
}

function replayPending(st: SessionTracer): void {
  const pending = st.pending ?? []
  st.pending = []
  for (const event of pending) mapEvent(st, event as SessionEvent)
}

type TraceRow = Record<string, unknown>

function rowsOf(events: readonly object[]): TraceRow[] {
  return events as TraceRow[]
}

function pageId(row: TraceRow): { logicalRef: string; contentHash: string } | undefined {
  const page = asRecord(row.page)
  const id = asRecord(page?.id)
  if (typeof id?.logicalRef !== 'string' || typeof id.contentHash !== 'string') return undefined
  return { logicalRef: id.logicalRef, contentHash: id.contentHash }
}

/** Build the full W17 manifest plus DSH passive-stub facts from finished bytes. */
function coverageManifest(st: SessionTracer, path: string, jsonl: string, events: readonly object[]): object {
  const rows = rowsOf(events)
  const open = rows.find(row => row.type === 'session.open') ?? {}
  const declares = rows.filter(row => row.type === 'page.declare')
  const faults = rows.filter(row => row.type === 'page.fault')
  const pages = new Set(declares.map(row => {
    const id = pageId(row)
    return id === undefined ? '' : `${id.logicalRef}\u0000${id.contentHash}`
  }).filter(Boolean))
  const turns = new Set(rows.filter(row => row.type === 'turn.render' && typeof row.turn === 'number').map(row => row.turn))
  const bySource: Record<string, number> = { tool_recall: 0, identifier_scan: 0, explicit_api: 0, semantic: 0 }
  for (const row of faults) if (typeof row.source === 'string' && row.source in bySource) bySource[row.source]++
  const stubbedRefs: StubRecord[] = st.stubbedRefs.map(record => ({ ...record }))
  return {
    xcabiCoverage: '0.1',
    traceFile: basename(path),
    traceDigest: createHash('sha256').update(jsonl).digest('hex'),
    session: {
      sessionID: String(st.sessionId),
      ...typeof open.environmentId === 'string' ? { environmentId: open.environmentId } : {},
      model: typeof open.model === 'string' ? open.model : 'unknown',
      provider: typeof open.provider === 'string' ? open.provider : 'dsh',
    },
    toolTable: { readOnlyRegistered: [], default: 'MUTATING' },
    instrumentation: {
      ts: rows.every(row => typeof row.ts === 'string' && row.ts.length > 0),
      toolEffect: false,
      identifierScan: true,
    },
    plugin: {
      version: packageVersion,
      harness: 'deepseek-harness',
      adapter: 'dsh',
      capabilities: { stubWire: 1 },
      stubDropped: stubbedRefs.length > 0 ? 'recoverable' : 'off',
      evictedTokens: st.evictedTokens,
      stubCount: stubbedRefs.length,
      stubbedRefs,
    },
    captures: {
      turns: turns.size,
      pages: pages.size,
      declares: declares.length,
      declaresByClass: { READ_ONLY: 0, MUTATING: 0 },
      faults: faults.length,
      faultsBySource: bySource,
    },
  }
}

/** Write the finished trace and its exact-byte coverage sidecar. Returns the trace path. */
export function flushTracer(st: SessionTracer, config: CtxvmDshConfig): string {
  normalize(st)
  if (!st.tracer) throw new Error('flushTracer: no tracer for session ' + String(st.sessionId))
  const finished = st.tracer.finish()
  const dir = resolveTraceDir(config.traceDir)
  mkdirSync(dir, { recursive: true, mode: 0o700 })
  const path = join(dir, `${String(st.sessionId)}-${Date.now()}.jsonl`)
  writeFileSync(path, finished.jsonl, { mode: 0o600 })
  const coveragePath = `${path}.coverage.json`
  const coverage = coverageManifest(st, path, finished.jsonl, finished.events)
  writeFileSync(coveragePath, `${JSON.stringify(coverage, undefined, 2)}\n`, { mode: 0o600 })
  st.tracePath = path
  st.coveragePath = coveragePath
  return path
}
