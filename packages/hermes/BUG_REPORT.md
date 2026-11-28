# BUG REPORT — ctxvm-tracer plugin

Date: 2026-10-24
Card: T17 (ctxvm UC1 v0 — Hermes plugin for within-harness session capture)
Plugin version: 0.2.0
Status: ROOT CAUSE CONFIRMED AND FIXED (code verified end-to-end); deployment restart pending

## Symptom

Trace files contained only `session.open`, `turn.render`, and `call.meta` —
**zero `page.declare` events** — while `hookStats` reported hundreds of
`post_tool_calls` and `completed` calls. `traceStats.pages` was always 0.

Representative meta from a live capture:

```json
"hookStats": {
  "session_starts": 12, "pre_tool_calls": 259, "post_tool_calls": 258,
  "completed": 235, "errored": 50, "pre_llm_calls": 47, "session_ends": 46
},
"traceStats": { "turns": 1, "pages": 0, "faults": 0, "residentTokens": 0 }
```

## Root cause (confirmed, not hypothesised)

The hook handlers increment `stats` **unconditionally**, then call the tracer
only if `_ensure_plugin()` returns a non-None plugin:

```python
def on_post_tool_call(**kwargs):
    stats["post_tool_calls"] += 1        # always counted
    vm = _ensure_plugin()                # None while tracing is disabled
    if vm is not None:
        vm.on_post_tool_call(kwargs)     # page.declare would happen here
```

So `hookStats` counts **hook fires**, not **recorded events**. A session whose
tool calls happen while `_traced()` is False records nothing, and the later
flush writes a tracer that has only seen `session.open`. That matches the
observed files exactly: full hook counters, `pages: 0`, `turns: 1`.

Two contributing conditions made this look like a tracer bug:

1. **Tracing was enabled after the work, not before.** `/ctxvm-trace start` only
   affects hooks that fire *after* it runs. It does not retroactively record
   calls already made in that process.
2. **The installed plugin was stale.** `~/.hermes/plugins/ctxvm-tracer/` held an
   older build (no `_state()`, no `pluginVersion`, module-level `_trace_dir`)
   while the repo had the fixed code. A long-running Hermes process keeps the
   module it imported at startup; on-disk edits do nothing until restart.

## Fixes applied (all verified)

### 1. `tool_name` vs `tool` — packages/hermes/src/plugin.py

Hermes passes `tool_name=function_name`. The plugin read `payload.get("tool")`,
which is `None` live. Now:

```python
tool = payload.get("tool") or payload.get("tool_name")
```

Applied in `on_pre_tool_call` and `on_post_tool_call`.

### 2. Tool result shape — `extract_page_body()`

Hermes tool results are usually plain strings. `result.get("content")` raised
`AttributeError`, silently swallowed by the fail-open dispatcher, producing zero
pages. `extract_page_body()` now handles `str`, `dict` with a `content` list,
`dict` with `text`, `list`, `None`, and other types.

### 3. Process-global state survives re-import — live/__init__.py

Hermes re-registers plugins between sessions, which creates a new module object
and resets module-level variables — losing both the trace dir and every declared
page. State now lives on `sys._ctxvm_tracer_state`:

```python
def _state():
    state = getattr(sys, "_ctxvm_tracer_state", None)
    if state is None:
        state = {...}
        setattr(sys, "_ctxvm_tracer_state", state)
    return state
```

`sys` is never reloaded, so tracing config and the tracer survive any number of
`register()` calls.

### 4. Flush-all, not flush-by-session — `_flush_traces()`

`on_session_end` no longer looks up a tracer by `session_id` (the id in the end
hook does not reliably match the id used during tool calls). It calls
`finish_all()` and writes one file per tracer.

### 5. Idempotent `finish()` — packages/hermes/src/plugin.py

`finish()` used to append `turn.render` / `call.meta` to `_events` on every
call, so multiple flushes (session end, unload, atexit) duplicated records. The
tail is now computed per call and never appended.

### 6. Diagnostic: `skipped_untraced`

New counter in `hookStats`. Non-zero together with `pages: 0` means tracing was
switched on **after** the calls — the tracer did not miss events, it did not
exist yet. This removes the main false-alarm signal.

`/ctxvm-trace status` now also reports `version`, `register_calls`, and
per-tracer `events`/`pages`:

```
ctxvm-trace: enabled=True, dir=/tmp/cap, name=x, version=0.2.0,
  register_calls=1, tracers=[ses-1:events=7,pages=3]
```

## Verification

End-to-end through the installed plugin path with Hermes-shaped payloads
(`tool_name`, `status="ok"`, plain-string `result`).

Case B — tracing enabled before any call:

```
event types: ['session.open', 'page.declare', 'page.declare', 'page.declare',
              'page.render', 'page.render', 'page.render', 'turn.render', 'call.meta']
traceStats: {'turns': 1, 'pages': 3, 'faults': 0, 'residentTokens': 45}
skipped_untraced: 0
```

Case A — two tool calls made while tracing was off, then enabled:

```
skipped_untraced: 5
traceStats: {'turns': 0, 'pages': 1, ...}   # only the call made after start
```

Case A reproduces the reported failure exactly and shows the counter naming the
cause.

CI: rust 44/44, ts 12+8, python 21/21, schema 412, hub byte-identity — all green.

## Deployment requirement

The fix is live only after Hermes reloads the plugin module. A running process
keeps the code it imported at startup, so editing files is not enough:

```bash
# from a shell OUTSIDE the running Hermes process
systemctl --user restart hermes-gateway.service   # gateway-backed sessions
# standalone `hermes` CLI process: exit and start it again
```

