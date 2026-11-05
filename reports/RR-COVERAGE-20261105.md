# RR-COVERAGE-20261105 — W17: the coverage manifest

Card: W17 (08.1-UPDATE-PROMPT.md), the #2 item in `research/synthesis-20261105.md`.
Status: landed; gate green; one commit. Dates: 2026-11-05.

## What was built

A flushed capture is now a **triple**: `<file>.jsonl`, `<file>.meta.json`, `<file>.coverage.json`.
The manifest is a sidecar, not a tenth trace event — the sealed nine-verb envelope is untouched, and
the manifest describes a run's instrumentation rather than reporting an observation.

`tools/coverage_check.py` is the authority. It is stdlib-only, takes the trace path and the manifest
path, and exits 0 when the pair is consistent, 1 for each violated law (one printed line each) and 2
for usage, IO or JSON errors. Every lane's test suite invokes it through a subprocess, so a lane
cannot drift from the checker by importing it.

## Shape v0.1

```json
{
  "xcabiCoverage": "0.1",
  "traceFile": "<name>.jsonl",
  "traceDigest": "<sha256 over the trace bytes>",
  "session": { "sessionID": "...", "environmentId": "...", "model": "...", "provider": "..." },
  "toolTable": { "readOnlyRegistered": ["..."], "default": "MUTATING" },
  "instrumentation": { "ts": true, "toolEffect": true, "identifierScan": true },
  "plugin": { "version": "...", "harness": "...", "harnessVersion": null },
  "captures": {
    "turns": 0, "pages": 0, "declares": 0,
    "declaresByClass": { "READ_ONLY": 0, "MUTATING": 0 },
    "faults": 0,
    "faultsBySource": { "tool_recall": 0, "identifier_scan": 0, "explicit_api": 0, "semantic": 0 }
  }
}
```

Design decisions, and why:

- **Session facts are read from the trace's own `session.open` row**, never from the environment. They
  are therefore byte-true by construction, and the checker verifies them against the same bytes it
  digests. `sessionID` is the exception and is documented as a pairing fact: it appears in the meta
  sidecar and cannot be verified from the trace.
- **`default` must be `MUTATING`.** A different value is a law violation, not an extension — the W15
  fail-safe default is restated where it can be checked.
- **The registration law runs on what the trace already carries.** For every `tool_result` declare that
  stamps a `toolEffect`, the tool name (text between `tool:` and the first `(` in the `logicalRef`,
  matched by full name and by leaf after the last dot) must be consistent: registered READ_ONLY tools
  never carry MUTATING, unregistered names never carry READ_ONLY.
- **`instrumentation.ts` is a real toggle.** Each lane re-reads `CTXVM_TRACE_TS` at flush time, mirroring
  the tracer's per-trace opt-out, so a D9 capture claims `false` and still passes.
- **Flush-only.** Write-through partials never get a manifest; a pruned partial would leave coverage
  describing bytes that no longer exist.
- **Prune and era law.** `_prune_traces` deletes the coverage file with its capture. The UC1 era-copy
  lists in both lanes include `coverage.json`, so a handoff package carries the manifest.
- **One truth per table.** opencode exports `readOnlyTable()` and `READ_ONLY` from the plugin module and
  the shim imports the same binding; ai-sdk exports `READ_ONLY_TOOLS` from the tap. Stamps and the
  manifest cannot desync.

## The live bug the checker found

Building the hermes lane against real capture bytes exposed a defect that no fixture would have shown:
the stamp site read `kwargs.get("tool")`, while live payloads carry **`tool_name`** (the hook table in
`packages/hermes/HOOKS.md`). Every live hermes `page.declare` had therefore been classified `MUTATING`
on plugin 0.8.0.

Evidence: the witness log for the live capture contains 447 `tool=None` rows. The corpus fixture
`corpus/m4/hermes-live-session-01.jsonl` predates W15 and carries no `toolEffect` at all, so the fixture
could not have caught it.

Fix: `tool = kwargs.get("tool") or kwargs.get("tool_name")` at the post stamp, the post witness and the
pre witness in `packages/hermes/live/__init__.py`.

## Lanes and tests

| lane | writer | table | instrumentation |
|---|---|---|---|
| hermes 0.9.0 | `_flush_traces` (after meta) | `read_file, search_files` + `CTXVM_READONLY_TOOLS` | all true |
| opencode | `flushTraces` (after `writeMeta`) | `READ_ONLY` (load-time export) | `ts` at flush |
| ai-sdk | `writeCapture` (after meta) | `READ_ONLY_TOOLS` (tap export) | `ts` at flush |

Hermes: 112 → 117 tests. The five new tests are: a stamp test that registers FakeCtx hooks, fires
`pre_tool_call`/`post_tool_call` with `tool_name: "read_file"` and asserts a flushed READ_ONLY row; a
checker-green flush; lane-fixed constants; no manifest at write-through partials; and a tampered-pair
test with five negatives (wrong digest, registered-MUTATING flip, unregistered-READ_ONLY, dropped
`toolEffect` key, wrong counts). Retention now pins that the sidecar dies with its capture.

opencode: 61 tests (live-adapter extended with key set, digest over the bytes, sorted table,
instrumentation, version agreement and checker run).

ai-sdk: 45 tests (integration test extended: parse, digest, table, `ts: false` under D9, checker exit 0).

## Reproduction

```sh
for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done   # leaked CTXVM_* break direct runs
node --test packages/ai-sdk/test
node --test packages/opencode/test
node --test packages/node/test
python -m pytest packages/hermes -q
bash tools/run-ci.sh

# the checker, on any flushed pair
python3 tools/coverage_check.py <trace>.jsonl <trace>.coverage.json
```

Gate output, 2026-11-05:

```
[ctxvm-ci] ts suites green (21 + 61 + 45 tests); python suites green (117 + 44 + 8 tests)
[ctxvm-ci] ALL GATES GREEN
```

## What this does not claim

- **Not tamper evidence.** A manifest that describes a trace is only as good as the directory it sits
  in. The pair is verifiable; the pair is not signed.
- **`identifierScan` has no byte shadow.** The field records that the scan instrumentation ran; nothing
  in the trace proves it per-event.
- **`sessionID` cannot be checked.** It is carried for pairing with the meta sidecar.
- **Coverage is a manifest of instrumentation, not of risk.** It says which classes and toggles were in
  force. It does not say the run was adequate.

## Open, for the owner

- The 0.9.0 fix reaches live captures only after `~/.hermes/plugins/ctxvm-tracer/` is re-synced and the
  gateway restarts; the running gateway holds 0.8.0 in memory.
- The provider identity is still `unknown` in live traces until the plugin settings or the payload
  supply it.
- Next cards, in the order the synthesis suggests: monitor-replay tier 1 (TPR/FPR over `corpus/m1`–`m8`),
  then the collide-proof trace filename.
