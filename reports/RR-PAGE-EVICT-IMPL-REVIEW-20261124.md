# RR-PAGE-EVICT-IMPL-REVIEW-20261124 — my split implemented: Rust replay gate + two conformance vectors; paper wording owed; hermes emitter assigned

Review lane, verify-then-record. Owner split: hermes lane writes the emitter + checker (prompt `design/PAGE-EVICT-HERMES-PROMPT.md`); I implement the rest under an owner-recorded one-time write override. Date 2026-11-24. $0, no model call, no push.

## 1. What I implemented and verified

**Rust replay cross-check** (`rust/crates/ctxvm-core/src/replay.rs`):
- New `Divergence::StubRenderTurnMismatch { evict_turn, first_stub_render_turn, page }`.
- `check_stub_render_turns()` — full-replay-only pass: for each `page.evict@t`, the first recorded `page.render(mode=stub)` for that PageId must be at turn t (RFC-0 `page.evict@t → stub visible at t`). **Presence-gated**: traces whose adapter records no stub renders are unaffected; `replay_turn` (point-in-time) does not run it.
- New unit test `stub_render_turn_must_match_evict_turn_when_recorded` — green (render@evict), red (render one turn later), and no-render-presence case. `cargo test -p ctxvm-core` → **37 passed**.

**Conformance vectors** (`rust/crates/ctxvm-conformance/vectors/`):
- `stub-evict-green.jsonl` — evict@1 + stub render@1 → replay `divergences: []`.
- `stub-evict-turn-mismatch.jsonl` — evict@1 + stub render@2 → replay `divergences: [StubRenderTurnMismatch{evict_turn:1, first_stub_render_turn:2, …}]`.
- Both validate under the **sealed v0** schema (`validate_schema.py`: 65 checks PASS) — no `schemaVersion`/`ts` (those are v0.1-only), no `page.declare.turn` (v0.1-only). Law 1 intact.

**Design corrections recorded before implementing** (`RR-PAGE-EVICT-DESIGN-ERRATUM-20261124`): the design §4 wrongly required `page.render` to carry `stubText` — impossible under sealed v0/v0.1 (`additionalProperties: false`); corrected to a **turn + PageId** cross-check, with text identity checked checker-side against request stub slots. The design card was fixed in place with an inline note.

## 2. Paper wording — owed, not applied (honest blocker)

The design §5 requires Part I/II A3/A4 wording to change **in the same landing** as the wire change ("stub-mode emits a `page.render(mode=stub)` + `page.evict` per dropped result, while drop mode still emits neither"). I did **not** apply it:
- the canonical Part I/II paper source is **not a tracked file in this repo** (only `research/white-paper-Part-III*` are tracked; the reviewed Part II copy is gitignored under `research/uncommitted/`);
- the hermes emitter has **not landed**, so asserting stub-mode emission in the paper now would claim behavior that does not yet exist (and paper/wire would disagree until it does).

Recorded as an owed item for the research lane, to land **with** the hermes emitter. Proposed wording is in the design §5. No fabricated edit to a gitignored file.

## 3. Division of work

- **Hermes lane (assigned, prompt written):** emit `page.evict` at the stub seam, byte-identical `stubText`, visibility turn, drop-mode zero, per-session; `tools/coverage_check.py` presence+version-gated rule; 0.13.31 → 0.13.32 bump/sync; red-before tests. Not landed yet.
- **Me (done):** Rust cross-check + vectors. **Owed (blocked on hermes + research source):** paper wording.
- No cost/paging/model/determinism claim; no re-score/pooling; no default-on/D17/release; no `stubText` redaction claim; emitting does not retroactively fill the re-read gap.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
