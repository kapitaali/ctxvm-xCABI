/**
 * UC1-RESUME-MIRROR — resume surface for the OpenCode plugin lane.
 *
 * Line-for-line TS mirror of `packages/hermes/src/uc1_handoff.py` (B3, commit
 * 8871dda) — the UC1 resume beat: given a paused handoff snapshot directory,
 * decompress its trace-N.jsonl.zst, run the `replay` counterproof (exit 0
 * required), and stamp the artifact checksums into a SHA-256 provenance
 * digest. Mirrored behavior is the reference, not the design prose — where
 * design §3 of uc1-plugin.md asks for four verification checks, the reference
 * implements the replay counterproof + digest; AA/EE differences are disclosed
 * in reports/RR-UC1RESUME-MIRROR-20261025.md.
 *
 * Topology follows the reference: uc1_handoff.py duplicates its helper family
 * (`_rust_bin_dir` / `_bin_path` / `_run`) per module, so this mirror carries
 * its own copies instead of importing `uc2-forensics.ts`. The resume beat
 * only: pause (B2) has not landed on the opencode lane, so the pause-only
 * helpers (`_parse_json`, `_rfc3339_z`) have no counterpart here.
 *
 * Reason strings, result shape, turn parsing, digest algorithm, and the
 * decompressed file placement are mirrored byte-exactly:
 *
 *   "snapshot dir not found: {dir}"
 *   "no trace-*.jsonl.zst in {dir}"
 *   "cannot parse turn from {name}"
 *   "zstd decompress failed: {stderr}"
 *   "replay exit {code}: {stderr}"
 *   "snapshot verified: replay exit 0 at turn {n}"
 *
 * with result {exit_code, verified, reason, evidence}; success evidence =
 * {snapshot, snapshotDigest, snapTurn, turn, artifacts}; artifact list =
 * sorted full-path file list INCLUDING the decompressed trace written inside
 * the snapshot dir (reference quirk mirrored), absent "checksums.sha256"
 * falls back to hashing name+bytes per artifact.
 *
 * Disclosed latent fix (never-block law): the reference would crash on
 * FileNotFoundError if the `zstd` CLI is missing; the mirror reports a loud
 * unverified failure instead. zstd exists on both dev and CI hosts.
 */

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const REPLAY_BIN = "replay";
const EXPORT_BIN = "export";

/** Shape of a `_run`-style subprocess result (mirror of uc1_handoff._run). */
interface RunResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

/** Evidence stamped into the sidecar's `resumeFrom` key (09-plugin-parity §3). */
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

/** Mirror of the reference contract: {"exit_code", "verified", "reason", "evidence"}. */
export interface ResumeResult {
  exit_code: number;
  verified: boolean;
  reason: string;
  evidence: ResumeEvidence;
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

function fail(exit_code: number, reason: string, evidence: ResumeEvidence): ResumeResult {
  return { exit_code, verified: false, reason, evidence };
}

/** Mirror of `UC1Handoff.resume()`: verify + provenance; never blocks. */
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
  // Path("trace-3.jsonl.zst").stem == "trace-3.jsonl"; turn from the
  // second dash segment, digits only (the reference's int() rejects anything
  // else — "cannot parse turn from …").
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
    },
  };
}
