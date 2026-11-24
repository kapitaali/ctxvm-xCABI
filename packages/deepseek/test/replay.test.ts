/**
 * W22 acceptance #2/#3 — trace → validate → replay.
 *
 * Integration test: skipped unless CTXVM_TEST_TRACE is set to a captured trace
 * and the ctxvm repo root is available. Run manually:
 *
 *   CTXVM_REPO=/home/theb/Documents/ctxvm node --test test/replay.test.ts
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'

const repo = process.env.CTXVM_REPO
const trace = process.env.CTXVM_TEST_TRACE

test('captured trace validates and replays without divergence', { skip: !repo || !trace }, () => {
  execFileSync(`${repo}/venvs/odps/bin/python`, [`${repo}/spec/rfc-0.1/validate_schema_v0_1.py`, trace!], { stdio: 'pipe' })
  const out = execFileSync('cargo', [
    'run', '--quiet', '--release', '-p', 'ctxvm-conformance', '--bin', 'replay', trace!,
  ], { cwd: repo, stdio: 'pipe' })
  const report = JSON.parse(out.toString())
  assert.deepEqual(report.divergences, [])
})
