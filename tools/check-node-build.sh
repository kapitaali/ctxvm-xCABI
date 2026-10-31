#!/usr/bin/env bash
# Build-parity gate for @ctxvm/node (W10 node build).
#
# The repo ships SOURCE (Node type-strips the .ts files); the published tarball must ship
# compiled JS because Node refuses TypeScript under node_modules. Two artefacts must
# therefore stay behaviourally identical, and nothing else proves it: the type-stripped
# sources and the emitted dist/. This script builds and compares them on a full trace plus
# the identity helpers, with the D9 ts opt-out for byte stability.
#
# Usage: bash tools/check-node-build.sh   (requires `npm i` inside packages/node once)
set -euo pipefail
cd "$(dirname "$0")/.."
cd packages/node

[ -d node_modules ] || { echo "check-node-build: run 'npm i' in packages/node first" >&2; exit 2; }

npm run build --silent
CTXVM_TRACE_TS=0 node --input-type=module -e '
import assert from "node:assert/strict";

const INIT = { agentId: "opencode", model: "openai/gpt-5", provider: "openai", budgetTokens: 120000 };
function run(createTrace) {
  const vm = createTrace(INIT);
  vm.page({ ref: "file:src/auth.ts", kind: "file", content: "export const S = 1;\n" });
  vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: "SESSION = configured\n" });
  vm.page({ ref: "summary:t0", kind: "summary", content: "turn-0 micro-summary" });
  vm.render();
  vm.render();
  vm.render();
  vm.scan({ text: "opening src/auth/session.ts to verify the change", latencyMs: 12 });
  vm.render({ latencyMs: 1240 });
  return vm.finish().jsonl;
}
const src = await import("./src/index.ts");
const dist = await import("./dist/index.js");
const a = run(src.createTrace);
const b = run(dist.createTrace);
assert.equal(b, a, "dist output differs from src output");
for (const v of [{ b: 1, a: [1, { z: null, y: "x" }] }, "plain", 3, true, null]) {
  assert.equal(dist.canonicalJson(v), src.canonicalJson(v), "canonicalJson diverged");
}
assert.equal(dist.contentHash("hello world"), src.contentHash("hello world"), "contentHash diverged");
console.log(`check-node-build: OK — ${b.trim().split("\n").length} events byte-identical, dist imports resolve without type stripping`);
'
