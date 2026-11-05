# W20 — four trace-surface extensions, priced before they are built

**Status:** design note only. Four proposals, each with a shape, a cost, a non-claim and the decision
it needs. **Nothing here is implemented**, and none of it may be described as a safety feature: three
of the four add fields the format does not have, and the fourth adds evidence the format cannot
produce by itself.

**Why one note for four items.** They share one constraint. RFC-0.1 is *additive*: a new optional
field on an existing event, declared before `ts`, gated on `schemaVersion "0.1"`. A new event type is
not additive — it would need v0.2, a new envelope, and a replay path that does not exist. So every
proposal below is either a field, a sidecar, or a refusal to proceed.

## 1. Refusals and policy version

**Question.** When a model declines a request, what does the trace say?

**What exists.** Nothing. A refusal today looks like an assistant message with no tool call: a turn
with a render, no declares, no faults. A trace cannot distinguish "declined" from "answered in prose"
or "the harness never sent the request".

**Why a field and not an event.** A `turn.refusal` verb would break the nine-verb envelope. The
additive shape is a field on `turn.render`, before `ts`:

```json
{ "type": "turn.render", "turn": 7, "residentTokens": 1204, "evictedTokens": 0,
  "headroom": 198796, "prefix": { "source": "measured", "toolSchemas": 21 },
  "outcome": { "kind": "refusal", "policy": "provider-default",
               "policyVersion": "2026-09-01", "category": "harm" }, "ts": "..." }
```

**The honest difficulty.** `turn.render` is stamped at render time (the snapshot law: re-flush must
re-derive identical bytes). A refusal is known only after the response. Two ways out, and the choice
is the owner's:

| Option | Cost | Risk |
|---|---|---|
| Cache the outcome per turn and stamp it in the re-derived tail | same five touchpoints as W13 | a mid-session flush before the response omits it; the last flush is the record, so a crash between response and flush loses it |
| Sidecar `<file>.outcomes.json`, one row per turn | no schema change; a checker like W17's | not replayed by `ctxvm replay`; a second artifact to keep honest |

**Non-claim.** Recording a refusal is not a judgement that it was correct, and `policy` is whatever
the harness says it is. A trace that says `policyVersion "2026-09-01"` proves only that a harness
claimed that string.

**Decision needed:** field or sidecar, and who supplies `policy`/`policyVersion` (provider, harness, or
operator). Until that is answered, an implementation would invent a taxonomy.

## 2. Page provenance and trust attributes

**Question.** Can a page say where it came from and whether it may be trusted?

**What exists.** `page.declare` carries `page{id, kind, tokens, ...}`, `turn`, `latencyMs`,
`toolEffect`. Kind is a content shape (`tool_result`, `file`, `summary`, `image_ref`), not an origin.

**Proposed shape**, additive on `page.declare`, before `ts`:

```json
"origin": "user | tool | retrieval | model | system",
"trust": "trusted | untrusted | unknown",
"readers": ["compose", "tool:write_file"]
```

- `origin` is asserted by the harness at declaration. It is not inferred from content.
- `trust` defaults to `unknown` and is never inferred. A harness that cannot classify says so.
- `readers` is optional; absence means "unrestricted", and a policy layer that needs it must fail
  closed rather than assume the page is safe to propagate.

**What it enables.** A CaMeL-style layer (arXiv:2503.18813) needs exactly control/data flow plus a
capability policy. These three attributes carry the data-flow half inside the trace, and W15's
`toolEffect` already carries the call's side-effect class. **What it does not do:** enforce anything.
The check would live in the harness, and a trace cannot prove the harness ran it.

**Cost.** Three optional fields, five touchpoints each, plus a validator negative per default rule
(`trust` absent ≠ `trusted`). The real cost is adapter work: each lane must know the origin of what it
declares, and a lane that guesses would poison the field.

**Decision needed:** is `trust` asserted by the harness or by policy configuration? And does an
unclassified page block a run, or merely get recorded?

## 3. Paging as an attack surface

**Question.** If an adversary can influence what gets evicted, what does that buy them?

**The mechanism.** Eviction is a policy decision over content the model may have authored in part.
Three attacks follow, and none needs a vulnerability in the tracer:

1. **Safety-instruction eviction.** Inflate context so the page carrying operator instructions is
   evicted, then act without it.
