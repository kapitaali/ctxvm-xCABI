# redaction-block.md — the D14 sidecar-first redaction record

Status: **PROPOSAL-ONLY** — a design proposal, not a shipped surface; no wire change is proposed,
so the RFC-0/0.1 additive law (five touchpoints + negative) is not exercised here. Authored
2026-11-09 per Packet 3's verdict 2 (D14 answered 2026-11-08); the carrier card + verify sweep is
`reports/RR-P3REDACT-20261109.md` (LOG `RR-P3REDACT-20261109`), and the owner cleared this
`design/` placement in-session on 2026-11-09 (the P1 precedent lift; kay references:
`diff-normalisation`-scoped). Working title `redaction-block`; the final name is ratified with the
card (Part II cites the card id, never a draft field name).

## Sidecar-first (the chosen first option)

The scanner already stamps its identity — scanner SHA-256, scan-list version `w8-dq-v1`, UTC date —
into every drop's `provenance.json` (`tools/dq-secret-scan.py:18–21`; each corpus drop carries
`provenance.json` + `checksums.sha256`). A redaction record lives beside that stamp with no wire
change, and the artifact that "describes its own redaction after leaving its corpus drop" is then
the drop itself. **A session field is only needed if a trace must describe its own redaction
independently of its drop** — after the trace leaves `corpus/<drop>/` without its sidecars. This
card weighs both and stays sidecar-first; a wire-additive field opens only when a real consumer need
is shown (the D13 posture: capture-side canonicalisation destroys harness faithfulness; the same
conservatism applies).

## Required properties

1. **A stage LIST, not one stage.** Entries for capture, flush, export — each with `policyId`,
   `ruleSetVersion`, `stage`, and `replacedFieldCount` (aligned with Part II §9.1–§9.2's list
   shape: one artifact can be redacted twice). Stage semantics per the paper: capture replaces page
   content before declaration; flush rewrites content fields; export produces a third-party slice.
2. **Absence means "unknown," never "none."** An artifact with no redaction record says nothing
   about redaction — the v0.0-era corpus predates any block, so absence is provably not evidence of
   none.
3. **A reference policy.** One entry per rule set declaring how `logicalRef` was treated — enum
   `raw | keyed-hashed | dropped` — grounded in `RR-FIELDAUD-20261107` ("raw — the leak channel",
   `:44`; "raw, and the dominant surface": 112 raw `tool:` refs in the frozen corpus, `:65–71`; the
   m1 healthy fixture carries `file:src/auth.ts` raw at capture). Today's value is `raw`, declared
   for what it is.
4. **The block is an assertion.** Without tamper evidence — not built (Part II §9.4 still reads "No
   verifier exists") — the record is a claim by the writer, never a proof. The existing scanner is a
   pre-drop LINT, not a verifier (`RR-FIELDAUD-20261107:106–108`: "pre-drop lint, not the draft's
   §9.4 verifier (no stage-list comparator, no third-party standard)") — the card keeps that
   distinction explicit so no "verified" escapes an unverifiable design.

## The keyed-hash disposition (the packet's UNKNOWN)

*Is keyed-hashing refs consistent with page_id minting?* `page_id` is `(logical_ref, content_hash)`
as a `PartialEq/Eq/Hash` identity (`rust/crates/ctxvm-codec/src/model.rs:14–22`). A deterministic
session/drop-scoped keyed hash preserves equality WITHIN one artifact — replay, rendering, and stub
semantics never parse the ref string, they only compare it — so minting stays internally consistent.
The costs are structural: (a) cross-drop joins break (the `environmentId` precedent: hashed +
salted-by-worktree is why the env key cannot join across environments, `RR-FIELDAUD:88–91`); (b) it
collides with the consumer-side diff rule N1 (`design/diff-normalisation.md`) — keyed refs are not
comparable between artifacts, so raw-ref diffs become intra-artifact only; (c) all frozen fixtures
pin raw ref bytes, so any keyed EMITTER needs a declared fixture-regen path.

**Disposition:** the card proposes only the declaration enum; `raw` is the shipped value; enabling
`keyed-hashed` emission stays a future owner-gated card that must pass a golden-vectors test BEFORE
the proposal (the reviewer's precondition — met by not proposing an emitting rule here).
`dropped` is listed as an enum value for completeness.

## Falsifiers

- **Verdict 2:** a seeded-canary test — plant synthetic secrets and personal data in fixtures; if
  the scanner's recall is low, "scan clean" cannot support "redacted" and the card must say so.
  Until the canary exists, "scan clean" claims only "the `w8-dq-v1` pattern list found zero
  matches" (lint strength).
- **Verdict 1 (the consent half, for the sibling plugin card):** a user who runs the plugin without
  reading the docs and cannot tell a trace exists.

## Constraints carried from the packet

`spec/rfc-0` sealed; any wire field = additive RFC-0.1 card (five touchpoints + negative) or a v0.2
design note, owner-gated; privacy law `08.1 §4` (redaction DQ + secrets scan before anything leaves
the machine) stays blocking; default-capture behavior change = plugin card, never a packager
affectation. `contentHash` stays a HASHED surface, untouched (its dictionary-attack caveat is
recorded honestly in `RR-FIELDAUD:84–87`; redacting it is out of scope — it is the page-identity
half that replay consumes).

## Open (explicit UNKNOWN)

- The seeded-canary test does not exist; the tamper-evident chain is not built (Part II lists it
  first among three pieces of work).
- No session field is proposed in this option, so no RFC-0.1 additivity proviso is exercised.
- Whether `stubText`/`reason` mitigation (bounded vocabulary or pre-drop validation — the audit's
  own two static mitigations) lands inside this card or beside it stays with the owner.
- The consent/release-half plugin card (first-run notice minimum; opt-in stronger) binds at D6/D17
  and remains owner-routed code work.
