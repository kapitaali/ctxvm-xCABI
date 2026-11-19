# RR-HARNESSVER-20261119 — the harnessVersion metadata gap, fixed (sidecar-only)

Lane: hermes. Production plugin change, **sidecar-only — no wire field, no five-touchpoint card, no
RFC change**. Version **0.13.27 → 0.13.28**, synced; **gateway restart owed to the operator** (not
performed here). No model call, no spend, no push.

## 1. The defect and its root cause

`RR-H12DIAG-REVIEW:18,45` recorded `harnessVersion: null` on the 0.13.27 diagnostic capture as a
metadata gap. Root cause: both sidecar writers read only `os.environ.get("CTXVM_HERMES_VERSION")`
(`_canon_meta` and the coverage manifest's `plugin` block), and **the gateway does not export that
variable** (confirmed: `/proc/4486/environ` carries no `CTXVM_HERMES_VERSION`). So every live capture
carried null. The frozen m6/m7 corpus shows the field *was* populated when the env was set — the
channel works; it is simply unset in the gateway.

## 2. The fix

New helper `_harness_version()` in `live/__init__.py`, wired into both call sites:

1. `CTXVM_HERMES_VERSION` env override (preserves the existing parity channel and the `9.9.9` test),
2. else `importlib.metadata.version("hermes-agent")` — the host's own installed distribution,
3. else `None`. Fail-open (law 5): any error resolves to None, never raises into a turn.

**Source probed, not guessed:** `hermes_constants` exposes no public version getter (only private
`_run_version_probe`/`_version_probe_ok` helpers for locating the CLI binary); `hermes_cli` has no
`__version__`. `importlib.metadata.version("hermes-agent")` returns **0.21.5** on this host and is the
stable, truthful source. The value is the installed distribution version, not the CLI banner string.

## 3. Test correction (recorded, not a relaxation)

`test_plugin.py::test_instrumentation_and_sidecar_identities_are_lane_fixed` asserted
`assertIsNone(manifest["plugin"]["harnessVersion"])` — it **pinned the defect** as if null were a
lane-fixed identity. harnessVersion is host-resolved, not lane-fixed. The assertion now compares the
sidecar value to `_harness_version()` (hermetic: both sides use the same resolver in the same
environment), with a comment naming the correction. This is a deliberate fix of a test that asserted
the bug, not a weakening to force a pass.

## 4. New tests + red-before

`test_capture_smoke.py::HarnessVersionResolutionTests` (2 tests):
- `test_unset_env_resolves_the_installed_host_version` — env unset, `importlib.metadata.version`
  mocked to a `7.7.7-host` sentinel; both meta and coverage sidecars must carry it. **Red-before:**
  `AssertionError: None != '7.7.7-host'` (the old code read only the env). Green after the fix.
- `test_env_override_still_wins_over_the_host_distribution` — env `9.9.9` beats the mocked host
  distribution (regression guard for the override precedence).

## 5. Blast radius checked — no cascade

- **No fixture regen:** committed hermes fixtures are wire-only `.jsonl`; `pluginVersion`/
  `harnessVersion` live in sidecars, not the trace. `generate_traces.py` writes only `.jsonl`.
- **Frozen corpus untouched** (law 5); m6/m7 already carry non-null values.
- `tools/coverage_check.py:353–355` accepts `harnessVersion` as **string or null** — a populated
  string stays valid.
- The only other `harnessVersion` assertion (`test_plugin.py:1843`, env `9.9.9`) still passes.

## 6. Version, sync, restart

- `PLUGIN_VERSION` and `plugin.yaml` both **0.13.28** (gate version-guard agrees).
- `bash tools/sync-plugin.sh` → 2 files copied, repo/installed/manifest all 0.13.28, installed-set
  load check OK. `ctxvm.py` still excluded by the import-derived set (owner ruling `RR-DEFAULTS`).
- **Gateway stale:** pid 4486 (started 11:13) holds 0.13.27. Captures taken before the operator
  restarts are still labelled 0.13.27 with null harnessVersion. The restart is the operator's call
  (`handoff/LANES.md` §"The gateway"); it was **not** performed here.

## 7. Verification

- `python3 -m pytest packages/hermes -q` (root, `CTXVM_*` cleared) → **228 passed, 15 subtests**.
- `(cd packages/hermes && python -m pytest test/ -q)` (gated path) → **228 passed, 15 subtests**.
- `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared → **rc=0 ALL GATES GREEN** (ts 24+62+46+14;
  python **228**+8+66; schema 682; export round-trip + hub byte-identity green).
- `bash tools/sync-plugin.sh` → OK, versions agree, load check passes.
- `bash tools/check-handoff.sh` → ALL PASS; `bash tools/git-hygiene.sh` → OK (at close).

## 8. Repro

```
python3 -m pytest packages/hermes/test/test_capture_smoke.py -q -k HarnessVersion
python3 -m pytest packages/hermes -q
bash tools/run-ci.sh && bash tools/sync-plugin.sh --check
```

## 9. Open

- Review-lane verification + recording of this card.
- **Operator gateway restart** to put 0.13.28 live; until then captures stay 0.13.27/null.


---

**Superseded (2026-11-19, live verification):** the `importlib.metadata` source in §2 is absent in
the gateway's git source install, so 0.13.28 did not populate harnessVersion live. The corrected
canonical resolver and version 0.13.29 are recorded in `reports/RR-HVREV-20261119.md`.
