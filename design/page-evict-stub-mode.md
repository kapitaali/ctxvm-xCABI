# page.evict in stub mode — design of record

Status: **ruled 2026-11-24** (`reports/RR-PAGE-EVICT-RULING-20261124.md`, owner "make it a ruling"),
cleared to author as a design of record. This card is the plan; it authorizes no code, version bump, restart, or
release. Implementation is a separate owner-routed work order to the hermes lane. Research suggestion:
`reports/RR-PAGE-EVICT-RESEARCH-20261124.md`, verified in `RR-PAGE-EVICT-RESEARCH-REVIEW-20261124.md`. Reviewer
follow-up: `reports/RR-REVIEWER-PARTC-REVIEW-20261124.md`.

## 1. The one-line design

**Emit `page.evict` from the same seam that writes the stub into the request — not from a plan hook that only knows
an eviction was planned — with `stubText` byte-identical to the text actually sent, and tag `turn` as the turn at
which that stub first becomes visible; replay cross-checks it against the first `page.render(mode=stub)` for the
same page and fails if unequal.**

## 2. Why (verified locators — these are the corrected paths)

- `page.evict` is a **sealed v0 verb**: `spec/rfc-0/x-cabi.schema-v0.json:73` requires `type`/`turn`/`page`/`stubText`;
  `spec/rfc-0/RFC-0-xCABI.md:96–107` says renderers never invent or rewrite stub text. v0.1 carries `stubText`
  (`spec/rfc-0.1/x-cabi.schema-v0.1.json:301–311`). **No schema change, no five-touchpoint law** — the verb exists.
- **Timing is already normative:** `rust/crates/ctxvm-core/src/page_table.rs:4–13` and RFC-0 §6 — `page.evict @ t →
  stub visible AT t` (batched at the boundary before the tagged turn); `page.fault @ t → full FROM t+1`. The reviewer's
  two-calls-per-turn bucketing concern is exactly the risk of tagging at the *call* boundary instead of the *turn*
  boundary. This is the design question the card settles.
