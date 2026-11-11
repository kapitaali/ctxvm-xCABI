# RR-W8BARMSTATE-20261111 — plugin 0.11.0 resolves the arm per session but RECORDS it per process:
## the sidecar can attest another session's arm, and the counters are cumulative, not the session's

Card: the review side's reading of the other lane's `3455f01` ("plugin 0.11.0: the arm is resolved per
session, not per process"). The resolution half is right; the **recording** half is still process-global,
which is the same defect class this card's experiment was voided by once already.

## 1. What 0.11.0 gets right (confirmed in the committed code)

- `packages/hermes/live/profile_policy.py` resolves the arm **per call** from
  `hermes_constants.get_hermes_home()` — the gateway's per-turn contextvar
  (`gateway/run.py::_profile_runtime_scope` → `set_hermes_home_override` → `copy_context`) — and reads
  exactly two keys from that home's `config.yaml` (`context.engine`,
  `plugins.entries.ctxvm-tracer.settings.budgetTokens`) with a narrow scanner (no PyYAML in the gateway
  interpreter).
- The engine now **declines to select** when the session's profile says `compressor`
  (`context_engine.py`: `self._meter["skipped_control"] += 1`, request left untouched) and adopts the
  session's budget only when its constructor was given none and the home exists; the plugin registers
  with `v_budget=None` (`__init__.py:1839-1841`).
- The sidecar gains `arm`, `engineSetting`, `skippedControl`, and `profile` is now the session's home
  (`__init__.py:612-626`).

This is the analogue the books name: **the profile carries the arm's settings, resolved per invocation
rather than snapshotted once per process** (`handoff/packets/P8-cache-stable-selection.md`: the arms are
separated by the profile each was invoked with and by nothing inside the trace). Measured by the other
lane: `policy(w8bn-naive)` → control/compressor/200000/default; `policy(w8bn-paged)` →
paged/ctxvm/70000/settings. **The design change is the right one.**

## 2. The catch: the resolution is per session, the *record* is per process

`_state()` is the tracer's **process-global** state — a dict hung off `sys` so it survives re-imports
(`packages/hermes/live/__init__.py:680-694`). The resolved arm is written into it at hook time
(`__init__.py:1148-1152`):

```
st["serving_profile"] = pol["profile"]
st["budget_tokens"]   = pol["budget"]
st["budget_source"]   = pol["budgetSource"]
st["arm"]             = pol["arm"]
st["engine_setting"]  = pol["engine"]
```

and read back at **flush** time (`__init__.py:612-626`), i.e. later, at session end:

```
"profile":        _state().get("serving_profile") or _serving_profile(),
"arm":            _state().get("arm"),
"engineSetting":  _state().get("engine_setting"),
"skippedControl": _engine_skipped_control(),
"budgetTokens":   _state().get("budget_tokens") or _budget_from_env(),
```

Because the state is on `sys`, it is **shared by every plugin instance and every session in the gateway
process**, across profiles. Three consequences follow, each a mechanism-level reading of the committed
code (not yet measured end-to-end in a live pair):

