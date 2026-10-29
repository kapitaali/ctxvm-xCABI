# RFC-0.1 Proposal — intentional re-execution, provider usage, a capture clock, and the declare turn

**Status: PROPOSAL ONLY. Nothing here is applied.** The sealed surface
(`spec/rfc-0/x-cabi.schema-v0.json`, `spec/rfc-0/RFC-0-xCABI.md`) is untouched;
`02-xcabi-events-v0.md` is untouched. Unsealing is **D4** and belongs to the owner.
This document is the W7 deliverable of `08.1-UPDATE-PROMPT.md`; its fixtures under
`design/rfc-0.1/` are **proposal fixtures**, deliberately not part of the v0 gate.

**Card:** W7 — "RFC-0.1 from umpire's friction" (`08.1-UPDATE-PROMPT.md` §W7).
**Evidence sources:** umpire's committed fixtures (`~/Documents/umpire/fixtures/`,
Apache-2.0, same author); the sealed RFC-0 at `spec/rfc-0/`; W4's audit
(`packages/hermes/OBSERVABILITY.md`); W6's mapping (`design/otel-mapping.md`);
W12's reconciliation (`design/runtime-abi/00-reconciliation-and-justification.md`).

---

## 1. The friction, reproduced

Umpire prices deliberate re-decisions as `page.fault source:"tool_recall"`.
On its A/B demo ledger the ctxvm reference replayer records **three
`faultOfResidentPage` violations** — the pages never left memory; the re-runs are
intended:

```
$ rust/target/release/replay ~/Documents/umpire/fixtures/ab-demo.ledger.jsonl
{
  "events": 6,
  "divergences": [],
  "violations": [
    { "seq": 2, "kind": "faultOfResidentPage" },
    { "seq": 3, "kind": "faultOfResidentPage" },
    { "seq": 5, "kind": "faultOfResidentPage" }
  ]
}
EXIT=0
```

RFC-0 §8 is unambiguous: "A fault MUST target a stubbed page; faulting a resident
page is a conformance [violation]" (`spec/rfc-0/RFC-0-xCABI.md:121`). Violations are
telemetry, not gates (§13), so the replay exits 0 — but every downstream consumer
that classifies faults by source sees three real-looking faults:

```
$ python3 -m benchmarks.metrics.metrics ~/Documents/umpire/fixtures/ab-demo.ledger.jsonl --no-boot
hardFaultRecall: 0.0
```

The `0.0` is **not** a model-behaviour claim: the decision-ledger profile records no
`page.render` facts, so recovery is undefined by construction. The honest reading is
narrower and sufficient: **the three deliberate re-runs are indistinguishable from
hard faults to every classifier keyed on `source`.** W3's ground truth takes
`tool_recall` as a hard fault, so an A/B fixture would feed three false hard faults
into a gate metric.

