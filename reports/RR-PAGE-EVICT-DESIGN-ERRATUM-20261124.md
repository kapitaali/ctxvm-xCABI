# RR-PAGE-EVICT-DESIGN-ERRATUM-20261124 — design §4 corrected before implementation: page.render carries no stubText

Review lane, self-correction on the design of record I authored (`design/page-evict-stub-mode.md`). Date 2026-11-24. $0, no code, no push.

## 1. The defect I found and fixed

While implementing the Rust cross-check, I found the design §4 originally required the first `page.render(mode=stub)`
row to "carry the same S" (`stubText`) as its `page.evict`. **That is impossible under sealed v0:**
- `spec/rfc-0/x-cabi.schema-v0.json:62–71` — `page.render` requires `type`/`turn`/`page`/`mode`,
  `additionalProperties: false`; no `stubText`.
- `spec/rfc-0.1/x-cabi.schema-v0.1.json:262–280` — same shape (+ optional `ts`); no `stubText`.
- Only `page.evict` carries `stubText` (v0 schema `:73`, v0.1 `:301`).

## 2. The correction (applied to the design card)

- **Replay cross-check is turn + PageId**, not text: for each `page.evict` at turn t for PageId P, the first
  `page.render(mode=stub)` for the same P must exist at turn **t** (fail otherwise). This still mechanically gates the
  reviewer's two-calls-per-turn timing caveat.
- **Stub-text identity** is guaranteed upstream by the emitter using one stub object for both the request body and
  the event (hermes prompt §3.1), and checked **checker-side** against the request's stub slots — not on `page.render`.
- §6 conformance negatives adjusted: green = evict+render at the same turn; negative = render at a **different** turn;
  the `stubText`-mismatch negative is a checker-side case, not a render-field case.

## 3. Why this is recorded, not buried

The design of record is cited by the ruling (`RR-PAGE-EVICT-RULING`) and the hermes prompt; a silent fix would leave
those pointing at a card whose text had changed. This card records the before/after, and the design carries an inline
erratum note at §4. No law was broken — the sealed schemas were **not** changed; the design text was corrected to match
them. No cost/paging/model claim; no implementation of the emitter (hermes lane) or restart.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
