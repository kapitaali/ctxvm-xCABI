# Packet P11: canonical ordering — sorted keys vs struct order, and who owns the compatibility line

STATUS: queued 2026-11-11 (registered in handoff/QUESTIONS.md).

## Question

Python/TS canonicalise by sorted keys; Rust roundtrips by struct order; replay accepts either (F9 = ACCEPTED). The friction card proposes documenting it in an RFC-0.1 compatibility note "as packet P5" — but the kit's P5 is another question, so that line has NO owner. Who owns it?

**Q1.** Which surface owns the "canonical order" line?

(a) ONE line in RFC-0.1's compatibility note (owner + D-number);
(b) umpire's `00-SPEC.md` only (no RFC-0.1 byte);
(c) a CONFORMANCE TEST instead of a note: a ctxvm test that a sorted-keys line and a struct-order line parse to the same model and replay identically;
(d) accept silently.

**Q2.** If (c): what must it assert — same parsed model, same derived page table, or byte-identical report — and where does it live (vectors or a unit test)?

**Q3.** If (a): NORMATIVE ordering, or only a compatibility statement ("both accepted")? A normative sorted-keys rule would forbid the `ts`-last wire order.

## Constraints

Sealed v0 does not change. RFC-0.1 is additive and version-gated; a doc line is not a field, but a landed RFC's normative text is owner-gated (D-number). The codec stays strict (unknown fields are hard errors), so the note must not imply anything new is accepted. `ts` rides LAST on every event (law 3), so a sorted-key byte form CANNOT equal the struct-order form; no byte-identical-lines claim across crates.

## Evidence

1. Friction card (`design/umpire-friction-vs-rfc01.md`, F9): "Accept the friction — document, do not change spec"; its note proposal: "sorted vs struct order deserves one line — proposed as packet P5, not applied".
2. The kit's P5 is `P5-calibration-transfer.md` — so the canonical-order documentation has no packet and no owner. That is the gap this closes.
3. umpire canonical JSON = sorted keys + minimal separators + `ensure_ascii=False` (`~/Documents/umpire/spec/ledger_tools.py:21-23`); the Rust model roundtrips by struct order (`rust/crates/ctxvm-codec/src/model.rs:139`+).
4. The crux: `ts` is the LAST field of every Rust event variant (`model.rs:161,:179,:189,:199,:211,:220`) and sorted keys put `ts` BEFORE `type` — the byte forms differ by construction, so "both accepted" is the only honest rule. F9 says that; F9 does not say it anywhere a consumer meets it.
5. Measured: umpire `validate_ledger.py` PASS (130 checks) and ctxvm replay on the ab-demo ledger (6 events, 0 divergences, 0 violations — `RR-UGATE-20261111` §1). NOT measured: a proof that a sorted-keys line and a struct-order line derive the SAME page table — no such test exists.

## Output wanted

1. The ruling among (a)/(b)/(c)/(d), one line + reason.
2. If (c): the exact assertion + where the test lives.
3. If (a): normative ordering, or compatibility statement only?
4. The falsifier: the observation that would change the ruling.
5. Mark UNKNOWN what the packet cannot decide.
