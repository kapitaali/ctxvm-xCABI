# RR-PAGE-EVICT-RESEARCH-REVIEW-20261124 — verified: research's page.evict suggestion is sound; three stale locators flagged

Review lane, verify-then-record. Subject: `reports/RR-PAGE-EVICT-RESEARCH-20261124.md` (research lane, **untracked** — left for owner/review), the research-side answer to the reviewer's owner-gated `page.evict` card. Date 2026-11-24. $0, no model call, no push.

## 1. The suggestion (recorded for the owner's ruling on the page.evict card)

Emit `page.evict` **from the same seam that writes the stub into the request**, with `stubText` byte-identical to the text actually sent; set `turn` = the turn at which the stub first becomes visible, and cross-check in replay against the first `page.render(mode=stub)` for that page — fail if unequal. Add a negative fixture (drop-mode capture emits **zero** `page.evict`). Update Part I/II wording in the **same landing** so paper and wire agree. Stub mode only; drop mode's `RR-W8CEVICT` honesty decision stands. Route to hermes; review verifies trace/validator; no default-on without a new ruling.

## 2. Verified substance

| claim | check | result |
|---|---|---|
| timing semantics `page.evict @ t → stub visible at t`, `page.fault @ t → full from t+1` | `rust/crates/ctxvm-core/src/page_table.rs:4–13` and `spec/rfc-0/RFC-0-xCABI.md:88–93` | **verbatim** — the reviewer's two-calls-per-turn timing concern is real and bounded by this rule |
| stub text is what the model saw; renderers never invent/rewrite | `spec/rfc-0/RFC-0-xCABI.md:96–107` | normative — supports "emit from the stub seam, not a plan hook" |
| v0.1 schema carries `stubText` | `spec/rfc-0.1/x-cabi.schema-v0.1.json:301–311` | present, required |
| A3/A4 format-scoped wording | `reports/RR-PAPER-REVIEW-20261115.md:266–288` | verbatim — the paper-merge-in-same-card suggestion is grounded |

So the card's central reasoning is sound: the derived page table can honestly show stubbed slots, and a re-read of a stubbed page stops being misclassed as `faultOfResidentPage` — a metric-integrity reason, not a paging claim.

## 3. Stale locators — flagged, substance intact

Three file:line locators in the card do **not** resolve as written:
- `research/white-paper.md:152–153` (Part I event table) — no such file today;
- `research/white-paper-Part-II.md:28–30` — no such file (the reviewed copy is `research/uncommitted/white-paper-Part-II_reviewed.md`);
- `rust/crates/ctxvm-codec/src/page_table.rs:5–15` — the file is `rust/crates/ctxvm-core/src/page_table.rs`.

The *quoted substance* verifies in RFC-0 and `RR-PAPER-REVIEW` (above), so this is a locator defect, not an evidence failure. The research lane should fix the paths before the card is used as the page.evict design record. Recorded so nobody hits dead pointers.

## 4. Scope / status

The card is a **suggestion, not a ruling** — the `page.evict` card remains **owner-gated and unwritten**. No `page.evict` emission, no code, no default-on, no D17, no re-score/pooling, no cost/paging/model claim. Note the honest boundary it keeps: emitting `page.evict` makes *future* captures self-describing but does **not** retroactively fill the accepted re-read/attestation gap (`RR-PARTC-ARM-RESULT`, `RR-RETRY-BLOCKED`). No stubText-redaction claim (G4 models only `logicalRef`).

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
