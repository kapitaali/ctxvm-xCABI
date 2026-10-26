# RR — UC1-VERIFY-CHECKS — design §3 (1)(3)(4) in-module on BOTH sides (v-next beat)

**Card:** UC1-PLUGIN v-next from the §0 frontier — the in-module boot-check
completion (approved cross-lane one card per the argv-fix precedent, including
this session's newest code fact: the resume DIGEST hashes only the recorded
checksum hex strings, so a corrupted artifact with an intact checksums file
passed boot verification on BOTH sides before this card).

**Design ruling (operator, 2026-10-26):** §3(3) is implemented LAW-AWARE — the
era pair canonical, derivedFrom diagnostic-only (design §3 was written pre-m6
expecting full-vs-slice `a_extends_b`; the m6 knowledge-stateful-tail law means
a full-vs-package diff diverges lawfully whenever later pages exist, so the
strict reading would unverify good snapshots). Same ruling produced the design
§3 amendment below.
Also fixed: their `resume()` docstring promised "Read manifest.yaml +
checksums.sha256 for snapshot integrity" while the body read NEITHER — the same
docstring-vs-body gap as their `/ctxvm-handoff` flush bug, same file; the
docstring's step 2 is now real on both sides.

## What landed (both sides, one commit)

**`packages/hermes/src/uc1_handoff.py` + `packages/opencode/src/uc1-handoff.ts`
(byte-mirrored):** after the existing decompress + replay counterproof, resume()
now runs, in order:

1. **§3(1) byte-level:** `checksums.sha256` required; every row re-verified
   against the artifact bytes (`checksum mismatch for <name>` / `checksummed
   artifact missing: <name>` / `checksums.sha256 missing: <dir>`); then the
   manifest template cross-check — `sliceTurn` must exist and equal the trace's
   turn (`manifest sliceTurn <x> != trace turn <n>`); light template read, NO
   yaml dependency introduced on either side.
2. **§3(3) law-aware diff:** era candidate = files matching `*-turn-{N}.jsonl`
   beside the package (the mid-session chain's era copies, when
   `CTXVM_HANDOFF_DIR == CTXVM_TRACE_DIR`); relation must be `identical`
   (`era diff <name>: relation <rel> expected identical` otherwise →
   unverified). Without an era: manifest `derivedFrom` diffed DIAGNOSTIC ONLY —
   any divergence (the m6 lawful shape) is surfaced, never verdict-forming; a
   relative derivedFrom resolves from the resuming process's cwd exactly as the
   manifest's own `verify.diff` hint assumes; neither source on disk →
   `evidence.diff = null` (skipped).
3. **§3(4) surfacing:** `page-table-N.json` required and JSON-readable
   (`page-table-N.json unreadable`, no engine-specific message text — parity),
   turn field must match the trace turn (`page-table turn <x> != trace turn
   <n>`); slots counted into `evidence.projection = {turn, slots}` and rendered
   by both call sites as `projection: <k> slot(s) at turn <n>` +
   `diff: source=… relation=…` / `diff: skipped — no source slice on disk`
   (witness lines only on the verified path; failures stay loud via the reason
   line).

All new failure paths: `exit_code 2`, `verified=False`, tracer continues
UNVERIFIED (design law). The SUCCESS contract is unchanged — same reason
string (`snapshot verified: replay exit 0 at turn N` — m6-era sidecars and the
drop README quoting it stay byte-true), same digest, same artifact list, plus
three additive evidence keys: `manifest {sliceTurn}`, `projection {turn,
slots}`, `diff {source, relation} | null`. Per the B3 sidecar law (09 §3
extension: the whole evidence dict flows into `resumeFrom`), the new keys ship
as nested opt-in sidecar fields — the sidecar CANON top-level shape is
untouched, and m6-era sidecars on disk stay valid as captured (re-baseline
verified: the shipped `corpus/m6` package re-runs the NEW chain green — see
Witnesses).

