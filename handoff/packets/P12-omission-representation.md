# Packet P12: representing omission — what should a trace say about a page that left the request?

STATUS: queued 2026-11-13. The lane's own work is done first (the kit's law): the five questions are answered
in `reports/RR-OMISSION-20261113.md` (proposal-only). The owner's decision is D19.

## Question

Q1. Is the recommended shape right — count + identity, checked, identity ON THE WIRE (an RFC-0.1 per-turn
dropped-page list on `turn.render`) — or in the SIDECAR (free, but Part I §12's "a pure function of a trace"
must become "of a trace and its sidecar")?

Q2. Is the check rule right PER CALL (the sidecar's per-call `before − after` vs the engine's per-call removed
tokens), given the trace's counter is a LAGGING CUMULATIVE?

Q3. The SCOPED VIEW (which pages existed at turn N): the lane says it CANNOT REPLACE the table projection (one
engine; whole-table residency) and must be an ADDITIONAL export field — or should the recorded field's
semantics change?

## Constraints

- v0 is sealed; RFC-0.1 is additive and version-gated (five touchpoints; `ts` last). The checker and the
  adapter are the hermes lane's — this lane proposes.
- The paper forces the choice: Part I §12 calls a view "a pure function of a trace", so an omission invisible
  on the wire makes that false FOR REMOVAL POLICIES, and "leave it unrepresented" contradicts the paper.
- No `page.evict` with an empty stub — it asserts a substitution that never happened ("a missing event is a
  gap; a wrong event is a falsehood", `RR-W8CEVICT` §3).

## Evidence

1. The gap: the derived table claims 21 pages / 86,569 tokens (turn-invariant), the request carried 12 pages /
   47,805; v0 has NO omission verb (`page.evict` requires `stubText`); `turn.render.evictedTokens` is unchecked
   in v0 (OPEN T-OVICT) and is a LAGGING CUMULATIVE (210,856 = 5.44x the unique 38,764); the derived table is
   NOT turn-scoped (the cut is positional); the provider's receipts witness the removal (paged ÷ control =
   0.563 at turn 19 vs the trace's 0.570) => the derived table is the false part.
2. The checker's EXISTING rule: version-gated (`plugin.version >= 0.13.2`, arm not `control` —
   `evictedPagesCount` must be positive) and DORMANT on the capture that needs it (its plugin block has NO
   `evictedTokens` key, so the precondition is false).
3. The coupling: the export's projection and the replay's inference are ONE ENGINE (`export.rs:149-154`,
   `replay.rs:59,76`); the recorded residency is whole-table, so a scoped REPLACEMENT would make v0.1 captures
   DIVERGE; it must be an ADDITION — and RFC-0.1 R5 already puts `page.declare.turn` on the wire, so the data
   exists and the cheap half is free.

## Output wanted

1. Does the shape hold — count + identity ON THE WIRE + a PER-CALL check — or the sidecar route?
2. Is the PER-CALL rule the right form, or per-turn — and is "addition, not replacement" right for the scoped
   view?
3. The falsifier: the observation that would change the recommendation; mark UNKNOWN what the packet cannot
   decide.
