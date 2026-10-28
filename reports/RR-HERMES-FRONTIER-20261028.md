# RR-HERMES-FRONTIER-20261028 — Hermes plugin: tool=None mapping fix + /ctxvm-resume UX

## Card executed: hermes frontier items (2 of 3 remaining)

## What was done

**1. Gateway `tool=None` hook-key mapping** (`packages/hermes/src/plugin.py`)
- `Tracer.page()` and `Tracer.recall()`: changed `input.get("tool", "unknown")` to
  `input.get("tool") or "unknown"`. A gateway payload with `tool:null` (key present,
  value null) previously fell through `input.get("tool", "unknown")` returning `None`
  (key exists), producing `tool:None(...)` refs. Now `None` is treated as falsy and
  replaced with `"unknown"`, matching the `CtxvmPlugin` handler law
  (`payload.get("tool") or payload.get("tool_name")`) already in place.

**2. Verified-boot resume-brief UX** (`packages/hermes/live/__init__.py`)
- Added `/ctxvm-resume <snapshot-dir>` slash command, gated by `CTXVM_FEATURES=handoff`
  (same gate as `/ctxvm-handoff`).
- Calls `uc1.resume(snapshot_dir)` and prints a brief result: exit_code, verified,
  reason, snapshotDigest, projection (slots at turn), and diff (source + relation).
- Never blocks the agent loop: any failure returns verified=False with a loud reason.

## Tests added
- `test_plugin.py`: `test_tool_none_maps_to_tool_name` — gateway payload with
  `tool:null` + `tool_name` set still declares a page with a valid ref.
- `test_uc1_handoff.py`: `test_resume_command_registered_with_feature`,
  `test_resume_command_not_registered_without_feature`, `test_resume_usage_output`.
- `test_uc1_handoff.py` `FakeCtx`: now stores all registered handlers in a `handlers`
  dict (matching `test_uc_registry.py` pattern) instead of overwriting a single
  `.handler` attribute — required because `/ctxvm-resume` is now registered after
  `/ctxvm-handoff`.

## Verification
- `test_plugin.py`: 25 tests OK
- `test_uc1_handoff.py`: 34 tests OK
- `test_uc2_forensics.py`: 10 tests OK
- `test_uc_registry.py`: 11 tests OK
- All 80 hermes tests green.

## Deviations from card
None — these were frontier items with no formal card.

## Discoveries
None beyond the fix itself.

## Open questions
- The third frontier item (gated handoff-inject v-next beat) remains parked pending
  orchestrator sign-off per 08-HANDOFF.md §0.
- Pre-existing uncommitted changes in `packages/ai-sdk/` (index.ts, test, resume-brief.ts)
  are not part of this commit.
