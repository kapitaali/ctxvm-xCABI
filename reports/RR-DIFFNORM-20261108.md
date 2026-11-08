# RR-DIFFNORM-20261108 — Packet 1 answered: the cross-harness claim split, the consumer-side diff-normalisation profile authored

Card: assimilate the external reviewer's Packet-1 answer into the kit (QUESTIONS/PROJECT-STATE/packet
status) and, on the owner's explicit clearance (the lane's `design/**` read-never-edit scope was lifted
for this request in-session), author the proposal card `design/diff-normalisation.md`. Nothing else in
`design/`, `spec/`, `packages/`, `corpus/`, or `research/**` changed; no capture behavior, no schema
byte; the card mints nothing (§5 of the card: "this proposal mints nothing" — implementation and
`--profile` wiring are future cards, not this one).

## Verdict sentence

D13 is answered on the record: the Pillar-1 sentence splits — replayable and conformance-testable stay
(unqualified), "diffable" becomes qualified by a consumer-side normalisation profile, "reconstructs
any turn" is narrowed to within-trace derivation, and the absence claim becomes a scoped "we found
none in this review"; the proposal card exists (`design/diff-normalisation.md`) and its OP-N2 carries
the verdict's (a)/(b)/(c) with (a) adopted and (b) deferred — all of it waiting only on owner
ratification and the white-paper lane's edit routing.

## The reviewer's verdicts (verbatim content, recorded 2026-11-08)

1. **Split, don't narrow all the way.** Replayable + conformance-testable supported; "diffable" not
   supported as written; "reconstructs any turn" not supported. Replacement sentence (quoted in the
   card §1 and in QUESTIONS P1): traces from different harnesses validate against one schema and
   replay in one engine … a cross-harness diff needs the normalisation rules proposed in RFC-0.1.
   Absence claim → "We found none in this review," with search scope stated; falsifier = a
   third-harness trace that fails validation or replay.
2. **Consumer side, not capture.** Canonicalising at capture would destroy harness faithfulness; a
   versioned diff-time profile of mapping tables per harness needs no wire change; additive RFC-0.1
   only if analysis shows a truly needed field.
3. **N1 and N3 as rules, N2 (page-body semantics) as an open problem** — hash mismatches reported as
   their own divergence class; canonical-hash field deferred; ties to Part II §9.7. Sub-check the
   reviewer requested: whether the RFC-0.1 `turn` field already defines the unit.
4. **Apply the same fix at `:635` and sweep echoes** ("same bytes", "byte-identically", "any
   harness"); the paper is the white-paper lane's file — route the edit through the owner, apply to
   the working-tree revision, not committed HEAD bytes.

The reviewer worked only from the packet and flagged exactly that dependency; every packet citation
was verified against the books before recording: Pillar-1 at committed HEAD `:115` / working-tree
`:117` (grep, both files), the W5 classification row intact at `08-HANDOFF.md:970` (D1/D2, D3, D4
hermes `pre_llm` once per user turn, "W7 intake = 5 items"), and `page_id` = `(logical_ref,
content_hash)` verbatim at `rust/crates/ctxvm-codec/src/model.rs:14–21`.

## The `turn` unit check (the verdict-3 sub-question)

`spec/rfc-0.1/x-cabi.schema-v0.1.json` types `turn` as `{type: integer, minimum: 0}` with no
description (checked at both the `page.declare` and `page.evict` sites, 2026-11-08), and normative text
R5 (`spec/rfc-0.1/*` §R5) says only "`page.declare` gains an optional `turn` (integer >= 0)". So the
unit is NOT in the wire layer today; the profile defines the mapping itself (card §3 N3), and a wire
normative clarifier would be an owner-gated additive card.

## Files touched, verified

- `design/diff-normalisation.md` — NEW, proposal-only (the one `design/` file this lane has ever written;
  owner-cleared). Sections: problem (W5-located), diff-time placement, the three profile rules,
  fail-closed + falsifier, out-of-scope minter list, three owner questions.
- `handoff/QUESTIONS.md` — P1 row updated to **answered 2026-11-08** with the two-line verdict
  summary; `handoff/packets/P1-cross-harness-claim.md` gains a one-line STATUS header;
  `handoff/PROJECT-STATE.md` — header delta, Done/In-progress/Next reflowed, D13 line rewritten to
  ANSWERED; sizes: PROJECT 5,217 → 5,361/6,144, QUESTIONS 1,139 → 1,765/3,072, P1 packet 2,614 →
  2,752/3,072 (all `wc -c`).
- Commands: `bash tools/check-handoff.sh` → exit 0 (8,140/8,192 for the pack); `session-start.sh
  N --with-context` for N=1,2,3 → 16,257 / 15,699 / 16,111 bytes, all exit 0. The assimilation first
  pushed the worst-case paste to 16,567 — the tool caught it and named the cut target exactly as the
  owner's review forecast; PROJECT was then compressed (D13 line + Next reflow) so it fits again with
  a 127-byte margin. Fix 3's discipline is now enforced evidence, not just structure.

## Open questions carried into the card (§6)

1. Profile registry: how a consumer learns which profile to load (session.open's W5 D7/R2 fields vs an
   explicit profile id).
2. N3 tie-breaks need the pair's live replay before any implementation card.
3. OP-N2 (b) stays deferred until Part II §9.7 rules on content-bearing capture.

## Limitations

- The card is proposal-only text: no consumer implements it yet, so no claim of working software.
- The verdicts rest on ONE cross-harness pair (W5). More pairs (ai-sdk not yet seconded) can move N1's
  table; the falsifier is written precisely for that reason.
- The paper echo sweep has not run — `research/**` is another lane's file; until the routed edit lands,
  Part I still says what it says at `:115` (HEAD) / `:117` (WIP).
