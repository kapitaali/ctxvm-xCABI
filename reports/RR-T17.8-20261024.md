# RR-T17.8-20261024 — Hermes live capture fixed; corpus/m4 (LIVE) dropped

**Card:** T17.7 / T17.8 (ctxvm UC1 v0 — Hermes plugin for within-harness session capture)
**Date:** 2026-10-24
**Plugin version:** 0.2.0
**Commits:** `27822e6` (T17.7 fix), this report + corpus/m4 (T17.8)

## 1. What was broken

Three live captures produced trace files with `page.declare: 0` while `hookStats`
reported 258 `post_tool_calls` and 235 `completed`. That combination was read as
"the tracer drops events". It was not.

The hook handlers increment counters **before** checking whether a tracer
exists:

```python
stats["post_tool_calls"] += 1      # always
vm = _ensure_plugin()              # None while tracing is disabled
if vm is not None:
    vm.on_post_tool_call(kwargs)   # only here would a page be declared
```

`hookStats` therefore counts **hook fires**, not recorded events. The recorded
window contained no successful `post_tool_call` handling, so the flush wrote a
tracer that had only seen `session.open`.

Two conditions produced that state:

1. Tracing was enabled after the tool calls. `/ctxvm-trace start` is not
   retroactive.
2. The installed plugin was an older build (no `_state()`, no `pluginVersion`,
   module-level `_trace_dir`) than the repository, and a running Hermes process
   keeps the module it imported at startup.

## 2. Defects fixed (T17.7, commit `27822e6`)

| # | Defect | Consequence | Fix |
|---|--------|-------------|-----|
| 1 | `payload.get("tool")` | ref built from `None`; Hermes sends `tool_name` | `tool or tool_name` in both tool hooks |
| 2 | `result.get("content")` | `AttributeError` on plain-string results, swallowed by the fail-open dispatcher → 0 pages | `extract_page_body()` handles str/dict/list/None/other |
| 3 | module-level `_plugin` / `_trace_dir` | reset on re-import, discarding trace dir and pages | state on `sys._ctxvm_tracer_state` |
| 4 | flush by `session_id` lookup | end-hook id does not match the tool-call id | `_flush_traces()` flushes all tracers |
| 5 | `finish()` appended its tail to `_events` | repeated flushes duplicated `turn.render`/`call.meta` | tail computed per call, never appended (idempotent) |
| 6 | no visibility into skipped work | "pages: 0" was ambiguous | `skipped_untraced` counter + richer `/ctxvm-trace status` |

`/ctxvm-trace status` now reports the running build and live tracer state:

```
ctxvm-trace: enabled=True, dir=/tmp/ctxvm-capture, version=0.2.0,
  register_calls=1, tracers=[local-7ebc530650:events=14,pages=9]
```

A status line without `version=` means the process is executing an older module.

## 3. Verification (three layers)

### 3.1 Unit

`packages/hermes/test/test_plugin.py` — 21/21, including live-shape cases
(`tool_name`, `status="ok"`, plain-string result) and a `tool_name`-only variant.

### 3.2 Isolated end-to-end through the installed plugin path

Case B (tracing enabled before any call):

```
types: session.open, page.declare ×3, page.render ×3, turn.render, call.meta
traceStats: turns 1, pages 3, faults 0, residentTokens 45
skipped_untraced: 0
```

Case A (two calls made with tracing off, then enabled):

```
skipped_untraced: 5
traceStats: turns 0, pages 1
```

Case A reproduces the reported failure and shows the counter naming the cause.

### 3.3 Live capture (this is the new evidence)

After the gateway restart, `/ctxvm-trace status` reported `version=0.2.0`,
`register_calls=1`. A real session was recorded with a deliberate beat, then
flushed:

```
local-<session-id>.jsonl — 23 events
  session.open            1
  page.declare           13   (read_file, terminal, skill_view, memory)
  page.render             4
  page.fault              1   tool_recall @ turn 1
  turn.render             2   residentTokens 7540, headroom 112460
  call.meta               2   providerReported false

hookStats: pre 27 / post 26 / completed 25 / errored 1 / skipped_untraced 0
traceStats: turns 2, pages 13, faults 1, residentTokens 7540
```

