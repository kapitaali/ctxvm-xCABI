# RR-T20-PINPRECISION — replay `--pin (ref, hash)` precision mode

- **Card:** T20 (user-directed 2026-10-24; the last unbuilt `--pin` surface from RR-UCVERIFY class F) · **Status:** DONE
- **Date:** 2026-10-24 · **Repo:** ctxvm (`main` @ `d793ce3`) · **Spend:** USD 0 (local build only)
- **Depends:** RR-UCVERIFY-20261024 (class F remainder), RR-UC2REPLAY-20261024 (T16 — broad `--pin <ref>` base)

## 1. What this card added

### Problem

T16's `--pin <ref>` flips **every** stubbed content-hash variant whose `logical_ref`
matches. For a trace that declares several hashes under one ref (the M1b A/B
shape — e.g. a page observed under two different contents), the probe cannot
ask "was THIS variant the one they needed?" — it flips all of them at once.

### ctxvm-core (2 new unit tests; 24 → 26)

- **`Pin`** enum, the overlay's matching form:
  - `Pin::Ref(String)` — the T16 broad form (unchanged semantics).
  - `Pin::Identity { logical_ref, content_hash }` — T20 precision: flip only
    the Stub slot with that exact page identity.
- `TurnProjection::with_forced_resident` now takes `&[Pin]` (was
  `&BTreeSet<String>`); flip rules per form, stub text dropped, re-tally,
  facts/violations untouched — all unchanged for the broad form.

### `replay` CLI (same binary, T16 contract extended)

```
replay <file> --turn N --pin <ref>            # broad, every variant (T16)
replay <file> --turn N --pin '(ref, hash)'    # precision, one variant (T20)
replay <file> ... --pin page:(ref, hash)      # memo prefix composes
replay <file> --turn N --pin ref1 --pin '(ref2, hash2)'   # mixed kinds allowed
```

- Parsing: `page:` prefix stripped up front (composes with both forms);
  tuple split at the **last** comma — refs may contain commas (tool-call
  shapes), while the hash is always the final component.
- Validation (exit 2, one precise message for the first bad pin):
  ref not declared (`declared refs: …` roster) · ref declared but hash not
  (`declared hashes for it: …` roster) · malformed tuple (missing/unclosed
  paren, missing comma, empty fields — form spelled out).
- Report shape **unchanged** (T16 compat): `pins` stays an array of strings —
  precision pins appear in their normalized `(ref, hash)` textual form;
  `forcedResident`/`projection` keys unchanged.
- Already-Full precision targets are valid (declared) but produce no flip —
  flips count Stub→Full only, same as broad.
- Exit contract untouched: 0 clean · 1 divergences · 2 usage/IO/parse;
  `--pin` still requires `--turn`.

## 2. Validation evidence (witnessed 2026-10-24)

```
$ cargo build --workspace                     # 0 warnings
$ cargo test --workspace                      # 44/44 (codec 9 · conformance 8 ·
test result: ok. ...                             core 26 · tokenizer 1)

synthetic two-variant trace (tool:read_file(x)@h-a1 + @h-a2, both evicted @1;
file:b resident):
  baseline turn 1            → resident 400 / stubbed 240
  --pin tool:read_file(x)    → forced [h-a1, h-a2], resident 640   (broad, T16)
  --pin '(tool:read_file(x), h-a1)' → forced [h-a1], resident 520,
                                      h-a2 still stubbed            (precision)
  --pin file:b --pin 'page:(tool:read_file(x), h-a1)' → forced [h-a1, h-b],
                                      both kinds apply, pins labels mixed forms
  --pin '(file:b, h-b)'      → valid (declared), forced [], projection unchanged
                                 (flips count Stub→Full only)

m1 session-thrashing (--turn 5; ref has exactly one variant):
  broad `--pin tool:read_file(path="src/auth/session.ts")`  → forced [sha256:9f2ac17d]
  precision `--pin '(tool:read_file(path="src/auth/session.ts"), sha256:9f2ac17d)'`
    → identical flip — equivalence when single-variant; the tuple handles
    quote/paren/comma-bearing refs correctly

error paths (all exit 2): undeclared hash (with per-ref hash roster) · unknown
ref (with refs roster) · `(ref)` missing comma · empty hash · unclosed tuple ·
--pin without --turn (T16 rule).  comma-bearing ref inside a tuple parses as a
ref (no false "malformed").

regression: no-flag replay exits — 9 fixtures 0; vectors/session-divergent + events-v0
exit 1 (divergent by design, same as the T16 record); --turn 3 on divergent = 1,
--turn 0 = 0.  (Witness note: an earlier sweep line printed false 0s — `$(basename)`
in the same printf resets `$?`; re-measured directly, no functional regression.)

$ tools/run-ci.sh  →  rust 44/44 · ts 12+8 · schema 320 checks · hub byte-identity
                     →  ALL GATES GREEN
```

## 3. Honest deviations / limitations

- **Tuple form needs quoting in shells** (parens are metacharacters);
  `--pin '(ref, hash)'` is the documented spelling. No unquoted alias was added
  (an `@`/`:` separator risks colliding with refs containing those chars — the
  last-comma rule is collision-free for the hash-last shape).
- **A broad ref that is literally `(x)` would mis-parse** as a malformed tuple.
  No declared ref in any corpus begins with `(`; if one ever does, add an escape
  rather than clever form-detection.
- **Detection of hash-not-declared lists ALL declared hashes for the ref**, not
  the turn-proximate ones — deliberate keep-it-simple; the roster is small.
- Same visibility-not-correctness limit as T16 (pinned render proves presence,
  not model behavior); unchanged.

## 4. Files

- modified: `rust/crates/ctxvm-core/src/render.rs` (`Pin` + overlay signature), `rust/crates/ctxvm-core/src/lib.rs` (export), `rust/crates/ctxvm-conformance/src/bin/replay.rs` (parse/resolve/labels), `00-README.md`, `08-HANDOFF.md`, `reports/LOG.md`, this report.
- synthetic witnesses under `/tmp/opencode/t20/` — not committed; corpus/spec untouched; `packages/hermes/` (T17, other agent) untouched.

## 5. Next

UCVERIFY class F is now fully closed (replay turn/pin/output ✓, profile ✓, diff ✓,
pin precision ✓). Remaining design-concept: `ctxvm export` (ODPS snapshot
packaging; T17's Phase-0 spike feeds the resume half) and profile summary
windowing. T17 review when the Hermes workstream reports.
