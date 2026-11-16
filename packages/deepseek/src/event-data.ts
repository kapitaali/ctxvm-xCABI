/**
 * W22 — one place that adapts DSH's committed SessionEvent envelope to the
 * adapter's read sites. DSH publishes `{type, seq, time, data, surfaceOp?,
 * sourceEventSeqs?}`; payload fields live under `data`, while surface metadata
 * stays on the envelope. The merged view keeps the unit fixtures readable and
 * prevents a flattened read from silently seeing `undefined` in the live path.
 */
import type { SessionEvent } from '@deepseek-ai/dsh-session/types'

type Envelope = {
  type?: unknown
  seq?: unknown
  time?: unknown
  data?: unknown
  surfaceOp?: unknown
  sourceEventSeqs?: unknown
  ignorable?: unknown
}

/** Payload fields plus envelope metadata, in one record. */
export function eventData(event: SessionEvent | Envelope): Record<string, unknown> {
  const envelope = event as Envelope
  const payload = envelope.data !== undefined && envelope.data !== null && typeof envelope.data === 'object'
    ? envelope.data as Record<string, unknown>
    : envelope as Record<string, unknown>
  const merged: Record<string, unknown> = { ...payload }
  for (const key of ['type', 'seq', 'time', 'surfaceOp', 'sourceEventSeqs', 'ignorable'] as const) {
    if (envelope[key] !== undefined) merged[key] = envelope[key]
  }
  return merged
}

export function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : undefined
}

export function asString(value: unknown): string {
  return typeof value === 'string' ? value : String(value ?? '')
}

export function asNumberArray(value: unknown): number[] | undefined {
  return Array.isArray(value)
    ? value.filter((item): item is number => typeof item === 'number')
    : undefined
}