Gates on the redacted corpus copy:

```
python3 spec/rfc-0/validate_schema.py corpus/m4/hermes-live-session-01.jsonl
SCHEMA CONFORMANCE: PASS (78 checks)

rust/target/release/replay corpus/m4/hermes-live-session-01.jsonl
{ "events": 23, "divergences": [], "violations": [{ "seq": 16, "kind": "faultOfResidentPage" }] }
EXIT=0
```

The single violation is the intended echo beat (identical `sha256sum` issued
twice), not a defect. The errored call (`read_file` on a missing path) produced
no page, as required by T6 §2, and is accounted for by `errored: 1`.

## 4. Corpus drop M4

`corpus/m4/`, mirroring the m2/m3 layout:

| File | Purpose |
|------|---------|
| `hermes-live-session-01.jsonl` | redacted live trace, 23 events |
| `hermes-live-session-01.meta.json` | session id, harness, plugin version, hook counts, trace stats |
| `provenance.json` | harness/plugin identity, redaction record, beats, limitations |
| `README.md` | what the capture shows and why m3 was synthetic |
| `checksums.sha256` | integrity for both artefacts |

**Redaction.** Paths rewritten before commit: `$REPO`, `$HERMES_HOME`, `$HOME`,
`$CAPTURE`. The pass was verified structurally — line count unchanged, every
line parses, the event stream is identical after applying the same substitution
in memory, and the schema validator plus replay engine pass on the redacted
file. No credentials, tokens, environment values, or third-party personal data
were present. One `tool:memory` ref embeds the first 120 characters of a stored
project convention about bug-report layout; reviewed, not personal data.

**This closes the m3 limitation.** m3 recorded live capture as blocked by
gateway process architecture. That diagnosis was incomplete: the gateway
restart recipe works, and the remaining defect was in the plugin, not the
harness.

## 5. Repository updates

- `04-odps-dataproduct-corpus.yaml` — `productVersion` 0.3.0 → **0.4.0**,
  `x-cabi.latestDrop` → `corpus/m4`, description extended with the m4 drop,
  re-validated comment added.
- `tools/run-ci.sh` — m4 added to fixtures, `corpus/m4` checksums verified,
  `replay corpus/m4/hermes-live-session-01.jsonl` added to gate 3, python test
  count corrected to 21.
- `hub/catalog.yaml`, `hub/index.html` — regenerated by `tools/build-hub.sh`;
  `hub/hub.sha256` re-baselined.
- `packages/hermes/BUG_REPORT.md` — confirmed root cause, fixes, evidence,
  deployment and operating rules.
- `packages/hermes/HOOKS.md` — hook-terrain pin (unchanged by this card).
- `packages/hermes/live/plugin.yaml` — 0.1.0 → 0.2.0.

## 6. Full gate

```
[ctxvm-ci] rust suite green                        44/44
[ctxvm-ci] ts suites green (12 + 8); python green  21
SCHEMA CONFORMANCE: PASS (435 checks)
[ctxvm-ci] schema + export round-trip gate green   (incl. m4 replay)
[ctxvm-ci] hub byte-identity green
[ctxvm-ci] ALL GATES GREEN
```

Schema checks rose 412 → 435, exactly the 23 new live events.

## 7. Operating notes

1. Start tracing **before** the work: `/ctxvm-trace start <dir>`.
2. Flush with `/ctxvm-trace stop`; the file is `<session-id>.jsonl` (Hermes ids
   begin with `local-`).
3. Read `skipped_untraced` before concluding the tracer lost anything.
4. After changing plugin source, restart the process that hosts the plugin;
   confirm with `version=` in `/ctxvm-trace status`.

## 8. Remaining limitations

- v0 is observe-only: no eviction, no stub rendering, no second-slot paging. m4
  cannot show those shapes; the m1 synthetic vector remains the eviction
  reference.
- Faults are deduped per page·source, so sustained re-fetch pressure appears as
  one row plus per-turn `call.meta`, not repeated rows.
- `tokenizerId` is `apx4-char` (ceil(chars/4)); token figures are approximations.
- `call.meta` carries `providerReported: false` throughout — the harness did not
  surface provider cache counters, so hit/miss figures are residency estimates.
