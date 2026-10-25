# Corpus drop M5 — first interactive self-capture (OpenCode)

First capture recorded **inside a long-running interactive OpenCode TUI session** for the
**ctxvm Trace Corpus**: the agent (adapter `packages/opencode/live/ctxvm.ts`, harness
OpenCode 2.1.4) recorded its *own* working turns — a repository-hygiene card plus its
verification runs — through the same promise-plugin adapter, and the trace was flushed
only at the TUI's graceful exit. Where m2 drove the adapter with scripted one-shot CLI
invocations (`opencode run --standalone --auto`, one run per beat) and m4 used the Hermes
`/ctxvm-trace start|stop` governor, m5 is the third flush path: **plugin unload at TUI
exit**, with the whole chain observed by the adapter's diagnostic witness.

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|------|--------|------------|-------|-------|--------|--------|
| `opencode-live-session-01.jsonl` | interactive self-capture: hardware of its own session — hygiene card execution + instrumented-adapter verification on a resumed session | 17 records (17 ok / 0 error) | 14 | 17 | 17 | 80 |

Per-file provenance — harness version, invocation, flush semantics, honest misses — is in
`provenance.json` and the `.meta.json` sidecar. Integrity is in `checksums.sha256`.

## What this capture shows

1. **Seventeen `page.declare` events from real tool results** across three tool families:
   `shell` (12 pages), `edit` (4), `write` (1). Tool refs are
   `tool:<name>(<canonical-args>)` with args truncated at 120 characters — `shell` refs
   are command prefixes, `edit`/`write` refs are file paths.
2. **The cold-entry double-row law, 17/17.** Every novel page faults exactly once
   (`source: "identifier_scan"`) in the completing call's turn, then renders in full on
   the next model request: declare → fault@t → full render@t+1. The OpenCode adapter
   produces this shape deliberately (the context hook fires once per *model request*, and
   an agentic working turn spans several xCABI turns); the capture proves the law holds
   on sustained real workloads, not just the one-shot echoes of m2.
3. **All-full renders, zero evictions.** All 17 `page.render` events are `mode: full`;
   `residentTokens` is constant at 2055 at every one of the 14 turn boundaries
   (`headroom: 197945` against the declared 200000 budget) and there is no `page.evict`
   event. There is no paging pressure by construction, so `netTokenReduction` is 0.0
   against the counterfactual-no-paging baseline by construction — the capture is a
   reference-string/flush-mechanics proof, not a policy-sweep dataset (see the UC3 sweep
   RR for pressure data).
4. **Turn accounting is real and dense.** 14 `turn.render` + 14 `call.meta` over 80
   events — the deepest reference string in the corpus (m2: 22/33 events over 6 turns;
   m4: 23 over 2). `hookStats` records `contexts: 14, before: 17, after: 17,
   completed: 17, errored: 0`; every completed call declared exactly one page.

## Why a self-capture needed a diagnosis first

The interactive path was previously *blocked*: the adapter's first tested quit (2026-10-25
morning) flushed nothing — hooks were silent and the traceback (if any) invisible. The
plugin loads in the CLI/TUI process (TUI processes carry the `CTXVM_*` capture env;
`opencode serve --service` carries none), so a quit *can* lose the in-memory slice before
any write. Two changes fixed the loop:

| Change | Effect |
|--------|--------|
| `ctxvm.ts` instrumented with a best-effort witness (`hooks-witness.log`: one line per hook fire + per flush attempt) | a missing flush became diagnosable |
| stop sequence = TUI first (the flush owner — SIGTERM runs plugin cleanup while the session is still coherent), then the background service, then verification | deterministic end-of-capture |

The flush then landed, witnessed:

```
2026-10-25T11:29:47 cleanup entered (plugin unload)
2026-10-25T11:29:47 cleanup finishAll -> 1 tracer(s)
2026-10-25T11:29:47 flush m5-self.jsonl bytes=16280 session=ses_e9c7bead…
2026-10-25T11:29:47 cleanup exit
```

One honest miss ships with the drop: the sidecar's `opencodeVersion` is `null` because
the boot recipe of this session omitted `CTXVM_OPENCODE_VERSION`. The erratum 
(`packages/opencode/live/README.md`) adds it to the recipe; the value is not backfilled.

## Validation

```
$ python3 spec/rfc-0/validate_schema.py corpus/m5/opencode-live-session-01.jsonl
SCHEMA CONFORMANCE: PASS (135 checks)

$ rust/target/release/replay corpus/m5/opencode-live-session-01.jsonl
{ "events": 80, "divergences": [], "violations": [17 × { "kind": "faultOfResidentPage" }] }
EXIT=0
```

The 17 violations are the cold-entry shape itself, not defects: replay classifies each
first-sight fault of a page that is (by the observe-only contract) resident-as-declared,
and the following all-full render feeds nothing new.

## Reproduction

```
# instruments the CLI/TUI process (opencode serve --service reaches none of it)
export CTXVM_TRACE_DIR=/tmp/opencode/self-capture
export CTXVM_TRACE_NAME=<a name that will not be flushed>   # later flushes overwrite
export CTXVM_MODEL=opencode/<model-id>
export CTXVM_PROVIDER=opencode
export CTXVM_AGENT_ID=ctxvm-self
export CTXVM_BUDGET_TOKENS=200000
export CTXVM_OPENCODE_VERSION="$(opencode --version)"        # erratum 2026-10-25
opencode --continue
# ...work turns...
# end the TUI gracefully (SIGTERM): flush fires on plugin unload.
# A hard kill (or a plain `kill -9`) discards the in-memory slice silently.
```

Snapshot the flushed file immediately if a later boot of the same name may flush again.
See `packages/opencode/live/README.md` for the full recipe and the flush-semantics
erratum (v2.1.4, 2026-10-25).
