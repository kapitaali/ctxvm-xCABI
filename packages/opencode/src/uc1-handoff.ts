/**
 * UC1-PAUSE-MIRROR + UC1-RESUME-MIRROR — UC1 handoff module for the OpenCode plugin lane.
 *
 * Line-for-line TS mirror of `packages/hermes/src/uc1_handoff.py` (B2 pause beat
 * + B3 resume, `8871dda`; consolidates the earlier resume-only `uc1-resume.ts`
 * into the §1.2 file-naming law `uc1-handoff.{ts,py}`). Mirrored semantics:
 *
 *   pause()   — the flush is the CALLER's duty (reference comment: "flush
 *               happens via the live adapter's _flush_traces()"): era-snapshot
 *               the flushed `{name}.{jsonl,meta.json}` with cp -n semantics
 *               (never clobbers an existing era), package it through the
 *               committed Rust `export` binary (--turn N --output
 *               <dir>/handoff/ --odps), then (reference verbatim) best-effort
 *               replay counterproof. Result shape
 *               {exit_code, snapshot, report, stderr, verified, divergences,
 *               witness} with witness = {paused_at, turn, handoff_dir,
 *               artifacts} (mirrored quirk: artifacts = the snapshot dict's
 *               VALUES, incl. the snapshot dir path, the label, and the turn).
 *   resume()  — zstd decompress of trace-N.jsonl.zst written INSIDE the
 *               snapshot dir, `replay --turn N` counterproof (exit 0),
 *               §3(1)(3)(4) v-next checks (checksums byte-validated, manifest
 *               sliceTurn cross-check, law-aware era/derivedFrom diff,
 *               projection surfaced), then the checksums-provenance digest;
 *               byte-identical reason strings; result
 *               {exit_code, verified, reason, evidence}.
 *
 * Disclosed deltas (RR-UC1PAUSE-MIRROR-20261025):
 *   - argv LAW FIXED both sides in the same card: the reference assembled
 *     [trace, str(turn), --output DIR, --odps] (a bare positional — the real
 *     binary rejects it: `unexpected second positional '2'`, exit 2), so every
 *     hermes pause(..., turn=N) failed on the wire; the mirror emits the
 *     documented form [trace, --turn N, --output DIR, --odps] and the hermes
 *     argv assembly is patched to match in the same commit.
 *   - the pause replay counterproof is reference-dead (it checks the literal
 *     name "trace-N.jsonl.zst" that never exists), mirrored verbatim: verified
 *     stays True and the counterproof is unproven until the hermes lane
 *     retargets the artifact path;
 *   - CTXVM_HANDOFF_TURN junk: the reference crashes on int(); the mirror
 *     keeps the module non-blocking where the reference's FAILURE paths are
 *     non-blocking, and raises a loud equivalent for junk env values;
 *   - `paused_at` sub-second precision differs (python microseconds vs JS
 *     milliseconds; both Z-suffixed);
 *   - the reference's dead-path divergence reader would crash on non-dict
 *     parse (rep.get on a str); the TS dead path types its way around it.
 *
 * Flush-time wiring (`live/ctxvm.ts`): with CTXVM_HANDOFF_DIR (or
 * CTXVM_HANDOFF_TURN) set, cleanup calls pause() after flushing — the design
 * §2 "package at flush" path (CTVM_HANDOFF_TURN unset → no --turn). Mid-session
 * turn-shaped triggers require TS finish() idempotency (T17.7 parity on
 * @ctxvm/node) — explicit follow-up card.
 */

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const EXPORT_BIN = "export";
const REPLAY_BIN = "replay";
const DIFF_BIN = "diff";

/** Shape of a `_run`-style subprocess result (mirror of uc1_handoff._run). */
interface RunResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

/** Evidence stamped into the sidecar's `resumeFrom` key (09-plugin-parity §3:
 * the B3 landed law stores the WHOLE verify evidence dict, so the v-next keys
 * (UC1-VERIFY-CHECKS) flow through as nested opt-in fields — the CANON
 * top-level sidecar key list is untouched): `manifest` {sliceTurn},
 * `projection` {turn, slots}, `diff` {source, relation} | null (null = no
 * source on disk). */
