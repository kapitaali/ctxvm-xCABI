# RR — PLUGIN-DEFAULTS-20261101 — capture that works without a manual

**Trigger.** A real session was traced — then could not be found. The capture had landed in
`/home/theb/.hermes/~/.local/state/ctxvm/traces/`, a literal `~` directory under the process cwd.
That one symptom exposed four defects, all of which would have blocked adoption: a path that is
not expanded, capture that is off unless you know an env var, a `stop` that reports success while
writing nothing, and traces that describe their model as `unknown/unknown` on a harness that knows
it.

**The trace that started this** (`ctxvm-dev.jsonl`, 2,114 bytes, 8 events, `replay` exit 0):

```
session.open · page.declare ×5 · turn.render ×1 · call.meta ×1
2,219 resident tokens · 1 turn · 0 faults · 0 evictions · touch_ratio 0.000 → waste 1.000
model: unknown/unknown   provider: unknown   budgetTokens: 200000
```

Hooks fire, the wire format is right (`schemaVersion: 0.1`, per-event `ts`), and every one of those
five pages was touched once — which is why the waste metric is degenerate at one turn, exactly as
`RR-W5-20261030` recorded for the same harness.

## Defects

1. **`~` was not expanded.** `/ctxvm-trace start ~/…` stored the raw string; the plugin then did
   `Path(dir).mkdir(...)`, resolving it against the process cwd. The capture "disappeared" into a
   directory literally named `~`. (Earlier diagnosis in chat blamed the hooks; that was wrong, and
   the witness log in the *other* directory was the clue — it only had `init` lines because the
   process that produced them had an absolute env path.)
2. **Capture was OFF by default.** Both adapters returned early without `CTXVM_TRACE_DIR`. A
   tracing framework that records nothing until the user guesses a variable name does not get
   adopted, and in a systemd-hosted gateway the variable has to be set in the unit, not the shell.
3. **`stop` lied.** It printed "tracing stopped, traces flushed" even when `finish_all()` returned
   zero traces, which is precisely the case that needs a different sentence.
4. **Identity was env-only.** `session.open` said `unknown/unknown` although Hermes knew the model
   and provider of the running session.

## Fixes

| Defect | Fix (both adapters) |
|---|---|
| literal `~` | `_resolve_trace_dir` / `resolveTraceDir`: `expanduser` + `expandvars` + `resolve`; tested that no `/~` can appear |
| off by default | unset → `${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces`; directories created `0700` |
| no opt-out | `CTXVM_TRACE=0` / `off` / `false` / `no` or an empty dir disables — documented, not implied |
| dishonest stop | `_flush_traces()` returns a count; `stop` says `N trace(s) flushed` or `0 traces written — no events were captured between start and stop` |
| silent dir confusion | `/ctxvm-trace status` prints the resolved absolute dir **and its source** (slash command / env / default / disabled) |
| unknown identity | `identity_from_payload()` reads `model`/`model_name`/`model_id` and `provider`/`provider_name` from the hook payload and stamps them into `session.open` and `.meta.json`, falling back to env |
| stale copies | `PLUGIN_VERSION` 0.2.0 → 0.3.0 and `plugin.yaml` 0.3.0, so a running copy is identifiable from its own output |

Contract written down in `09-plugin-parity.md` §5.1, with the input→result table both adapters
implement, so the next adapter cannot drift.

## Verification

- **Hermes suite:** 91 → **95 passed** (4 new: default dir, `~` expansion, opt-out, identity
  stamping; 2 rewritten to the new contract — the old tests asserted default-off and the old stop
  wording, which is what a contract change should force).
