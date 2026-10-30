# RFC-0.1 — xCABI Additive Extension

**Status:** Applied (D4 approved 2026-10-30). Additive to RFC-0 (sealed).
**Scope:** new files under `spec/rfc-0.1/` only. RFC-0 (`spec/rfc-0/`, `02-xcabi-events-v0.md`) is untouched.

## R0 — Version boundary

A trace MAY declare `schemaVersion: "0.1"` on its `session.open` line. A trace
without the field is a v0 trace. A consumer that does not know the value MUST
reject the trace; it MUST NOT guess. Unknown `schemaVersion` values are rejected.

## R1 — intentional_rerun

`faultSource` gains the value `intentional_rerun`: a deliberate re-execution of
a page. An `intentional_rerun` fault is valid whether the page is resident or
stubbed. A v0.1 replayer MUST exempt it from the fault-resident rule (no
`faultOfResidentPage` violation) and MUST NOT dedupe it per `(page, source)`:
each deliberate re-run is a separately priced event. This differs from every
other source. `intentional_rerun` is never ground truth for W3 waste metrics.

## R2 — model_pin out of ref

`model_pin` is excluded from the page ref (validated by capture where
`model`/`provider` are `unknown/unknown`).

## R3 — call.meta providerUsage

`call.meta` gains an optional `providerUsage` object: `{ inputTokens,
outputTokens, cachedInputTokens? }` (integers >= 0). Omitted (never null) when
the provider did not report.

## R4 — timestamps

Every event gains an optional `ts` (RFC 3339 UTC, millisecond precision).
`page.declare` gains an optional `latencyMs`.

## R5 — turn on page.declare

`page.declare` gains an optional `turn` (integer >= 0).

## Compatibility

v0 traces replay byte-identical. v0 validators reject v0.1-only lines (the
sealed boundary). Adapters learn R1 emission in a later card; this card ships
the schema, the replayer exemption, and the normative text.
