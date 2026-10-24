# Corpus drop M4 — first LIVE Hermes plugin trace

First **live** slice of Hermes plugin traces for the **ctxvm Trace Corpus**. It
supersedes the synthetic-only limitation recorded in `corpus/m3`: the live
capture now works because the plugin was fixed in T17.7 (see
`packages/hermes/BUG_REPORT.md`).

Recorded inside a running Hermes session by the installed plugin (version
0.2.0), not synthesised. Paths are redacted (`$REPO`, `$HERMES_HOME`, `$HOME`,
`$CAPTURE`); the redacted file passes the schema validator and the replay engine
unchanged in structure.

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|------|--------|------------|-------|-------|--------|--------|
| `hermes-live-session-01.jsonl` | live Hermes session: corpus inspection, validation, one deliberate echo beat, one failing call | 26 recorded (25 ok / 1 error) | 2 | 13 | 1 | 23 |

Per-file provenance — harness version, plugin version, redaction, limitations —
is in `provenance.json` and the `.meta.json` sidecar. Integrity is in
`checksums.sha256`.

## What this capture shows

1. **Thirteen `page.declare` events from real tool results**, spanning four tool
   families: `read_file`, `terminal`, `skill_view`, `memory`. Tool refs are
   `tool:<name>(<canonical-args>)` with args truncated at 120 characters.
2. **One `tool_recall` fault.** The same `sha256sum` command was issued twice and
   returned identical output, so the second completion hit an already-resident
   page with an unchanged `contentHash`. The replay engine classifies it as
   `faultOfResidentPage` — the measured double fetch, from a real loop.
3. **One errored call produced no page.** `read_file` on a non-existent path
   returned `status: "error"`; the tracer declares pages only for successful
   results (T6 §2). `hookStats` records `completed: 25, errored: 1`, so the
   missing page is accounted for rather than dropped silently.
4. **Turn accounting is real, not zero.** Two `turn.render` events report
   `residentTokens: 7540` with `headroom: 112460` against the declared 120000
   budget. Every `call.meta` carries `providerReported: false`, so cache figures
   remain estimates.

## Why m3 was synthetic and m4 is not

`corpus/m3` recorded live capture as blocked: `CTXVM_TRACE_DIR` set in a CLI
shell did not reach the long-running process where plugins load, and the plugin
itself had three defects that made completed calls record nothing.

T17.7 fixed all of them:

| Defect | Effect | Fix |
|--------|--------|-----|
| `payload.get("tool")` | ref built from `None` on live payloads (Hermes sends `tool_name`) | read `tool` or `tool_name` |
| `result.get("content")` | `AttributeError` on plain-string results, swallowed fail-open → 0 pages | `extract_page_body()` handles all shapes |
| module-level `_plugin` | reset on re-import, discarding trace dir and pages | state on `sys._ctxvm_tracer_state` |
| flush by session id | end-hook id did not match tool-call id | flush all tracers via `finish_all()` |

`hookStats` now also carries `skipped_untraced`, which separates "the tracer
missed events" from "tracing was switched on after the calls". It is `0` here,
so this window is complete for its duration.

## Validation

```
$ python3 spec/rfc-0/validate_schema.py corpus/m4/hermes-live-session-01.jsonl
SCHEMA CONFORMANCE: PASS (78 checks)

$ rust/target/release/replay corpus/m4/hermes-live-session-01.jsonl
{ "events": 23, "divergences": [], "violations": [{ "seq": 16, "kind": "faultOfResidentPage" }] }
EXIT=0
```

The single violation is the intended echo beat, not a defect: the RFC-0 replay
engine flags a completed call that lands on a resident page with unchanged
content.

## Reproduction

```
# inside a running Hermes session
/ctxvm-trace start $CAPTURE
<perform tool calls>
/ctxvm-trace stop
```

Then validate the flushed `local-*.jsonl` with `spec/rfc-0/validate_schema.py`
and the replay binary. See `packages/hermes/HOOKS.md` for the hook-terrain pin
and `packages/hermes/BUG_REPORT.md` for the defect history.
