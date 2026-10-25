# 09 — Plugin parity contract (hermes ⇄ opencode) & shared capture kit

**Status:** contract in force (KIT-1, 2026-10-25) · **Scope rules:** applies to *new emissions*;
shipped corpus drops (`corpus/m1`–`m5`) are frozen goldens whose `.meta.json` sidecars describe
their own era (each drop's `provenance.json` records what it shipped).
**Decisions referenced:** plugin organization "What is decided" row in `00-README.md`; the
m5 flush-semantics erratum in `packages/opencode/live/README.md`.

---

## 1. Choices on record (the why)

1. **One deployable plugin per harness.** The plugin = capture substrate + use-case modules
   dispatched by a thin `live/` entry. No per-UC top-level plugins: UC1 handoff snapshots and
   UC2 forensic queries read the exact trace the substrate writes; separate installs would mean
   duplicated hook wiring, N hook scans per model request, and racing writers on one trace.
2. **Use cases are feature-gated submodules inside the plugin** — `{harness}/src/uc1-handoff.{ts,py}`,
   `uc2-forensics.{ts,py}`, `uc3-planner.{ts,py}` — enabled via `CTXVM_FEATURES`
   (`trace` default, byte-compatible with everything shipped m1–m5). The `live/` entry never
   grows fat; it registers and dispatches.
3. **Engine logic converges on shared bindings; ports stay thin.** `@ctxvm/node` (TS) is the
   reference; hermes's `src/plugin.py` is currently a Python mirror — acceptable for thin
   wrappers, replaced where the engine demands determinism (ctxvm-py / PyO3 card for UC1).
4. **Both plugins emit the identical wire format** — §2 (events) and §3 (sidecar) define
   "identical", and §4 defines how it is enforced.

---

## 2. Event layer — already identical, and now locked

Empirical audit over all three live drops (KIT-1 audit script output, 2026-10-25):
`corpus/m2/live-echo.jsonl` (opencode), `corpus/m4/hermes-live-session-01.jsonl` (hermes),
`corpus/m5/opencode-live-session-01.jsonl` (opencode). Key signature per event type:

| type | keys — identical in all three drops |
|---|---|
| `session.open` | `agentId, budgetTokens, model, provider, tokenizerId, type` |
| `page.declare` | `page, type` |
| `page.fault` | `page, source, turn, type` |
| `page.render` | `mode, page, turn, type` |
| `turn.render` | `evictedTokens, headroom, residentTokens, turn, type` |
| `call.meta` | `cacheEstimate, provider, turn, type` |

The common tracer substrate (`@ctxvm/node`, mirrored as `packages/hermes/src/plugin.py`)
makes this fall out by construction; `spec/rfc-0/validate_schema.py` + the replay engine keep
it. **Rule:** a new event type or field enters the wire ONLY via an RFC-0 revision, and the
revision lands as one card: both emitters, the schema validator, this table, and both parity
tests (`packages/opencode/test/meta-parity.test.ts`,
`packages/hermes/test/test_plugin.py::CanonicalSidecarParity`) in the same commit.

## 3. Sidecar layer — canonical `.meta.json` (the layer that HAD drift)

Audit finding: events identical; sidecars differed — hermes carried `pluginVersion` +
hook-terrain counter names (`session_starts, pre_tool_calls, post_tool_calls, pre_llm_calls,
session_ends, skipped_untraced`), no harness version; opencode carried a harness version
(`opencodeVersion`) with no plugin version, and hook-agnostic counter names. Canonical shape
(both emitters write EXACTLY these keys, in this order):

```json
{
  "sessionID": "<session id>",
  "harness": "opencode-v2-promise-plugin | hermes-python-plugin",
  "harnessVersion": "<harness product version or null>",
  "pluginVersion": "<adapter's own semver or null>",
  "model": "<provider/model-id>",
  "provider": "<provider id>",
  "budgetTokens": <declared budget, T9 bookkeeping>,
  "capturedAt": "<RFC-3339 with Z suffix>",
  "hookStats": {
    "contexts": <model requests>,          // opencode: context hook; hermes: pre_llm_call
    "before":  <execute-before fires>,     // opencode: execute.before; hermes: pre_tool_call
    "after":   <execute-after fires>,      // opencode: execute.after;  hermes: post_tool_call
    "completed": <ok results>, "errored": <failed results>,
    "extraHookStats": { <hook-terrain-specific counters> },   // hermes: session_starts, session_ends, skipped_untraced; opencode: {}
    "sessions": ["<sessionID>", ...]
  },
  "traceStats": { "turns": n, "pages": n, "faults": n, "residentTokens": n }
}
```

**Environmental version keys:** opencode reads `CTXVM_OPENCODE_VERSION` into `harnessVersion`
(recipe export; the m5 `opencodeVersion: null` miss was this var's absence — fixed by the
erratum); hermes reads `CTXVM_HERMES_VERSION` the same way. `pluginVersion`: opencode reads
its own `packages/opencode/package.json` via `import.meta.url` (best-effort → null); hermes
keeps its `PLUGIN_VERSION` constant (`0.2.0` as landed). `capturedAt` is normalized to a
`Z`-suffixed RFC-3339 string on both sides (hermes previously emitted `+00:00` — cosmetic
but exactly-same means exactly-same).

**Mapping table (single source of truth for the hermes mirror):**

| canonical key | hermes source counter | opencode source counter |
|---|---|---|
| `hookStats.contexts` | `pre_llm_calls` | `contexts` |
| `hookStats.before` | `pre_tool_calls` | `before` |
| `hookStats.after` | `post_tool_calls` | `after` |
| `hookStats.completed` / `.errored` | `completed` / `errored` | `completed` / `errored` |
| `hookStats.extraHookStats` | `{session_starts, session_ends, skipped_untraced}` | `{}` |
| `hookStats.sessions` | session id list | session id list |

Both writers in `packages/hermes/live/__init__.py` (`_write_trace`, `_flush_traces`) build the
sidecar through one module-level helper `_canon_meta(session_id, hook_stats, trace_stats)`;
opencode's cleanup in `packages/opencode/live/ctxvm.ts` emits exactly this shape. The parity
tests in both packages assert the exact key list above against live emissions.

## 4. Enforcement

- `packages/opencode/test/meta-parity.test.ts` — asserts (a) the §2 signature table on a live
  mini-run, (b) the §3 sidecar key list (via the live-adapter flush path). **Fails loudly on
  any drift.**
- `packages/hermes/test/test_plugin.py` — `CanonicalSidecarParity`: the same §2 table through
  the hermes tracer + the §3 `_canon_meta` shape/mapping assertions.
- `tools/run-ci.sh` gates both suites; the counts in the gate-2/2b log line are kept current
  by the same card that adds the tests (mirror discipline with `ci.yml`).
- `tools/verify-capture.sh` (§5) verifies ANY capture end-to-end — the same tool proves the
  same wire format for both harnesses on demand.
- `packages/opencode/test/fixtures/uc2-diagnose-golden.json` + golden tests on BOTH sides
  (hermes `UC2GoldenParityTests` in `test_uc2_forensics.py` and the golden test in
  `packages/opencode/test/uc2-forensics.test.ts`) — `UC2Forensics.diagnose` verdicts pinned
  on real corpus anchors; either implementation drifting from the shared fixture fails
  loudly. Requires the release binaries; both gates build them (`run-ci.sh` gate 1b,
  Actions `ts` job). (UC2-MIRROR, 2026-10-25.)

## 5. Shared capture kit — the same tools for both harnesses

| Tool | What it does | Both harnesses? |
|---|---|---|
| `tools/verify-capture.sh <trace.jsonl>` | replay (divergences/violations) → profile → export round-trip → metrics KPIs → one-out policy sim → sidecar cat | yes — operates on the trace file only; it is the standard gate before promoting any capture |
| `tools/snapshot-capture.sh <dir> <name> <era-label>` | copies `<dir>/<name>.jsonl{,.meta.json}` to era files **immediately after a flush** (flushes overwrite one name — era snapshots are the m5 lesson) | yes |
| hooks-witness | one timestamped line per hook fire and flush attempt, appended to `<CTXVM_TRACE_DIR>/hooks-witness.log` — a missing flush becomes diagnosable | yes — opencode since the m5 instrumentation; hermes from KIT-1 |
| `tools/uc2-forensics.sh diagnose <trace.jsonl> <fault-turn>` | UC2 verdict decomposition (replay fact gate + profile evidence) via the `@ctxvm/opencode` mirror module `src/uc2-forensics.ts` — the same verdicts hermes ships in-harness behind `/ctxvm-forensics` | yes — the opencode v2.1.2 plugin surface has no command hook (3 hooks only), so this kit entry IS the opencode lane's user-facing UC2 surface |
| `packages/opencode/test/fixtures/uc2-diagnose-golden.json` | golden `diagnose()` outputs over real corpus anchors, generated by the hermes reference — pinned by tests on BOTH sides in the same card (§4 enforcement) | yes — the fixture is the parity pin for the UC2 verdict logic |
| flush trigger | **opencode:** graceful TUI exit (SIGTERM) → plugin cleanup (TUI holds the plugin; `opencode serve --service` carries no capture env; recorded in the live README erratum) · **hermes:** `/ctxvm-trace stop` or session end (`on_session_end` flushes so the gateway staying up does not lose the capture) | same contract, per-harness trigger |

Re-install note: the hermes plugin lives as a copy under `$HERMES_HOME/plugins/`; after
adapter changes, re-install the updated copy (T17 recipe; `hermes plugins doctor --ci` to
verify registration).

## 6. DoD rule for every future card that touches a plugin's wire behavior

Add the capability (both packages), update §2/§3 tables, extend BOTH parity tests, run
`tools/run-ci.sh` ALL GATES GREEN, and re-install the hermes copy if its adapter changed.
One card owns one change — never patch one harness's format without the other in the same
commit, so byte-parity never regress silently.
