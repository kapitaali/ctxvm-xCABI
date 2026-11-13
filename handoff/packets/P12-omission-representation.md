# Packet P12: representing omission — what should a trace say about a page that left the request?

STATUS: answered 2026-11-13 (card `reports/RR-OMISSIONANSWER-20261113.md`): ruling = THE WIRE — an
optional, omitted-when-unknown list of removed-page identities with token counts, PER CALL (not per
turn); the sidecar kept as a documented fallback; the check per call and FAIL CLOSED (a capture with
removals and no list is a violation); the scoped view an ADDITION under a new field name, never a
change to the recorded `residentTokens`; no `page.evict` reuse. Owner's decision: D19.

## Question (as asked)

Q1. Is the recommended shape right — count + identity, checked, identity ON THE WIRE (an RFC-0.1 dropped-page
list on `turn.render`) — or in the SIDECAR (free, but Part I §12's "a pure function of a trace" must become
"of a trace and its sidecar")?

Q2. Is the check rule right PER CALL (the sidecar's per-call `before − after` vs the engine's per-call removed
tokens), given the trace's counter is a LAGGING CUMULATIVE?

Q3. The SCOPED VIEW (which pages existed at turn N): the lane says it CANNOT REPLACE the table projection (one
engine; whole-table residency) and must be an ADDITIONAL export field — or should the recorded field's semantics
change?

## Constraints

- v0 is sealed; RFC-0.1 is additive and version-gated (five touchpoints; `ts` last). The checker and the
  adapter are the hermes lane's — this lane proposes only.
- The paper forces the choice: Part I §12 calls a view "a pure function of a trace", so an omission invisible
  on the wire makes that false FOR REMOVAL POLICIES; "leave it unrepresented" contradicts the paper.
- No `page.evict` with an empty stub — it asserts a substitution that never happened ("a missing event is a
  gap; a wrong event is a falsehood", `RR-W8CEVICT` §3).

## Evidence (as measured; locators in the card)

The derived table claims 21 pages / 86,569 tokens while the request carried 12 / 47,805; v0 has NO omission
verb; the counter is unchecked in v0 and a LAGGING CUMULATIVE; the provider's receipts put the paged request
at 0.563 of the control's at turn 19; the checker's existing rule is DORMANT on the capture that needs it; the
export's projection and the replay's inference are ONE ENGINE. Locators: `RR-OMISSIONANSWER-20261113.md`
§1–§3, `RR-OMISSION-20261113.md` §1.

## Output wanted

1. Does the shape hold — count + identity ON THE WIRE + a PER-CALL check — or the sidecar route?
2. Is the PER-CALL rule the right form, or per-turn — and is "addition, not replacement" right?
3. The falsifier; mark UNKNOWN what the packet cannot decide.
