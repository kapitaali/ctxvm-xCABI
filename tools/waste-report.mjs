#!/usr/bin/env node
/**
 * tools/waste-report.mjs — the W1 dogfood lens over xCABI traces (adoption push).
 *
 * Reads one or more xCABI JSONL traces (or handoff snapshot dirs / .zst slices)
 * and reports, per trace:
 *
 *   rendered tokens            Σ turn.render.residentTokens        (metrics.py law)
 *   identifier-touched share   Σ declared tokens of DISTINCT faulted pages ÷ rendered
 *                              (metrics.py touch_ratio, HONESTLY NAMED: the only
 *                              model-behavior surface v0 records is page.fault, so
 *                              this is "pages the harness observed the model's own
 *                              output re-referencing", an interest signal — never a
 *                              reading guarantee)
 *   waste (upper bound)        1 − share; AND the stale-token upper bound: tokens of
 *                              tool-result pages evicted and never referenced again
 *                              × remaining turns — the tokens a context-stuffing
 *                              harness would reprocess. UPPER BOUND by construction.
 *   duplicate tool-call rate   page.declare grouped by logicalRef (tool + canonical
 *                              args): k ≥ 2 declares = re-executed call. contentHash
 *                              splits true duplicates (identical result — a
 *                              content-addressed ledger could have served it) from
 *                              changed results (re-execution was legitimate). D1 input.
 *   provider-reported share    call.meta with providerReported=true (0 across the
 *                              current corpora — the W2b gap, surfaced not hidden).
 *   re-mention amplification   null (UNVERIFIED): the 84.4× paper figure's exact
 *                              formula is not pinned in-repo yet — defining it with
 *                              ground truth is W3. Never fudged.
 *
 * Count provenance: every token count in the current corpora is tokenizer-scoped
 * (`apx4-char`, estimated — see RR-W2-20261029); the report prints the session's
 * tokenizerId and marks numbers estimated vs provider accordingly.
 *
 * Directional/single-corpus by nature: n = the traces given, one machine, one
 * author. The limitations block is printed with every report.
 *
 * Usage: node tools/waste-report.mjs TRACE.jsonl [MORE...]   (dir/.zst handled)
 * Output: one JSON object per trace (machine-readable; the RR quotes it).
 */

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// ── input loading (a trace file, a .zst slice, or a snapshot dir) ────────────

function loadTrace(arg) {
  let path = arg;
  let tmp = null;
  try {
    if (!path.endsWith(".jsonl")) {
      // snapshot dir → sorted-first trace-*.jsonl.zst (the resumeVerify law)
      const zst = readdirSync(path).filter((n) => /^trace-.*\.jsonl\.zst$/.test(n)).sort()[0];
      if (!zst) throw new Error(`no trace-*.jsonl.zst in ${path}`);
      path = join(path, zst);
    }
    if (path.endsWith(".zst")) {
      tmp = join(mkdtempSync(join(tmpdir(), "ctxvm-w1-")), "trace.jsonl");
      const d = spawnSync("zstd", ["-d", path, "-o", tmp, "-f"], { encoding: "utf8" });
      if (d.status !== 0) throw new Error(`zstd failed: ${(d.stderr ?? "").trim()}`);
      path = tmp;
    }
    return JSON.parse(
      "[" +
      readFileSync(path, "utf8")
        .split("\n")
        .filter((l) => l.trim())
        .join(",") +
      "]",
    );
  } finally {
    if (tmp) rmSync(tmp, { force: true });
  }
}

// ── the lens ─────────────────────────────────────────────────────────────────

const pageKey = (page) => `${page?.id?.logicalRef ?? page?.logicalRef}|${page?.id?.contentHash ?? page?.contentHash}`;

