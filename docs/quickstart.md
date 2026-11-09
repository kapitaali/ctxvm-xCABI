# Quickstart — install, wrap, profile (clone-and-build today)

Nothing is published yet (npm / crates.io / PyPI are all pending the owner gate).
Today's install is a **clone plus a Rust build**. Full packaging audit: `design/packaging.md`, `reports/RR-PKG-20261109.md`.

## 1. Build the Rust core (32 seconds on one machine; run from repo root)

There is **no `Cargo.toml` at the repo root** — the workspace lives in `rust/`.

```sh
git clone https://github.com/kapitaali/ctxvm-xCABI.git
cd ctxvm-xCABI
cargo build --release   # if this fails, you are at the root; use rust/'s workspace below
```

If the command above errors with "could not find Cargo.toml", you are at the root:

```sh
cd rust
cargo build --release   # 6 binaries: replay, profile, diff, export, tokens, stream
cd ..
```

Verified 2026-11-09 from a fresh clone: `cargo build --release` (release profile) exits 0 in ~32 s on x86_64 Linux.

## 2. Replay a demo trace (each step echoes "exit 0 = ok")

```sh
./rust/target/release/replay corpus/m1/session-thrashing.jsonl   # exit 0 = no replay divergence
./rust/target/release/profile corpus/m1/session-thrashing.jsonl  # per-page/turn profile
./rust/target/release/stream ~/.local/state/ctxvm/traces          # sessions grouped by environment
```

If step 2 says "no such file", you are `rust/` — `cd ..` and retry.

## 3. Wrap one agent (nothing captured unless a trace dir is set)

OpenCode — add a shim `<project>/.opencode/plugins/ctxvm.ts`:

```ts
export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts";
```

```sh
CTXVM_TRACE_DIR=/tmp/ctxvm-capture CTXVM_TRACE_NAME=demo \
CTXVM_MODEL=<provider/model> CTXVM_PROVIDER=<provider> \
opencode run --standalone --auto -m <provider/model> "your task"
```

Hermes — copy `packages/hermes/live/` to `~/.hermes/plugins/ctxvm-tracer/`, enable, then:

```
/ctxvm-trace start /tmp/ctxvm-capture demo
... run your task ...
/ctxvm-trace stop
```

## 4. Profile the result

```sh
./rust/target/release/profile /tmp/ctxvm-capture/demo.jsonl
```

If the trace exists but looks empty, the run did not exit gracefully — the flush happens at process exit (`packages/opencode/live/README.md`, `packages/hermes/live/README.md`).

## Fail points this quickstart hit (and fixed in the doc)

1. **Root has no `Cargo.toml`** — `cargo build` at the root errors. The build command is `cd rust && cargo build --release` (README's one-liner omits it).
2. **Token counting** — the default (non-`tiktoken`) build only knows `apx4-char`. `tokens --tokenizer tiktoken-o200k_base` needs a rebuild: `cargo build --release --features tiktoken -p ctxvm-conformance -p ctxvm-tokenizer` (or accept `apx4-char`).

## Edge notes

- `cargo install --path rust/crates/ctxvm-conformance` puts all six binaries on `PATH` (use once built).
- Every number above is from the clean run in `reports/RR-PKG-20261109.md` §6; no registry was contacted for the build.
