# xCABI 0.1 — compatibility notes

**Status:** applied 2026-11-11 — **D18** (the owner confirmed the content as proposed on 2026-11-11, including C3's ordering rule; the D-number may be renumbered). Scope: companion to `RFC-0.1-xCABI.md`; that document and
the sealed `spec/rfc-0/` are unchanged by this file. **Clause naming:** the `C1`–`C3` below are the *compatibility-note* clauses; the W8 close-out's
`C1`–`C7` (`RR-W8SIM`) are the *budget-simulation* findings — a different series, and the two must not
be cited as one. The three clauses below are the **P10 and P11
answers verbatim in substance** (page-identity dispatch, and the key-order compatibility statement
plus its pointer to the conformance test); C3 is the reviewer's own conditional — "if one [a digest or
chain] is computed over serialised bytes, key order matters for it, and the note must say so" —
triggered by the umpire ref digest, which is exactly that. The content changes only with a new
D-number.

## C1 — A page's identity is verb-dependent

`page.declare` carries its page identity **nested** (`page.id.logicalRef`, `page.id.contentHash`);
every other page-carrying verb carries it **flat** (`page.logicalRef`, `page.contentHash`) —
`page.render`, `page.evict`, `page.fault`, `page.pin`, `page.unpin`.

A consumer MUST read identity from the shape the event type defines, and MUST dispatch on the event
type — **never on which fields happen to be present**. A reader that accepts either shape by
sniffing fields will silently pass a malformed line: the validator rejects a `page.declare` that
carries a flat identity, while a presence-sniffing reader accepts and keys it.

Both shapes are part of the **sealed RFC-0** schema and remain so. This note harmonises nothing: no
field is added, no existing shape is changed, and a v0 trace's dispatch requirement is permanent.

## C2 — Key order within an event is not significant to parsing or replay

Events written in sorted-key order and in the emitter's field order are accepted equally; the codec
remains **strict about unknown fields**. This is a compatibility statement about what a consumer
MUST ACCEPT, never about what an emitter MUST EMIT: `ts` rides last in the emitter's order (and the
byte forms therefore differ by construction), and no byte-identical-lines claim is made across
crates.

The page table is a **pure function of the parsed model** — `ctxvm_core::render::derive_projection`
is documented as a "pure derive from a raw event slice — **identical bytes for identical inputs,
guaranteed**" — so equal parsed models entail equal derived page tables. The
conformance test is the executable form of this clause: the vector pair
`rust/crates/ctxvm-conformance/vectors/order-{struct,sorted}-{ts,nots}.jsonl` (the same event set
written twice, with and without `ts`) with the expected report
`order-expected-report.json`, asserted by `rust/crates/ctxvm-conformance/tests/key_order.rs`.

## C3 — The canonical form of a hash input (normative, for hash inputs only)

A **hash input** is canonicalised as JSON with:

- object keys sorted by **Unicode code point** (not by UTF-16 code unit — the two orderings differ
  for characters outside the Basic Multilingual Plane, which would change the canonical bytes and
  therefore the digest);
- minimal separators (`,` and `:`), no whitespace;
- **no ASCII escaping** (non-ASCII characters are emitted as themselves);
- a restricted value set: **strings, exact integers (no fraction, no exponent), booleans, null,
  arrays, and objects**. **Floating-point values are not admissible in a hash input**, and the duty
  is split, because the two implementations can only see part of it:
  - **The producer MUST NOT put a float in a hash input.** The spelling is unrecoverable downstream:
    `JSON.parse("1.0")` yields the number `1`, so a consumer cannot tell an integral float from an
    integer, while Python keeps the float and would spell it `1.0`. A consumer that meets `1.0` as a
    float value MUST **reject** it, never coerce it — coercing turns `1.0` into `"1"` in one
    implementation and `"1.0"` in another, which is the divergence this clause exists to remove.
- **integer range**: integers must satisfy `|n| <= 2^53 - 1` (9007199254740991). A larger integer
  is not exactly representable in an IEEE-754 double and therefore not portable between
  implementations; a consumer MUST **reject** it, or the producer MUST carry it as a **string**.
  `-0` is not admissible either (it is not distinguishable from `0` in a double).
- **strings must be valid Unicode scalar values**: a lone surrogate MUST be rejected, not escaped.
  (JavaScript's `JSON.stringify` escapes lone surrogates; Python with `ensure_ascii=False` emits them
  raw and the UTF-8 encoding then fails.)
- **no normalisation is applied**: NFC and NFD forms of the same visible string are different inputs
  and hash differently. The producer owns normalisation.

This clause is normative because a hash input is not free-form text: the page reference's truncation
digest is computed over the canonical bytes, so the canonical form must match byte for byte across
implementations. **It is enforced, not merely described**: the case file
`rust/crates/ctxvm-conformance/vectors/canonical-form-cases.jsonl` carries, for each case, the input
JSON text, the expected canonical bytes and the expected digest — all generated by Python's
`canonical_json` (the reference implementation) — and the TS implementation runs that file; umpire's
Python side is expected to run the same file. A hash input containing a floating-point value is **outside** this clause — the
repo's standing convention bans floats from identity comparisons (`RR-W7-20261029.md` §4) — and is
therefore not covered by this note. Two implementations that disagree on ordering or on number spelling produce
different digests **silently** — no error, just a different identity.

*C3 is scoped to hash inputs only.* It does not constrain a trace line's key order (C2), and it does
not constrain what a consumer must accept.