export interface ResumeEvidence {
  /** snapshot dir exactly as the caller passed it (env value, not resolved). */
  snapshot?: string;
  snapshotDigest?: string;
  snapTurn?: number;
  /** duplicated convenience key — present in the reference's evidence too. */
  turn?: number;
  /** sorted full-path artifact list including the decompressed trace. */
  artifacts?: string[];
  [key: string]: unknown;
}

/** Mirror of the resume contract: {"exit_code", "verified", "reason", "evidence"}. */
export interface ResumeResult {
  exit_code: number;
  verified: boolean;
  reason: string;
  evidence: ResumeEvidence;
}

/** Reference pause contract: {"exit_code", "snapshot", "report", "stderr",
 * "verified", "divergences", "witness"} — early failure omits the last three
 * (reference shape mirrored exactly). */
export interface PauseResult {
  exit_code: number;
  snapshot: Record<string, unknown>;
  report: unknown;
  stderr: string;
  verified?: boolean;
  divergences?: unknown[];
  diff_relation?: string | null;
  witness?: {
    paused_at: string;
    turn: number | null;
    handoff_dir: string;
    artifacts: unknown[];
  };
}

export interface PauseOptions {
  /** Reference trace_dir argument (env CTXVM_HANDOFF_DIR wins when set). */
  traceDir: string;
  /** Reference turn argument (env CTXVM_HANDOFF_TURN fallback when omitted). */
  turn?: number | null;
  /** Reference handoff_name argument (env CTXVM_HANDOFF_NAME fallback). */
  handoffName?: string | null;
}

function isDir(path: string): boolean {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
}

