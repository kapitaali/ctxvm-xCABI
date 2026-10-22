# CtxVM — Work Reports Index

| Report | Task | One-line summary |
|---|---|---|
| RR-T0-20261022 | T0 | Repo init'd (main@bba1f8f); idempotent `tools/setup-env.sh` builds venvs/odps (py3.14) + venvs/odcs (py3.12, datacontract-cli); both verify green on 1st and 2nd run |
| RR-T1a-20261022 | T1a | BLOCKED-at-DoD: rust/ workspace scaffold written; rustup user-local install removed at user request (global toolchain expected); finish = `cd rust && cargo test` |
| RR-T1a-20261022 (RESOLUTION) | T1a | DONE: user installed global cargo/rustc 1.99.1; `cargo test` 4/4 green; note: non-login shells need `. "$HOME/.cargo/env"` |
| RR-T1b-20261022 | T1b | 9-type event model + strict JSONL codec (allowlist gate; floats/unknown-fields hard errors) + 10-line golden vectors roundtripping byte-identical; 15 tests green, 0 warnings |
| RR-T1c-20261022 | T1c | Playback page-table state machine + deterministic renderer (slots/tallies, verbatim stubs); locked effect-timing + ordering rules; 4 hand-summed scenarios + byte-level determinism property; core README; 24 tests total, 0 warnings |
| RR-T1d-20261022 | T1d | M0 GATE MET: `replay()` static fact-checking (3 divergence kinds) + session-clean/divergent fixtures + `replay` CLI (exit 0/1/2); 28 tests, 0 warnings |
