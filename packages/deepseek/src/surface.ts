/** DSH surface provenance helpers shared by the tracer and page-table fold. */
import { asRecord, asNumberArray } from './event-data.ts'

/** True only for an object-form replacement, never an append with sourceEventSeqs. */
export function isReplacement(event: Record<string, unknown>): boolean {
  const op = asRecord(event.surfaceOp)
  return op?.op === 'replace'
}

/**
 * Resolve the single original surface node from a replacement.
 * startSeq/endSeq are authoritative; sourceEventSeqs may contain earlier sources.
 */
export function replacementSourceSeq(event: Record<string, unknown>): number | undefined {
  const op = asRecord(event.surfaceOp)
  if (op?.op !== 'replace') return undefined
  const start = op.startSeq
  const end = op.endSeq
  if (typeof start !== 'number' || !Number.isSafeInteger(start) || start < 0 || start !== end) return undefined
  const sources = asNumberArray(event.sourceEventSeqs)
  if (sources === undefined || !sources.includes(start)) return undefined
  return start
}
