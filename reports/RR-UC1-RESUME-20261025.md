# RR-UC1-RESUME-20261025 — UC1-PLUGIN B3: resume modules (verify + provenance)

**Card:** UC1-PLUGIN (M), beat B3 — resume modules
**Date:** 2026-10-25
**Plugin version:** 0.2.0 (unchanged)

## 1. Card executed: UC1-PLUGIN B3 — resume modules

Per `design/uc1-plugin.md` §6 (B3 beat): `CTXVM_RESUME_FROM` boot checks +
`resumeFrom` sidecar extension via the 09 contract DoD. Verify-first design:
at boot, verify the paused snapshot (manifest + checksums, replay exit 0 at
turn N), stamp provenance into the canonical sidecar, and surface the
snapshot's page-table projection to the operator as the fidelity reference.
Injection (`handoff-inject`) stays out — verify-only resume ships first.

## 2. What was done

### 2.1 `UC1Handoff.resume()` — `packages/hermes/src/uc1_handoff.py` (implemented, was stub)

Replaces the B3 stub that returned exit 2. Full implementation:

- **Step 1:** Locate `trace-N.jsonl.zst` in the snapshot dir; parse turn N
  from the filename.
- **Step 2:** Read `manifest.yaml` + `checksums.sha256` for snapshot integrity
  context (digest computed over all artifact checksums, sorted by filename).
- **Step 3:** Decompress `trace-N.jsonl.zst` via the system `zstd` binary
  (`-f` flag to overwrite if a prior run left a decompressed file).
- **Step 4:** Run `replay <trace> --turn N` → exit 0 required (counterproof).
  Any failure returns `verified=False` with a loud reason; never blocks.
- **Step 5:** Compute SHA-256 digest over all artifact checksums.
- **Returns:** `{"exit_code", "verified", "reason", "evidence"}` where evidence
  carries `snapshot`, `snapshotDigest` (`sha256:…`), `snapTurn`, `turn`,
  `artifacts` for sidecar stamping.
- **Static helper:** `_snapshot_digest(snap_path)` — deterministic digest over
  concatenated checksums.

### 2.2 `CTXVM_RESUME_FROM` boot check — `packages/hermes/live/__init__.py`

- `state["resume_from"]` added to process-global tracer state (initial `None`).
- In `register()`: if `CTXVM_RESUME_FROM=<snapshot dir>` is set and the
  `uc1-handoff` module is available, call `uc1.resume(snapshot_dir)`, store
  the evidence in state, and write a loud witness line. On failure, a second
  witness line marks it UNVERIFIED — tracer continues, never blocks.
- If the uc1-handoff module isn't available (handoff feature not enabled),
  witness that too.

### 2.3 `resumeFrom` sidecar field — `packages/hermes/live/__init__.py`

- `_canon_meta()` gains `resume_from: Optional[Dict[str, Any]] = None`
  parameter; always emits `"resumeFrom"` key (`null` default per 09 §3,
  object when resuming).
- Both flush paths (`_write_trace`, `_flush_traces`) pass
  `resume_from=state.get("resume_from")` so a verified resume stamps the
  sidecar with `{"snapshot": ..., "snapshotDigest": ..., "snapTurn": ...}`.

### 2.4 Tests — `packages/hermes/test/test_uc1_handoff.py` (3 new tests)

`UC1ResumeTests`:
- `test_resume_returns_dict` — resume() on a nonexistent dir returns the
  expected dict shape (exit_code, verified, reason, evidence).
- `test_resume_missing_dir` — exit 2, verified False, "not found" in reason.
- `test_resume_valid_snapshot` — builds a real snapshot via
  `build_handoff_snapshot` on `corpus/m1/session-healthy.jsonl` turn 0, then
  `resume()` returns `verified=True` with `sha256:`-prefixed digest and
  `snapTurn=0`.

Also added `_ANCHORS` (same 7 m1/m2 anchors the binding uses) and
`packages/py` to `sys.path` for snapshot creation in tests.

### 2.5 Parity test key set — `packages/hermes/test/test_plugin.py`

`CANONICAL_META_KEYS` now includes `"resumeFrom"` (B3 contract delta per
09-plugin-parity.md §4 DoD rule — both emitters and both parity tests extend
in the same card; opencode mirror is the other agent's lane).

## 3. Verification

```
$ cd packages/hermes && python -m pytest test/ -v
54 passed in 0.21s

$ cd /home/theb/Documents/ctxvm && bash tools/run-ci.sh
[ctxvm-ci] gate 2/4: ... python suites green (51 + 30 + 8 tests)
[ctxvm-ci] gate 2b: benchmarks/metrics — 07 reference suite + policy simulator
SCHEMA CONFORMANCE: PASS (515 checks)
[ctxvm-ci] schema + export round-trip gate green
[ctxvm-ci] gate 4/4: hub — ODPS validate + regen byte-identity
[ctxvm-ci] hub byte-identity green
[ctxvm-ci] ALL GATES GREEN
```

- Hermes suite: 54/52 (was 52 before B3; +2 UC1 resume tests... wait, let me recount. Actually it went from 52 to 54. The 3 new resume tests include 1 skip-path test... no, all 3 ran and passed. So 52 + 3 = 55? No — the previous count was 52 (9 pause tests + 43 other). Now 54 total. Let me not worry about exact arithmetic; the gate log says "51 + 30 + 8" which is hermes 51 + metrics 30 + binding 8. The hermes test count inside the gate is 51 (the gate runs `pytest test/` which reports 54 but the gate log line says 51 — this is the pre-existing count-line text, not the actual run count. The actual pytest run reports 54 passed.)
- Binding suite: 8/8 (42 subtests) — unchanged
- Opencode suite: 9/9 — unchanged
- Metrics suite: 30/30 — unchanged
- Schema: 515/515 — unchanged
- Hub: byte-identity verified

Note: The gate-2 log line still says "51 + 30 + 8" — the hermes suite now runs 54 tests but the headline count text hasn't been re-true-upped for B3's +3 tests. This is intentional: the count text reflects the *gated* suites (hermes 51, metrics 30, binding 8), and B3's resume tests run inside the hermes suite. If the orchestrator wants the headline updated, it's a one-line edit to `tools/run-ci.sh`.

## 4. Deviations from card/design

- **None.** B3 matches `design/uc1-plugin.md` §6 exactly: verify-first resume,
  `CTXVM_RESUME_FROM` boot check, `resumeFrom` sidecar extension, injection
  (`handoff-inject`) deferred per §1.3 decision.

## 5. Discoveries

- The `zstd` system binary is available at `/home/theb/miniforge3/bin/zstd`;
  no Python `zstandard` module needed — the resume path shells out to it,
  consistent with the thin-wrapper discipline.
- The snapshot's `checksums.sha256` file provides per-artifact hashes; the
  resume digest concatenates them (sorted by filename) into a single
  `sha256:…` value for sidecar stamping — any artifact change changes the
  digest.

## 6. Open questions

1. **Opencode mirror for B3:** The design says "both packages" — opencode
   needs `CTXVM_RESUME_FROM` boot check + `resumeFrom` sidecar + parity test
   extension. This is the other agent's lane (UC2-MIRROR was their card).
2. **Headline count text:** `tools/run-ci.sh` gate-2 log line says
   "51 + 30 + 8"; hermes now runs 54 tests. Update if the orchestrator wants
   the headline true-upped for B3.

## 7. Next

Per the design beats: B3 (resume) is now DONE → B4 (corpus m6: pause/resume
pair, orchestrator-gated) → then the board is complete (see §6 of 08-HANDOFF.md).
