// Content-bearing fixture bank generator (research lane, Phase 0).
// Emits valid xCABI traces via the REAL @ctxvm/node tracer (read-only dependency),
// paired with actual page body text so tau and tau\p exist as text.
// Stratified on tool_recall (the E1-positive stratum). No model call, no spend.
import { mkdirSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, dirname } from 'node:path'
import { createTrace } from '/home/theb/Documents/ctxvm/packages/node/dist/index.js'

const ROOT = dirname(fileURLToPath(import.meta.url))
const TRACES = join(ROOT, 'traces')

const N_ITEMS = 20
const N_FILE_PAGES = 10 // + 1 tool_result recall target = 11 unique pages (>= 10)
const TOPICS = [
  'auth-gateway', 'billing-ledger', 'cache-proxy', 'audit-log', 'search-index',
  'queue-broker', 'session-store', 'rate-limiter', 'config-vault', 'notify-hub',
  'metrics-pipe', 'feature-flags', 'blob-store', 'schema-registry', 'token-minter',
  'retry-scheduler', 'geo-router', 'consent-manager', 'export-worker', 'health-probe',
]

function fileBody(topic, j) {
  return [
    `Document ${j} for the ${topic} service.`,
    `The ${topic} component exposes setting doc${j}_value = ${100 + j * 7} in its default profile.`,
    `Operators consult document ${j} when reconciling the ${topic} rollout; it records the`,
    `baseline threshold and the owner contact for stage ${j}. Reference tag: ${topic}-doc-${j}.`,
  ].join('\n') + '\n'
}

function targetBody(topic) {
  return [
    `read_file result for ${topic}/target.md:`,
    `configured_mode = strict`,
    `target_threshold = 42`,
    `fallback = document 3`,
    `This tool result is the recall target for the ${topic} fixture.`,
  ].join('\n') + '\n'
}

function prompt(topic) {
  return `Using the provided ${topic} documents and the tool result, state the configured target_threshold and which document is the fallback. Answer from the context only.`
}

// Reconstruct the full context tau, or tau\p when excludeRef is given. Pure.
export function buildContext(item, excludeRef = null) {
  const parts = item.pages
    .filter(p => p.logicalRef !== excludeRef)
    .map(p => `[${p.logicalRef}]\n${p.body}`)
  return `${item.prompt}\n\n${parts.join('\n\n')}`
}

function main() {
  mkdirSync(TRACES, { recursive: true })
  const items = []
  for (let i = 0; i < N_ITEMS; i++) {
    const id = `fb${String(i + 1).padStart(2, '0')}`
    const topic = TOPICS[i]
    const vm = createTrace({
      agentId: `fixture-bank-${id}`,
      model: 'synthetic/fixture-v1',
      provider: 'synthetic',
      budgetTokens: 120_000,
    })
    const pages = []
    for (let j = 1; j <= N_FILE_PAGES; j++) {
      const body = fileBody(topic, j)
      const r = vm.page({ ref: `file:fixtures/${topic}/doc-${j}.md`, kind: 'file', content: body })
      pages.push({ logicalRef: r.logicalRef, contentHash: r.contentHash, kind: 'file', tokens: r.tokens, body })
    }
    const tBody = targetBody(topic)
    const targetArgs = { path: `fixtures/${topic}/target.md` }
    const t = vm.page({ tool: 'read_file', args: targetArgs, content: tBody })
    pages.push({ logicalRef: t.logicalRef, contentHash: t.contentHash, kind: 'tool_result', tokens: t.tokens, body: tBody })

    vm.render() // turn 0: all pages revealed full
    vm.recall({ tool: 'read_file', args: targetArgs })
    vm.page({ tool: 'read_file', args: targetArgs, content: tBody }) // -> page.fault(tool_recall)
    vm.render({ latencyMs: 120 }) // turn 1

    const result = vm.finish()
    const traceRel = `traces/${id}.jsonl`
    writeFileSync(join(ROOT, traceRel), result.jsonl)
    items.push({
      id, topic, prompt: prompt(topic), pages,
      recallTarget: t.logicalRef,
      trace: traceRel,
      stats: result.stats,
    })
  }

  const bank = {
    schema: 'ctxvm-content-bearing-fixture-bank/v1',
    date: '2026-11-19',
    stratum: 'tool_recall',
    purpose: 'Content-bearing prompt+page fixtures paired with valid xCABI traces so tau and tau\\p exist as text; precondition for E0/E2 (RR-E2HOLD-20261119). Synthetic; no real sessions; no model call.',
    tracer: '@ctxvm/node dist (createTrace), RFC-0.1',
    n_items: items.length,
    items,
  }
  writeFileSync(join(ROOT, 'bank.json'), JSON.stringify(bank, null, 2) + '\n')

  const totalPages = items.reduce((s, it) => s + it.pages.length, 0)
  console.log(`wrote bank.json: ${items.length} items, ${totalPages} pages, stratum=tool_recall`)
  for (const it of items) {
    const tau = buildContext(it)
    const taup = buildContext(it, it.recallTarget)
    console.log(`${it.id}: pages=${it.pages.length} faults=${JSON.stringify(it.stats.faults)} turns=${it.stats.turns} tau=${tau.length}c taup=${taup.length}c`)
  }
}

if (process.argv[1] && import.meta.url === 'file://' + process.argv[1]) main()