- **OpenCode suite:** 58 → **59 passed** (the "inert without a dir" test became "inert only when
  explicitly disabled", plus a resolver test).
- **Full gate:** `ALL GATES GREEN`, counts trued up in `tools/run-ci.sh`
  (`ts suites green (20 + 59 + 45); python suites green (95 + 44 + 8)`).
- **Live evidence that hooks work:** the 8-event trace above, `replay` exit 0, witness lines for
  `session_start`, tool events, `session_end -> flush`, and `trace stop -> flush`.

## Limits, stated

- `identity_from_payload` accepts the key spellings seen across Hermes hook payloads; it has not
  been confirmed against a live payload in *this* build. `on_session_start` now witnesses
  `identity=...` with whatever it extracted, so the next captured session answers it directly. If
  the host supplies nothing, traces keep the env fallback and the gap is explicit rather than
  silent.
- The installed copy under `~/.hermes/plugins/ctxvm-tracer/` was re-synced (`__init__.py`,
  `plugin.py`, `plugin.yaml`; `src/` is a symlink into the repo). A **running gateway keeps the old
  module until it restarts** — the fix takes effect on the next gateway start, not mid-session.
- Default-ON means session content on disk by default. `0700` and the documented opt-out are the
  mitigations shipped here; a retention/size cap is **not** implemented and is the obvious next
  hardening item before this is offered to anyone else.

---

## Addendum (2026-11-01, after a real default-ON capture)

The first capture with the new defaults — no env vars anywhere, gateway restarted, capture ON by
default — wrote `ctxvm-dev.jsonl` (1,530 bytes) at session end and again on `/ctxvm-trace stop`,
same byte count both times:

```
6 events · session.open + page.declare ×3 + turn.render + call.meta
model: deepseek/deepseek-v4.1-flash-1017      ← from the hook payload, not env
provider: unknown                              ← the payload did not carry it
3 pages, all tool_result, 268 tokens, 1 turn, 0 faults, 0 evictions
touch_ratio 0.000 → waste 1.000 (degenerate at one turn) · replay exit 0
pluginVersion 0.3.0 · dir mode 0700
```

**Confirmed working:** default-ON with no environment, `~`-free absolute paths, `0700`, and
identity-from-payload for `model` — proof that the env-ritual is no longer needed, since the
gateway process had zero `CTXVM_*` variables.

**Confirmed still open:** `provider` is `unknown`. The payload carries `model` as a string but no
provider key under any spelling the adapter knows. Two honest remedies, neither taken here:
ask the host to include it (upstream), or set `CTXVM_PROVIDER` in the gateway's systemd
environment (the very ritual this card removed). `identity_from_payload` was broadened to accept
`provider_id` / `providerID` and a nested `model: {id, providerID}` object, so if a future payload
shape carries it, the trace will pick it up without another card.

**Also confirmed:** `session_start` never fires in this build — zero occurrences across every
witness log today. The tracer is created lazily by `pre_llm_call`, which is why capture works
anyway; the visible cost is that any identity the host only sends at session start is lost.

---

## Addendum 2 (2026-11-01) — the price of default-ON: write-through and retention

The first capture proved default-ON works. It also showed what default-ON costs: the capture is
written **once**, at the end, so a crash loses the session; and nothing bounds the directory, so an
always-on tracer grows without limit. Both are now addressed in the same card, in both adapters.

**Write-through.** While the session runs, the adapter persists `<file>.partial.jsonl` and
`.partial.meta.json` every `CTXVM_TRACE_WRITETHROUGH_EVERY` units of activity (default 10,
`CTXVM_TRACE_WRITETHROUGH=0` disables). A complete flush deletes the partial **before** writing the
final pair, so a partial can never be mistaken for a capture and a crash still leaves a readable
prefix.

The cadence unit differs by adapter and is documented rather than hidden: hermes can see its
tracer's event list and counts **events**; the opencode plugin hides that list behind
`finishAll()`, so its adapter counts **hook fires**. Same variable, same default, one stated caveat
in `09-plugin-parity.md` §5.1.

**Retention.** At flush time, complete captures beyond `CTXVM_TRACE_RETAIN_MAX` (default 200 files)
or older than `CTXVM_TRACE_RETAIN_DAYS` (default 30) are deleted oldest-first, never the file just
written, with a witness line recording the count. `0700` still applies to the directory.

**Verification.** Hermes suite 95 → **97** (write-through persists a partial and the flush clears it;
retention prunes beyond budget and keeps the written file). Opencode suite 59 → **60** (partial
written on the first hook fire, gone after cleanup, complete capture present). Counts trued up in
`run-ci.sh`; `ALL GATES GREEN`.

**Still not done.** Retention is age/count based, not size based: a corpus of enormous captures
under the file cap still occupies whatever it occupies. A byte budget (`CTXVM_TRACE_RETAIN_BYTES`)
is the obvious next increment and is deliberately not claimed here.

---

## Addendum 3 (2026-11-01) — a byte budget, because count is not size

Addendum 2 said plainly that retention was age- and count-based, not byte-based, and named the
increment. Done, in both adapters:

```
CTXVM_TRACE_RETAIN_BYTES   default 536870912 (512 MiB)
```

Pruning now walks captures newest-first and deletes while the running total (including the file just
written) exceeds the byte budget, alongside the existing count and age limits. The witness line
records all three budgets, so a directory that shrank says why:

```
retention deleted=N files (max=200, days=30, bytes=536870912)
```

Contract row added to `09-plugin-parity.md` §5.1 **before** the implementation, per the adapter
procedure: the table is the spec, and a change without a row is drift by construction.

**Verification.** Hermes suite 97 → **98** (four 1 KB captures, 2.5 KB budget → the two oldest go,
the just-written file survives, total stays inside the budget). Opencode suite 60 → **61** (same
property driven through `setup`/cleanup). `PLUGIN_VERSION` and `plugin.yaml` → 0.4.0 so a stale
in-process copy is identifiable from its own output. Counts trued up; `ALL GATES GREEN`; installed
wrapper and yaml synced, effective at the next gateway start.

**What is still not claimed.** The budget counts the capture files, not their sidecars or the
witness log, and it prunes at flush time only — a session that runs for hours without a flush can
exceed the budget until it ends. Both are small, both are now written down rather than assumed.
