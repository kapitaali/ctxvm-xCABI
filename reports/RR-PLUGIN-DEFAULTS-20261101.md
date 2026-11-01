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
