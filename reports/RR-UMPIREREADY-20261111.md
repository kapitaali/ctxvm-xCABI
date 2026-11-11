# RR-UMPIREREADY-20261111 — G1 and G2 are ready to apply on the owner's word: insertion points verified
## today, texts verbatim, and G2 is NOT a no-op (the transfer caveat is missing; the caveat already in
## the MCP is a different, weaker one)

Card: the review side's pre-flight for the two owner-ratable umpire edits still on the board — **G1** (the
ordering clause, from packet P4) and **G2** (the calibrated-confidence caller sentence, from packet
P5). Nothing is applied: both surfaces are owner-gated ("No umpire edit without owner approval" — the
P4/P5 cards), and this lane writes no umpire byte. What this card does is make the owner's word a
one-step edit.

## 1. G1 — the ordering clause: text, insert point, D-number

**The clause, verbatim** (`reports/RR-P4TS-20261109.md`, drafted 2026-11-09, awaiting approval):

> **Ordering (informational, not validator-enforced):** Within a ledger, event line order is the
> decision order (`session.open` is first, and one decision = one turn). Ledger events carry no
> wall-clock `ts`: RFC-0.1 R4's optional `ts` is purposefully unused in this profile, because
> unbounded wall-clock emission would make the §4 byte-identity audit unreproducible. An absent
> `ts` therefore means **unknown, never zero**, and line order implies no order across ledgers.
> A consumer needing cross-session order must supply its own semantics; per the 2026-11-09 P4
> record, none exists on the books (W14 keys per environment; the A5 analysis is single-session;
> `latency_ms` rides the records sidecar, not the ledger).

**The insert point, re-verified today** in the umpire repo (`~/Documents/umpire/00-SPEC.md`): §2
"Decision-ledger v0 — an xCABI-0.1 profile" holds the profile-constraints paragraph **L1–L5 at lines
37–43**, and the next heading "### Identity minting" is at **line 45** — so the clause goes at line 44.
The card's own citation ("L1–L5 end at `:45`") has drifted by one line; the *place* is unchanged and
this card records the current numbers.

