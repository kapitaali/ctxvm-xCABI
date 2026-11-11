# W8B lane — small handoff prompt (2026-11-11)

Give this to the agent running the W8B lane. It assumes no memory of our chat and no repo access
beyond what it reads itself. Companion to `design/W8B-PROMPT.md` (the master); this file carries
only what changed since, and what the lane owes.

Repo `/home/theb/Documents/ctxvm`, branch `main`. Gates: `bash tools/run-ci.sh` (capture `$?`),
`bash tools/check-handoff.sh`. Do not touch `spec/**`, `corpus/**`, `research/**`.

## 1. What you inherit (measured, not to be repeated)

- **W8 is closed negative** (`design/W8-CLOSURE-20261110.md`): the keep law is turn-granular, a
  `-z` session is one turn, so selection cannot act; the shape caps any evictable share at **5.3 %**
  session-weighted (25,404 of 479,076 request tokens; the first middle appears at turn 9).
- **T-A v2 landed** (your lane): the per-prompt question now asks only for what `read_file` reports
  (`total_lines`, `file_size`) plus the exact text of line 137; the artefact is
  `{files:{lines,bytes}, widest_file (largest bytes), marker_line}`; `tools/w8-checker-ta-v2.py`
  recomputes all three from the fixture bytes. Driver fixes: prompt rules in the digest, SIGTERM
  first (SIGKILL only after 20 s), `--limit N` smoke check, `max_turns` 12 → 6, `--expect-budget`
  accepts "any". Smoke on longcat: **1 `read_file` per prompt, 16.0 s / 11.2 s**, correct
  `250 / 16602` and correct line 137 both times, against 21 tool calls and a 120 s timeout on v1.
- **Your T-A v2 run then produced NO RECORD** (`reports/RR-W8B2-20261111.md` + your erratum): both
  arms, prompt-1 timeout at 120 s, no capture flushed, $0.0000. Correctly classified as a **pair
  attempt, not a cell** — the prediction block was unfilled, so nothing was bookable. The block for
  `w8b-cell-01` is now filled and committed in `reports/RR-W8B2CLASS-20261111.md`.
- **The measured shape** (your own runs): per-turn request 9,141 → 98,934, crossing 70,000 around
  turn 13 (the first middle in this card). `design/W8B-FREE-PLAN.md` estimated ~90k peak and ~21k
  evictable (~23 %) — the measurement is ~98.9k and ~28.9k (**29.2 %**), i.e. ~8k more evictable
  than planned.
- **The P11 conformance pair + test** are yours and are landing: four vectors
  (`order-{struct,sorted}-{ts,nots}.jsonl`), the expected report golden
  (`order-expected-report.json` — **it must be in the same commit**: the test `include_str!`s it, so a
  commit without it fails to compile on a fresh checkout), `tests/key_order.rs`, and the vectors README.
- **The calibration record moved**: the umpire MCP now serves the artifact of record
  (`cal-v1:057a5a35a9d4ec71`, test ECE 0.030163) — the superseded v2 map (ECE 0.026684) is no
  longer the default on either surface (`reports/RR-U2LIVE-20261111.md`).

## 2. Decisions the owner has ruled (do not re-open)

- **Subject fallback order**: **nvidia** (nemotron-super — the tested path) → **stepfun** → accept
  longcat is too slow for the 120 s cap only if both fail.
- **A new subject means new digests**: rewrite and re-commit the prediction block BEFORE the pair
  starts, not after (the block's own rule: a mismatch means the instrument is wrong).
- **The arm-attribution precondition, which is not the model's fault**: the paged arm reported
  `profile "default"` under profile `w8bn-paged` and `engine: null` / `engineSelections: 0`, i.e.
  **that arm was not the paged arm** — the arms are separated by the profile each was invoked with and
  by nothing inside the trace. Before any pair, assert **both** `engineSelections > 0` **and** the
  invocation's profile is `w8bn-paged` (not "default"); an engine engaging under the wrong profile
  looks instrumented and is still mis-attributed.
- **No cost-saving claim is available from a free run** (no cache price to break even against), and
  the break-even for a future **paid** variant is computable: n\* ≈ (w/r)(P′/S) = 10 × (98,934 / 28,934)
  ≈ **34 calls** against the 41 calls measured — which is why a paid cell at this shape is a fresh
  preregistration, not W8.

## 3. What the lane owes (four items, each small)

1. **Assert the third level in the P11 test.** The test's prose says "model, derived page table,
   replay report", but `ctxvm_core::ReplayReport` carries events/divergences/violations **only**
   (`rust/crates/ctxvm-core/src/replay.rs:48-55`), so no page table is compared. The one-call fix:
   `assert_eq!(ctxvm_core::render::derive_projection(&a, turn),
   ctxvm_core::render::derive_projection(&b, turn), …)` per turn (the draft is in
   `reports/RR-P11GAP-20261111.md` §7; `TurnProjection` derives `PartialEq`). Without it, the note's
   C2 clause rests on an untested inference — and the RFC-0.1 note's C2 pointer names that test.
2. **Append an erratum to `design/W8B-FREE-PLAN.md`** for the stale shape estimate (measured peak
   98,934 vs ~90k planned; evictable ~28.9k vs ~21k planned). Per your own rule, the prediction was
   the instrument that was wrong, and the correction belongs where the estimate lives.
3. **Scope the W8SIM sentence.** "No policy can save more than 5.3 %" holds only for policies that keep
   the first three turns, the last six and the system prompt — a different keep law could save more
   (`reports/RR-W8SIM-20261110.md`).
4. **Rename one "C3".** The W8 close-out's `C3` (budget simulation) and the RFC-0.1 note's `C3`
   (canonical-form clause) are different things in the same day's files; the note now says so
   explicitly, and the W8-side rename is yours.

## 4. Rules that apply to you here

- A **cell** is booked only with the prediction block filled and committed first; a pair without it is
  a **pair attempt**, recorded as such and not in any denominator.
- Arm attribution is runner-side: `engineSelections` and the invocation's profile, never the trace.
- Report what happened, including NO RECORD, as the outcome; do not promote a diagnostic to a result.
- Nothing pushed; the owner pushes. The kit (`handoff/`, `reports/LOG.md`, `08-HANDOFF.md`) is
  append-only: append, never rewrite a committed row.
