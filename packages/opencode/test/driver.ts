/** T9 fixture generator: recorded echo-session hook payloads → xCABI JSONL (committed).
 *  RR-RFC01E1: the committed `opencode-echo.jsonl` is a corpus/m1 drop source
 *  (checksums.sha256) and a sealed-v0 byte artifact — this driver REFUSES to
 *  overwrite it (`--force` overrides). Running this driver after the RFC-0.1
 *  emitter switch would otherwise silently rewrite the fixture as a v0.1 trace
 *  while gate 3 keeps validating it under the sealed v0 schema. */

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createCtxvmPlugin } from "../src/plugin.ts";
import { loadEchoFixture, replayHooks } from "./replay-registry.ts";

const here = dirname(fileURLToPath(import.meta.url));
mkdirSync(join(here, "..", "fixtures"), { recursive: true });

const FROZEN = join(here, "..", "fixtures", "opencode-echo.jsonl");
if (existsSync(FROZEN) && !process.argv.includes("--force")) {
  console.error(
    "opencode-echo.jsonl is a corpus/m1 drop source (checksums.sha256) — " +
      "regenerating would break frozen provenance and the sealed-v0 gate; pass --force to override",
  );
  process.exit(3);
}

const events = loadEchoFixture();
const frozen = JSON.stringify(events); // mirror-contract tripwire: the replay must not mutate payloads

const plugin = createCtxvmPlugin({
  agentId: "opencode",
  model: "anthropic/claude-sonnet-4-5",
  provider: "anthropic",
  budgetTokens: 200_000,
});
replayHooks(plugin, events);

if (JSON.stringify(events) !== frozen) throw new Error("payload mutated during replay — mirror contract violated");

const [record] = plugin.finishAll();
writeFileSync(join(here, "..", "fixtures", "opencode-echo.jsonl"), record.trace.jsonl);
console.log(
  `opencode-echo.jsonl: ${events.length} hook events → ${record.trace.jsonl.split("\n").length - 1} xCABI events · ${record.trace.stats.pages} pages · ${record.trace.stats.turns} turns · ${record.trace.stats.faults} faults`,
);
