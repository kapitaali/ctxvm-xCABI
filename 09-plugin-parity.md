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
| `session.open` | `agentId, budgetTokens, model, provider, schemaVersion, tokenizerId, type` (+ optional `environmentId` R8) |
| `page.declare` | `page, type` (+ `turn` R5, + optional `toolEffect` R7) |
| `page.fault` | `page, source, turn, type` |
| `page.render` | `mode, page, turn, type` |
| `turn.render` | `evictedTokens, headroom, residentTokens, turn, type` |
| `call.meta` | `cacheEstimate, provider, turn, type` |

**RFC-0.1 boundary (2026-10-31, RR-RFC01E1):** from the emitter-version-switch card on,
new emissions carry `schemaVersion: "0.1"` on `session.open` (RFC-0.1 §R0 — the version
negotiation), so the `session.open` row above now includes it. The shipped drops this
table was audited from (`corpus/m1`–`m5`) stay v0 era: frozen goldens, never
regenerated. Both parity tests pin the new key set; drift lands in the same card on
BOTH sides.
**RFC-0.1 §R8 note (2026-11-01, W14):** `session.open` gains an OPTIONAL `environmentId`
(`env-` + 12 hex). opencode and ai-sdk derive it from the project directory (git remote first,
worktree path otherwise); the hermes gateway does **not** disclose the session's workspace — its cwd
is the gateway's — so that lane emits it only from an explicit `CTXVM_ENVIRONMENT_ID`, and omits the
key otherwise. A malformed value is dropped at the boundary, never coerced: no path may reach a
trace. Fixtures that pin bytes pin a fixed id (`env-000000000000`).
**RFC-0.1 §R7 note (2026-11-01, W15):** `page.declare` gains an OPTIONAL `toolEffect`
(`READ_ONLY` | `MUTATING`) between `latencyMs` and `ts`, tagged at tool REGISTRATION
by the adapter and never inferred from model text or result content. Every adapter
tags every tool_result it declares, so both lanes emit it; the key stays absent when
a direct tracer call supplies no class, and the parity tests treat it as an optional
key whose VALUE must be one of the two wire strings. `ts` remains last.
**RFC-0.1 §R3 note (2026-10-31, RR-RFC01E2/W2b):** the `@ctxvm/node` reference tracer
gains `noteUsage` — the ai-sdk lane additionally emits optional
`call.meta.providerUsage` AFTER `cacheEstimate` (canonical rust-writer order) when the
stream's `finish-step` carries the provider receipt. The two KIT ports emit it only
when their hook surfaces gain a usage source: opencode's terrain is
`session.context`/`tool.execute.before`/`tool.execute.after` (no usage facts —
audited by the recorded driver fixture) and hermes's is tool hooks + `pre_llm_call`
history (no usage facts). Per-lane omission (`providerUsage` optional in the v0.1
schema) keeps the key signatures above valid for both ports.

**W8 note (2026-11-06, RR-W8IMPL-20261106):** the "hermes has no usage source" clause
above is closed. Plugin 0.10.0 registers `post_api_request` and the lane now emits
optional `call.meta.providerUsage` on the canonical shape: `inputTokens` is the UNCACHED
input (prompt minus both cache buckets, clamped at zero), `outputTokens` and
`cachedInputTokens` ride as reported, whole numbers only, absence never coerced to zero.
Order is the rust writer's (`latencyMs`, `providerUsage`, `ts`). A receipt that arrives
while no pending meta exists is held and attaches to the next created meta (the node
`orphanUsage` law); a second receipt on one meta overwrites the first (last write wins,
because the last response describes what was finally sent). `cacheEstimate.
providerReported` stays `false` by owner ruling (option A, 2026-11-06): the estimate
keeps page-table semantics and the receipt is a separate fact — the est-to-provider
upgrade question stays open (RR-W2B1 §6). The opencode lane still emits no usage and its
table is untouched: hermes key-signature equality is a per-port assertion, which the
opencode mirror's own comment states.

