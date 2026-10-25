# RR-UC2-PLUGIN-20261025 — Hermes UC2 forensics plugin (ORG-1)

**Card:** UC2-PLUGIN (in-harness forensics surface for Hermes)
**Date:** 2026-10-25
**Plugin version:** 0.2.0 (unchanged)
**Commit:** none yet (working tree)

## 1. Card executed: UC2-PLUGIN

Expose the committed CLI half (replay --turn/--pin, profile, diff, export) as
Hermes plugin commands with verdict decomposition (context-management fault vs
model reasoning fault), per the UC2 memo §3.

## 2. What was done

### 2.1 UC2 forensics submodule — `packages/hermes/src/uc2_forensics.py` (REPLACED stub)

Replaced the no-op stub with a real implementation that shells out to the
committed Rust CLI binaries:

| Method | Wraps | Returns |
|--------|-------|---------|
| `replay(trace, turn, pins, output)` | `ctxvm replay` | `{"exit_code", "report", "stderr"}` |
| `profile(trace, events, turns, source, output)` | `ctxvm profile` | `{"exit_code", "report", "stderr"}` |
| `diff(a, b, output)` | `ctxvm diff` | `{"exit_code", "report", "stderr"}` |
| `export(trace, turn, output, odps)` | `ctxvm export` | `{"exit_code", "report", "stderr"}` |
| `diagnose(trace, fault_turn)` | replay + profile + verdict logic | `{"fault_turn", "verdict", "reason", "evidence"}` |

Binary discovery: `CTXVM_RUST_BIN_DIR` env override → `rust/target/release/`
relative to repo root → PATH fallback.

### 2.2 Verdict decomposition — `UC2Forensics.diagnose(trace, fault_turn)`

Implements UC2 §3 Phase 3–4:

1. Fact gate: `replay --turn fault_turn` must be divergence-free.
2. Profile all faults at `fault_turn`; confirm at least one exists.
3. Profile all evictions before `fault_turn`; collect evicted page refs.
4. Verdict: if any faulted page at `fault_turn` was evicted earlier →
   **context-management** (pager dropped needed content). Otherwise →
   **model-reasoning** (page was resident; pager not at fault).

Returns:
```json
{
  "fault_turn": 3,
  "verdict": "context-management",
  "reason": "page evicted before fault turn — pager dropped needed content",
  "evidence": {
    "faults_at_turn": [...],
    "evictions_before": [...],
    "replay_exit_code": 0,
    "replay_divergences": []
  }
}
```

### 2.3 Slash command — `/ctxvm-forensics` (live/__init__.py)

Registered when `CTXVM_FEATURES=uc2-forensics` (feature-gated, not registered by
default):

```
/ctxvm-forensics replay <trace> [--turn N] [--pin ref|(ref,hash)]... [--output FILE]
/ctxvm-forensics profile <trace> [--event <type>]... [--turns spec] [--source <src>] [--output FILE]
/ctxvm-forensics diff <a.jsonl> <b.jsonl> [--output FILE]
/ctxvm-forensics export <trace> [--turn N] [--output DIR] [--odps]
/ctxvm-forensics diagnose <trace> <turn>
```

Thin wrapper — the Rust engine is untouched. The command shells out to the
already-built binaries and formats their JSON output.

### 2.4 Feature registry integration

`UC2Forensics` is registered in `state["ucs"]` at `register()` time and
dispatched via `_enabled_stubs()` when `CTXVM_FEATURES=uc2-forensics`. The
`ctxvm-forensics` slash command is only registered when the feature is active.

### 2.5 Tests — `packages/hermes/test/test_uc2_forensics.py` (NEW, 9 tests)

| Class | Tests | Coverage |
|-------|-------|----------|
| `UC2ForensicsTests` | 6 | Instantiation, replay/profile/diff/export return dicts, diagnose returns verdict |
| `UC2DispatcherTests` | 3 | Command registered with feature, not registered without, diagnose via slash command |

Total hermes suite: 43/34 → 43/43 (34 pre-existing + 9 new UC2 tests). No regressions.

## 3. Verification

```
$ cd packages/hermes && python -m pytest test/ -q
43 passed in 0.14s

$ cd /home/theb/Documents/ctxvm && bash tools/run-ci.sh
[ctxvm-ci] rust suite green
[ctxvm-ci] gate 2/4: typescript ... python suites green (43 + 27 tests)
SCHEMA CONFORMANCE: PASS (515 checks)
[ctxvm-ci] schema + export round-trip gate green
[ctxvm-ci] gate 4/4: hub — ODPS validate + regen byte-identity
[ctxvm-ci] hub byte-identity green
[ctxvm-ci] ALL GATES GREEN
```

- Hermes suite: 43/43 (was 34, +9 UC2 forensics tests)
- Opencode suite: 9/9 (unchanged)
- Schema: 515 checks (unchanged; no new event types)
- Hub: byte-identity verified via build-hub.sh self-baseline
- Capture path byte-compatible: default `{trace}` features unchanged

## 4. Deviations from card

None. All DoD items addressed:
- ONE deployable plugin per harness — unchanged
- CTXVM_FEATURES-gated UC submodules — uc2-forensics added as third stub→real module
- Thin per-port wrapper, engine untouched — shells out to Rust binaries
- Per-UC test files — `test_uc2_forensics.py` with 9 tests
- run-ci/ci.yml gate constants updated — python count 34 → 43
- ALL GATES GREEN

## 5. Discoveries

None beyond card scope. The Rust binaries (`replay`, `profile`, `diff`, `export`)
were already built at `rust/target/release/` from prior UC work (T16-T21).

## 6. Open questions

None.

## 7. Next

Per §5, UC2-PLUGIN is DONE. The next OPEN card depending on ORG-1 is UC1-PLUGIN
(within-harness pause/resume + ctxvm-py PyO3 binding).
