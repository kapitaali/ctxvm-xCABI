# RR-PAGE-EVICT-RULING-20261124 — owner rules the page.evict design; card cleared to be authored

Owner decision 2026-11-24, verbatim: **"make it a ruling."** Subject: the research suggestion in
`reports/RR-PAGE-EVICT-RESEARCH-20261124.md` (verified in `RR-PAGE-EVICT-RESEARCH-REVIEW`), the answer to the
reviewer's owner-gated `page.evict` follow-up. Review lane, verify-then-record. $0, no model call, no push.

## 1. Interpretation recorded (so it can be corrected)

I read "make it a ruling" as: **the research design is accepted as the settled design for the `page.evict` card, and
the card is cleared to be authored as a design of record.** It does **not** by itself authorize the emitter code
change, a version bump, a gateway restart, a default-on change, or a release. If the owner meant the ruling to also
authorize implementation, that needs to be said explicitly and recorded as a new line.

## 2. The ruling — design settled

The `page.evict` card, when authored, shall specify:
1. **Emit from the stub seam** — the same code that writes the stub into the request — with `stubText` **byte-identical**
   to the text actually sent. Not from a plan hook that only knows an eviction was planned (honesty requirement).
2. **`turn` = the turn at which the stub first becomes visible**; replay must **cross-check** it against the first
   `page.render(mode=stub)` for the same `(logicalRef, contentHash)` and **fail** if unequal. This is the answer to the
   reviewer's two-calls-per-turn timing caveat; the timing rule itself is verified in `ctxvm-core/src/page_table.rs:4–13`
   and RFC-0 §6.
3. **Negative fixture:** a drop-mode capture must emit **zero** `page.evict` rows — the `RR-W8CEVICT` honesty decision
   still holds for removal (no stub text = no `page.evict`). **Stub mode only.**
4. **Paper and wire in the same landing:** update Part I/II wording (A3/A4 format- and adapter-scoped) so the white
   paper stops saying adapters emit full renders only, in the same change that makes it true.
5. **Checker/replay:** the derived table must show stubbed slots; replay checks totals; the checker may require every
   stub in the request to have a matching `page.evict` row. Scope this as a **sealed-v0** emitter change — no schema
   change, no v0.1-only field, no five-touchpoint law (the v0 verb and `stubText` already exist).
6. **Condition on the design record:** fix the three stale locators flagged in `RR-PAGE-EVICT-RESEARCH-REVIEW`
   (`research/white-paper.md`, `research/white-paper-Part-II.md`, `ctxvm-codec/src/page_table.rs` → the real paths)
   before the card is used as the design of record.

## 3. Routing (authoring the card, not implementing it)

- **Design of record:** `design/` holds plans of record and the owner clears new ones (`AGENTS.md:51`). This ruling
  clears the placement. The card is authored by the lane that owns the surface it primarily changes — the emitter is
  hermes-lane (`packages/hermes/**`); the research lane supplied the suggestion; the review lane verifies the
  trace/validator side and records the books. I do not author a `design/` plan of record myself without an explicit
  assignment, and I do not write `packages/**` or `tools/**`.
- **Explicitly not authorized by this ruling:** emitting `page.evict` in code, a version bump, gateway restart,
  default-on stub, D17 release action, registry/catalog, re-score of Part B, or pooling. No cost-saving/paging/model
  claim. `stubText` is a raw-text channel — no redaction claim (G4 models only `logicalRef`).
- **Honest boundary:** emitting `page.evict` makes *future* captures self-describing; it does **not** retroactively
  fill the accepted re-read/attestation gap (`RR-PARTC-ARM-RESULT`, `RR-RETRY-BLOCKED`).

## 4. Applied

This card, an append-only LOG row (four pipes), a day-file section in `reports/RR-DAY-20261124.md`, and the
`PROJECT-STATE.md` line updated to show the ruling. No push.
