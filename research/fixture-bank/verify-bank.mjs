// Phase 0 self-test for the content-bearing fixture bank v2. Zero model calls.
// Keeps all v1 checks (body<->hash/tokens, trace<->bank pairing, tool_recall stratum,
// >=10 pages, tau/tau\p, leakage, RFC-0.1 schema, replay 0 divergences) and adds the
// RR-E0ENRICH 2-hop guards: 3-tier touch count T(p) in {2,1,0} with Var(T)>0 on the
// referenceAnswer, referenceAnswer never in tau/trace, and structural causal necessity.
import { readFileSync } from 'node:fs'
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

const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const present = (text, token) =>
  new RegExp(`(?<![A-Za-z0-9_])${esc(token)}(?![A-Za-z0-9_])`, 'i').test(text)
const fileIds = (it, p) => [`doc${p.doc}_value`, `${it.topic}-doc-${p.doc}`]
const touch = (it, answer) => it.pages.filter(p => p.kind === 'file')
  .map(p => fileIds(it, p).reduce((s, id) => s + (present(answer, id) ? 1 : 0), 0))
const variance = a => { const m = a.reduce((s, x) => s + x, 0) / a.length; return a.reduce((s, x) => s + (x - m) ** 2, 0) / a.length }

const traceFiles = bank.items.map(it => join(ROOT, it.trace))

for (const it of bank.items) {
  const tag = it.id
  const filePages = it.pages.filter(p => p.kind === 'file')
  const pj1 = filePages.find(p => p.doc === it.primary)
  const pj2 = filePages.find(p => p.doc === it.fallback)

  ok(`${tag} body-hash`, it.pages.every(p => contentHash(p.body) === p.contentHash))
  ok(`${tag} body-tokens`, it.pages.every(p => approx4(p.body) === p.tokens))
  ok(`${tag} >=10 unique pages`, new Set(it.pages.map(p => p.logicalRef)).size >= 10)
  ok(`${tag} j1!=j2`, it.primary !== it.fallback)

  const raw = readFileSync(join(ROOT, it.trace), 'utf8')
  const events = raw.trim().split('\n').map(JSON.parse)
  const bankKeys = new Set(it.pages.map(p => `${p.logicalRef}|${p.contentHash}`))
  ok(`${tag} declare<->bank`, events.filter(e => e.type === 'page.declare')
    .every(e => bankKeys.has(`${e.page.id.logicalRef}|${e.page.id.contentHash}`)))
  const faults = events.filter(e => e.type === 'page.fault')
  ok(`${tag} tool_recall>=1`, faults.filter(e => e.source === 'tool_recall').length >= 1)
  ok(`${tag} pure tool_recall stratum`, faults.every(e => e.source === 'tool_recall'))
  ok(`${tag} recallTarget faulted`, faults.some(e => e.source === 'tool_recall' && e.page.logicalRef === it.recallTarget))

  const tau = buildContext(it)
  const taup = buildContext(it, it.recallTarget)
  const targetBody = it.pages.find(p => p.logicalRef === it.recallTarget).body
  ok(`${tag} tau nonempty`, tau.length > 0)
  ok(`${tag} tau\\p shorter`, taup.length < tau.length)
  ok(`${tag} target removed from tau\\p`, !taup.includes(targetBody))

  const leakRe = /\/home\/|\/Documents\/|\.mjs|bank\.json|tb-dsh-smoke|node_modules/
  ok(`${tag} trace no leakage`, !leakRe.test(raw))
  ok(`${tag} tau no leakage`, !leakRe.test(tau) && !leakRe.test(taup))

  // ── v2: 3-tier touch count on the referenceAnswer ──
  const T = touch(it, it.referenceAnswer)
  const Tj1 = fileIds(it, pj1).reduce((s, id) => s + (present(it.referenceAnswer, id) ? 1 : 0), 0)
  const Tj2 = fileIds(it, pj2).reduce((s, id) => s + (present(it.referenceAnswer, id) ? 1 : 0), 0)
  const distractorSum = T.reduce((s, x, k) => {
    const p = filePages[k]; return s + ((p.doc === it.primary || p.doc === it.fallback) ? 0 : x)
  }, 0)
  ok(`${tag} T(j1)=2`, Tj1 === 2, `Tj1=${Tj1}`)
  ok(`${tag} T(j2)=1`, Tj2 === 1, `Tj2=${Tj2}`)
  ok(`${tag} distractor T sum=0`, distractorSum === 0)
  ok(`${tag} Var(T)>0`, variance(T) > 0, `T=[${T.join(',')}]`)

  // referenceAnswer (the answer key) never exposed in tau or the trace
  ok(`${tag} refAnswer not in tau`, !tau.includes(it.referenceAnswer))
  ok(`${tag} refAnswer not in trace`, !raw.includes(it.referenceAnswer))

  // structural causal necessity: required facts live uniquely in the intended page
  const tauNoJ1 = buildContext(it, pj1.logicalRef)
  const tauNoJ2 = buildContext(it, pj2.logicalRef)
  const j1ids = fileIds(it, pj1)
  ok(`${tag} j1 facts uniquely in p_j1`, j1ids.every(id => present(pj1.body, id) && present(tau, id) && !present(tauNoJ1, id)))
  ok(`${tag} j2 fact uniquely in p_j2`, present(pj2.body, `doc${it.fallback}_value`) && present(tau, `doc${it.fallback}_value`) && !present(tauNoJ2, `doc${it.fallback}_value`))
  // the value assignment + pointer live uniquely in target.md (the prompt names
  // "target_threshold" but never "= 42", so the assignment is the causal fact)
  const targetAssign = 'target_threshold = 42'
  const ptr1 = `primary_document = ${it.primary}`
  ok(`${tag} target facts uniquely in target`,
    targetBody.includes(targetAssign) && tau.includes(targetAssign) && !taup.includes(targetAssign)
    && targetBody.includes(ptr1) && tau.includes(ptr1) && !taup.includes(ptr1))
}

const val = spawnSync('python3', [join(REPO, 'spec/rfc-0.1/validate_schema_v0_1.py'), ...traceFiles], { encoding: 'utf8' })
ok('schema v0.1 conformance', val.status === 0, (val.stdout || val.stderr || '').trim().split('\n').pop())

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