**Documentation-only, deliberately:** the clause claims **no L-number** (the L1–L5 list is "all enforced
by the validator"), so there is **no validator change and no negative** — the clause documents what the
validator already implies. Nothing in ctxvm's Rust/TS/Python nodes changes.

**The D-number is FRESH: the next free id is `D-U10`.** The A6 register is
`design/umpire-design-choices.md` — **in this repo** (4,340 B) — and it holds **D-U1 … D-U9**, none of
which is a `ts`/ordering candidate ("the A6 register's D-U1–D-U9 contain no ts candidate, so this is a
new decision, not a ratification", `RR-P4TS-20261109.md` §1). So the ratification is *two* edits in two
repos: a `D-U10` entry here, and the clause in the umpire books there.

**No contradiction to reconcile (checked today).** The umpire spec has **no** ordering or `ts` statement
at all — the only ordering language in it is `canonicalJson(v)`'s "recursively key-sorted compact JSON"
(`00-SPEC.md:47`), which is a **hash-input** rule, i.e. the domain of the RFC-0.1 note's **C3**, not of
**C2** (key order *within* an event) and not of this clause (line order *between* events). The three
surfaces are disjoint, so the clause can land without touching the D18 note.

## 2. G2 — the caller sentence: text, insert surfaces, and why it is not a no-op

**The sentence, verbatim** (`reports/RR-P5CAL-20261110.md`, the reviewer's own wording):

> Calibrated confidence was fitted on umpire's own label sets and has not been shown to
> transfer, so treat it as an uncalibrated score for your labels until you check it on a sample
> of your own labelled rows.

**The insert surfaces, re-verified today** in the umpire repo:

| surface | locator | current text |
|---|---|---|
| MCP server instructions | `umpire/mcp_server.py:67-77` (`INSTRUCTIONS`) | already carries a *different, weaker* caveat: "calibrated.confidence = fitted P(key is correct) … **it is not a correctness guarantee and is opt-in**" |
| `decide` tool description | `umpire/mcp_server.py:80-85` | lists the returned fields, no confidence caveat |
| spec, calibrated view | `umpire/00-SPEC.md:90-109` (§3 "Calibrated view (M2, optional)") | "Raw fields remain authoritative: calibration is a measurable layer with its own version, not a mutation of the decision or its identity." — no transfer caveat |

**So G2 is genuinely missing, not already done.** What the MCP carries today ("not a correctness
guarantee and is opt-in") is a *different* claim — it says the number is not a promise and is
optional. The substance of G2 (and of the P5 answer it comes from: **publish per-corpus calibration WITH
the caveat, no transfer claim**) is the **transfer** caveat: the calibration was fitted on umpire's own
label sets, was not shown to transfer, and a caller must therefore treat it as uncalibrated for its own
labels until it checks a sample of its own labelled rows. That sentence appears **nowhere** in the MCP
text or in `00-SPEC.md` §3 — checked by reading both today.

**The ratification home is also this repo:** the D-U register's **D-U1** entry is exactly the choice in
question ("### D-U1 — Calibration scope (seed: corpus-fitted calibration transfers?)" — options:
(a) per `(pin, seed, label set)` artifacts only; (b) per-pin generic calibration + label-set adaptation;
(c) no calibration, raw only). The P5 answer selects (a) with the caveat. One mechanical wrinkle for the
owner to settle: the register's own header reads "**inputs only, no choice made**", so recording a
choice needs either a per-entry "Resolved" line or a new section — this lane's recommendation is a short
"## Resolved" section at the end of the register (one word of the header changes with it), so the
register keeps its "inputs" character for the still-open D-U2…D-U9 while recording what has been decided.

## 3. What the owner's approval would cover, and what it would not

- **Would touch (umpire repo, owner-gated):** `00-SPEC.md` (G1's clause at line 44; optionally G2's
  sentence in §3's calibrated view), `mcp_server.py`'s `INSTRUCTIONS` and/or the `decide` description
  (G2's sentence) — plus the umpire books' own LOG row and day file, as the P4 card anticipated.
- **Would touch (this repo, this lane's, after the ruling):** `design/umpire-design-choices.md` — a
  `D-U10` entry for **G1** (the fresh decision) and a resolution line under **D-U1** for **G2** (the
  ratified choice) — plus the ctxvm card, LOG row and day file.
- **Would not touch:** `spec/rfc-0/` (sealed), the RFC-0.1 note's clauses (C2/C3 are a different surface),
  the vendored 0.1 validator, the four umpire fixtures, the live ledger, the calibration artifact, or
  anything in ctxvm's Rust/TS/Python nodes. No model spend, no new D-number minted without the owner's
  word.

## 4. Executed agent-doings

- Both insertion points were re-verified **today** in the umpire repo at the cited lines (L1–L5 at
  37–43; "### Identity minting" at 45; `mcp_server.py` INSTRUCTIONS 67–77 and tool description 80–85;
  `00-SPEC.md` §3 at 90–109), and the one-line drift in the P4 card's citation is recorded.
- The umpire spec was searched for any existing ordering/`ts` statement (there is none; only
  `canonicalJson`'s key-sorting, a hash-input rule) so the clause's non-contradiction is checked, not
  assumed.
- The MCP text and the spec's calibrated-view section were read in full to establish that G2's
  *transfer* caveat is absent and that the caveat already present is a different one.
- The D-U register was located in this repo (`design/umpire-design-choices.md`, 4,340 B), D-U1 and D-U9
  were read, and the next free id for G1's fresh decision is recorded as **D-U10**.
- Kit: this card + LOG row + a day-file line + the roadmap's G1/G2 entries. No umpire byte and no
  spec byte changed; nothing pushed.
