/**
 * T24 — handoff-inject (library lane): assemble the resume brief from a
 * verified handoff package. The design's gated control beat
 * (`design/uc1-plugin.md` §1.3(3), §3 "Injection (opt-in, later)") resolved
 * as INJECTION-AS-DATA (§7 ruling 2026-10-28): the capture hands the app the
 * assembled context material and the app prepends it to its own message
 * history — the middleware stays a byte-mirror in every case (design risk 5's
 * mutability temptation guarded; the design-letter mutation of
 * `params.prompt` is recorded as the v-next control shape, not built).
 *
 * Content-blindness law honored: `page.render` events carry references, not
 * text (the tracer meters decisions — RFC-0), so FULL-page materialization
 * uses the app-supplied `materialize` resolver; the library NEVER invents
 * content. STUBS are package-complete: `page.evict` carries `stubText` — the
 * exact text the model was told at eviction — and need no resolver. An
 * unresolvable slot degrades LOUDLY (explicit unresolved marker in the
 * brief); resolver results and a THROWING resolver both degrade the same way
 * — the brief is data, it must not break boot. Structural package problems
 * (missing table/slice) throw at init (loud, consistent with the T22 boot
 * law).
 *
 * Brief layout mirrors the m7 session-b manual recipe (llms.txt-led): the
 * operator rebuilt context from the 5 package artifacts by hand; this
 * automates exactly that assembly.
 */

import { spawnSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { snapshotDigest } from "./uc1-handoff.ts";

/** A page-table slot, normalized for the app-supplied resolver. */
export interface ResumeSlot {
  logicalRef: string;
  contentHash: string;
  kind: string;
  tokens: number;
  mode: "full" | "stub";
  pinned: boolean;
}

/**
 * App-supplied content resolver: return the CURRENT text for a full slot, or
 * null when unresolvable (the slot then degrades to a loud unresolved marker
 * inside the brief). Content ownership stays with the app — the library
 * orchestrates the assembly (T22 law: the module only orchestrates).
 */
export type MaterializeFn = (slot: ResumeSlot) => string | null;

/** The assembled brief: the TEXT the app prepends, plus the projection
 * counts for the witness line. */
export interface ResumeBrief {
  text: string;
  turn: number;
  slots: number;
  full: number;
  stub: number;
}

function isFile(path: string): boolean {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

/** The package's slice turn — same glob law as `resumeVerify` (sorted first
 * `trace-*.jsonl.zst`, turn from the second dash segment). */
function sliceTurn(dir: string): number {
  const zstFiles = readdirSync(dir)
    .filter((name) => /^trace-.*\.jsonl\.zst$/.test(name))
    .sort();
  if (zstFiles.length === 0) {
    throw new Error(`resumeBrief: no trace-*.jsonl.zst in ${dir}`);
  }
  const stem = zstFiles[0]!.replace(/\.zst$/, "");
  const segment = stem.split("-")[1]?.split(".")[0] ?? "";
  if (!/^[0-9]+$/.test(segment)) {
    throw new Error(`resumeBrief: cannot parse turn from ${zstFiles[0]}`);
  }
  return parseInt(segment, 10);
}

/** The decompressed slice: `resumeVerify` writes `trace-N.jsonl` into the
 * package at verified boot, so it is normally already there; the zstd
 * fallback keeps this function usable standalone (same placement law —
 * decompress INSIDE the snapshot dir). */
function loadSlice(dir: string, turn: number): string {
  const plain = join(dir, `trace-${turn}.jsonl`);
  if (isFile(plain)) return readFileSync(plain, "utf8");
  const decomp = spawnSync(
    "zstd",
    ["-d", join(dir, `trace-${turn}.jsonl.zst`), "-o", plain, "-f"],
    { encoding: "utf8" },
  );
  if (decomp.status !== 0) {
    throw new Error(
      `resumeBrief: zstd decompress failed: ${(decomp.stderr ?? "").trim()}`,
    );
  }
  return readFileSync(plain, "utf8");
}

function unresolvedMarker(logicalRef: string): string {
  return `[unresolved: ${logicalRef} — content not provided]`;
}

/**
 * Assemble the resume brief from the package in `dir`. Structural problems
 * (no slice, missing/unshaped page-table) throw — the caller runs this at
 * init AFTER a verified boot, so a throw there is a loud internal
 * inconsistency, not a silent degrade. Resolver results (and a throwing
 * resolver) degrade to markers inside the text — never thrown.
 */
export function assembleResumeBrief(
  dir: string,
  materialize?: MaterializeFn,
): ResumeBrief {
  const turn = sliceTurn(dir);
  const tablePath = join(dir, `page-table-${turn}.json`);
  if (!isFile(tablePath)) {
    throw new Error(`resumeBrief: page-table-${turn}.json missing: ${dir}`);
  }
  const table = JSON.parse(readFileSync(tablePath, "utf8")) as {
    slots?: Array<{
      reference?: {
        id?: { logicalRef?: string; contentHash?: string };
        kind?: string;
        tokens?: number;
      };
      mode?: string;
      pinned?: boolean;
    }>;
    tally?: unknown;
    violations?: unknown;
  };
  if (!Array.isArray(table.slots)) {
    throw new Error(`resumeBrief: page-table-${turn}.json has no slots array`);
  }

  // Stub texts: the slice's page.evict rows keyed by logicalRef (file order —
  // the LAST eviction before turn N is the current stub for a stub slot).
  const stubs = new Map<string, string>();
  for (const line of loadSlice(dir, turn).split("\n")) {
    if (!line.trim()) continue;
    let event: Record<string, unknown>;
    try {
      event = JSON.parse(line) as Record<string, unknown>;
    } catch {
      continue; // blank/malformed rows skip — the digest parser's split law
    }
    if (event.type !== "page.evict") continue;
    const page = event.page as { logicalRef?: string } | undefined;
    if (page?.logicalRef && typeof event.stubText === "string") {
      stubs.set(page.logicalRef, event.stubText);
    }
  }

  const slots: ResumeSlot[] = table.slots.map((slot) => ({
    logicalRef: slot.reference?.id?.logicalRef ?? "<no-logical-ref>",
    contentHash: slot.reference?.id?.contentHash ?? "<no-content-hash>",
    kind: slot.reference?.kind ?? "unknown",
    tokens: slot.reference?.tokens ?? 0,
    mode: slot.mode === "stub" ? "stub" : "full",
    pinned: slot.pinned === true,
  }));
  const full = slots.filter((slot) => slot.mode === "full");
  const stubbed = slots.filter((slot) => slot.mode === "stub");
  const digest = snapshotDigest(dir);

  const lines: string[] = [];
  lines.push(`# ctxvm resume brief — turn ${turn}`);
  lines.push("");
  lines.push(
    `Assembled from the verified handoff snapshot ${dir} (digest ${digest}, replay exit 0 at turn ${turn}).`,
  );
  lines.push(
    "Resident pages are materialized full; stubbed pages carry the slice's re-materialization instructions (what the model was told at eviction).",
  );
  lines.push("");
  lines.push(`## Resident pages (${full.length})`);
  if (full.length === 0) lines.push("(none)");
  for (const slot of full) {
    lines.push("");
    lines.push(
      `- ${slot.logicalRef} (${slot.kind}, ${slot.tokens} tok, ${slot.contentHash}${slot.pinned ? ", pinned" : ""}):`,
    );
    let text: string | null = null;
    if (materialize) {
      try {
        text = materialize(slot);
      } catch {
        text = null; // a throwing resolver degrades the same as null
      }
    }
    if (typeof text === "string" && text.length > 0) {
      lines.push(...text.split("\n").map((l) => `  ${l}`));
    } else {
      lines.push(`  ${unresolvedMarker(slot.logicalRef)}`);
    }
  }
  lines.push("");
  lines.push(`## Stubbed pages (${stubbed.length})`);
  if (stubbed.length === 0) lines.push("(none)");
  for (const slot of stubbed) {
    lines.push("");
    lines.push(`- ${slot.logicalRef} (${slot.kind}, ${slot.tokens} tok):`);
    const stub = stubs.get(slot.logicalRef);
    const body = stub ?? `[no stub text found in slice for ${slot.logicalRef}]`;
    lines.push(...body.split("\n").map((l) => `  ${l}`));
  }
  lines.push("");
  lines.push("## Projection");
  lines.push(`- slots: ${slots.length} (${full.length} full, ${stubbed.length} stub)`);
  if (table.tally !== undefined) {
    lines.push(`- tally: ${JSON.stringify(table.tally)}`);
  }
  if (Array.isArray(table.violations) && table.violations.length > 0) {
    lines.push(`- violations: ${JSON.stringify(table.violations)}`);
  }
  lines.push("");

  return { text: lines.join("\n"), turn, slots: slots.length, full: full.length, stub: stubbed.length };
}
