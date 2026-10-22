/** Spike replay-registry: applies recorded hook payloads to the T9 adapter (dev-build stand-in). */

import { readFileSync } from "node:fs";

import type { CtxvmPlugin } from "../src/plugin.ts";
import type { HookEvent } from "../src/opencode-contract.ts";

export function replayHooks(plugin: CtxvmPlugin, events: readonly HookEvent[]): void {
  for (const event of events) {
    if (event.hook === "session.context") plugin.onSessionContext(event.payload);
    else if (event.hook === "tool.execute.before") plugin.onToolExecuteBefore(event.payload);
    else plugin.onToolExecuteAfter(event.payload);
  }
}

/** Chronological recorded hook payload fixture (see fixtures/hook-payloads/README inside the RR). */
export function loadEchoFixture(): HookEvent[] {
  return JSON.parse(
    readFileSync(new URL("../fixtures/hook-payloads/echo-session.json", import.meta.url), "utf-8"),
  ) as HookEvent[];
}