function isFile(path: string): boolean {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

/** Mirror of `_rust_bin_dir`: CTXVM_RUST_BIN_DIR override → walk-up from this
 * module dir looking for rust/target/release with the export binary in it. */
export function rustBinDir(): string | null {
  const override = process.env.CTXVM_RUST_BIN_DIR;
  if (override && isDir(override)) return override;
  let dir = dirname(fileURLToPath(import.meta.url));
  for (;;) {
    const candidate = join(dir, "rust", "target", "release");
    if (isDir(candidate) && isFile(join(candidate, EXPORT_BIN))) return candidate;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

function binPath(name: string): string {
  const d = rustBinDir();
  if (d !== null) return join(d, name);
  return name;
}

/** Mirror of `_run`: shell out to a Rust binary; identical not-found law. */
function run(name: string, args: readonly string[]): RunResult {
  const proc = spawnSync(binPath(name), [...args], { encoding: "utf8" });
  if (proc.error) {
    return {
      exit_code: 2,
      stdout: "",
      stderr: `binary not found: ${name} (set CTXVM_RUST_BIN_DIR or add rust/target/release to PATH)`,
    };
  }
  // proc.status is null only when the child was killed by a signal; mirror the
  // conventional negative-code encoding.
  const exit_code = proc.status === null ? -(proc.signal ?? 0) : proc.status;
  return { exit_code, stdout: proc.stdout ?? "", stderr: proc.stderr ?? "" };
}

/** Mirror of `_parse_json`: JSON-parse stdout, else return the raw string. */
function parseJson(stdout: string): unknown {
  try {
    return JSON.parse(stdout);
  } catch {
    return stdout;
  }
}

/** Mirror of `_rfc3339_z` (Z-suffixed UTC timestamp; JS yields millisecond
 * precision vs the reference's microseconds — cosmetic, disclosed). */
function rfc3339Z(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// Pause (mirror of UC1Handoff.pause)
// ---------------------------------------------------------------------------

/** Mirror of the reference's turn-from-env read: `int(env.get(…, "0")) or None`.
 * Junk env values crash the reference (uncaught int()); the mirror raises a
 * loud equivalent instead of silently mis-parsing. int()-permitted forms
 * accepted: optional sign, digits with underscores, surrounding whitespace. */
function turnFromEnv(): number | null {
  const raw = process.env.CTXVM_HANDOFF_TURN;
  const spec = (raw ?? "0").trim();
  if (!/^[-+]?[0-9_]+$/.test(spec) || !/[0-9]/.test(spec)) {
    throw new Error(`UC1 pause: invalid integer in CTXVM_HANDOFF_TURN: '${spec}'`);
  }
  const parsed = parseInt(spec.replace(/_/g, ""), 10);
  return parsed === 0 ? null : parsed;
}

/** The mid-session trigger arm reads the SAME env turn law the module reads —
 * single truth for `CTXVM_HANDOFF_TURN` (`int(…, "0") or None`; junk raises). */
export function pauseTurnFromEnv(): number | null {
  return turnFromEnv();
}

export function uc1Pause(options?: PauseOptions): PauseResult {
  const traceDir = options?.traceDir ?? "";
  let handoffDir = process.env.CTXVM_HANDOFF_DIR || traceDir;
  if (!handoffDir) {
    return {
      exit_code: 2,
      snapshot: {},
      report: {},
      stderr: "CTXVM_HANDOFF_DIR (or trace_dir) is required for uc1 pause",
    };
  }
  const name =
    options?.handoffName ?? process.env.CTXVM_HANDOFF_NAME ?? "handoff";
  let turn = options?.turn ?? null;
  if (turn === null || turn === undefined) {
    turn = turnFromEnv();
  }

  // Era snapshot label uses the turn so repeated pauses keep history. The
  // flush itself is the caller's duty (reference: "flush happens via the live
  // adapter's _flush_traces()"); here we snapshot whatever flushed file exists
  // for `name`.
  const snapshot: Record<string, unknown> = {};
  for (const ext of ["jsonl", "meta.json"] as const) {
    const src = join(handoffDir, `${name}.${ext}`);
    const dst = join(handoffDir, `${name}-${turn === null ? "flush" : `turn-${turn}`}.${ext}`);
    if (isFile(src)) {
      if (!existsSync(dst)) copyFileSync(src, dst);
      snapshot[ext] = dst;
    }
  }

  // Package through the committed export binary. argv LAW (fixed in the
  // UC1-PAUSE-MIRROR card, both sides): the reference assembled a bare
  // positional turn (`[trace, str(turn), --output DIR, --odps]`) which the
  // binary rejects; the documented CLI form is used instead.
  const snapshotDir = join(handoffDir, "handoff");
  const exportArgs: string[] = ["--output", snapshotDir];
  if (turn !== null) exportArgs.unshift("--turn", String(turn));
  exportArgs.push("--odps");
  const traceJsonl = join(handoffDir, `${name}.jsonl`);
  const result = run(EXPORT_BIN, [traceJsonl, ...exportArgs]);

  // Step 4: verification (replay counterproof) — best effort, never blocks.
  // Retargeted (UC1-VERIFY-CHECKS follow-up): glob the package's zst, replay
  // it at its turn, type-guard the divergence reader, and — when a turn is set
  // — run the era-vs-package shellDiff expecting `identical` (m6 law: the era
  // copy beside the package is the canonical pair).
  let replayOk = true;
  const replayDivergences: unknown[] = [];
  let diffRelation: string | null = null;
  const zstFiles = existsSync(snapshotDir)
    ? readdirSync(snapshotDir)
        .filter((n: string) => /^trace-.*\.jsonl\.zst$/.test(n))
        .sort()
    : [];
  if (result.exit_code === 0 && zstFiles.length > 0) {
    const zstName = zstFiles[0];
    const zstPath = join(snapshotDir, zstName);
    const stem = zstName.replace(/\.zst$/, "");
    const segment = stem.split("-")[1]?.split(".")[0] ?? "";
    let sliceTurn: number | null = /^[0-9]+$/.test(segment)
      ? parseInt(segment, 10)
      : null;
    if (sliceTurn === null) sliceTurn = turn;
    if (sliceTurn !== null) {
      const decompressed = join(
        (process.env.TMPDIR ?? process.env.TEMP ?? "/tmp"),
        `trace-${sliceTurn}-${Date.now()}.jsonl`,
      );
      const decomp = spawnSync(
        "zstd",
        ["-d", zstPath, "-o", decompressed, "-f"],
        { encoding: "utf8" },
      );
      if (decomp.status === null || decomp.status !== 0) {
        replayOk = false;
      } else {
        const replayResult = run(REPLAY_BIN, [decompressed, "--turn", String(sliceTurn)]);
        if (replayResult.exit_code !== 0) replayOk = false;
        const rep = parseJson(replayResult.stdout);
        const div =
          typeof rep === "object" && rep !== null
            ? (rep as Record<string, unknown>).divergences
            : undefined;
        if (Array.isArray(div)) replayDivergences.push(...div);
        // Era-vs-package diff (when turn is set): identical required.
        if (turn !== null && replayOk) {
          const eraPath = snapshot.jsonl;
          if (typeof eraPath === "string" && isFile(eraPath)) {
            const d = shellDiff(eraPath, decompressed);
            diffRelation = d.relation;
            if (diffRelation !== null && diffRelation !== "identical") {
              replayOk = false;
            }
          }
        }
      }
    }
  }

  snapshot.handoff_dir = snapshotDir;
  snapshot.label = turn === null ? "flush" : `turn-${turn}`;
  snapshot.turn = turn;

  return {
    exit_code: result.exit_code,
    snapshot,
    report: parseJson(result.stdout),
    stderr: result.stderr,
    verified: replayOk,
    divergences: replayDivergences,
    diff_relation: diffRelation,
    witness: {
      paused_at: rfc3339Z(),
      turn,
      handoff_dir: handoffDir,
      // Reference quirk mirrored: the SNAPSHOT DICT's values (era copies,
      // then handoff_dir, label, turn).
      artifacts: Object.values(snapshot),
    },
  };
}

// ---------------------------------------------------------------------------
// Resume (mirror of UC1Handoff.resume / B3, 8871dda)
// ---------------------------------------------------------------------------

function fail(exit_code: number, reason: string, evidence: ResumeEvidence): ResumeResult {
  return { exit_code, verified: false, reason, evidence };
}

/** Mirror of `UC1Handoff._snapshot_digest`: SHA-256 over the concatenated
 * checksum hex strings (sorted by filename) from checksums.sha256; when the
 * file is missing, SHA-256 over name||bytes of every artifact except
 * checksums.sha256 itself. */
export function snapshotDigest(snapshotDir: string): string {
  const checksumsFile = join(snapshotDir, "checksums.sha256");
  if (!isFile(checksumsFile)) {
    // Fallback: hash each artifact file directly.
    const h = createHash("sha256");
    for (const name of readdirSync(snapshotDir).sort()) {
      const artifact = join(snapshotDir, name);
      if (isFile(artifact) && name !== "checksums.sha256") {
        h.update(Buffer.from(name, "utf8"));
        h.update(readFileSync(artifact));
      }
    }
    return "sha256:" + h.digest("hex");
  }

  // Lines: "<hash>  <filename>" (split on the first whitespace run); the
  // filename never reaches the digest — only the sorted hex strings do.
  const lines = readFileSync(checksumsFile, "utf8").trim().split("\n");
  const entries: Array<[string, string]> = [];
  for (const line of lines) {
    const m = line.match(/^\s*(\S+)\s+(.+)$/);
    if (m) entries.push([m[2].trim(), m[1].trim()]);
  }
  entries.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  const h = createHash("sha256");
  for (const [, digestHex] of entries) h.update(Buffer.from(digestHex, "utf8"));
  return "sha256:" + h.digest("hex");
}

/** Mirror of `UC1Handoff.resume()`: verify + provenance; never blocks.
 * v-next checks (UC1-VERIFY-CHECKS, 2026-10-26, both sides in one card):
 *   (1) every checksums.sha256 row re-verified against the artifact BYTES (the
 *       digest hashes only the recorded hex strings, so a corrupted artifact
 *       passed verification before this card) + manifest `sliceTurn` ↔ trace
 *       turn cross-check;
 *   (3) law-aware diff (m6 knowledge-stateful-tail law): the era copy
 *       `*-turn-N.jsonl` beside the package is the canonical source pair
 *       (relation `identical` REQUIRED — a mismatch is NOT a lawful
 *       divergence); without an era the manifest `derivedFrom` trace is diffed
 *       DIAGNOSTIC ONLY (its divergence at `turn.render` residency rows is the
 *       lawful shape — surfaced, never failing); no source on disk = skipped;
 *   (4) the projection (`page-table-N.json` slots) is surfaced: structured
 *       evidence here + a witness line at the call site.
 * Any new-check failure = verified=False, tracer continues UNVERIFIED. */
export function resumeVerify(snapshotDir: string): ResumeResult {
  if (!isDir(snapshotDir)) {
    return fail(2, `snapshot dir not found: ${snapshotDir}`, {});
  }

  // sorted glob of trace-*.jsonl.zst → determine turn N from the filename.
  const zstFiles = readdirSync(snapshotDir)
    .filter((name) => /^trace-.*\.jsonl\.zst$/.test(name))
    .sort();
  if (zstFiles.length === 0) {
    return fail(2, `no trace-*.jsonl.zst in ${snapshotDir}`, {});
  }
  const zstName = zstFiles[0];
  // Path("trace-3.jsonl.zst").stem == "trace-3.jsonl"; turn from the second
  // dash segment, digits only (the reference's int() rejects anything else —
  // "cannot parse turn from …").
  const stem = zstName.replace(/\.zst$/, "");
  const segment = stem.split("-")[1]?.split(".")[0] ?? "";
  if (!/^[0-9]+$/.test(segment)) {
    return fail(2, `cannot parse turn from ${zstName}`, {});
  }
  const turn = parseInt(segment, 10);

  // Decompress zst INTO the snapshot dir (reference placement is mirrored —
  // the decompressed file then shows up in artifacts and the fallback digest).
  const decompressed = join(snapshotDir, `trace-${turn}.jsonl`);
  const decomp = spawnSync(
    "zstd",
    ["-d", join(snapshotDir, zstName), "-o", decompressed, "-f"],
    { encoding: "utf8" },
  );
  if (decomp.status === null || decomp.status !== 0) {
    return fail(
      2,
      `zstd decompress failed: ${(decomp.stderr ?? "").trim()}`,
      { turn, snapshot: snapshotDir },
    );
  }

  // Replay counterproof: exit 0 required.
  const replay = run(REPLAY_BIN, [decompressed, "--turn", String(turn)]);
  if (replay.exit_code !== 0) {
    return {
      exit_code: replay.exit_code,
      verified: false,
      reason: `replay exit ${replay.exit_code}: ${replay.stderr.trim()}`,
      evidence: { turn, snapshot: snapshotDir },
    };
  }

  // --- §3(1) v-next: checksums VALIDATED at byte level ---------------------
  const checksumsFile = join(snapshotDir, "checksums.sha256");
  if (!isFile(checksumsFile)) {
    return fail(
      2,
      `checksums.sha256 missing: ${snapshotDir}`,
      { turn, snapshot: snapshotDir },
    );
  }
  // Rows in FILE order ("<hash>  <name>", split on the first whitespace run);
  // blank/malformed rows skip — mirrors the digest parser's split law.
  const checksumLines = readFileSync(checksumsFile, "utf8").trim().split("\n");
  for (const line of checksumLines) {
    const m = line.match(/^\s*(\S+)\s+(.+)$/);
    if (!m) continue;
    const digestHex = m[1].trim();
    const name = m[2].trim();
    const artifact = join(snapshotDir, name);
    if (!isFile(artifact)) {
      return fail(
        2,
        `checksummed artifact missing: ${name}`,
        { turn, snapshot: snapshotDir },
      );
    }
    const actual = createHash("sha256").update(readFileSync(artifact)).digest("hex");
    if (actual !== digestHex) {
      return fail(
        2,
        `checksum mismatch for ${name}`,
        { turn, snapshot: snapshotDir },
      );
    }
  }

  // --- §3(1) v-next: manifest template cross-check -------------------------
  const manifestFile = join(snapshotDir, "manifest.yaml");
  if (!isFile(manifestFile)) {
    return fail(
      2,
      `manifest.yaml missing: ${snapshotDir}`,
      { turn, snapshot: snapshotDir },
    );
  }
  const manifestText = readFileSync(manifestFile, "utf8");
  // Light template read (module-generated manifest; no YAML dependency on
  // either side): only `sliceTurn:` cross-checks the trace turn.
  const sliceTurnMatch = manifestText.match(/^\s*sliceTurn:\s*(\d+)\s*$/m);
  if (!sliceTurnMatch) {
    return fail(
      2,
      `manifest sliceTurn not found for trace turn ${turn}`,
      { turn, snapshot: snapshotDir },
    );
  }
  const sliceTurn = parseInt(sliceTurnMatch[1], 10);
  if (sliceTurn !== turn) {
    return fail(
      2,
      `manifest sliceTurn ${sliceTurn} != trace turn ${turn}`,
      { turn, snapshot: snapshotDir },
    );
  }

  // --- §3(3) v-next: LAW-AWARE diff relation -------------------------------
  // Canonical pair: the era copy `*-turn-N.jsonl` written beside the package
  // by the mid-session chain — `identical` REQUIRED. Without an era, the
  // manifest `derivedFrom` trace is diffed DIAGNOSTIC ONLY (divergence at
  // `turn.render` residency rows is the knowledge-stateful lawful shape).
  let diffEvidence: { source: string; relation: string } | null = null;
  const eraRe = new RegExp(`-turn-${turn}\\.jsonl$`);
  const decompressedName = `trace-${turn}.jsonl`;
  const eraCandidates = readdirSync(snapshotDir)
    .filter((name) => eraRe.test(name) && name !== decompressedName)
    .sort();
  if (eraCandidates.length > 0) {
    const eraName = eraCandidates[0];
    const d = shellDiff(join(snapshotDir, eraName), decompressed);
    if (d.relation === null) {
      return fail(2, d.reason as string, { turn, snapshot: snapshotDir });
    }
    if (d.relation !== "identical") {
      return fail(
        2,
        `era diff ${eraName}: relation ${d.relation} expected identical`,
        { turn, snapshot: snapshotDir },
      );
    }
    diffEvidence = { source: eraName, relation: d.relation };
  } else {
    // Relative derivedFrom values resolve from the RESUMING process's cwd
    // (the manifest's own verify.diff hint assumes the session root — the
    // golden tests chdir to the repo root for exactly this reason).
    const dfMatch = manifestText.match(/^\s*derivedFrom:\s*'([^']*)'/m);
    if (dfMatch && isFile(dfMatch[1])) {
      const d = shellDiff(dfMatch[1], decompressed);
      if (d.relation !== null) diffEvidence = { source: dfMatch[1], relation: d.relation };
      // Diagnostic-only either way: never verdict-forming (m6 law).
    }
  }

  // --- §3(4) v-next: projection surfaced -----------------------------------
  const pageTableFile = join(snapshotDir, `page-table-${turn}.json`);
  if (!isFile(pageTableFile)) {
    return fail(
      2,
      `page-table-${turn}.json missing: ${snapshotDir}`,
      { turn, snapshot: snapshotDir },
    );
  }
  let slotsCount = -1;
  try {
    const table = JSON.parse(readFileSync(pageTableFile, "utf8")) as {
      turn?: unknown;
      slots?: unknown;
    };
    if (Array.isArray(table.slots)) slotsCount = table.slots.length;
    if (typeof table.turn === "number" && table.turn !== turn) {
      return fail(
        2,
        `page-table turn ${table.turn} != trace turn ${turn}`,
        { turn, snapshot: snapshotDir },
      );
    }
  } catch {
    return fail(
      2,
      `page-table-${turn}.json unreadable`,
      { turn, snapshot: snapshotDir },
    );
  }
  if (slotsCount < 0) {
    return fail(
      2,
      `page-table-${turn}.json unreadable`,
      { turn, snapshot: snapshotDir },
    );
  }

  const digest = snapshotDigest(snapshotDir);
  return {
    exit_code: 0,
    verified: true,
    reason: `snapshot verified: replay exit 0 at turn ${turn}`,
    evidence: {
      snapshot: snapshotDir,
      snapshotDigest: digest,
      snapTurn: turn,
      turn,
      artifacts: readdirSync(snapshotDir)
        .map((name) => join(snapshotDir, name))
        .filter((p) => isFile(p))
        .sort(),
      manifest: { sliceTurn },
      projection: { turn, slots: slotsCount },
      diff: diffEvidence,
    },
  };
}

/** Run the rust `diff` CLI (source first, slice second — the manifest's own
 * verify.diff order) and scrape the lowercase relation from its JSON stdout.
 * `{relation: null, reason}` when the invocation or output is unusable. */
function shellDiff(
  source: string,
  slice: string,
): { relation: string | null; reason?: string } {
  const d = run(DIFF_BIN, [source, slice]);
  const brace = d.stdout.indexOf("{");
  if (brace === -1) {
    return {
      relation: null,
      reason: `diff tool failed: ${(d.stderr || d.stdout).trim()}`,
    };
  }
  try {
    const parsed = JSON.parse(d.stdout.slice(brace)) as { relation?: unknown };
    if (typeof parsed.relation === "string") return { relation: parsed.relation };
  } catch {
    /* fall through */
  }
  return { relation: null, reason: "diff tool output unparseable" };
}
