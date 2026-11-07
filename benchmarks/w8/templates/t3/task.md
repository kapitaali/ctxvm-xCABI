# Task T3 — spec-to-code compliance deltas

The workspace holds the twenty source modules of `packages/*/src` as line-aligned parts.
`MANIFEST.tsv` maps every `*.partNN` file to its logical path and line range; concatenating
a file's parts in manifest order reproduces it exactly.

Five conformance behaviours are stated below. Each is an implication over a module's text.
For each behaviour, decide which of the twenty modules violate it and write the answer as
**`deltas.json` in the workspace root**.

## Deliverable schema

```json
{
  "specSource": "02-xcabi-events-v0.md",
  "filesExamined": 20,
  "behaviours": [
    {
      "id": "B1",
      "behaviour": "<short restatement, not judged>",
      "predicate": "<the implication, not judged>",
      "examined": 20,
      "violators": [{"file": "packages/node/src/tracer.ts", "trigger": "JSON.parse"}]
    }
  ]
}
```

* `behaviours` has exactly the five entries below, in this order.
* `violators` lists, in ascending path order, every module that satisfies the antecedent
  but not the consequent. `trigger` is the exact token from the antecedent that the module
  contains (for a two-token antecedent, the one it actually contains). A module that does
  not contain the antecedent is not a violator — it is out of scope for that behaviour.
* The prose fields are not judged; the ids, `examined` and the violator lists are.

## The five behaviours

A token counts as present when that exact string occurs anywhere in the module's text.

* **B1 — strict codec.** A module that parses trace JSON (`JSON.parse` or `json.loads`)
  must declare an allowlist, because the codec rejects unknown fields rather than dropping
  them: the module must also contain `allowlist` or `ALLOW`.
* **B2 — wire order.** A module that reads `providerUsage` must also read `latencyMs`
  (`latencyMs` precedes `providerUsage` on the wire).
* **B3 — line stamping.** A module that emits a trace line — it contains `page.declare` or
  `turn.render` — must name `schemaVersion`, which every line carries.
* **B4 — fault taxonomy.** A module that handles `page.fault` must name an RFC-0.1 fault
  source: `identifier_scan` or `tool_recall`.
* **B5 — eviction tally.** A module that handles `page.evict` must name `evictedTokens`,
  the tally field the render projection reads.

Read the parts. `deltas.json` must be the only file you create.
