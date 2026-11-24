MASTER PROMPT — hermes lane: emit `page.evict` in stub mode (page.evict design of record)

Owner assigned 2026-11-24 (answer to the routing question: "split work between this lane and hermes lane"). Design of
record: `design/page-evict-stub-mode.md` — read it fully first. You own `packages/hermes/**` and `tools/coverage_check.py`;
you do NOT write `research/**` (research lane does the paper wording in this same landing, coordinated by owner),
`rust/**` (review lane does the replay cross-check + conformance vector), `spec/**` (sealed), `experiments/**`, or
`handoff/**` (review lane). No version release, no gateway restart (operator), no default-on stub, no D17 action,
no push.

## 0. Entry ritual
1. Read `design/page-evict-stub-mode.md`, `AGENTS.md` (laws 1–10), `handoff/LANES.md`, `reports/RR-PAGE-EVICT-RULING-20261124.md`,
   `reports/RR-PAGE-EVICT-RESEARCH-REVIEW-20261124.md` (verified locators), `reports/RR-PARTC-FIX-20261124.md` (the 0.13.31 stub seam).
2. `git log --oneline -8 && git status --short`; name your exact paths; never `git add -A`; other lanes' WIP is in the tree.
3. `bash tools/check-handoff.sh` and `bash tools/git-hygiene.sh` at entry; private index + `git read-tree HEAD` on close.

## 1. The one-line change

Emit a sealed-v0 `page.evict` event at the **stub seam** — the code that writes the stub into the request — with
`stubText` **byte-identical** to the stub content actually sent, and `turn` = the turn at which that stub first becomes
visible. Drop mode emits **zero** `page.evict`. No schema change (the v0 verb and v0.1 `stubText` key already exist).

## 2. Architecture you must respect (verified)

- The engine (`packages/hermes/live/context_engine.py`) builds stubs in `_stub_message()` (`:1038`) and inserts them
  in `_emit_transcript_slot()` (`:1069`, `:1085`); it does NOT write xCABI events. Events are written by the tracer
  core (`packages/hermes/src/plugin.py`, `_push()` `:263`) and the bridge observer in `packages/hermes/live/__init__.py`
  (`_record_plan` `:1542`, which has `_vm.tracer_for(_target)`).
- The plan payload (`context_engine.py:581–610`) already carries `stubDropped`, `stubCount`, and `dropped`. **Carry the
  exact stub text(s)** and the visibility turn(s) from the stub seam into that payload, then emit `page.evict` in the
  bridge observer via the tracer. This is still "the stub seam" — the event's text and the request's text come from one
  object; do NOT emit from `_plan()` alone (it only knows a drop was decided).
- `refs_for_identity_tokens()` (`plugin.py:376`) maps dropped keys to refs; reuse it so the event's `page` identity
  matches the corresponding `page.render`/`page.declare` `PageId`.
- Per-session, never process-global: `_record_plan`/`_record_selection` are already per-session (`_state()` keyed by
  session id); follow that. This repo has been burned twice by process-global arm state.

## 3. Exact acceptance conditions

1. `stubText` in the event == the stub's `content` string exactly (same object or asserted-equal copy). No reformat.
2. `turn` = first visibility turn (RFC-0: `page.evict@t → stub visible at t`); if the plan is computed a turn before
   the stub is sent, tag the visibility turn, not the plan turn. Note Hermes's two-calls-per-turn bucketing.
3. Drop mode (`stubDropped: off`) emits **zero** `page.evict` — negative fixture; gate on the per-session setting.
4. Sealed v0: `spec/rfc-0/x-cabi.schema-v0.json` and the v0 validator do NOT change (law 1). v0.1 `stubText` key
   (`spec/rfc-0.1/x-cabi.schema-v0.1.json:301`) is already there — no five-touchpoint card.
5. `tools/coverage_check.py`: add a **presence-gated + version-gated** rule (mirror `:451–459`) — if a captured request
   carries a stubbed slot (`stubDropped == "recoverable"`) and `evictedTokens > 0`, require a matching `page.evict` row
   per stubbed ref with `stubText` equal to the slot's text. Old/off fixtures must still pass. Name this file explicitly
   in your commit (hermes-owned).
6. `ts` rides last on every event; the codec allowlist already includes `page.evict` (`ctxvm-codec/src/jsonl.rs:64`).

## 4. Tests + red-before (prove each can fail)

- Stub-mode synthetic capture emits one `page.evict` per stubbed page, `stubText` byte-identical to the request stub.
- Drop-mode synthetic capture emits zero `page.evict` (honesty guard).
- Two sessions in one process (one `recoverable`, one `off`) — each sidecar/capture carries only its own `page.evict`
  rows; no process-global leakage.
- Checker red case: a `recoverable` sidecar with `evictedTokens>0` and a missing/mismatched `page.evict` row must FAIL;
  green/old-version/off cases pass. Record each red rc and the restore. No vacuous negatives.
- Reuse the 0.13.31 hostile-arg protections (`_stub_arg_excerpt`, cap/escape) — a hostile argument must not inject into
  `page.evict.stubText` either.

## 5. Hygiene + verification

- Version **0.13.31 → 0.13.32** in both places (`packages/hermes/live/__init__.py`, installed copy); `bash tools/sync-plugin.sh`.
  State gateway restart owed to operator. The Part C stub-arm preflight must now cite 0.13.32, not 0.13.30/31.
- `python3 -m pytest packages/hermes -q` (report derived count), `bash tools/run-ci.sh` unpiped with `CTXVM_*` cleared,
  `tools/check-handoff.sh`, `tools/git-hygiene.sh`, CJK/secret/home sweeps.
- Own `reports/RR-PAGE-EVICT-IMPL-<date>.md` + LOG row (four pipes) + day section; route shared files to review lane.
  Private index; `git read-tree HEAD` reset; attribution `kapitaali`; no push.

## 6. Claim ceiling / not yours

No cost-saving, paging-quality, model-quality, determinism claim. No arm, no model call, no spend, no re-score of Part
B, no pooling. The Rust replay cross-check + conformance vector and the paper wording are NOT your files — another lane
owns them; do not touch. Emitting `page.evict` does not retroactively fill the re-read/attestation gap. No `stubText`
redaction claim (G4 models only `logicalRef`).

## 7. The one sentence

Make the event and the request body come from one seam: byte-identical `stubText`, visibility-turn tag, zero in drop mode,
per-session, with a checker that can fail — then version-bump and hand the trace to review.