function analyze(events) {
  const open = events.find((e) => e.type === "session.open") ?? {};
  const declares = events.filter((e) => e.type === "page.declare");
  const renders = events.filter((e) => e.type === "page.render");
  const evicts = events.filter((e) => e.type === "page.evict");
  const faults = events.filter((e) => e.type === "page.fault");
  const turnRenders = events.filter((e) => e.type === "turn.render");
  const metas = events.filter((e) => e.type === "call.meta");

  const turns = turnRenders.map((e) => e.turn);
  const maxTurn = turns.length ? Math.max(...turns) : null;
  const renderedTokens = turnRenders.reduce((s, e) => s + (e.residentTokens ?? 0), 0);

  // declared tokens, last-declare-wins per key (metrics.py law)
  const declared = new Map(); // key -> tokens
  for (const e of declares) declared.set(pageKey(e.page), e.page.tokens ?? 0);

  // duplicate ledger: declares grouped by logicalRef (tool + canonical args)
  const byRef = new Map(); // logicalRef -> [{contentHash, kind}]
  for (const e of declares) {
    const ref = e.page?.id?.logicalRef ?? "?";
    if (!byRef.has(ref)) byRef.set(ref, []);
    byRef.get(ref).push(e.page?.id?.contentHash ?? "?");
  }
  const dupGroups = [...byRef.entries()].filter(([, hashes]) => hashes.length >= 2);
  const reExecutions = dupGroups.reduce((s, [, hs]) => s + hs.length - 1, 0);
  const trueDupHashes = dupGroups.filter(([, hs]) => new Set(hs).size === 1).length;
  const changedResults = dupGroups.length - trueDupHashes;

  // faults: touched (distinct keys, metrics.py law) + source split
  const faultedKeys = new Map(); // key -> [sources]
  for (const e of faults) {
    const k = pageKey(e.page);
    if (!faultedKeys.has(k)) faultedKeys.set(k, []);
    faultedKeys.get(k).push(e.source);
  }
  const touchedTokens = [...faultedKeys.keys()].reduce((s, k) => s + (declared.get(k) ?? 0), 0);
  const srcCount = {};
  for (const srcs of faultedKeys.values()) for (const s of srcs) srcCount[s] = (srcCount[s] ?? 0) + 1;

  // stale-tool-result upper bound: evicted, never referenced again afterwards
  const lastEvict = new Map(); // key -> max evict turn
  for (const e of evicts) {
    const k = pageKey(e.page);
    lastEvict.set(k, Math.max(lastEvict.get(k) ?? -1, e.turn ?? 0));
  }
  let staleTokens = 0, stalePages = 0, recalledAfterEvict = 0;
  const staleDetail = [];
  for (const [k, tEvict] of lastEvict) {
    const laterFault = faults.some((f) => pageKey(f.page) === k && (f.turn ?? 0) > tEvict);
    const laterFull = renders.some(
      (r) => pageKey(r.page) === k && r.mode === "full" && (r.turn ?? 0) > tEvict);
    if (laterFault || laterFull) { recalledAfterEvict += 1; continue; }
    const toks = declared.get(k) ?? 0;
    const carried = toks * Math.max(0, (maxTurn ?? tEvict) - tEvict);
    staleTokens += carried; stalePages += 1;
    staleDetail.push({ logicalRef: k.split("|")[0], tokens: toks, evictedAt: tEvict, stuffingWouldReprocess: carried });
  }
  staleDetail.sort((a, b) => b.stuffingWouldReprocess - a.stuffingWouldReprocess);

  return {
    session: {
      agentId: open.agentId ?? null, model: open.model ?? null, provider: open.provider ?? null,
      budgetTokens: open.budgetTokens ?? null, tokenizerId: open.tokenizerId ?? null,
      tokensSource: "estimated", // every current corpus counts are apx4 estimates (W2b pending)
    },
    events: events.length,
    turns: turnRenders.length,
    renderedTokens,
    evictedTokensFlow: turnRenders.reduce((s, e) => s + (e.evictedTokens ?? 0), 0),
    declaredPages: declared.size,
    identifierTouchedShare: renderedTokens > 0 ? touchedTokens / renderedTokens : null,
    touchedTokens,
    faultSources: srcCount,
    waste: renderedTokens > 0 ? 1 - touchedTokens / renderedTokens : null,
    staleUpperBound: {
      note: "UPPER BOUND — tokens evicted and never referenced again × remaining turns; what a context-stuffing harness would reprocess",
      pages: stalePages, tokens: staleTokens,
      evictedAndRecalled: recalledAfterEvict,
      top: staleDetail.slice(0, 5),
    },
    duplicates: {
      note: "declare grouped by logicalRef (tool + canonical args); true = identical contentHash (a content-addressed ledger could have served it); changed = re-execution was legitimate",
      totalDeclares: declares.length,
      distinctRefs: byRef.size,
      reExecutedRefs: dupGroups.length,
      reExecutions,
      trueDuplicates: trueDupHashes,
      changedResults,
      rate: declares.length > 0 ? reExecutions / declares.length : null,
      top: dupGroups.slice(0, 5).map(([ref, hs]) => ({ logicalRef: ref.slice(0, 72), declares: hs.length, identicalResults: new Set(hs).size === 1 })),
    },
    providerReported: {
      callMetas: metas.length,
      trueCount: metas.filter((e) => e.cacheEstimate?.providerReported === true).length,
    },
    reMentionAmplification: null,
  };
}

// ── output ───────────────────────────────────────────────────────────────────

const LIMITATIONS = [
  "Directional, single-corpus: n = the traces analyzed, one machine, one author. Not a general claim.",
  "All token counts are tokenizer-scoped estimates (`tokenizerId` per session — apx4-char across the current corpora); no provider-reported usage exists yet (W2b). Numbers are unit-true only within one tokenizer.",
  "identifier-touched share is inferred from page.fault records (the only model-behavior surface v0 records): an interest signal, not a reading guarantee. waste = 1 − share is an upper bound, not 'context the agent never reads'.",
  "staleUpperBound assumes a stuffing harness carries each stale page to the session end; real stuffing harnesses may summarize/compact (then the bound overstates), and the page might have been read while resident (then 'waste' overstates).",
  "re-mention amplification is null: the 84.4x paper figure's formula is not pinned in-repo (UNVERIFIED here) — W3 defines it with ground truth.",
  "Duplicate-call detection keys on logicalRef = tool + canonical args: same args with different contentHash means the world changed between calls, not that the model erred.",
];

const out = [];
for (const arg of process.argv.slice(2)) {
  let report;
  try {
    report = { trace: arg, ...analyze(loadTrace(arg)) };
  } catch (err) {
    console.error(`waste-report: ${arg}: ${err.message}`);
    process.exitCode = 2;
    continue;
  }
  out.push(report);
}
if (out.length) {
  console.log(JSON.stringify(
    process.argv.includes("--with-limitations")
      ? { reports: out, limitations: LIMITATIONS }
      : out.length === 1 ? out[0] : out,
    null, 2,
  ));
}
