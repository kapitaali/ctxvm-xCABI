# RR-UC1-BINDING-20261025 — ctxvm-py binding (UC1-PLUGIN beat B1)

**Card:** UC1-PLUGIN (M), beat B1 — ctxvm-py binding
**Date:** 2026-10-25
**Plugin version:** 0.2.0 (unchanged)

## 1. Card executed: UC1-PLUGIN B1 — ctxvm-py binding

Per `design/uc1-plugin.md` §5 (B1 binding beat): create `packages/py/ctxvm-py`
exposing the committed Rust CLI binaries (replay, profile, diff, export) as a
Python API, with tests that byte-compare binding output vs the Rust CLI on
m1/m2 anchors. Gate 2 gains the binding test.

## 2. What was done

### 2.1 Binding package — `packages/py/` (NEW)

**`packages/py/pyproject.toml`** — setuptools-based package `ctxvm-py` 0.1.0,
console script `ctxvm-py`.

**`packages/py/ctxvm_py/__init__.py`** — public API surface:
`replay()`, `profile()`, `diff()`, `export()`, `build_handoff_snapshot()`.

**`packages/py/ctxvm_py/_cli.py`** — thin subprocess wrapper around the committed
Rust CLI binaries (`rust/target/release/replay`, `profile`, `diff`, `export`).
Binary discovery via `CTXVM_RUST_BIN_DIR` env override, then walking up from the
package to `rust/target/release/`, then PATH fallback. Raises `RuntimeError` on
non-zero exit. All functions return parsed JSON dicts.

**`packages/py/ctxvm_py/__main__.py`** — CLI entry point `ctxvm-py
<replay|profile|diff|export> <trace> [args...]`.

### 2.2 Binding tests — `packages/py/test/test_ctxvm_py.py` (NEW, 8 tests)

`BindingVsRustTests` — byte-compare Python binding vs Rust CLI on all 7 m1/m2
anchors (42 subtests total):
- `test_replay_matches_rust_on_anchors` — `replay()` vs `ctxvm replay`
- `test_replay_turn_matches_rust_on_anchors` — `replay(turn=N)` vs
  `ctxvm replay --turn N`
- `test_profile_matches_rust_on_anchors` — `profile()` vs `ctxvm profile`
- `test_profile_faults_matches_rust_on_anchors` — `profile(events=["page.fault"])`
  vs `ctxvm profile --event page.fault`
- `test_diff_self_matches_rust_on_anchors` — `diff(x, x)` vs `ctxvm diff x x`
- `test_export_matches_rust_on_anchors` — `export()` vs `ctxvm export`
- `test_export_odps_writes_artifacts` — `build_handoff_snapshot()` writes
  `trace-0.jsonl.zst`, `page-table-0.json`, `manifest.yaml`, `llms.txt`,
  `checksums.sha256`
- `test_build_handoff_snapshot_writes_artifacts` — same via `export --odps`

All binding output is byte-identical (JSON-equal) to the Rust CLI on every
anchor.

### 2.3 CI integration

**`tools/run-ci.sh`** — added `( cd packages/py && python -m pytest test/ -q )`
to gate 2; updated gate log line to "python suites green (51 + 27 + 8 tests)".

**`.github/workflows/ci.yml`** — added `@ctxvm/py binding tests` step to gate 2.

## 3. Verification

```
$ cd packages/py && python -m pytest test/ -q
8 passed, 42 subtests passed in 0.26s

$ cd /home/theb/Documents/ctxvm && bash tools/run-ci.sh
[ctxvm-ci] gate 2/4: typescript ... python suites green (51 + 27 + 8 tests)
[ctxvm-ci] gate 2b: benchmarks/metrics — 07 reference suite + policy simulator
SCHEMA CONFORMANCE: PASS (515 checks)
[ctxvm-ci] schema + export round-trip gate green
[ctxvm-ci] gate 4/4: hub — ODPS validate + regen byte-identity
[ctxvm-ci] hub byte-identity green
[ctxvm-ci] ALL GATES GREEN
```

- Hermes suite: 52/52 (unchanged from UC1-PAUSE)
- Opencode suite: 9/9 (unchanged)
- Python binding suite: 8/8 (new, 42 subtests)
- Benchmarks/metrics: 27/27 (unchanged)
- Schema: 515 checks (unchanged; no new event types)
- Hub: byte-identity verified via build-hub.sh self-baseline

## 4. Deviations from card/design

- **Binding implementation:** The design anticipated a PyO3/maturin binding
  (`packages/py/` with maturin build). maturin is not installed and the
  environment constraints prohibit self-installing toolchains. Per the design's
  explicit fallback discipline ("until the binding lands, the modules shell the
  committed rust binaries"), `ctxvm_py` is a pure-Python subprocess wrapper
  around the Rust CLI binaries. The Python API is stable; when maturin is
  available, the shell-out can be replaced by native FFI calls with no API
  change. Open question #2 from the design (CI surface for maturin) remains
  open — the binding test runs against the prebuilt `rust/target/release/`
  binaries, which gate 1 already builds.

## 5. Discoveries

- The Rust `export` CLI requires `--output DIR` (refuses to write into the
  working directory). The Python `export()` wrapper mirrors this — callers must
  pass `output_dir`, or use `build_handoff_snapshot()` which manages the
  output directory.
- The export report JSON uses `dq.replayDeterminism` (camelCase) not
  `replay_determinism` (snake_case), and artifact filenames include the turn
  number (`trace-0.jsonl.zst`, not `trace-N.jsonl.zst`). Tests assert against
  the actual CLI output.

## 6. Open questions (from design, unchanged)

1. `handoff-inject` stays OUT of the first implementation beats (verify-only
   resume first) — confirm.
2. ctxvm-py binding needs maturin/venv wiring in gate 2 — **kept off-gate for
   now** (binding runs against prebuilt Rust binaries; maturin/venv wiring can
   be added when the real PyO3 binding replaces this shell-out wrapper).
3. opencode has no command surface — witness-only pause acceptable for v0
   (hermes keeps `/ctxvm-handoff` slash).

## 7. Next

Per the design beats: B1 (binding) is now DONE → B3 (resume modules:
`CTXVM_RESUME_FROM` boot checks + `resumeFrom` sidecar extension via the 09
contract DoD) → B4 (corpus m6 drop, orchestrator-gated).