**RFC-0.1 §R4 note (2026-10-31, RR-R4TS1 + RR-R4TS2):** per-event `ts` — RFC 3339 UTC
ms, riding LAST on every line, default ON with the per-trace opt-out `CTXVM_TRACE_TS=0`
(D9; §R4 keeps the field optional). LANDED on ALL FOUR lanes: node + its opencode/ai-sdk
inheritors in RR-R4TS1, the hermes python port in RR-R4TS2 (both `_push` stamped, tail
stamps minted at the turn's render snapshot time so repeated `finish()` stays
byte-idempotent, byte-compare pins run under the named opt-out). The audit-table corpus
above (m1–m5, plus every fixtured drop) is FROZEN pre-§R4 goldens — the "identical in all
three drops" claim describes those captured bytes and stays true. Both ports' parity
tables gained `ts` in their own cards; the one-card-both-emitters rule (§6) parses as
"one card owns one ADOPTION step" — the schema itself landed complete with RFC-0.1. The
opencode table's ts row comment carries the lane pointers.

**RFC-0.1 §R5 + §R4 note (2026-10-31, RR-R5TURN):** `page.declare` now carries `turn`
(§R5 — the tracer's counter AT DECLARATION TIME; pre-first-render declarations stamp as
0, the RFC-0 §5 convention `page.fault` already uses) and accepts `latencyMs` (§R4's
`page.declare` half) as an ACCEPTED-BUT-UNEMITTED slot. Wire order: `type, page, turn,
latencyMs?, ts` — `turn` always, `latencyMs` only when a caller supplied a whole number
of milliseconds ≥ 0 (strict intake: absent/invalid ⇒ omitted, never null, never float;
`bool` excluded on the python side because bool IS an int there). Reveal bookkeeping is
unchanged — a page still renders full at the boundary AFTER its declaration, so a
declaration turn and its render turn can differ by more than one.
**Why latencyMs is unemitted:** neither KIT terrain carries a timing fact — opencode's
hooks are `session.context`/`tool.execute.before`/`tool.execute.after`, hermes's are tool
pairs + `pre_llm_call` history (audited in RR-W2B1 §1). The key signatures below stay
TRUE to the wire: both parity tables gained `turn` and NOT `latencyMs` (the
providerUsage precedent — an optional field enters the table when a fixture exercises
it). Both emitters landed in ONE card, which is this file's own §6 rule shape ("both
emitters, the validator, this table, and both parity tests in the same commit").

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
  "traceStats": { "turns": n, "pages": n, "faults": n, "residentTokens": n },
  "resumeFrom": { "snapshot": "<snapshot dir as passed>", "snapshotDigest": "sha256:…",
                  "snapTurn": N, "turn": N, "artifacts": ["<sorted artifact paths>"] } | null | {}
}
```

**Environmental version keys:** opencode reads `CTXVM_OPENCODE_VERSION` into `harnessVersion`
(recipe export; the m5 `opencodeVersion: null` miss was this var's absence — fixed by the
erratum); hermes reads `CTXVM_HERMES_VERSION` the same way. `pluginVersion`: opencode reads
its own `packages/opencode/package.json` via `import.meta.url` (best-effort → null); hermes
keeps its `PLUGIN_VERSION` constant (`0.2.0` as landed). `capturedAt` is normalized to a
`Z`-suffixed RFC-3339 string on both sides (hermes previously emitted `+00:00` — cosmetic
but exactly-same means exactly-same).

**B3 extension (UC1 handoff resume, 2026-10-25):** the canonical sidecar carries a trailing
`resumeFrom` key — both `_canon_meta` and the opencode cleanup stamp it LAST. Three states
(mirroring the hermes law): `null` when the session is not resuming (the key still appears —
the canonical shape is unconditional); the evidence dict
`{snapshot, snapshotDigest, snapTurn, turn, artifacts}` when a `CTXVM_RESUME_FROM` boot check
verified the paused snapshot; `{}` when the boot check ran and failed early (missing dir /
no zst / unparseable turn — never `null`; the empty object means "resumption attempted, not
trusted"). Deviation from design §3's slim `{snapshot, snapshotDigest, snapTurn}` trio: the
landed reference (`8871dda`) stores the whole verify evidence dict — parity wins (the TS
mirror follows the hermes reference byte-for-byte; delta disclosed in
RR-UC1RESUME-MIRROR-20261025).

**B3 v-next extension (UC1-VERIFY-CHECKS, 2026-10-26, both sides in one card):**
the boot check implements design §3 (1)(3)(4) in-module; the evidence dict gains
`manifest` (`{sliceTurn}`), `projection` (`{turn, slots}` from `page-table-N.json`
— the §3(4) fidelity reference, also rendered as a witness line at both call
sites), and `diff` (`{source, relation}` law-aware per the m6 ruling: era copy
`*-turn-N.jsonl` vs the package slice requires `identical` and a MISMATCH
unverifies; the manifest `derivedFrom` diff is diagnostic only — its divergence
at `turn.render` residency rows is the knowledge-stateful lawful shape; no
source on disk → `null`). New failure reasons (`checksum mismatch for <name>`,
`checksummed artifact missing: <name>`, `checksums.sha256 missing: <dir>`,
`manifest...`, `era diff...`, `page-table...`) are byte-identical on both sides
and pinned by 11 mirrored tests each. Success reason/exit/digest unchanged.
Since the sidecar law stores the whole evidence dict, these keys flow through
`resumeFrom` as nested opt-in fields — the sidecar CANON top-level shape is
untouched (m6-era sidecars on disk stay valid as captured).

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

### 3.1 W17 coverage manifest — `<file>.coverage.json` (the third pair member)

A coverage manifest is a **sidecar**, not a tenth event. The sealed nine-verb envelope is
untouched. It is written at **full flush only** — never at a write-through partial, because a
pruned partial would leave coverage describing bytes that no longer exist — and it describes the
run's instrumentation rather than reporting a harness observation.

Shape v0.1 (all three lanes write exactly these keys):

| key | content | how the checker proves it |
|---|---|---|
| `xcabiCoverage` | `"0.1"` | literal |
| `traceFile` | basename of the trace it covers | equals the trace path's basename |
| `traceDigest` | sha256 hex over the trace bytes | recomputed from the file on disk |
| `session` | `sessionID, environmentId, model, provider` | session facts read FROM the trace's own `session.open` row, so they are byte-true by construction; `sessionID` is a pairing fact and is not byte-verifiable |
| `toolTable` | `readOnlyRegistered: [...], default: "MUTATING"` | registration law on stamps: a registered READ_ONLY tool never carries MUTATING, an unregistered name never carries READ_ONLY; `default` other than MUTATING is a violation |
| `instrumentation` | `ts, toolEffect, identifierScan` | real lane toggles, not decoration |
| `plugin` | `version, harness, harnessVersion` | present and typed |
| `captures` | `turns, pages, declares, declaresByClass, faults, faultsBySource` | exact equality with the events; all four fault sources always present |

**The checker is the law.** `tools/coverage_check.py` is stdlib-only and takes the trace and the
manifest as arguments; it exits 0 when consistent, 1 on each violated law (one printed line each)
and 2 on usage, IO or JSON error. It is invoked through a subprocess in every lane's tests, so the
lanes cannot drift from the checker by importing it.

Lane rows:

| lane | file written by | `toolTable` source | `instrumentation` |
|---|---|---|---|
| hermes (`packages/hermes/live/__init__.py`) | `_flush_traces`, after the meta sidecar | `_HERMES_READ_ONLY_TOOLS` (`read_file, search_files` + `CTXVM_READONLY_TOOLS`) | all three true (no per-run toggles) |
| opencode (`packages/opencode/live/ctxvm.ts`) | `flushTraces`, after `writeMeta` | `READ_ONLY` exported from `src/plugin.ts` (load-time snapshot; the shim imports the same binding, so stamps and manifest cannot desync) | `ts` re-read at flush from `CTXVM_TRACE_TS`, mirroring the tracer's per-trace opt-out |
| ai-sdk (`packages/ai-sdk/src/flush.ts`) | `writeCapture`, after the meta write | `READ_ONLY_TOOLS` exported from `src/tap.ts` | `ts` re-read at flush, same rule as opencode |

**Prune and era law.** Retention treats the coverage file as the third member of the pair: `_prune_traces`
deletes `<file>.coverage.json` with its capture and never orphans coverage. The UC1 era-copy lists
(`packages/hermes/src/uc1_handoff.py`, `packages/opencode/src/uc1-handoff.ts`) include `coverage.json`,
so a handoff package carries the manifest next to the bytes it describes.

**What the checker caught.** Building the hermes lane against real live bytes exposed a live bug: the
stamp site read `kwargs.get("tool")` while live payloads carry `tool_name` (the hook table in
`packages/hermes/HOOKS.md`), so every live hermes declare had been classified MUTATING — 447 witness
rows read `tool=None` on plugin 0.8.0 bytes. Both the post stamp and the pre witness now use
`kwargs.get("tool") or kwargs.get("tool_name")`.

### 3.2 W21 collision law — a reused trace name never replaces another session's bytes

A post-restart capture reused the default name and the write-through replaced the 13:0x evidence
under identical filenames (`RR-LIVE-20261104`). The rule now, identical in all three lanes:

- Before writing, read `<file>.meta.json`. If it exists and its `sessionID` is **different** from the
  session being flushed, write `<file>-<sha256(sessionID)[:8]>.jsonl` (and the same suffixed meta and
  coverage sidecars) instead.
- If the sidecar is absent, unreadable, or names the same session, keep `<file>`. A session therefore
  keeps its own name across repeated flushes, and a mid-session flush still supersedes its own bytes.
- The coverage manifest's `traceFile` and the retention `keep` argument both use the RESOLVED name.
  With a suffix, passing the base name would leave the file just written unprotected by the prune
  guard, so the two must move together.

The rule is per flush, not per process: no session-keyed cache is kept, because the meta sidecar is
the authority for who owns a name and a cache could outlive a directory cleanup.

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
- `packages/opencode/src/uc1-handoff.ts` (+ the golden fixture
  `packages/opencode/test/fixtures/uc1-resume-golden.json`) — `src/uc1-handoff.ts` is the
  line-for-lines TS mirror of the hermes `UC1Handoff` — resume() AND (UC1-PAUSE-MIRROR,
  2026-10-25) the pause() beat, consolidated under the §1.2 file-naming law
  (superseding the earlier resume-only `uc1-resume.ts`). Same reason strings, turn
  parsing, digest algorithm, `{turn, snapshot}` failure evidence; the pause argv law
  was FIXED BOTH SIDES the same card (the reference assembled a bare positional turn —
  `[trace, str(turn), --output DIR, --odps]` — which the real binary rejects: `unexpected
  second positional '2'`; the documented `--turn N` flag form is now used on both).
  wired behind `CTXVM_RESUME_FROM` in `live/ctxvm.ts` (witness lines byte-match the hermes
  register() block, Python-style `True`/`False` rendering included). Golden tests on BOTH
  sides (hermes `UC1ResumeGoldenParityTests` in `test_uc1_handoff.py`; TS `uc1-resume.test.ts`)
  deep-equal the committed fixture — generated by the hermes reference on
  `corpus/m1/session-healthy.jsonl` @turn 0 via the binding. Fixture discipline: cwd=repo
  root + RELATIVE trace argv (manifest/llms embed the argv string; a relative argv keeps the
  artifact bytes host-independent). Requires the release binaries AND the `zstd` CLI — both
  gates build the binaries, `zstd` ships on dev and CI hosts. Hermes side additionally lands
  the design §3 witness chain (`UC1ResumeWitnessTests`: m2-echo @2 → diff `a_extends_b` →
  replay `--turn 2` exit 0 → page-table turn stamped). (UC1-RESUME-MIRROR, 2026-10-25.
  Superseded file name in this bullet's test listing: the TS tests now live in
  `test/uc1-handoff.test.ts` — same file law as the module above.)

- `@ctxvm/node` `finish()` idempotency (UC1-TRIGGER, 2026-10-26) — T17.7 parity mirror of
  the hermes `plugin.py finish()` docstring law: the tail (turn.render × (turn+1) +
  call.meta) is computed per call and NEVER appended to the live event stream, so
  repeated flushes (mid-session handoff trigger, session end, dispose) produce the same
  JSONL and lifecycle recorded AFTER a first flush joins the next transcript exactly
  once; `pendingMeta` is never cleared (re-rendered each call — hermes law). Pinned by
  tests BOTH sides in the same card (hermes `TracerTests.test_finish_idempotent_tail_
  regenerates` — the reference docstring had never been test-enforced — mirror-paired
  with the node tracer test asserting the same three laws).

- `live/ctxvm.ts` mid-session turn-shaped handoff trigger (UC1-TRIGGER, 2026-10-26) —
  design §2 trigger law for opencode: with `CTXVM_HANDOFF_TURN=N` (positive int; the
  `"0"`/unset value stays the flush-time package path via the same env law
  `int(…,"0") or None`), the context hook fires ONCE per session right after the turn-N
  boundary (probe = idempotent `finish()` — events untouched), then flushes through the
  SAME naming law → era copy → packages with `--turn N` (uc1Pause re-reads the env —
  one turn law, single truth); tracing CONTINUES unless `CTXVM_HANDOFF_STOP=1`, which
  disposes the hook registrations (pause is not teardown by default). Arm-but-degrade: a
  junk env value is a loud witness line and capture continues (the module's mirrored
  loud raise is kept inside the module; the hermes reference crashes its slash command
  instead — their lane). At cleanup the flush-time package runs only as the FALLBACK
  (nothing fired → still exported with the env turn; something fired → no second
  package).

## 5. Shared capture kit — the same tools for both harnesses

| Tool | What it does | Both harnesses? |
|---|---|---|
| `tools/verify-capture.sh <trace.jsonl>` | replay (divergences/violations) → profile → export round-trip → metrics KPIs → one-out policy sim → sidecar cat | yes — operates on the trace file only; it is the standard gate before promoting any capture |
| `tools/snapshot-capture.sh <dir> <name> <era-label>` | copies `<dir>/<name>.jsonl{,.meta.json}` to era files **immediately after a flush** (flushes overwrite one name — era snapshots are the m5 lesson) | yes |
| hooks-witness | one timestamped line per hook fire and flush attempt, appended to `<CTXVM_TRACE_DIR>/hooks-witness.log` — a missing flush becomes diagnosable | yes — opencode since the m5 instrumentation; hermes from KIT-1 |
| `tools/uc2-forensics.sh diagnose <trace.jsonl> <fault-turn>` | UC2 verdict decomposition (replay fact gate + profile evidence) via the `@ctxvm/opencode` mirror module `src/uc2-forensics.ts` — the same verdicts hermes ships in-harness behind `/ctxvm-forensics` | yes — the opencode v2.1.2 plugin surface has no command hook (3 hooks only), so this kit entry IS the opencode lane's user-facing UC2 surface |
| `packages/opencode/test/fixtures/uc2-diagnose-golden.json` | golden `diagnose()` outputs over real corpus anchors, generated by the hermes reference — pinned by tests on BOTH sides in the same card (§4 enforcement) | yes — the fixture is the parity pin for the UC2 verdict logic |
| `packages/opencode/test/fixtures/uc1-resume-golden.json` | golden UC1 resume verification (digest/turn/reason/artifact set) over `corpus/m1/session-healthy.jsonl` @turn 0, generated by the hermes reference — pinned by tests on BOTH sides in the same card (§4 enforcement) | yes — `src/uc1-handoff.ts` (opencode) and hermes `UC1Handoff.resume()` deep-equal the same fixture |
| UC1 pause mirror (`src/uc1-handoff.ts`) | `UC1Handoff.pause()` mirror: era-snapshot of the flushed `.jsonl{,.meta.json}` with `cp -n` semantics, export `--turn N --output <dir>/handoff/ --odps`, argv law fixed both sides; the packaged tree is byte-compared against a direct export CLI run in tests (design §6 B2 TODO closed) | yes — hermes module + `/ctxvm-handoff` slash command; opencode flush-time env path |
| `CTXVM_HANDOFF_DIR[_TURN]` flush-time handoff (opencode) | with the handoff envelope set, the adapter cleanup packages the just-flushed capture (design §2 "unset turn = package at flush"); the witness line mirrors the hermes `/ctxvm-handoff` rendering (`exit_code/verified/divergences`, Python-cased booleans) | opencode half of design §2 (hermes trigger is the slash command); mid-session turn-shaped triggers LANDED in UC1-TRIGGER (2026-10-26) with the T17.7 `@ctxvm/node` idempotency — the cleanup package is then a fallback only (see §4) |
| `CTXVM_RESUME_FROM` boot check | resume-time verify: decompress + replay counterproof + checksums-provenance digest → loud witness lines, tracer continues UNVERIFIED on failure; stamps the §3 `resumeFrom` sidecar key | yes — hermes `register()` (`live/__init__.py`) and opencode `setup()` (`live/ctxvm.ts`); opencode's check is capture-gated (no capture dir → no check) |
| flush trigger | **opencode:** graceful TUI exit (SIGTERM) → plugin cleanup (TUI holds the plugin; `opencode serve --service` carries no capture env; recorded in the live README erratum) · **hermes:** `/ctxvm-trace stop` or session end (`on_session_end` flushes so the gateway staying up does not lose the capture) | same contract, per-harness trigger |

### 5.1 Trace-dir contract — ON by default, `~` expanded, honest stop (2026-11-01)

Three defects made a working plugin look broken on a real machine: a `~` in
`/ctxvm-trace start ~/…` was not expanded (the capture landed in a literal `~` directory under
the process cwd), capture was OFF unless `CTXVM_TRACE_DIR` was set (so an unconfigured harness
recorded nothing), and `stop` printed "traces flushed" whether or not a file was written. The
contract is now explicit and identical in `packages/hermes/live/__init__.py`
(`_resolve_trace_dir`) and `packages/opencode/live/ctxvm.ts` (`resolveTraceDir`):

| Input | Result |
|---|---|
| `CTXVM_TRACE=0` / `off` / `false` / `no` | tracing disabled (documented opt-out) |
| dir unset | `${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces` — **capture is ON** |
| dir empty string | disabled (explicit opt-out) |
| dir with `~` or `$VAR` | expanded, then made absolute (`resolve`) |
| any other dir | made absolute |

Directories are created `0700` — session content lives inside. `/ctxvm-trace status` reports
the resolved absolute dir **and its source** (slash command / env / default / disabled), and
`/ctxvm-trace stop` reports `N trace(s) flushed` or explicitly `0 traces written — no events
were captured between start and stop`, which is the sentence that would have saved the
2026-11-01 diagnosis.

**Static prefix (`turn.render.prefix`, W13).** Hermes exposes `pre_api_request`, whose payload
carries the counters the host already paid to compute: `tool_count`, `message_count`,
`request_char_count`, `system_prompt`, and its own `approx_input_tokens`. The adapter records them
on the turn's render row. The OpenCode adapter cannot see the request, so it emits
`{"source": "unknown"}` — a stated absence, never a zero. Field parity is enforced by
`packages/opencode/test/meta-parity.test.ts`; the schema rejects a prefix with no `source`, an
invented source, and a negative count.

**Write-through and retention (same card).** Default-ON carries two obligations: a crash must cost
at most a bounded amount of work, and the directory must not grow without bound.

| Env | Default | Behaviour |
|---|---|---|
| `CTXVM_TRACE_WRITETHROUGH` | `1` (on) | persist `<file>.partial.jsonl` + `.partial.meta.json` while the session runs |
| `CTXVM_TRACE_WRITETHROUGH_EVERY` | `10` | cadence: hermes counts tracer **events**, opencode counts **hook fires** (its plugin hides the event list behind `finishAll()`) |
| `CTXVM_TRACE_RETAIN_MAX` | `200` | maximum complete captures kept in the dir |
| `CTXVM_TRACE_RETAIN_DAYS` | `30` | age limit for complete captures |
| `CTXVM_TRACE_RETAIN_BYTES` | `536870912` (512 MiB) | byte budget for complete captures (count alone cannot bound size) |

A complete flush deletes the partial before writing the final pair, so a partial can never be
mistaken for a capture; retention prunes oldest-first and **never** deletes the file just written.
Both are witnessed (`write-through events=… (partial)`, `retention deleted=… files …`), so the
directory's history is as diagnosable as its contents.

Session identity (`model`, `provider` in `session.open` and `.meta.json`) now comes from the
host payload when the host supplies it (`identity_from_payload`: `model` / `model_name` /
`model_id`, `provider` / `provider_name`), falling back to `CTXVM_MODEL` / `CTXVM_PROVIDER`.
A captured trace therefore no longer reads `unknown/unknown` on a harness that knows its own
model.

**Priority chain (0.4.1): payload > plugin settings > env > `unknown`.** The middle layer is
the host-owned plugin settings subtree (hermes
`plugins.entries.<id>.settings.identity.model` / `.identity.provider`, read as the single
mapping `ctx.get_config("identity")` at register() — before any hook fires; a bare
`settings.provider` key is also accepted).

**Reserved-root erratum (2026-11-06, RR-IDENTITY-20261106):** the 0.4.1 text named
`settings.model` / `.provider` read per key. The host refuses a plugin settings key whose first
segment is `model`, `plugins`, `security` or `settings` (`hermes_cli/plugins_state.py:17`), so
`get_config("model")` raised — and because the whole loop sat inside one `try`, the raise on
`model` aborted the lookup before `provider` was ever asked for. The documented remedy for
`provider: unknown` was therefore dead on every release since 0.4.1, silently. The reader now
takes the non-reserved `identity` mapping first and then only the bare `provider` key, because
`model` is refused on every host version seen and asking for it can only log the rejection warning on
every load — the noise that hid the defect. Model comes from the `identity` mapping or not at all. It exists because hermes ~v0.22.5 does not send `provider` at
tracer-creation time: the turn-prep `pre_llm_call` payload carries `model`/`platform` only
(`packages/hermes/HOOKS.md` §1, source-verified) and `provider` only reaches the
`pre_api_request`/`post_api_request` payloads, after the tracer already exists. A default-ON
gateway with no `CTXVM_*` env can therefore complete its identity from its own declared
settings without the owner reaching for an env var. (Upstream ask, preferred long-term: add
`provider` to the `pre_llm_call` payload.)

**Identity immutability law.** Identity is stamped once at tracer creation — it rides
`session.open` and every `call.meta` on the wire, and write-through persists each event
immediately, so a later "provider fix" on disk would produce a partial-file/final divergence.
The adapters therefore never backfill identity: a session opened before the host revealed its
provider keeps `"unknown"`. Lateness is observed, not erased — future identity facts ride
the per-turn `call.meta` chain the same way usage does.

Re-install note: the hermes plugin lives as a copy under `$HERMES_HOME/plugins/`; after
adapter changes, re-install the updated copy (T17 recipe; `hermes plugins doctor --ci` to
verify registration).

### 5.4 Slash-command surface — discoverable, with honest defaults (2026-11-03)

Three commands are always registered; two more appear only when their feature is enabled:

| Command | Behaviour |
|---|---|
| `/ctxvm-start [dir] [name]` | start capture. **No arguments is the normal case**: the dir is `CTXVM_TRACE_DIR` if set, else `${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces` (0700), and the name is `CTXVM_TRACE_NAME` if set, else `<session-id>` |
| `/ctxvm-trace start [dir] [name] \| stop \| status` | the same start, plus a truthful stop (reports `0 traces written` when nothing was captured) and a status that names the resolved dir **and its source** |
| `/ctxvm-help [command\|environment]` | no argument lists every command; a command prints usage, what it changes and the defaults; `environment` prints every `CTXVM_*` variable this plugin reads with its current value and its fallback |
| `/ctxvm-forensics ...` | only with `CTXVM_FEATURES=forensics`: replay, profile, diff, export, diagnose |
| `/ctxvm-handoff [turn]`, `/ctxvm-resume <dir>` | only with `CTXVM_FEATURES=handoff`: pause with a packaged snapshot, and verified boot from one |

Source labelling matters as much as the value: a dir that came from an argument says `slash command`,
one from the environment says `env CTXVM_TRACE_DIR`, and one that fell through says `start (defaults)`.
An operator who cannot tell those apart cannot debug a capture that went to the wrong place.

`plugin.yaml` and `PLUGIN_VERSION` are asserted equal by a test, because a version bump that misses one
file is a silent no-op — and `plugin.yaml` is what the host displays.

### 5.3 Environment identity (W14, 2026-11-01)

| Lane | Source | Absent when |
|---|---|---|
| opencode | `deriveEnvironmentId(process.cwd())` — remote first, worktree path otherwise | never (the plugin runs in the project) |
| ai-sdk | same, unless the caller passes one | never (same reason) |
| hermes | `ctx.session_cwd()` — the host's own recorded session workspace (`hermes_cli/plugins.py:605`, backed by `hermes_cli/plugin_session.py`, whose docstring says it is "never the gateway process's own cwd"). An explicit `CTXVM_ENVIRONMENT_ID` still wins. | the host records no workspace for the session |

Hermes was the exception until 2026-11-04 and no longer is. The plugin still must not hash
`os.getcwd()`: it executes inside the gateway process, whose working directory is the install root and
is shared by every session. But the host does expose the session's own recorded workspace to a plugin
handle — `ctx.session_cwd()`, documented as "never the gateway process's own cwd" — so the hermes lane
derives the id from that, per session, and only reports absence when the host records none.

What the host does **not** put in any hook payload is a workspace path (`on_session_start`,
`pre_tool_call`, `post_tool_call`, `pre_llm_call`, `pre_api_request`, `on_session_end` were all
audited). The value comes from the plugin handle, not the payload, which is why the adapter stamps it
onto the payload itself before the tracer sees it.

Both derivations must agree: `_normalize_remote` in the hermes adapter and `normalizeRemote` in the
node tracer are the same rule (drop scheme, credentials, port and `.git`; lowercase). Checked:
`/home/theb/Documents/ctxvm` → `env-2b4652ae9d98` from both.

### 5.2 Side-effect classification — the registration table (W15, 2026-11-01)

The class is a property of the tool NAME at registration. It is never inferred from arguments,
model text or result content, two calls to one name share one class, and **an unregistered name is
`MUTATING`** — an unknown tool is assumed to have written something.

| Adapter | Table | Source of the default |
|---|---|---|
| hermes | `{read_file, search_files}` | the host's own read/search bucket (`model_tools.py:615`, `_READ_SEARCH_TOOLS` in the install) |
| opencode | `{read, glob, grep, list, webfetch}` | that harness's documented read tools |
| ai-sdk | same as opencode | the middleware lane sees names only |

`CTXVM_READONLY_TOOLS` (comma-separated) **extends** the table for any lane. It is never required:
classification works with zero environment set, because default-on with no `CTXVM_*` is the property
the capture contract already established. An extension entry is an owner statement, not an inference.

Consequence to state rather than hide: the hermes table covers two tools out of a wide catalog, so a
real session reads mostly `MUTATING`. That is the fail-safe working, and until the host publishes a
broader read bucket the field is coarse. Audit only — there is no write-ahead log, no dry-run, and
nothing here prevents a mutating call or makes replaying one safe.

## 6. DoD rule for every future card that touches a plugin's wire behavior

Add the capability (both packages), update §2/§3 tables, extend BOTH parity tests, run
`tools/run-ci.sh` ALL GATES GREEN, and re-install the hermes copy if its adapter changed.
One card owns one change — never patch one harness's format without the other in the same
commit, so byte-parity never regress silently.
