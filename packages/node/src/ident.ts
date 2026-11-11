/** xCABI identity primitives — T6/T7 contract (hash, canonical args, token estimation). */

import { createHash } from "node:crypto";

export type Json =
  | null
  | boolean
  | number
  | string
  | readonly Json[]
  | { readonly [k: string]: Json };

const ARGS_LIMIT = 120;

/** RFC-0.1 D18 (`spec/rfc-0.1/COMPATIBILITY.md`, clause C3): object keys sort by UNICODE
 *  CODE POINT. JS's default `Array#sort` compares UTF-16 code units, which places an
 *  astral-plane key (U+1D11E, first unit 0xD834) BEFORE a BMP key (U+FF00) that Python's
 *  `sort_keys=True` places after it - a silent digest divergence, since the two forms would
 *  canonicalise to different bytes for the same input. Comparing code points matches Python
 *  (and Rust's BTreeMap) and is the order C3 requires.
 */
function compareCodePoints(a: string, b: string): number {
  const ca = Array.from(a); // the string iterator yields whole code points
  const cb = Array.from(b);
  const n = Math.min(ca.length, cb.length);
  for (let i = 0; i < n; i++) {
    const x = ca[i].codePointAt(0)!;
    const y = cb[i].codePointAt(0)!;
    if (x !== y) return x < y ? -1 : 1;
  }
  return ca.length - cb.length; // a prefix sorts first
}

/** Comparator-stable canonical JSON: recursively sorted object keys, minimal separators. */
export function canonicalJson(value: Json): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const obj = value as { readonly [k: string]: Json };
  const sorted = Object.keys(obj).sort(compareCodePoints);
  const body = sorted.map((k) => `${JSON.stringify(k)}:${canonicalJson(obj[k])}`).join(",");
  return `{${body}}`;
}

/** RFC-0.1 D18 (`spec/rfc-0.1/COMPATIBILITY.md`, clause C3): a hash input must be ADMISSIBLE -
 *  strings are valid Unicode scalar values (no lone surrogate), numbers are integers within
 *  +/-2^53-1 and never -0, and the value set is string | integer | boolean | null | array | object.
 *  An inadmissible input MUST be rejected, never coerced: coercing turns `1.0` into `"1"` in one
 *  implementation and `"1.0"` in another, which is the divergence C3 exists to remove.
 *
 *  Exported and tested, NOT yet wired into the minting path: rejecting a tool call whose arguments
 *  carry an integral float is a behavioural change with a blast radius beyond the note (follow-up
 *  card; the blast radius is named there).
 */
export function validateHashInput(value: Json, path = "$"): void {
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number") {
    if (!Number.isInteger(value)) throw new Error(`canonical: non-integer number at ${path}`);
    if (!Number.isSafeInteger(value)) throw new Error(`canonical: integer outside +/-2^53-1 at ${path}`);
    if (Object.is(value, -0)) throw new Error(`canonical: -0 at ${path}`);
    return;
  }
  if (typeof value === "string") {
    for (let i = 0; i < value.length; i++) {
      const c = value.charCodeAt(i);
      if (c >= 0xd800 && c <= 0xdbff) {
        const next = value.charCodeAt(i + 1);
        if (!(next >= 0xdc00 && next <= 0xdfff)) throw new Error(`canonical: lone surrogate at ${path}`);
        i++;
      } else if (c >= 0xdc00 && c <= 0xdfff) {
        throw new Error(`canonical: lone low surrogate at ${path}`);
      }
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((v, i) => validateHashInput(v, `${path}[${i}]`));
    return;
  }
  for (const [k, v] of Object.entries(value)) validateHashInput(v, `${path}.${k}`);
}

/** `sha256:<8 hex>` — content-identity digest form used by the reference fixtures (RFC-0 §6: `contentHash: S`). */
export function contentHash(content: string): string {
  const hex = createHash("sha256").update(content, "utf-8").digest("hex").slice(0, 8);
  return `sha256:${hex}`;
}

function hex8(content: string): string {
  return contentHash(content).slice("sha256:".length);
}

/** Declared-token approximation `apx4-char` — documented v0 baseline; token counts are `tokenizer_id`-scoped and not gated. */
export function approx4(content: string): number {
  return Math.ceil([...content].length / 4) || 0;
}

/**
 * `tool:<server>.<name>(<canonicalArgs>)`; canonical args longer than 120 chars truncate
 * with a `#<sha256.8>` tail so identity stays stable, readable, and short (T6 §2/§3).
 */
export function toolRef(server: string | undefined, name: string, args: Json): string {
  const canonical = canonicalJson(args);
  const trimmed = canonical.length <= ARGS_LIMIT ? canonical : `${canonical.slice(0, ARGS_LIMIT)}#${hex8(canonical)}`;
  const prefix = server ? `${server}.${name}` : name;
  return `tool:${prefix}(${trimmed})`;
}

export function fileRef(path: string): string {
  return `file:${path}`;
}

export function summaryRef(id: string): string {
  return `summary:${id}`;
}

export function imageRef(url: string): string {
  return `image:${url}`;
}

/**
 * Identity candidates a page exposes to `identifier_scan`: the ref's path/value/symbol
 * fragments, longest-ish first. The scan matches page identity by substring-in-text.
 */
export function identityTokens(logicalRef: string): readonly string[] {
  const body = logicalRef.replace(/^[a-z_]+:/, "");
  const innerMatch = body.match(/^([^(]*)\((.*)\)$/);
  const argZone = innerMatch ? innerMatch[2] : body;
  const tokens = new Set<string>();
  tokens.add(body);
  if (innerMatch) tokens.add(innerMatch[1]);
  for (const m of argZone.matchAll(/"([^"]+)"/g)) tokens.add(m[1]);
  for (const m of body.matchAll(/[A-Za-z0-9][\w./:-]{5,}/g)) tokens.add(m[0]);
  return [...tokens]
    .filter((t) => t.length >= 3)
    .sort((a, b) => b.length - a.length);
}
