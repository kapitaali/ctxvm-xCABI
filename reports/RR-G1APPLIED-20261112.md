# RR-G1APPLIED-20261112 — G1 is applied: the ordering clause in `umpire/00-SPEC.md` §2 and D-U10 in
## the register, with the owner's wording change (the dated facts moved out of the clause)

Card: the owner approved packet P4's ordering clause on 2026-11-12 (reviewed) with one wording change.
It is applied, in two repos.

## 1. The two edits

**The umpire repo — `00-SPEC.md` §2**, inserted **after the profile constraints (L1–L5)** and **before
"### Identity minting"** ✓ — the insertion point the P4 card named, re-verified against the file before
the edit ✓ (the L1–L5 paragraph is at `:37-43`, the heading at `:45`):

> **Ordering (informational, not validator-enforced):** Within a ledger, event line order is the decision
> order (`session.open` is first, and one decision = one turn). Ledger events carry no wall-clock `ts`:
> RFC-0.1 R4's optional `ts` is purposefully unused in this profile, because unbounded wall-clock emission
> would make the §4 byte-identity audit unreproducible. An absent `ts` therefore means **unknown, never
> zero**, and line order implies no order across ledgers. A consumer needing cross-session order must
> supply its own semantics.

**The ctxvm repo — the register**, `design/umpire-design-choices.md`, gained **D-U10** ("Ledger ordering
and `ts`"), carrying the ruling (`ts` stays **optional**, paired with a consumer rule ✓), the rejected
options — (a) make `ts` mandatory: refused, it breaks the v0-only emitters and the 0.1/v0 asymmetry and
needs a version gate above 0.1; (b) leave it unstated: refused, a consumer then has no rule for an absent
`ts` and "unknown" would be read as "zero"; (c) optional plus a consumer rule: **adopted** ✓ — and the
independence from the D18 note (C2 is key order *within* an event, C3 the canonical form of *hash
inputs*, this is event order *between* lines ✓).

## 2. The owner's wording change, applied

The clause as drafted in the P4 card ended with a parenthetical of **current repo facts** — *"per the
2026-11-09 P4 record, none exists on the books (W14 keys per environment; the A5 analysis is
single-session; `latency_ms` rides the records sidecar, not the ledger)"* — which would go stale. It was
therefore **removed from the clause** and **moved to the D-U10 entry**, where the rationale and the dated
facts live ✓. What remains in the clause is timeless ✓: the ordering rule, the absent-`ts` meaning, the
no-cross-ledger-order rule, and the consumer's own duty.

## 3. What was not touched, and why it matters

- **No validator change and no negative** ✓ — the clause claims no L-number (the L1–L5 list is what the
  validator enforces; this clause is explicitly *informational*), so law 2's "version-branch the
  validator, never loosen it" is not engaged ✓.
- **No ledger, fixture, corpus or artifact byte changed** ✓ — the clause describes what the profile
  already does: the emitter writes no wall-clock `ts`, which is what keeps the §4 byte-identity audit
  reproducible ✓.
- **The umpire gate is ALL GATES GREEN** after the edit ✓ (umpire commit `1f7eae8`, card
  `reports/RR-G1ORDER-20261112.md` in that repo).

## 4. Executed agent-doings

- The approval was applied as a **specification edit to the umpire books** ✓, with the ruled wording
  change ✓ and the insertion point re-verified against the file rather than taken from the card ✓.
- The register entry was written with the rationale, the rejected options and the dated facts ✓.
- Kit (ctxvm): this card + the D-U10 entry + the LOG row + the day file + the roadmap's G1 entry (ticked,
  *Done when* met ✓) + PROJECT-STATE. The umpire-side edit is recorded in the umpire repo's own books ✓.
  Nothing published, nothing pushed ✓.
