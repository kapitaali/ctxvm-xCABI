/**
 * `@ctxvm/node` — telemetry-first tracer for agent loops (RFC-0 xCABI JSONL).
 *
 * Public surface v0 (the T6/T7 contract, mirroring `design/mcp-shim.md` §2–§4 and
 * `design/adapters.md`):
 *
 *   const vm = createTrace({ agentId, model, provider, budgetTokens })
 *   vm.page({ tool, args, content })        // tool result materializes → page
 *   vm.recall({ tool, args })               // pre-execution re-call mark (tool_recall)
 *   vm.render({ latencyMs })                // turn boundary; reveals + turn.render + call.meta
 *   vm.scan({ text })                       // identifier_scan over model output
 *   vm.finish()                             // → RFC-0 JSONL + stats
 *
 * T6/T7 design sketches referred to these as `page_raw`/`observe_recall`/`scan_text`;
 * the shipped names are the canonical ones (surfacing aliases is an adapter concern, not API).
 */

export {
  approx4,
  canonicalJson,
  contentHash,
  createTrace,
  fileRef,
  imageRef,
  inferKind,
  summaryRef,
  toolRef,
} from "./tracer.ts";

export type {
  FinishedTrace,
  FaultSource,
  PageKind,
  PageInput,
  PinInput,
  RecallInput,
  RenderInput,
  ScanInput,
  TraceInit,
  Tracer,
} from "./tracer.ts";

export type { Json } from "./ident.ts";
