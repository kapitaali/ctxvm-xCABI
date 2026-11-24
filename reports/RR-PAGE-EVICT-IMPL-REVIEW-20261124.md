# RR-PAGE-EVICT-IMPL-REVIEW-20261124 — verified: page.evict lands at the stub seam; build live at 0.13.32

Review lane, verify-then-record. Subject: hermes lane commits `4ba1cf2` (impl) + `6e3c348` (PROJECT-STATE delta),
card `reports/RR-PAGE-EVICT-IMPL-20261124.md`. Work order `design/PAGE-EVICT-HERMES-PROMPT.md`, design of record
`design/page-evict-stub-mode.md`. Date 2026-11-24. $0, no model call, no push.

## 1. Verified from disk

| claim | check | result |
|---|---|---|
| version 0.13.31 → 0.13.32 both places + installed | grep `__init__.py` | repo/installed **0.13.32** |
| sync | `sync-plugin.sh --check` | repo/installed/manifest 0.13.32, load check OK |
| gateway holds new build | `ps -p 48868` | pid 48868 started **14:54:12** after the files (14:53); holds 0.13.32 |
| suite | `pytest packages/hermes -q`, `CTXVM_*` cleared | **246 passed, 15 subtests** |
| gate | `run-ci.sh` unpiped, `CTXVM_*` cleared | **rc=0 ALL GATES GREEN** |
| real capture under new build | sidecar `local-f913ef…` | mtime **14:55:46**, `version 0.13.32`, arm control, stub `off`, `stubbedRefs []` — default-off attested on a live capture, upgraded from the 0.13.31 probe |
| Rust cross-check | `cargo test -p ctxvm-core` | **37 passed** (my prior split, still green) |
| kit/hygiene | `check-handoff.sh`, `git-hygiene.sh` | ALL PASS / OK |

## 2. Emitter verified against the design (`design/page-evict-stub-mode.md` §3)

- **One assembly, one object:** `select_context` computes `assembled` once and reuses it at all four sites; the observer
  fires with stub rows from that exact assembly — confirmed in `context_engine.py:580` (`_stub_rows` ready at emit time).
- **Byte-identical seam:** `_stub_message()` builds the stub; `_emit_transcript_slot()` records `{ids, stubText}` in
  `self._stub_rows` from **the same stub dict inserted into the request** (no re-derivation from `_plan`). Matches the
  design's honesty requirement and the reviewer's injection concern.
- **Tracer emitter** `Tracer.emit_evict(ref, stub_text, turn)` (`plugin.py:407`): sealed-v0 `page.evict` shape
  (`type/turn/page/stubText`), `page = (logicalRef, contentHash)` from the declared page, `stubText` byte-identical,
  `ts` last via `_push` (law 3). Returns False on unknown ref / non-string text (fail-open, never raises into a turn).
- **Visibility turn:** bridge observer sets `_visible = _tr._turn + 1` (`__init__.py:1563`) — the stub is sent in the
  request *after* `render()` increments, so RFC-0 `page.evict@t → visible@t` holds. This also matches the design's
  two-calls-per-turn caveat (tag the visibility turn, not the plan turn).
- **Per-session:** `stubbed_refs_by_session` keyed by session id (`__init__.py:1577`); the real 0.13.32 sidecar shows
  `stubbedRefs: []` on the operator's control profile — drop mode, as designed.
- **Checker rule** (`tools/coverage_check.py:461–490`): version-gated (`>= 0.13.32`) + presence-gated — a recoverable
  sidecar with `evictedTokens > 0` must have a `page.evict` row for each stubbed ref with byte-identical `stubText`;
  old/off fixtures exempt; the earlier `stubCount > 0` rule stays. Matches the design §4 and the hermes prompt §3.5.

## 3. Red-before / honesty checks

- Suite 246 includes 5 new laws (stub rows byte-identical to request body; drop mode emits zero rows; `emit_evict`
  byte-identity + `ts` last; unknown ref / non-string refusal; visibility turn = next after completed turn) — all pass.
- Checker rule proven independently per the card (mismatched `stubText` → violation line; matching → clean; old version →
  exempt). No vacuous negatives.
- Hostile-arg protection carried: `_stub_arg_excerpt` (cap 200, control-strip, bracket-escape) feeds the same stub dict
  that feeds `emit_evict`, so injection cannot reach `page.evict.stubText` either.
- Sealed v0 untouched: `git diff --stat -- spec/ rust/` empty (only my earlier replay/vector changes, already merged);
  v0 conformance vectors pass unchanged. A standalone `page.evict` with `ts` is v0.1-valid and v0-invalid — expected,
  since live traces carry `ts` while sealed v0 vectors do not. Law 1 intact.

## 4. Scope / claim ceiling

No cost-saving, paging-quality, model-quality, or determinism claim. No arm, model call, spend, re-score of Part B,
pooling, default-on, D17, registry/catalog action. `stubText` is a raw-text channel (G4 models only `logicalRef`) — no
redaction claim. Emitting `page.evict` makes *future* captures self-describing; it does **not** retroactively fill the
accepted Part C re-read/attestation gap (`RR-PARTC-ARM-RESULT`, `RR-RETRY-BLOCKED`). No push.

## 5. Owed (other lanes)

- Research lane: A3/A4 paper wording on the gitignored working source (`research/uncommitted/white-paper-Part-II_reviewed.md`,
  `white-paper_reviewed.md`) to land **with** this build so paper and wire agree (routed in
  `RR-PAGE-EVICT-PAPER-ROUTE-20261124`). The reviewed copy is intentionally gitignored by owner design.
- Review lane (me): replay cross-check + conformance vectors already landed (`6273724`). No further code needed from me.
- Operator: gateway restart done (pid 48868). No action owed from review.
- Future stub-arm preflight must cite **0.13.32**, not 0.13.30/31.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
