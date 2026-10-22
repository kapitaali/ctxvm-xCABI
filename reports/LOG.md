# CtxVM — Work Reports Index

| Report | Task | One-line summary |
|---|---|---|
| RR-T0-20261022 | T0 | Repo init'd (main@bba1f8f); idempotent `tools/setup-env.sh` builds venvs/odps (py3.14) + venvs/odcs (py3.12, datacontract-cli); both verify green on 1st and 2nd run |
| RR-T1a-20261022 | T1a | BLOCKED-at-DoD: rust/ workspace scaffold written; rustup user-local install removed at user request (global toolchain expected); finish = `cd rust && cargo test` |
| RR-T1a-20261022 (RESOLUTION) | T1a | DONE: user installed global cargo/rustc 1.99.1; `cargo test` 4/4 green; note: non-login shells need `. "$HOME/.cargo/env"` |
| RR-T1b-20261022 | T1b | 9-type event model + strict JSONL codec (allowlist gate; floats/unknown-fields hard errors) + 10-line golden vectors roundtripping byte-identical; 15 tests green, 0 warnings |
