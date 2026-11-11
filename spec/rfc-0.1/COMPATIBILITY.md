# xCABI 0.1 — compatibility notes

**Status:** applied 2026-11-11 — **D18**. Scope: companion to `RFC-0.1-xCABI.md`; that document and
the sealed `spec/rfc-0/` are unchanged by this file. The three clauses below are the **P10 and P11
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

The page table is a **pure function of the parsed model** (`ctxvm_core::render::derive_projection`:
"Pure function of decisions fed"), so equal parsed models entail equal derived page tables. The
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
  arrays, and objects**. **Floating-point values are not admissible in a hash input.**

This clause is normative because a hash input is not free-form text: the page reference's truncation
digest is computed over the canonical bytes, so the canonical form must match byte for byte across
implementations. A hash input containing a floating-point value is **outside** this clause — the
repo's standing convention bans floats from identity comparisons (`RR-W7-20261029.md` §4) — and is
therefore not covered by this note. Two implementations that disagree on ordering or on number spelling produce
different digests **silently** — no error, just a different identity.

*C3 is scoped to hash inputs only.* It does not constrain a trace line's key order (C2), and it does
not constrain what a consumer must accept.