1. **Cross-session overwrite.** Between an arm session's hook and its flush, any other session served
   by the same gateway process overwrites the five fields above. The operator's own chat is served by
   that same gateway — their own record says so ("the 'newest sidecar' heuristic was reading the
   operator's own chat", `RR-W8B-CONTRAST-20261111`) — and the default profile's plugin is enabled. So
   the window between an arm session's last hook and its flush is exactly the window in which the
   operator's chat (or any concurrent session) can replace `arm`, `profile`, `engineSetting` and
   `budgetTokens` with the default profile's values. The sidecar then attests **another session's arm**
   — the `profile: default` defect, back in the record rather than in the settings.
2. **Cumulative counters, not the session's.** `engineSelections` and `skippedControl` are read from the
   engine instance's meter (`__init__.py:503-514`, `:529-536`), and that instance is stored in the same
   process-global state (`:1841`). The meter counts **every** selection (or control-decline) that
   instance ever made. A `engineSelections > 0` in a sidecar is therefore not evidence about *that*
   session — it can be a previous session's selection. Worse, `skippedControl` is incremented by the
   engine's *decline* path, which the operator's default-profile chat triggers on every turn (its
   profile says `compressor`): so a **paged** arm's sidecar can show `skippedControl > 0` from another
   session's turns.
3. **Cross-arm contamination of the counters.** `state["engine_obj"]` is overwritten by whichever
   profile registered its engine last, so the counters reported in a sidecar can come from the **other
   arm's** engine instance. Their own code already states the underlying rule for the `engine` field —
   "meaningful only when one gateway serves one arm (plan 4c); a multiplexer serving both cannot attest
   either, and the runner must enforce the single-arm gateway" (`__init__.py:612-615`) — but the
   counters are not covered by that sentence.

So the commit title is accurate about the *resolution* and silent about the *recording*. The two halves
are different claims, and only the first one is per session.

## 3. Three concrete changes, cheapest first

1. **Key the arm fields by session id.** The hook already has `session_id` in its kwargs
   (`_stamp_environment` reads `kwargs.get("session_id")`) and the flush path already has one
   (`_coverage_manifest(session_id, …)`), and the file already has the per-session-dict precedent
   (`state.setdefault("flushed_at", {})[session_id] = time.time()`, `:1100-1102`). One dict —
   `st.setdefault("arms", {})[session_id] = {…}` — and the flush reads
   `st["arms"].get(session_id)`. Nothing else changes; the fallback path stays.
2. **Report the counters as a session delta.** Snapshot `engine_obj._meter` at the session's first hook
   and subtract at flush (`selections = meter["select"] - selections_at_start`), the same for
   `skipped_control`. Then `engineSelections > 0` means *this* session selected, and `skippedControl`
   means *this* session's turns were declines.
3. **Gate on the arm fields, never on `engine`.** `engine` is process-level by design and will read
   `ctxvm` in both arms (that field is what caused the original confusion). The gate's expected
   difference is: `arm` / `engineSetting` (control vs paged), `budgetTokens` + `budgetSource` (the
   control arm's 200000/default vs the paged arm's 70000/settings), `skippedControl > 0` **and**
   `engineSelections == 0` for the control arm, `skippedControl == 0` **and** `engineSelections > 0`
   for the paged arm, and `profile` equal to the arm's profile.

**A note on the profile half of the precondition** (this lane's `RR-UHANDOFF-20261111`): with 0.11.0's
new fields, the sidecar now *can* attest the profile — `sidecar.profile`, `sidecar.arm`,
`sidecar.engineSetting` — so the missing assertion becomes a **gate** rather than a reading, provided
the recording is keyed per session as in (1). Without (1), the field exists but is not trustworthy.

## 4. One command to confirm or refute the mechanism (for the lane that owns the code)

Run the probe for the paged arm while a second session in the **same** profile (or the operator's chat
in `default`) is active, then read the paged arm's sidecar: if `arm`/`profile`/`engineSetting` name the
*other* session's profile, the overwrite is real; if `skippedControl` is non-zero in the paged arm's
sidecar, the counter bleed is real. Both are one session apart, no model spend for the second one.

## 5. Executed agent-doings

- The other lane's commit was read at its committed bytes (`git show 3455f01:…`), not from the working
  tree; every storage site and read site cited above was located in that blob (lines 503-514, 529-536,
  612-626, 680-694, 1100-1102, 1148-1152, 1839-1841).
- The design was checked against the books' analogue and found correct; the recording path was checked
  against the same analogue and found process-global.
- Three changes proposed, each with its existing precedent in the file. No file of the other lane's was
  edited; no spec, schema, corpus, vector or umpire byte changed; nothing pushed.