- **What the model saw:** Part I / Part II define `page.render(mode)` as ground truth and `page.evict` as the paging
  decision + what the model was told (verified substance in `reports/RR-PAPER-REVIEW-20261115.md:266–288`, A3/A4
  wording). The derived page table currently says "resident" about pages the model saw as stubs; a re-read is then
  misclassed as `faultOfResidentPage` (E0's replay violation class). Emitting `page.evict` fixes that classification.
- **Honesty boundary:** the 2026-11-11 decision not to emit `page.evict` for the **drop** policy stands
  (`reports/RR-W8CEVICT-20261111.md`): removal emits no stub, so `page.evict` would assert a substitution that never
  happened. Part C made the substitution **real**, which is what re-opens this for stub mode only.

(The three stale locators carried in the research suggestion — `research/white-paper.md`,
`research/white-paper-Part-II.md`, `ctxvm-codec/src/page_table.rs` — are replaced above with the real paths.)

## 3. The design, concretely

1. **Emit site:** the stub seam in `packages/hermes/live/context_engine.py` — `_stub_message()` (`:1038`) builds the
   stub dict and `_emit_transcript_slot()` (`:1069`, `:1085`) inserts it into the request. Emit `page.evict` at that
   seam, so the event and the request body are produced by one code path. Do **not** emit from `_plan()`/the observer
   (`:581`), which only knows a drop was decided.
2. **`stubText` byte-identity:** the event's `stubText` must equal the stub's `content` string exactly — same object or
   an asserted equal copy. No reformatting, no re-escaping at the event boundary. The 0.13.31 `_stub_arg_excerpt()`
   cap/escape (`:300–307`) applies before both, so hostile arguments cannot inject into either.
3. **`turn` tag:** set to the turn at which the stub first becomes visible (RFC-0 `page.evict@t → visible at t`). Not
   the call index, not the two-calls-per-turn sub-step. If the engine's plan is computed one turn before the stub is
   sent, tag the visibility turn, not the plan turn.
4. **Page identity:** `page` = the dropped result's `(logicalRef, contentHash)`, the same `PageId` the stub and the
   corresponding `page.render(mode=stub)` carry.
5. **Drop mode emits zero `page.evict`** — negative fixture; the stub condition gates emission (`_stub_dropped ==
   "recoverable"`). One gateway serves every profile, so this must be per-session state, never a process global (the
   repo has been burned twice by that — `RR-PARTC-FIX` §4 tests two engines in one process).

## 4. Replay / checker cross-check (authority: Rust core)

- `rust/crates/ctxvm-core/src/page_table.rs` already implements the event-effect timing and verbatim stub text
  (`render.rs:25,385`). Add a **replay assertion**: for each `page.evict` at turn t for PageId P, the first
  `page.render(mode=stub)` for the same P at turn ≥ t exists, and its turn equals t; fail otherwise. This turns
  the reviewer's timing caveat into a mechanical gate, not an assumption.
- **Correction 2026-11-24 (design author, before implementation):** the original text here said the `page.render(mode=stub)`
  row must "carry the same S" (`stubText`). That is impossible — sealed v0 `spec/rfc-0/x-cabi.schema-v0.json:62–71`
  and v0.1 `:262–280` define `page.render` as `type`/`turn`/`page`/`mode` with `additionalProperties: false`; only
  `page.evict` carries `stubText`. The cross-check therefore compares **turn + PageId**; stub-text identity is
  guaranteed upstream by the emitter using one stub object (hermes prompt §3.1) and is checked at the checker against
  the request's stub slots, not on `page.render`. Recorded in `reports/RR-PAGE-EVICT-DESIGN-ERRATUM-20261124.md`.
- `rust/crates/ctxvm-codec/src/jsonl.rs:64` already allowlists the verb and its keys — **no codec change**.
- Checker (`tools/coverage_check.py`): add a presence-gated rule — if a request carries stubbed slots, a matching
  `page.evict` row must exist. Mirror the existing version-gated `stubDropped`/`stubCount` rule style (`:451–459`) so
  pre-change fixtures stay valid. Hermes-lane owned; name `tools/coverage_check.py` explicitly in the change commit.

## 5. Paper change in the same landing

Update the white paper's A3/A4 wording (`reports/RR-PAPER-REVIEW-20261115.md:266–288`) from "shipped adapters emit
full only, once per page, at first reveal" / "adapters do not yet emit stub renders" to the honest format- and
adapter-scoped statement that stub-mode emits a `page.render(mode=stub)` + `page.evict` per dropped result, while
drop mode still emits neither. Paper and wire must agree in the same commit. E1/E2/M1/M2/M3 conclusions do **not**
change — no result is re-scored or pooled.

## 6. Verification bar (when implemented)

- Conformance: the sealed v0 validator still rejects v0.1-only lines (law 1); existing `spec/rfc-0` and v0.1 vectors
  plus the conformance vectors (`rust/crates/ctxvm-conformance/vectors/events-v0.jsonl`, `session-clean.jsonl`) pass
  unchanged; add one vector with `page.evict` + `page.render(mode=stub)` at the same turn (green) and one negative
  with a `page.render(mode=stub)` at a different turn than its `page.evict` (the replay turn-mismatch gate). A
  `stubText`-identity negative is a checker-side case (event text vs request stub), not a render-field case —
  `page.render` has no `stubText` field.
- New test: drop-mode capture emits zero `page.evict` (honesty guard); stub-mode event text == request stub text;
  per-session isolation (two sessions, one stub one drop, in one gateway).
- `bash tools/run-ci.sh` unpiped with `CTXVM_*` cleared → rc=0 ALL GATES GREEN; `check-handoff.sh` ALL PASS;
  `git-hygiene.sh` OK; CJK/secret/home sweeps; private index + `git read-tree HEAD` reset; no push.

## 7. Scope and claim ceiling

- Stub mode only; sealed v0; no spec/schema change. **Not authorized by this design:** emitting in code, a version
  bump, gateway restart, default-on stub, D17 release action, registry/catalog, re-score of Part B, pooling.
- No cost-saving (law 7), paging-quality, model-quality, or determinism (law 8) claim. `stubText` is a raw-text
  channel (`RR-FIELDAUD`); G4's consumer reports `channels modelled: logicalRef` — do **not** claim stubText redaction.
- Emitting `page.evict` makes **future** captures self-describing; it does **not** retroactively fill the accepted
  re-read/attestation gap (`RR-PARTC-ARM-RESULT`, `RR-RETRY-BLOCKED`). No claim that it does.
- Routing: implementation to hermes lane (`packages/hermes/**`, `tools/coverage_check.py` named explicitly); replay
  and validator changes in the Rust core with conformance vectors; paper wording by research lane; review verifies
  trace/validator side and records the books. No lane writes another's files; no push.