2. **Thrash induction.** Force repeated re-fetches of attacker-controlled pages, which re-injects the
   attacker's text at every turn.
3. **Re-fetch laundering.** Get a page evicted and later re-fetched, so its content arrives again with
   a fresh `tool_recall` fault — indistinguishable, in the event stream, from a legitimate recall.

**What the trace can show.** `page.evict` rows with the page identity, `turn.render` pressure before
and after, and the faults that follow. A first detector is mechanical: an eviction row with no
preceding budget pressure, or an eviction of a `trust: trusted` page (once §2 exists), is a signal
worth a monitor.

**What is missing.** The corpus has no adversarial capture, and `corpus/m1`–`m8` contains no eviction
attack. Until §2 lands, "was the evicted page important?" is unanswerable.

**Experiment, if the owner wants it.** One synthetic harness, one attacker page with a known marker,
three arms (no eviction, policy eviction, adversary-influenced eviction). Metric: how often the marker
survives into the next turn's context, and whether the operator-instruction page is gone. That is a
tier-2 run (`design/W19-tier2-interventions.md`) and inherits its non-determinism.

**Non-claim.** This note proposes an audit surface, not a defence. No mitigation is specified.

## 4. Tamper evidence

**Question.** A checksum proves a file has not changed since it was written. What would prove it was
written by the harness that claims to have written it?

**What exists.** Per-drop `checksums.sha256`, and W17's `traceDigest` inside the coverage sidecar. Both
are integrity against accidental change by a party without write access to the directory. Neither is
tamper evidence against a party that can rewrite both the trace and the checksum — which is the same
party in every realistic audit.

**Options, cheapest first:**

| Option | What it buys | Cost | Verdict |
|---|---|---|---|
| Hash chain: each event carries `prev` (hash of the previous line) | detects insertion, deletion, reordering even if all files are rewritten | one field per event; breaks v0 byte-identity; replay must verify the chain | strong teeth, high cost — a v0.2 conversation |
| Merkle root over the file + detached signature | offline verification against a key that never touches the trace directory | signing key management; one sidecar | best ratio; recommended if the owner wants any tamper evidence |
| Append-only remote log (transparency log) | third-party verification of "this existed at time T" | infrastructure, privacy decision | strongest; out of scope for a local-first tool |
| Harness attestation (TPM/TEE) | proves *which binary* produced the bytes | platform-specific | out of scope |

**Recommendation.** Sign the Merkle root, ship the verification command, and say plainly that an
unsigned trace is only as trustworthy as its directory. Anything more requires infrastructure this
project does not have and a privacy decision the owner has not made.

**Non-claim.** A signature says the bytes were signed. It does not say they are true, and it does not
make the harness honest.

## Decision table

| # | Extension | Shape | Owner decision | Blocker |
|---|---|---|---|---|
| 1 | Refusal + policy version | field on `turn.render` or sidecar | field vs sidecar; who owns `policyVersion` | taxonomy would otherwise be invented |
| 2 | Page origin/trust/readers | three fields on `page.declare` | harness-asserted vs configured; fail-closed? | adapter must know the origin |
| 3 | Paging attack surface | none (audit + experiment) | run the tier-2 experiment? | needs §2 for "important page" |
| 4 | Tamper evidence | signed Merkle sidecar | key management; is signing in scope at all? | none, but it changes the product claim |

## Acceptance tests for any implementation

1. A new field is declared before `ts` in the Rust struct, added to `FIELD_ALLOWLIST`, added to the
   schema branch with `additionalProperties: false`, gated in `check_version`, and has a validator
   negative plus a conformance vector — the five touchpoints, no exceptions.
2. Absence is `unknown`, never a default that flatters: `trust` absent must not read as `trusted`;
   `origin` absent must not read as `user`.
3. A refusal record without `policyVersion` is rejected by the validator, not silently accepted.
4. A tamper-evidence verifier fails closed: a missing signature is a failure, not a warning.
5. No test asserts that any of these fields make a run safer.

## What this note does not do

- It does not implement any of the four.
- It does not claim the trace can police a model. Three of the four add *record*, one adds *evidence of
  authorship*; none adds *control*.
- It does not pick the owner's trade-offs. Each row in the decision table is a question, not a plan.
