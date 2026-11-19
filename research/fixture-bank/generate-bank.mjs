// Content-bearing fixture bank generator v2 (research lane).
// 2-hop causal chain (RR-E0ENRICH-20261119): target.md (tool_result, the tool_recall
// page) holds target_threshold + pointers (j1 primary, j2 fallback); the setting values
// (doc<j>_value) and reference tags (<topic>-doc-<j>) live ONLY in doc-<j>.md file pages.
// The prompt asks for facts that require visiting j1 (value + tag) and j2 (value only),
// giving a 3-tier touch count T(p) in {2,1,0} with Var(T) > 0 on the referenceAnswer.
// Emits valid xCABI traces via the REAL @ctxvm/node tracer. No model call, no spend.
import { mkdirSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, dirname } from 'node:path'
import { createTrace } from '/home/theb/Documents/ctxvm/packages/node/dist/index.js'

const ROOT = dirname(fileURLToPath(import.meta.url))
const TRACES = join(ROOT, 'traces')

const N_ITEMS = 20
const N_FILE_PAGES = 10
const TOPICS = [
  'auth-gateway', 'billing-ledger', 'cache-proxy', 'audit-log', 'search-index',
  'queue-broker', 'session-store', 'rate-limiter', 'config-vault', 'notify-hub',
  'metrics-pipe', 'feature-flags', 'blob-store', 'schema-registry', 'token-minter',
  'retry-scheduler', 'geo-router', 'consent-manager', 'export-worker', 'health-probe',
]

const val = j => 100 + j * 7
// deterministic, varied, distinct pointers within 1..10
const primaryOf = i => ((i - 1) % 10) + 1
const fallbackOf = i => ((i - 1 + 3) % 10) + 1

function fileBody(topic, j) {
  return [
    `Document ${j} for the ${topic} service.`,
    `The ${topic} component exposes setting doc${j}_value = ${val(j)} in its default profile.`,
    `Operators consult document ${j} when reconciling the ${topic} rollout; it records the`,
    `baseline threshold and the owner contact for stage ${j}. Reference tag: ${topic}-doc-${j}.`,
  ].join('\n') + '\n'
}

// target.md carries target_threshold + numeric pointers ONLY (no file values/tags).
function targetBody(topic, j1, j2) {
  return [
    `read_file result for ${topic}/target.md:`,
    `configured_mode = strict`,
    `target_threshold = 42`,
    `primary_document = ${j1}`,
    `fallback_document = ${j2}`,
    `This tool result is the recall target for the ${topic} fixture.`,
  ].join('\n') + '\n'
}

// Prompt asks for the 2-hop facts; uses generic forms (docN_value = V), no concrete
// file identifiers, so the prompt itself contributes no file-page touch tokens.
function prompt(topic) {
  return [
    `Using the provided ${topic} documents and the tool result, answer from the context only:`,
    `(1) the configured target_threshold;`,
    `(2) for the primary document named in the tool result, its setting token and value (in the form docN_value = V) and its reference tag;`,
    `(3) for the fallback document named in the tool result, its setting token and value (in the form docN_value = V) only.`,
  ].join('\n')
}

// Deterministic answer key for Phase 0 self-verification of T(p). NEVER in tau or trace.
function referenceAnswer(topic, j1, j2) {
  return [
    `target_threshold = 42`,
    `primary: doc${j1}_value = ${val(j1)}; reference tag ${topic}-doc-${j1}`,
    `fallback: doc${j2}_value = ${val(j2)}`,
  ].join('\n')
}

// Reconstruct tau, or tau\p when excludeRef is given. Pure. No referenceAnswer.
export function buildContext(item, excludeRef = null) {
  const parts = item.pages
    .filter(p => p.logicalRef !== excludeRef)
    .map(p => `[${p.logicalRef}]\n${p.body}`)
  return `${item.prompt}\n\n${parts.join('\n\n')}`
}

function main() {
  mkdirSync(TRACES, { recursive: true })
  const items = []
  for (let i = 1; i <= N_ITEMS; i++) {
    const id = `fb${String(i).padStart(2, '0')}`
    const topic = TOPICS[i - 1]
    const j1 = primaryOf(i)
    const j2 = fallbackOf(i)
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
      pages.push({ logicalRef: r.logicalRef, contentHash: r.contentHash, kind: 'file', tokens: r.tokens, body, doc: j })
    }
    const tBody = targetBody(topic, j1, j2)
    const targetArgs = { path: `fixtures/${topic}/target.md` }
    const t = vm.page({ tool: 'read_file', args: targetArgs, content: tBody })
    pages.push({ logicalRef: t.logicalRef, contentHash: t.contentHash, kind: 'tool_result', tokens: t.tokens, body: tBody })

    vm.render() // turn 0
    vm.recall({ tool: 'read_file', args: targetArgs })
    vm.page({ tool: 'read_file', args: targetArgs, content: tBody }) // -> page.fault(tool_recall)
    vm.render({ latencyMs: 120 }) // turn 1

    const result = vm.finish()
    const traceRel = `traces/${id}.jsonl`
    writeFileSync(join(ROOT, traceRel), result.jsonl)
    items.push({
      id, topic, prompt: prompt(topic), pages,
      primary: j1, fallback: j2,
      referenceAnswer: referenceAnswer(topic, j1, j2),
      recallTarget: t.logicalRef,
      trace: traceRel,
      stats: result.stats,
    })
  }

  const bank = {
    schema: 'ctxvm-content-bearing-fixture-bank/v2',
    date: '2026-11-19',
    stratum: 'tool_recall',
    enrichment: 'RR-E0ENRICH-20261119 2-hop causal chain; fixes v1 constant-T degeneracy (rho=NaN)',
    purpose: 'Content-bearing prompt+page fixtures paired with valid xCABI traces so tau and tau\\p exist as text; 3-tier touch count T(p) in {2,1,0} with Var(T)>0; precondition for E0/E2. Synthetic; no real sessions; no model call.',
    tracer: '@ctxvm/node dist (createTrace), RFC-0.1',
    identifierRule: 'T(p) = whole-token, case-insensitive presence of doc<j>_value and <topic>-doc-<j> in the answer; j from the file page logicalRef',
    n_items: items.length,
    items,
  }
  writeFileSync(join(ROOT, 'bank.json'), JSON.stringify(bank, null, 2) + '\n')

  const totalPages = items.reduce((s, it) => s + it.pages.length, 0)
  console.log(`wrote bank.json v2: ${items.length} items, ${totalPages} pages, stratum=tool_recall, 2-hop chain`)
  for (const it of items) {
    const tau = buildContext(it)
    const taup = buildContext(it, it.recallTarget)
    console.log(`${it.id}: j1=${it.primary} j2=${it.fallback} pages=${it.pages.length} faults=${JSON.stringify(it.stats.faults)} tau=${tau.length}c taup=${taup.length}c`)
  }
}

if (process.argv[1] && import.meta.url === 'file://' + process.argv[1]) main()
