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

## R6 — turn.render prefix (W13)

`turn.render` gains an optional `prefix` object describing the static cost the request pays on
every turn: `{ toolSchemas?, messageCount?, requestChars?, systemPromptBytes?, approxInputTokens?,
source }`. Every counter is optional; `source` is required and is one of `measured`, `estimated`,
`unknown`. `approxInputTokens` is the harness's own estimate and is never billed tokens.

Why: arXiv:2610.22732v1 §2.2 measures 23 tool schemas loaded on every turn while no repository
calls more than 7, and tool pruning alone recovers 13.2–17.7% of cost. A ledger that models only
pages that get touched cannot see that cost. `source: "unknown"` is a first-class answer: an
adapter that cannot see its request must not report a zero it did not measure.

## R7 — page.declare.toolEffect (W15)

`page.declare` gains an optional `toolEffect` (`READ_ONLY` | `MUTATING`) between `latencyMs` and
`ts`. The class is tagged at tool **registration** by the harness adapter — never inferred from tool
arguments, model text or result content — and it is valid only on pages with
`kind == "tool_result"`, because the class belongs to the tool call that produced the page.

Three laws: registration-owned, name-only, fail-safe. An unregistered tool is `MUTATING`; an absent
key means the adapter could not tell, and a consumer must treat absence the same way. `source`-free:
the key is omitted, never null.

Why: the Trace Engineering thread (@marfinxx, 30 Aug 2026) states the rule and the reason — "a model
that hallucinates an imaginary database schema with perfect JSON syntax returns `status: OK`", so a
status code cannot stand in for a side-effect class. That source is an unmeasured practitioner essay,
so it is cited as a design argument, not as evidence.

Audit only: this revision adds no write-ahead log, no dry-run execution, and no safety property. A
`MUTATING` page records what the tool *can* do, not what this call *did*.

## Compatibility

v0 traces replay byte-identical. v0 validators reject v0.1-only lines (the
sealed boundary). Adapters learn R1 emission in a later card; this card ships
the schema, the replayer exemption, and the normative text.