New helper mirrored: `_diff_relation` / `shellDiff` — shells the rust `diff`
CLI (source first, slice second, the manifest's own `verify.diff` order),
scrapes the lowercase relation from its JSON stdout; unusable invocation/output
→ `diff tool failed: <stderr>` / `diff tool output unparseable` (strict on the
era path, diagnostic on the derivedFrom path).

**Call sites:** `packages/hermes/live/__init__.py` register() + `packages/
opencode/live/ctxvm.ts` — the two surfacing witness lines, Python-style
rendering already matching.

## Tests (11 + 11 mirrored, one card)

`test_uc1_handoff.py` gains `UC1ResumeVerifyChecksTests`;
`uc1-handoff.test.ts` gains the v-next section — same literals asserted
byte-for-byte on both sides:

corrupted artifact → checksum mismatch; checksummed artifact missing; checksums
missing; manifest sliceTurn contradiction (row re-stamped via a `fixRow`
helper); era present + identical → verified with `diff {source, relation
identical}`; era present + mismatching (full m1 as a turn-0 "era" →
`a_extends_b` ≠ identical) → UNVERIFIED; derivedFrom divergence on a
stage-overwritten source → verified STAYS TRUE (the m6 shape reproduced from
committed corpus files only); no source → `diff null`, verified; projection
surfaced (slots from the actual page-table); unreadable page-table;
page-table turn contradiction. The shared golden fixture gains `manifest` /
`projection` / `diff` fields (m1 anchor @0: `{sliceTurn: 0}`, `{turn: 0, slots:
3}`, `{source: "corpus/m1/session-healthy.jsonl", relation: "a_extends_b"}`) —
pinned by `UC1ResumeGoldenParityTests` AND the TS golden test in the same card;
the TS golden test now chdirs to the repo root for the resume call (the
manifest's relative derivedFrom resolves from the resuming process's cwd —
mirroring the hermes golden class's existing chdir discipline).

## The one test-engineering discovery

A post-hoc `export <full> --turn N` slice ALWAYS prefix-extends its own source:
the slice carries the full trace's own post-hoc render tail (m6 law: exported
slices keep `turn.render` rows stamped with the source's flush-time knowledge).
Therefore the first version of the "lawful divergent" test was wrong —
`diff(m2-full, m2-slice@0)` came back `a_extends_b`, not divergent. The
divergent shape exists only between artifacts of DIFFERENT knowledge windows
(full session vs mid-session package) — reproduced in-test by overwriting a
staged derivedFrom source after packaging (exactly what happens when a pausing
session's flushed file is overwritten by the continued session), from committed
corpus files only.

## Witnesses

- `python3 -m pytest test/ -q` (packages/hermes): **70 passed** (59 + 11), one
  PRE-EXISTING SyntaxWarning (docstring backtick escape, line 97 — untouched
  here).
- `node --test test/` (packages/opencode): **47 pass, 0 fail** (36 + 11).
- `tools/run-ci.sh` → **ALL GATES GREEN**; counts truth line updated same-card:
  `ts 13 + 47 / python 70 + 30 + 8`.
- The shipped `corpus/m6` package re-run THROUGH the new chain post-card:
  `verified=True reason=snapshot verified: replay exit 0 at turn 3`,
  `diff {source: /tmp/…/m6-a.jsonl, relation: divergent}` (diagnostic-only,
  exactly the lawful shape), `projection {turn: 3, slots: 3}`,
  `manifest {sliceTurn: 3}` — the drop's package re-verifies on both a host
  with the capture paths present (diagnostic path) and any host without them
  (skip path).

## Disclosed

1. The rust `diff` CLI emits a human line before the JSON; the helper scrapes
   from the first `{` — if a future diff version changes stdout shape, the era
   path fails loud (strict) and the derivedFrom path degrades diagnostic (safe).
2. `evidence.snapshot` in the new failure paths carries each side's own
   pre-existing convention (TS: the raw arg; hermes `decompress/replay`: 
   `str(snap_path)`) — mirroring each side's own precedent file-internally;
   reasons embed the raw arg on both sides and are byte-identical for
   identical inputs.
3. Era candidate selection takes the sorted-first match when multiple
   `*-turn-N.jsonl` files exist (deterministic; the witness line names the
   file). A dir containing unrelated files ending in `-turn-N.jsonl` would be
   treated as era ancestry — none exists in the corpus convention today.
4. The `test_uc1_handoff.py:97` SyntaxWarning predates this card (docstring
   backtick escapes in the argv-law test) — not touched.

## Lane discipline

Their lane edited in ONE approved cross-lane card (uc1_handoff.py +
test_uc1_handoff.py + live/__init__.py — the argv-fix precedent); working tree
polled before staging; explicit paths only; one card commit + one bookkeeping
commit.

**Status:** UC1-PLUGIN §3 is now fully in-module on both sides — the boot
check covers all four design items; remaining open = their lane's two
disclosed pause fixes (counterproof dead code, handler flush), junk-env
loud-raise parity, the gated `handoff-inject` beat, and the optional
hermes-side m6 pair.
