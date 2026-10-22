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

/** Comparator-stable canonical JSON: recursively sorted object keys, minimal separators. */
export function canonicalJson(value: Json): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const sorted = Object.keys(value).sort();
  const body = sorted.map((k) => `${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(",");
  return `{${body}}`;
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
