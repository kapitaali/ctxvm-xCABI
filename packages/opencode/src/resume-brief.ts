/**
 * T25 — handoff-inject (per-harness beat, opencode lane): assemble the resume
 * brief from a verified handoff package. LINE-FOR-LINES MIRROR of
 * `packages/ai-sdk/src/resume-brief.ts` (T24) with ONE §7-ruled delta:
 * RESOLVER-LESS v0 (ruling 2026-10-28) — the plugin lane has no app-supplied
 * content source, so FULL slots always degrade to the loud unresolved marker
 * while STUBS stay package-complete (`page.evict` `stubText`). The opencode
 * module law (imports `../../node/src/index.ts` only) makes the ai-sdk module
 * unreachable — hence this mirror importing the opencode `uc1-handoff.ts`.
 *
 * Content-blindness law honored: `page.render` events carry references, not
 * text (the tracer meters decisions — RFC-0), so the brief never invents
 * content. Structural package problems (missing table/slice) THROW from here
 * — the live adapter catches them at arm time (the never-breaks-capture law
 * lives there; a verified boot already fail-closed every reachable shape, so
 * the catch is defense-in-depth).
 *
 * Brief layout mirrors the m7 session-b manual recipe (llms.txt-led): the
 * operator rebuilt context from the 5 package artifacts by hand; this
 * automates exactly that assembly.
 */

import { spawnSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { snapshotDigest } from "./uc1-handoff.ts";

/** A page-table slot, normalized for the brief. */
export interface ResumeSlot {
  logicalRef: string;
  contentHash: string;
  kind: string;
  tokens: number;
  mode: "full" | "stub";
  pinned: boolean;
}

/** The assembled brief: the TEXT the plugin prepends, plus the projection
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
 * Assemble the resume brief from the package in `dir` (resolver-less v0 —
 * §7 ruling: the plugin lane has no app-supplied content source). Structural
 * problems (no slice, missing/unshaped page-table) throw — the caller runs
 * this at arm time AFTER a verified boot, behind a catch that disarms loudly
 * (never-breaks-capture).
 */
export function assembleResumeBrief(dir: string): ResumeBrief {
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
    "Resident pages are listed with their identity (content is not carried by the package — fetch from your own store as the operator recipe did); stubbed pages carry the slice's re-materialization instructions (what the model was told at eviction).",
  );
  lines.push("");
  lines.push(`## Resident pages (${full.length})`);
  if (full.length === 0) lines.push("(none)");
  for (const slot of full) {
    lines.push("");
    lines.push(
      `- ${slot.logicalRef} (${slot.kind}, ${slot.tokens} tok, ${slot.contentHash}${slot.pinned ? ", pinned" : ""}):`,
    );
    // Resolver-less v0 (§7 ruling): the plugin lane has no app-supplied
    // content source — full slots degrade LOUDLY, never silently, never
    // thrown (the m7 recipe had the operator fetch content by hand).
    lines.push(`  ${unresolvedMarker(slot.logicalRef)}`);
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

  return {
    text: lines.join("\n"),
    turn,
    slots: slots.length,
    full: full.length,
    stub: stubbed.length,
  };
}
