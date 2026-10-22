/**
 * Generates the two committed fixture traces (T8 DoD):
 *
 *   fixtures/tracer-healthy.jsonl  — mirror of the benchmarks/metrics healthy flow
 *   fixtures/tracer-recall.jsonl   — double fetch · identifier scan · fresh fetch · pins
 *
 * Run from `packages/node`:  npm run gen  →  npm run validate  →  npm run replay
 * (both gates are repo-root tools: 108-check validator, `cargo replay` exit-0 gate).
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createTrace } from "../src/tracer.ts";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, "..", "fixtures");
mkdirSync(outDir, { recursive: true });

function emit(name: string, jsonl: string, stats: Record<string, number>): void {
  writeFileSync(join(outDir, name), jsonl);
  console.log(
    `${name}: ${jsonl.split("\n").length - 1} events · ${stats.pages} pages · ${stats.turns} turns · ${stats.faults} faults · resident ${stats.residentTokens} tok`,
  );
}

// ── scenario 1 — healthy flow (all pages declared pre-turn; one scanned touch) ──
{
  const vm = createTrace({
    agentId: "healthy-demo",
    model: "openai/gpt-5",
    provider: "openai",
    budgetTokens: 120_000,
  });
  vm.page({ ref: "file:src/auth.ts", kind: "file", content: "export const SESSION_TTL_MS = 30 * 60 * 1000;\n" });
  vm.page({
    tool: "read_file",
    args: { path: "src/auth/session.ts" },
    content: "SESSION = configured\nprovider = integration-test\n",
  });
  vm.page({ ref: "summary:t0", kind: "summary", content: "turn 0: session middleware verified\n" });
  vm.render();
  vm.render();
  vm.render();
  vm.scan({ text: "opening src/auth/session.ts to verify the change", latencyMs: 12 });
  vm.render({ latencyMs: 1_240 });
  const result = vm.finish();
  emit("tracer-healthy.jsonl", result.jsonl, result.stats);
}

// ── scenario 2 — waste ledger: double fetch, scan touch, fresh fetch, pins ──
{
  const vm = createTrace({
    agentId: "recall-demo",
    model: "openai/gpt-5",
    provider: "openai",
    budgetTokens: 80_000,
  });
  const sessionAuth = "SESSION middleware: redis-backed, TTL 30m, rotation on login\n";
  const freshSessionAuth = "SESSION middleware: redis-backed, TTL 45m, rotation on login\nversion bumped\n";
  vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: sessionAuth });
  vm.page({ ref: "file:src/db/schema.sql", kind: "file", content: "CREATE TABLE sessions (id uuid, user_id uuid);\n" });
  vm.render(); // turn 0: both pages revealed full

  // double fetch — identical args re-call lands on the resident page
  vm.recall({ tool: "read_file", args: { path: "src/auth/session.ts" } });
  vm.page({ tool: "read_file", args: { path: "src/auth/session.ts" }, content: sessionAuth }); // → page.fault(tool_recall)@0
  vm.render({ latencyMs: 860 }); // turn 1: no composition change

  vm.scan({ text: "checked src/auth/session.ts — the 30m TTL is applied", latencyMs: 9 }); // → page.fault(identifier_scan)@1
  vm.render(); // turn 2

  // fresh fetch — the underlying resource changed ⇒ new page identity, never scored as waste
  vm.recall({ tool: "read_file", args: { path: "src/auth/session.ts" } });
  vm.page({
    tool: "read_file",
    args: { path: "src/auth/session.ts" },
    content: freshSessionAuth,
  }); // → page.declare (hash-v2), no fault
  vm.render({ latencyMs: 990 }); // turn 3: v2 revealed full

  vm.pin({ ref: "file:src/db/schema.sql", reason: "explicit_api: hot loop" });
  vm.unpin({ ref: "file:src/db/schema.sql", reason: "explicit_api: cooled" });

  const result = vm.finish();
  emit("tracer-recall.jsonl", result.jsonl, result.stats);
}
