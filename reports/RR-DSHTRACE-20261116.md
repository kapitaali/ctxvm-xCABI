# RR-DSHTRACE-20261116 — validating the first web-UI traces from the OpenCode route

**Lane:** dsh adapter. **Date:** 2026-11-16. **Sample:** n = 2 session traces, both private live
captures on disk under `~/.local/state/ctxvm/traces/`. No trace bytes are committed.

The owner supplied the adapter's disposal log after shutting down `dsh web`:

```
[ctxvm] session/disposed session-a47fde9a-…
[ctxvm] trace written: ~/.local/state/ctxvm/traces/session-a47fde9a-…-1794838568647.jsonl
[ctxvm] session/disposed session-830bc015-…
[ctxvm] trace written: ~/.local/state/ctxvm/traces/session-830bc015-…-1794838568651.jsonl
[ctxvm] effect cleanup; flushing 0 live session(s)
```

These are the two sessions seen in the startup log in `RR-OPENDSH-20261116` §2.4, including the
one that previously crashed on resume.

## 1. What was run

```sh
T1=~/.local/state/ctxvm/traces/session-a47fde9a-de6b-43a9-8808-a166fb5d2111-1794838568647.jsonl
T2=~/.local/state/ctxvm/traces/session-830bc015-3be6-40c3-b913-11f552de5424-1794838568651.jsonl
python3 spec/rfc-0.1/validate_schema_v0_1.py "$T1" "$T2"
./rust/target/release/replay "$T1"
./rust/target/release/replay "$T2"
```

## 2. Results

| Check | Both traces |
|---|---|
| file size | 400 bytes each |
| `validate_schema_v0_1.py` | `OK: all checks passed` |
| `ctxvm replay` exit | 0 |
| events | 3 |
| `divergences` | 0 |
| `violations` | 0 (so no `faultOfResidentPage` rows) |

Each trace is exactly:

```
{"type":"session.open","agentId":"dsh:session-<prefix>","model":"unknown","provider":"dsh",
 "budgetTokens":200000,"tokenizerId":"apx4-char","schemaVersion":"0.1"}
{"type":"turn.render","turn":0,"residentTokens":0,"evictedTokens":0,"headroom":200000,
 "prefix":{"source":"unknown"}}
{"type":"call.meta","turn":0,"provider":"dsh",
 "cacheEstimate":{"estHitTokens":0,"estMissTokens":0,"providerReported":false}}
```

## 3. What this does and does not witness

**Does witness.** The `@ctxvm/dsh` adapter is live in the restarted web profile: it created one
tracer per session, registered the page-table projection, emitted a schema-valid v0.1 skeleton,
and flushed both traces cleanly on disposal. The previously failing session no longer crashes
during projection (the fix in `RR-DSHPROJ-20261116`). Replay derives an empty page table with no
divergence.

**Does not witness.** These traces carry **no provider/model identity** (`provider: "dsh"`,
`model: "unknown"`), **no `page.declare` / `page.fault` / `page.render` rows**, **no
`providerUsage`**, and **no `ts` key on any event**. So they are not evidence that the OpenCode Go
model selection, its tool calls, or its token accounting were captured. The model selection itself
is evidenced by the web UI behaviour and the headless run in `RR-OPENDSH-20261116`, not by these
trace bytes.

The missing identity is a known W22 limitation, already recorded in `RR-W22-20261115` §Limitations:
the adapter falls back to `provider: "dsh"`, `model: "unknown"` when no `request/header` precedes the
other events. This live pair confirms that limitation still holds in the web path. The absent `ts`
is consistent with the capture shell's `CTXVM_TRACE_TS=0` opt-out (D9); the exited web process's
environment was not inspected, so that attribution is UNVERIFIED.

## 4. Claim ceiling and next step

No cost or saving claim; no model-output, safety, or general-correctness claim; no "deterministic"
outside page-table derivation. The two sessions are private live captures and stay in the state
directory (AGENTS law 9).

Next step, not performed here: extend the W22 adapter to map DSH's `request/header` and
`tool/result` events into `session.open` identity and page declarations, then rerun one web session
and validate a trace that actually carries the OpenCode model and its tool work. That is a source
change in `packages/deepseek/**` (dsh lane) and needs owner clearance.

## 5. Files and commit

- Repo: this card and one LOG row; no trace bytes, corpus, spec, tools, or research file changed.
- Prior cards in the chain: `RR-OCDIFF-20261113`, `RR-OCDSH-20261116` (+ addenda),
  `RR-DSHPROJ-20261116`, `RR-OPENDSH-20261116`.
