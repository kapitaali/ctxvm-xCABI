// Phase 0 self-test for the content-bearing fixture bank. Zero model calls.
// Verifies: body<->hash integrity (real tracer functions), trace<->bank pairing,
// tool_recall stratum, >=10 pages, tau/tau\p constructibility, no leakage,
// RFC-0.1 schema conformance, and replay-clean (0 divergences) for every trace.
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, dirname } from 'node:path'
import { spawnSync } from 'node:child_process'
import { contentHash, approx4 } from '/home/theb/Documents/ctxvm/packages/node/dist/index.js'
import { buildContext } from './generate-bank.mjs'

const ROOT = dirname(fileURLToPath(import.meta.url))
const REPO = '/home/theb/Documents/ctxvm'
const bank = JSON.parse(readFileSync(join(ROOT, 'bank.json'), 'utf8'))
const checks = []
const ok = (name, pass, detail = '') => checks.push({ name, pass: !!pass, detail })

const traceFiles = bank.items.map(it => join(ROOT, it.trace))

for (const it of bank.items) {
  const tag = it.id
  // body <-> hash / token integrity using the real tracer functions
  const hashOk = it.pages.every(p => contentHash(p.body) === p.contentHash)
  const tokOk = it.pages.every(p => approx4(p.body) === p.tokens)
  ok(`${tag} body-hash`, hashOk)
  ok(`${tag} body-tokens`, tokOk)
  ok(`${tag} >=10 unique pages`, new Set(it.pages.map(p => p.logicalRef)).size >= 10)

  const events = readFileSync(join(ROOT, it.trace), 'utf8').trim().split('\n').map(JSON.parse)
  const bankKeys = new Set(it.pages.map(p => `${p.logicalRef}|${p.contentHash}`))
  const declares = events.filter(e => e.type === 'page.declare')
  const declOk = declares.every(e => bankKeys.has(`${e.page.id.logicalRef}|${e.page.id.contentHash}`))
  ok(`${tag} declare<->bank`, declOk)
  const faults = events.filter(e => e.type === 'page.fault')
  const tr = faults.filter(e => e.source === 'tool_recall').length
  ok(`${tag} tool_recall>=1`, tr >= 1, `tool_recall=${tr}`)
  ok(`${tag} pure tool_recall stratum`, faults.every(e => e.source === 'tool_recall'))
  ok(`${tag} recallTarget faulted`, faults.some(e => e.source === 'tool_recall' && e.page.logicalRef === it.recallTarget))

  // tau / tau\p constructible as actual text
  const tau = buildContext(it)
  const taup = buildContext(it, it.recallTarget)
  const targetBody = it.pages.find(p => p.logicalRef === it.recallTarget).body
  ok(`${tag} tau nonempty`, tau.length > 0)
  ok(`${tag} tau\\p shorter`, taup.length < tau.length)
  ok(`${tag} target removed from tau\\p`, !taup.includes(targetBody))

  // no leakage of real filesystem/bank paths into the trace or the model-visible tau.
  // (the synthetic agentId "fixture-bank-fbNN" is a legitimate identifier, not a path.)
  const raw = readFileSync(join(ROOT, it.trace), 'utf8')
  const leakRe = /\/home\/|\/Documents\/|\.mjs|bank\.json|tb-dsh-smoke|node_modules/
  ok(`${tag} trace no leakage`, !leakRe.test(raw))
  ok(`${tag} tau no leakage`, !leakRe.test(tau) && !leakRe.test(taup))
}

// RFC-0.1 schema conformance over all traces
const val = spawnSync('python3', [join(REPO, 'spec/rfc-0.1/validate_schema_v0_1.py'), ...traceFiles], { encoding: 'utf8' })
ok('schema v0.1 conformance', val.status === 0, (val.stdout || val.stderr || '').trim().split('\n').pop())

// replay-clean for every trace
let replayBad = []
for (const it of bank.items) {
  const r = spawnSync(join(REPO, 'rust/target/release/replay'), [join(ROOT, it.trace)], { encoding: 'utf8' })
  let div = null
  try { div = JSON.parse(r.stdout).divergences } catch { div = ['unparseable'] }
  if (r.status !== 0 || !Array.isArray(div) || div.length !== 0) replayBad.push(it.id)
}
ok('replay 0 divergences (all 20)', replayBad.length === 0, replayBad.join(','))

const failed = checks.filter(c => !c.pass)
for (const c of checks) console.log(`${c.pass ? 'PASS' : 'FAIL'} ${c.name}${c.detail ? ' :: ' + c.detail : ''}`)
console.log(`\n${checks.length - failed.length}/${checks.length} checks passed`)
console.log(failed.length === 0 ? 'BANK_PHASE0_OK' : 'BANK_PHASE0_FAIL')
process.exit(failed.length === 0 ? 0 : 1)
