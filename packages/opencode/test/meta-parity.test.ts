/** KIT-1 parity tests — the wire format is shared with packages/hermes.
 * Source of truth: 09-plugin-parity.md §2/§3. Every change lands in the SAME
 * card on BOTH sides, so this file stays a mirror of
 * packages/hermes/test/test_plugin.py::CanonicalSidecarParity. */

import assert from "node:assert/strict";
import { test } from "node:test";

import { createCtxvmPlugin } from "../src/plugin.ts";
import { loadEchoFixture, replayHooks } from "./replay-registry.ts";

/** 09-plugin-parity.md §2: canonical per-type key signature (compare as sets).
 * RFC-0.1 (RR-RFC01E1): session.open gains `schemaVersion` — updated on BOTH
 * sides in the same card, together with the contract doc table (2026-10-31). */
const CANONICAL_EVENT_KEYS: Record<string, string[]> = {
  // R4-ts (RFC-0.1 §R4, D9 policy, RR-TS1-20261031): ts rides on every event of
  // the node-inherited lanes (default ON, CTXVM_TRACE_TS=0 opt-out). Optional.
  "session.open": ["agentId", "budgetTokens", "model", "provider", "schemaVersion", "tokenizerId", "ts", "type"],
  "page.declare": ["page", "ts", "type"],
  "page.fault": ["page", "source", "turn", "ts", "type"],
  "page.render": ["mode", "page", "turn", "ts", "type"],
  "turn.render": ["evictedTokens", "headroom", "residentTokens", "turn", "ts", "type"],
  "call.meta": ["cacheEstimate", "provider", "turn", "ts", "type"],
  // hermes key-signature equality is a per-port assertion: hermes's own ts card
  // (per-lane law D8/D9, RR-W2B1 §R3-note precedent) updates its table then.
};

test("every emitted event type matches the canonical key signature (09-plugin-parity.md §2)", () => {
  const plugin = createCtxvmPlugin({
    agentId: "opencode",
    model: "anthropic/claude-sonnet-4-5",
    provider: "anthropic",
    budgetTokens: 200_000,
  });
  replayHooks(plugin, loadEchoFixture());
  const [record] = plugin.finishAll();
  const events = record.trace.jsonl
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as Record<string, unknown>);
  const exercised = new Set<string>();
  for (const event of events) {
    const type = event.type as string;
    const want = CANONICAL_EVENT_KEYS[type];
    assert.ok(want, `event type outside the canonical table: ${type}`);
    assert.deepEqual(
      Object.keys(event).sort(),
      [...want].sort(),
      `canonical key drift for ${type} — update 09-plugin-parity.md §2 AND the hermes mirror in the same card`,
    );
    exercised.add(type);
  }
  for (const type of Object.keys(CANONICAL_EVENT_KEYS)) {
    assert.ok(
      exercised.has(type),
      `canonical type ${type} not exercised by the live fixture — the table must stay emission-proven`,
    );
  }
});