Cross-check that the new build is live:

```
/ctxvm-trace status      # must report version=0.2.0
```

## Operating rule

Start tracing **before** the tool calls that must be recorded:

```
/ctxvm-trace start /tmp/ctxvm-capture
... do the work ...
/ctxvm-trace stop
```

Files are written as `<session-id>.jsonl`. Hermes session ids begin with
`local-`, so a healthy capture shows `local-*.jsonl` in the directory.

## Files changed

- `packages/hermes/src/plugin.py` — `extract_page_body`, `tool_name` fallback,
  idempotent `finish()`
- `packages/hermes/live/__init__.py` — `sys`-backed state, `_active_trace_dir`,
  flush-all, `skipped_untraced`, richer `status`, guarded `atexit`
- `packages/hermes/live/plugin.yaml` — version 0.2.0
- `packages/hermes/test/test_plugin.py` — 21 tests including live-shape cases
- `~/.hermes/plugins/ctxvm-tracer/` — installed copies synced, `__pycache__` cleared

---

# BUG REPORT — shadow record discarded when a selected page has no unique ref

Date: 2026-11-28
Plugin version: 0.13.37 (live, harness 0.23.4)
Status: ROOT CAUSE LOCATED IN CODE AND CONFIRMED BY LIVE FAILURES; the exact offending page is not yet
identified. No fix applied.
Evidence base: authorized shadow batch `shadow-batch-20261128-ratified-v1` (18 attempts,
16:45:47–17:03:46 UTC).

## Symptom

The collector excluded 11 of 18 attempts: ten by `sidecar_failures`, one by `sidecar_selections`.
Per-attempt sidecar counters record 15 shadow write failures; `_swallowed.log` holds 25
`shadow_record` errors inside the batch window.

```text
~/.local/state/ctxvm/traces/_swallowed.log
2026-11-28T18:50:16 shadow_record: ValueError: page entry does not resolve to exactly one logical ref
...
2026-11-28T19:03:12 shadow_record: ValueError: page entry does not resolve to exactly one logical ref
```

25 of the 29 occurrences of this error class fall inside the batch window; the other 4 date from
2026-11-26. Two other classes exist in the same file: 125
`ShadowSchemaError: budget_tokens must be a non-negative integer` and 3
`ValueError: page entry needs an exact contentHash`.

## Root cause

`live/__init__.py:1247` `_write_shadow_record` builds each page entry through `_hashed_pages`:

```python
refs = tracer.refs_for_identity_tokens([entry["ids"]], content_hash=content_hash)
if len(refs) != 1:
    raise ValueError("page entry does not resolve to exactly one logical ref")
```

The raise lands in the function's single `except Exception` handler, so the **entire record** is
discarded, not only the unplaceable page. `shadow_counts_by_session` was already incremented before the
write, so the sidecar reports `shadowSelections > recorded lines` and `shadowWriteFailures > 0`. Both are
collector gates (`tools/collect-shadow.py:746-760`), so the attempt is excluded.

`refs_for_identity_tokens` (`src/plugin.py:376`) returns `len != 1` in two cases:

- **empty** — the unit's `content_hash` (the engine's hash of the request-time tool-result text,
  `live/context_engine.py:830`) is not a declared `ref|contentHash` pair for any ref, so `exact` is
  empty, `candidates` is empty and `matches` is empty;
- **more than one** — two refs declare the same content hash and both match the identity stems.

## What is proven, and what is not

Proven: the raising branch is exactly the logged error and it discards whole records; 25 live
occurrences in the batch window; 11 of the authorized 18 attempts were excluded, consuming 61% of the
attempt budget; the batch ended at 2 informative of 12 (both `read-once-pressure`), `status:
UNDERPOWERED`; `dependency-chain` lost 5 of its 6 attempts to this defect and could not reach its
target. Whether an excluded attempt would have been informative is not knowable from the receipts.

Not proven: which page entry raised. The record is not written by design and the payload is not
logged. An offline replay of the stored session messages (attempts 5 and 6:
`_classify` → `_update_page_state` → `_credit_demand` → `_hard_keep` → `_plan` → the same resolver)
resolves every selected page to exactly one ref. The replay reproduces neither the system prompt nor
the harness-side request formatting, so the live text that produced the hash is not reconstructible
from `state.db`. The leading hypothesis — the request-time tool-result text and the tracer's declared
content are not the same string — stays a hypothesis.

## Repro

```bash
grep 'does not resolve' ~/.local/state/ctxvm/traces/_swallowed.log | wc -l   # 29 total, 25 in window

python3 - <<'PY'
import json, glob, os
b = os.path.expanduser('~/.local/state/ctxvm/w8-runs/shadow-batch-20261128-ratified-v1/attempts')
for p in sorted(glob.glob(b + '/*/receipt.json')):
    r = json.load(open(p)); c = json.load(open(os.path.join(os.path.dirname(p), 'coverage.json')))
    print(r['attempt'], r['shape'], r['failed_gates'], (c.get('plugin') or {}).get('shadowWriteFailures'))
PY
```

## Fix directions (ruling required)

1. Make one unplaceable page non-fatal for the record: skip it, keep the rest, carry a counted
   content-free marker so the exclusion stays visible. Needs a schema/freeze decision.
2. Keep the record fail-closed but log a content-free diagnostic (page kind, hash prefix, ref count) at
   the raise site, so the next batch can identify the page without guessing.
3. Close the identity gap: make the engine's unit hash and the tracer's declared hash come from the
   same string by construction, so the resolver cannot miss.

Do not weaken `_validate_shadow_record` or the collector gates to make a batch pass.