The proposed fix must also cover the second umpire issue — `model_pin`/`seed` are
excluded from the ref (`spec/ledger_tools.py`: "identical (state, labels) under
another pin/seed is a priced re-decide, not a new identity"). That exclusion is
**correct** and should stay; §3.2 explains why and what replaces it.

---

## 2. Five motivations, one proposal

Each item below has an independent source and an independent reason to move. They
are batched because D4 is one unsealing decision; they do not depend on each other.

| # | Motivation | Source | What RFC-0.1 must add |
|---|---|---|---|
| R1 | intentional re-execution is priced as a paging fault | W7 card; umpire `ab-demo` (3 violations above) | fault source `intentional_rerun` |
| R2 | `model_pin`/`seed` excluded from the ref | W7 card; umpire `spec/ledger_tools.py` | normative clarification only (no schema change) |
| R3 | provider-reported usage has nowhere to go | W4B B3; `packages/hermes/OBSERVABILITY.md` F3; official `post_api_request.usage` | optional `call.meta.providerUsage` |
| R4 | xCABI has no clock; OTel spans are time-less | W6 §3 gap 1; W12 step 1 | optional `ts` on every event, `page.declare.latencyMs` |
| R5 | `page.declare` carries no turn; tool spans cannot parent | W6 §3 gap 3 | optional `page.declare.turn` |

A sixth, infrastructural item (**R0**) is proposed because R1–R5 need a
machine-readable boundary: an optional `session.open.schemaVersion` (`"0.1"`).
Without it a strict consumer cannot tell a v0 trace from a v0.1 trace without
trial-parsing. See §3.6.

---

## 3. Proposed changes

All new fields are **optional and omitted when unknown — never null** (RFC-0 §5
discipline). All integers are non-negative. No floats anywhere. Field order follows
the schema declaration order; new fields append at the end of their event object.

### 3.1 R1 — `page.fault.source: "intentional_rerun"`

Add one value to the closed fault-source enum:

```
faultSource := tool_recall | identifier_scan | explicit_api | semantic | intentional_rerun
```

Semantics (normative, proposed):

1. An `intentional_rerun` row records a **deliberate** re-execution of a page's
   producer — A/B pin comparison, re-seeding, explicit replay — not a paging miss.
2. It **MUST NOT** be reported as `faultOfResidentPage`; it is valid whether the
   page is resident or stubbed. The intent marker, not the residency, decides.
3. It **MUST NOT** be deduped per `(page, source)`: each deliberate re-run is a
   separately priced event. (This differs from every other source.)
4. It is **not** ground truth for recovery metrics: `hard_fault_recall` already
   keys on `tool_recall`/`explicit_api`, so the new value is excluded by
   construction (W3 law, `07-benchmarks-go-no-go.md` §W3).
5. It **is** a cost event: tools that price re-execution count it, with the
   payload's declared tokens and the record sidecar's latency.

Before/after, using the actual umpire ledger (§1):

```jsonl
{"type":"page.fault","turn":1,"page":{"logicalRef":"tool:decide({\"labels\":[...],\"state\":{...}}#7110b419)","contentHash":"sha256:52114663"},"source":"tool_recall"}
```
becomes

```jsonl
{"type":"page.fault","turn":1,"page":{"logicalRef":"tool:decide({\"labels\":[...],\"state\":{...}}#7110b419)","contentHash":"sha256:52114663"},"source":"intentional_rerun"}
```

Full fixtures: `design/rfc-0.1/ab-demo.before.jsonl` (verbatim from umpire) and
`design/rfc-0.1/ab-demo.after.jsonl` (the three rows above changed). Applying the
proposed classification to the after file yields **3 intentional re-runs, 0 paging
faults** (a rule-level check, not a v0.1 replay — no v0.1 replayer exists yet);
under the sealed v0 parser the after file is rejected at line 3:

```
$ rust/target/release/replay design/rfc-0.1/ab-demo.after.jsonl
ctxvm replay: parse error: line 3: invalid event: unknown variant `intentional_rerun`,
expected one of `tool_recall`, `identifier_scan`, `explicit_api`, `semantic`
EXIT=2
```

That rejection is the **expected** compatibility boundary, not a bug (see §4).

**Rejected alternative — an `"intentional": true` flag on the existing source.**
It is orthogonal and therefore tempting, but it leaves every consumer's fault
classifier wrong by default: W3's `hard_faults()` and any dashboard keyed on
`source:"tool_recall"` would include deliberate re-runs unless each is taught the
flag. A distinct source makes the safe behaviour the default. The flag is recorded
as the fallback if D4 prefers a smaller enum change.

### 3.2 R2 — `model_pin`/`seed` stay out of the ref (normative clarification)

No schema change. RFC-0.1 states explicitly:

- Page identity is the pair `(logicalRef, contentHash)`; for a decision page the
  ref is minted from `(state, sorted label set)` **only**. `model_pin` and `seed`
  are pricing/provenance context, carried by the record sidecar, never by the ref.
- A re-execution under another pin or seed is **R1**, not a new page identity.

Why keep the exclusion: including pin/seed would make the same state under a new
seed a *different* page (a `page.declare`, not a priced re-decide), multiply the
page table per A/B arm, and destroy the property umpire exists to measure — that
identical-state re-classifications are priced. The current fixture witnesses the
intent: all four `ab-demo` records mint the same ref; the pin changes between
records 1 and 2, the response hash changes (`sha256:52114663` → `sha256:abf8ca0d`),
and the ledger correctly declares a second slot rather than inventing a new page.
The three priced rows are exactly R1.

### 3.3 R3 — `call.meta.providerUsage`

Add an optional object:

```json
"providerUsage": {
  "inputTokens": 48080,
  "outputTokens": 312,
  "cachedInputTokens": 0
}
```

- `inputTokens` and `outputTokens` are **provider-reported** integers (the harness
  actually observed them); `cachedInputTokens` is optional and provider-reported.
- **Absence means unknown**; the field is omitted, never null, never estimated.
- `cacheEstimate.providerReported` keeps its current meaning — whether the
  hit/miss *split* is provider-reported. The two facts are independent: a harness
  can report total usage without a cache split. Do not infer one from the other.
- The trace's `tokenizerId` does not describe `providerUsage`; those counts are the
  provider's own units. A consumer that needs one unit set must not add them to
  `residentTokens` (the W3/W6 dishonesty trap).

Before (real m7 shape, providerReported false):

```jsonl
{"type":"call.meta","turn":0,"provider":"nvidia","cacheEstimate":{"estHitTokens":0,"estMissTokens":48080,"providerReported":false}}
```

After (Hermes `post_api_request.usage` wired):

```jsonl
{"type":"call.meta","turn":0,"provider":"nvidia","cacheEstimate":{"estHitTokens":0,"estMissTokens":48080,"providerReported":false},"providerUsage":{"inputTokens":48080,"outputTokens":312}}
```

This is W4B B3's routing target; the adapter change follows only after D4.

### 3.4 R4 — a capture clock: `ts` on every event, `page.declare.latencyMs`

Add one optional field to **every** event object:

```
ts : string — RFC 3339 UTC timestamp with milliseconds, e.g. "2026-10-29T15:16:58.123Z"
```

And one optional field to `page.declare`:

```
latencyMs : integer >= 0 — tool wall-clock duration; call.meta.latencyMs already exists
```

Semantics (normative, proposed):

- `ts` is the **emitter's wall clock at append time**. It is capture metadata, not
  replay state: the replayer MUST ignore it when deriving the page table, and MUST
  order events by stream position, never by `ts`.
- `ts` is **omitted in deterministic golden fixtures** (today's vectors stay
  byte-identical); live emitters include it. Determinism claims remain scoped to
  the render structure, not to wall-clock metadata.
- For OTel: a span's start is the event's `ts`; its end is `ts + latencyMs` when
  the duration is present. If a duration is absent, the next event's `ts` is the
  best-effort end and the exporter MUST mark the span as derived (W6 §3).
- `latencyMs` on `call.meta` already exists and remains the LLM-call duration;
  `page.declare.latencyMs` is the tool-call duration (Hermes `post_tool_call`
  carries `duration_ms`). W12's real-latency measurement becomes possible once
  live emitters set these fields.

Before/after:

```jsonl
{"type":"call.meta","turn":1,"provider":"nvidia","cacheEstimate":{...}}
{"type":"call.meta","turn":1,"provider":"nvidia","cacheEstimate":{...},"ts":"2026-10-29T15:16:58.123Z","latencyMs":1240}
```

### 3.5 R5 — `page.declare.turn`

Add one optional field to `page.declare`:

```
turn : integer >= 0 — the turn open when the page was declared; absent = unknown
```

- Replay is unchanged: declarations still take effect at the next render, and
  first-declaration-wins still governs identity.
- The field exists so a tool span can be parented to the turn in which it
  happened (W6 §3 gap 3). Emitters SHOULD set it whenever a turn is open; a
  pre-turn declaration omits it (the v0 "declare is turn-free" rule remains the
  honest shape when no turn exists).

### 3.6 R0 — the version marker

Add an optional `schemaVersion` to `session.open`:

```jsonl
{"type":"session.open","schemaVersion":"0.1","agentId":"…", …}
```

Rules (proposed): an RFC-0.1 emitter MUST set `"0.1"`; a trace without the field is
v0; a consumer that does not know the value must **reject the trace, never guess**.
This also gives W4B B4's observer-contract version a home when a sidecar needs it
(record the emitter's contract alongside the trace's schema version).

---

## 4. Compatibility statement

- **Producer side: additive.** Every RFC-0 event remains valid in RFC-0.1; new
  fields are optional except `schemaVersion` for v0.1 emitters. No existing field
  changes type or meaning.
- **Consumer side: intentionally strict.** RFC-0 validators set
  `additionalProperties:false` and a closed enum, so a v0 strict validator
  **rejects** a v0.1 trace that uses any new field or the new source — demonstrated
  above with `replay` exit 2. This is the sealed-format contract working as
  designed: no silent reinterpretation. Consumers that want both versions branch
  on `session.open.schemaVersion`.
- **Replay semantics.** v0 traces replay exactly as today. The only semantic change
  is R1: a v0.1 replayer MUST exempt `intentional_rerun` from the
  `faultOfResidentPage` rule and MUST NOT dedupe it. Everything else is metadata.
- **Determinism.** The render structure stays a pure function of `(events, turn)`.
  `ts` is excluded from replay state; golden fixtures omit it and stay
  byte-identical.
- **No floats.** `ts` is a string; durations and usage are integers. `providerUsage`
  is never summed with `residentTokens` (different unit systems).
- **Corpus.** Existing drops remain v0 and remain valid. A v0.1 capture is a new
  drop with `schemaVersion:"0.1"` and a manifest version bump; there is no
  retroactive rewrite of any committed trace.

## 5. Migration note

1. **Emitters** (in order of value): set `schemaVersion:"0.1"`; map deliberate
   re-executions to R1 (umpire's builder switches the source, refs and hashes
   unchanged — see §6); include `ts` on live appends; wire `providerUsage` where the
   harness exposes usage (Hermes `post_api_request.usage`, the ai-sdk tap); set
   `page.declare.turn` and `page.declare.latencyMs` where a turn/duration is open.
2. **Consumers**: accept the v0.1 marker, then the optional fields; keep the v0
   path byte-identical. Validators gain a version branch and new negative cases.
3. **Umpire**: after D4, regenerate its four fixture triplets with R1; the page-table
   baselines change only in the fault `source` values. The refs, hashes, and token
   counts are unchanged (byte-compatibility proven in §6).
4. **Metrics**: `hard_faults()` already excludes the new source by construction;
   `net_cost` can prefer `providerUsage` when present; no formula changes are
   required by R2–R5.
5. **Rollback**: because v0 traces are untouched, the unsealing is reversible at
   the schema-file level; a v0.1 trace cannot be silently downgraded, which is the
   desired property.

## 6. Umpire's Python minting vs ctxvm's golden vectors

The card requires the result either way. Ran umpire's `spec/ledger_tools.py`
against the node reference `packages/node/src/ident.ts` (`@361043e`):

```
decide MATCH      # 4 cases, incl. labels-order scrambling and >120-char truncation
hash MATCH        # 4 contents
approx MATCH      # 9 lengths
canon MATCH       # nested key-order canonicalization
CROSS-IMPLEMENTATION: BYTE-IDENTICAL

umpire committed fixtures re-minted: 17 records, mismatches=0
```

**Verdict: byte-compatible, but NOT an independent implementation.** Umpire's
module header declares itself a "Python mirror of `ctxvm/packages/node/src/ident.ts`
@ 361043e — byte-compatible for ASCII-only payloads". A mirror that passes is a
conformance check, not a second implementation; the repo may **not** claim "second
implementation" on this evidence. If an independent minting is wanted, it needs a
different author/codebase and the same vectors — an explicit future ask, not this
card.

Caveats recorded: ASCII-only scope per umpire's §2 rule; floats are banned by both
sides; `labels` are sorted-unique by umpire's `decide_ref` law (the comparison
applies that law to the node side too); non-ASCII payloads were not part of the
committed vectors.

## 7. What approval would change (D4)

If the owner approves RFC-0.1, the follow-on card is mechanical and testable:

1. Add `spec/rfc-0.1/x-cabi.schema-v0.1.json` (v0 file stays sealed for reading).
2. Teach `spec/rfc-0/validate_schema.py` the `schemaVersion` branch and add the
   negative corpus (unknown source, negative usage, malformed `ts`, negative turn).
3. Teach the replayer R1 (exempt + no-dedupe) behind the version branch; add its
   unit tests.
4. Add v0.1 proposal fixtures to the conformance suite only after they are valid;
   keep v0 vectors byte-identical.
5. Update `07` §W3 (intentional re-runs are not ground truth) and `02`/RFC text.

Nothing in this list is started here.

## 8. Decisions requested (D4)

1. Approve **R1 as a new source** (`intentional_rerun`) rather than an
   `intentional` flag? (Recommendation: source.)
2. Approve **R2 as a clarification only** (pin/seed stay out of the ref)?
3. Approve **R3–R5 as optional additions**, with R0 (`schemaVersion`) as the
   version boundary?
4. Approve the **scope split**: RFC-0.1 = these six items; everything else (e.g.
   a sidecar contract-version slot, provider cache-write split) waits.
