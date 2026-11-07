# RR-STOPSEM-20261107 — one session's stop silenced a whole gateway

Card: plugin 0.10.3. Behaviour change in one slash command; no wire change, no engine change.

## The incident

The W8 orchestrator lost capture mid-morning. Its diagnosis was exact: at 13:29:20 a
`/ctxvm-trace stop` ran in the gateway, and from then on the process wrote nothing — not for its
smoke runs, not for the working session — although the process environment still carried
`CTXVM_TRACE_DIR=/tmp/w8/traces` and `CTXVM_TRACE_NAME=w8`.

The mechanism is one sentinel in `_active_trace_dir()`:

```python
value = state["trace_dir"]
if value == "":  # explicitly stopped in this process; do not fall back to env
    return None
return value or _resolve_trace_dir(os.environ.get("CTXVM_TRACE_DIR"))
```

`stop` set `state["trace_dir"] = ""`. The comment shows the intent — a deliberate stop must not be
undone by the fallback — but the state is **process-wide**, and a gateway process serves every
session, including delegated work. So one operator action disabled a deployment.

## Why it was hard to see

Capture failing silently looks exactly like capture succeeding on an idle system. The stop message
said "0 traces written", which reads as "nothing was captured" but meant "nothing was left pending".
Two misleading signals in the same minute, and neither of them said "disabled".

## The fix

Capture configured by the deployment's environment is not one session's preference. `stop` now
flushes and then falls back to the environment, leaving the process armed:

```
ctxvm-trace: 3 trace(s) flushed; capture STAYS ARMED from the environment at /tmp/w8/traces
(this process serves many sessions — use /ctxvm-trace stop --hard to silence it).
```

`stop --hard` keeps the old behaviour for the operator who really wants silence in that process. A
capture started by a slash command (`start <dir>`) is still stopped outright by `stop`, because then
the command, not the environment, owns it.

The count message changed too: "nothing was pending to flush … this does not mean no events were
captured". A test pins that the phrase "0 traces written" is gone.

## Tests

- `test_stop_keeps_env_configured_capture_armed`: with `CTXVM_TRACE_DIR` set, `stop` leaves
  `_active_trace_dir()` at that directory and says "STAYS ARMED"; `stop --hard` then returns `None`.
- `test_slash_command_start_then_stop`: a command-started capture is still disabled by `stop`, and
  the message must not claim "0 traces written".
- Python 172 → 173.

## What the run needs

Nothing structural — but the rule is now stated for the record: **a gateway serving a measurement
must not let a session-level command change deployment-level capture state**, and any future
command that mutates process-wide state needs a per-session or `--hard` boundary.
