# Packet P11: canonical ordering — sorted keys vs struct order, and who owns the compatibility line

STATUS: answered 2026-11-11 (card RR-P11CANON-20261111.md): ruling (c) owner, (a) as a short POINTER —
test FIRST, then the note states a fact the test enforces (equal parsed model, equal page table, equal
replay report; never equal bytes; with and without `ts`; vector pair + Rust unit test). Two divergences
measured today (astral key order, number forms) TRIGGER the reviewer's third falsifier: a digest over
serialised bytes exists, so the note needs a canonical form for hash inputs only.

## Question

Python/TS canonicalise by sorted keys; Rust roundtrips by struct order; replay accepts either (F9 = ACCEPTED). The friction card proposed documenting it in an RFC-0.1 note - but the kit's P5 is another question, so that line has NO owner. Who owns it?

**Q1.** Which surface owns the "canonical order" line?

(a) ONE line in RFC-0.1's compatibility note (owner + D-number);
(b) umpire's `00-SPEC.md` only (no RFC-0.1 byte);
(c) a CONFORMANCE TEST instead of a note: a ctxvm test that a sorted-keys line and a struct-order line parse to the same model and replay identically;
(d) accept silently.

**Q2.** If (c): what must it assert (parsed model, page table, report?) and where does it live?

**Q3.** If (a): NORMATIVE ordering, or only a compatibility statement? A normative rule would forbid the `ts`-last wire order.

## Constraints

Sealed v0 does not change; RFC-0.1 is additive and version-gated; a doc line is not a field, but a landed RFC's text is owner-gated (D-number). The codec stays strict, so the note must not imply anything new is accepted. `ts` rides LAST (law 3), so the two byte forms cannot be equal.

## Evidence

1. Friction card (`design/umpire-friction-vs-rfc01.md`, F9): "Accept the friction - document, do not change spec"; its note proposal: "sorted vs struct order deserves one line - proposed as packet P5, not applied".
2. The kit's P5 is the calibration question, so the canonical-order documentation has no packet and no owner - the gap this closes.
3. umpire canonical JSON = sorted keys + minimal separators + `ensure_ascii=False` (`~/Documents/umpire/spec/ledger_tools.py:21-23`); Rust roundtrips by struct order (`model.rs:139`+).
4. The crux: `ts` is the LAST field of every Rust event variant (`model.rs:161,:179,:189,:199,:211,:220`) and sorted keys put `ts` BEFORE `type` - the byte forms differ BY CONSTRUCTION, so "both accepted" is the only honest rule.
5. Measured: umpire `validate_ledger.py` PASS (130 checks); ctxvm replay on the ab-demo ledger (6 events, 0 divergences, 0 violations - `RR-UGATE-20261111` §1). NOT measured: a proof that the two orders derive the SAME page table.

## Output wanted

1. The ruling among (a)/(b)/(c)/(d), one line + reason.
2. If (c): the exact assertion + where the test lives.
3. If (a): normative ordering, or compatibility statement only?
4. The falsifier: the observation that would change the ruling.
5. Mark UNKNOWN what the packet cannot decide.
