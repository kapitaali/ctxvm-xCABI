# `@ctxvm/node` — xCABI tracer

Telemetry-first tracer for agent loops. Emits **RFC-0 xCABI JSONL** from page
materialization, recall marks, turn rendering, output scanning, pinning, and
passive stub facts. Mirror mode remains the default: the tracer never selects or
rewrites caller content. `stub()` records a replacement that the harness already
decided, emitting the required `page.evict` + `page.render(mode="stub")` pair.

Zero runtime dependencies. Requires **Node ≥ 22.6**. TypeScript sources run
directly in-repo via type stripping; published packages ship compiled `dist/`.

## Build

```sh
npm i
npm run build
npm pack --dry-run
bash ../../tools/check-node-build.sh
npm test
```

`tools/check-node-build.sh` compares source and built output byte-for-byte under
`CTXVM_TRACE_TS=0`.

## Quick start

```ts
import { createTrace } from "./src/index.ts";

const vm = createTrace({
  agentId: "opencode", model: "openai/gpt-5", provider: "openai", budgetTokens: 120_000,
});

vm.page({ tool: "read_file", args: { path: "src/auth.ts" }, content: "…" });
vm.render();
vm.recall({ tool: "read_file", args: { path: "src/auth.ts" } });
vm.page({ tool: "read_file", args: { path: "src/auth.ts" }, content: "…" });
vm.scan({ text: modelOutputText });
vm.finish();
```

## Passive stub API

```ts
const original = vm.page({ ref: "tool:read_file({\"path\":\"a.ts\"})", content: "full body" });
vm.render();
vm.stub({
  ref: original.logicalRef,
  contentHash: original.contentHash,
  stubText: "[ctxvm: dropped result for read_file({\"path\":\"a.ts\"}); re-run to restore.]",
});
```

`stub()` returns `false` without emitting either row when the PageId is unknown,
the text is empty/not a string, or the turn is invalid. `contentHash` is optional
for compatibility; adapters with durable provenance should pass it to select the
exact historical PageId. Both rows use the same explicit/current turn and `ts`
rides last. A full re-fetch after a stub restores full mode from the next turn.

Turn facts are derived from the effective schedule: pages stubbed at turn `t` are
excluded from `residentTokens` at `t` and later until restored. Mirror-only output
is unchanged.

## Identity and timing

- Page identity is `(logicalRef, contentHash)`; a fresh hash is a new PageId.
- `page.evict@t` means stub visible at `t`; `page.fault@t` restores full at `t+1`.
- `finish()` is idempotent: live events are pushed once; turn/meta tails are
  re-derived without duplication.

## Gates

```sh
npm test
npm run validate
npm run replay
```

The validator/replay commands use the repository's sealed fixtures. Passive stub
traces must also pass the adapter-aware coverage checker when a sidecar is present.
