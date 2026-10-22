# CtxVM — Work Reports Index

| Report | Task | One-line summary |
|---|---|---|
| RR-T0-20261022 | T0 | Repo init'd (main@bba1f8f); idempotent `tools/setup-env.sh` builds venvs/odps (py3.14) + venvs/odcs (py3.12, datacontract-cli); both verify green on 1st and 2nd run |
| RR-T1a-20261022 | T1a | BLOCKED-at-DoD: rust/ workspace scaffold written; rustup user-local install removed at user request (global toolchain expected); finish = `cd rust && cargo test` |
| RR-T1a-20261022 (RESOLUTION) | T1a | DONE: user installed global cargo/rustc 1.99.1; `cargo test` 4/4 green; note: non-login shells need `. "$HOME/.cargo/env"` |
| RR-T1b-20261022 | T1b | 9-type event model + strict JSONL codec (allowlist gate; floats/unknown-fields hard errors) + 10-line golden vectors roundtripping byte-identical; 15 tests green, 0 warnings |
| RR-T1c-20261022 | T1c | Playback page-table state machine + deterministic renderer (slots/tallies, verbatim stubs); locked effect-timing + ordering rules; 4 hand-summed scenarios + byte-level determinism property; core README; 24 tests total, 0 warnings |
| RR-T1d-20261022 | T1d | M0 GATE MET: `replay()` static fact-checking (3 divergence kinds) + session-clean/divergent fixtures + `replay` CLI (exit 0/1/2); 28 tests, 0 warnings |
| RR-T4-20261022 | T4 | RFC-0 spec + strict 2020-12 JSON Schema + validator; three-way cross-validation 55/55 PASS (50 vector lines + 5 negative gates); open questions parked for RFC-1 |
| RR-T3-20261022 | T3 | 07's 4 metric formulas as executable reference impl (`benchmarks/metrics/`: pure fns + counterfactual baseline + CLI JSON); 2 replay-consistent schema-valid fixtures (healthy 12 ev / thrashing 41 ev); 18/18 pytest green after correcting plan-phase hand-sums against the fixture (6200 not 7200); fixtures + validator argv = 108/108 schema PASS; venv A gained pytest via setup script |
| RR-T5-20261022 | T5 | SDK-made artifacts prove the hub-as-ODPC-repo claim: odpc-build from staged manifest → hub/catalog.yaml (ODPC v1.0, 1 productReference → ../04-…yaml hub-relative) + hub/index.html; committed; tools/build-hub.sh 4-step chain (source-gate/build/ref-rewrite/revalidate) ran clean twice, byte-identical (sha256 OK); refs+explain+odpc-summary prove ODPC→ODPS link per their SDK |
| RR-T6-20261022 | T6 | design/mcp-shim.md (145/180 lines): callTool decorator; handle = verbatim (v0) / RFC-0 §7 stub (v1); Pichay tool_recall matching on canonical tool+args; resident re-calls = FaultOfResidentPage ledger rows (double-fetch metric, zero new event kinds); 3-flag surface; 24-line pseudocode
