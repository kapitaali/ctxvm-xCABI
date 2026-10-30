# W5 Hermes capture (interactive TUI — the task text is the script)

1. Boot Hermes with the capture env. Direct boots export it; gateway users set it
   per the corpus/m7 recipe (`systemctl --user set-environment CTXVM_*…` + restart —
   `corpus/m7/README.md` carries the exact sequence and the flush-semantics caveats).

   ```
   CTXVM_FEATURES=trace \
   CTXVM_TRACE_DIR=/tmp/ctxvm-w5 \
   CTXVM_TRACE_NAME=w5-hermes \
   CTXVM_RUST_BIN_DIR=<repo>/rust/target/release \
   CTXVM_AGENT_ID=hermes \
   CTXVM_BUDGET_TOKENS=120000 \
   CTXVM_MODEL=<provider/model> CTXVM_PROVIDER=<provider> \
   CTXVM_HERMES_VERSION="$(hermes --version | head -1)" hermes
   ```

2. In the fresh session, start the tracer:

   ```
   /ctxvm-trace start /tmp/ctxvm-w5 w5-hermes
   ```

3. Paste `task.md` verbatim (the file next to this recipe). Let the task finish.

4. Stop and flush:

   ```
   /ctxvm-trace stop
   ```

The capture lands at `/tmp/ctxvm-w5/w5-hermes.jsonl` (+ `.meta.json` sidecar).
Single-session discipline: one session per capture name; each flush overwrites
`<name>.jsonl` (era snapshots only exist in the pause/resume flow, which W5 does not
use). Full plugin recipes: `packages/hermes/live/README.md`.
