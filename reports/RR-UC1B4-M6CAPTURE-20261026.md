# RR — UC1-B4-M6CAPTURE — corpus m6: the first real pause/resume pair (opencode both sides, mid-session turn 3)

**Card executed:** UC1-PLUGIN beat B4 — the operator-gated m6 corpus drop (proposal
`reports/B4-PROPOSAL-20261025.md`, their `7a2d4a0`). Operator rulings on the proposal's
open questions (2026-10-26): **(1)** m6 is produced **opencode both sides** — design §4
does not claim cross-harness handoff, and the hermes canonical flow would fail on the
wire today because their `/ctxvm-handoff` handler still ships without the
flush-before-package its docstring promises (their pause card disclosure, unpatched in
their lane); **(2)** mid-session **turn 3 with real pages**, not the trivial
package-at-flush. Card on the kapitaali lane: the opencode adapter is this lane's UC1
end-to-end surface (UC1-PAUSE-MIRROR + UC1-TRIGGER landed the whole chain).

## The real captures (two separate one-shot agent runs)

Scratch workspace `/tmp/opencode/m6-ws` (only the shim + `notes/*.md` fixtures), shim
`.opencode/plugins/ctxvm.ts` re-exporting the repo adapter absolute path (recipe in
`packages/opencode/live/README.md`), model `opencode/glm-5.3-flash-free` (USD 0), m2
pattern `opencode run --standalone --auto`.

- **session-a (pause beat)** — `CTXVM_TRACE_DIR=CTXVM_HANDOFF_DIR=/tmp/opencode/m6-cap/a`,
  `CTXVM_TRACE_NAME=m6-a`, `CTXVM_HANDOFF_TURN=3`, sequenced real tool work (read
  alpha+beta → edit alpha phrase → re-read alpha (new contentHash) → read gamma →
  `shell cat notes/*.md`). Witnessed, in order: 7 context fires; at turn 3
  `handoff trigger turn=3 session=ses_e88e3edb… (flush → era copy → package → continue
  unless CTXVM_HANDOFF_STOP=1)` → mid-session flush (2671 bytes) → era copies
  `m6-a-turn-3.{jsonl,meta.json}` → **`ctxvm-handoff: exit_code=0 verified=True
  divergences=[]`** → four MORE context fires (turns 4–6; tracing continued — STOP
  unset) → exit flush (4573 bytes). The full trace: 32 events, 7 turns, 6 pages across
  read/edit/shell, 5 cold-entry faults. The trigger's probe was the just-landed
  idempotent `finish()` — the event stream untouched by the pause (that card was built
  FOR this beat; the drop is its first real-run witness).
- **session-b (resume beat)** — `CTXVM_RESUME_FROM=/tmp/opencode/m6-cap/a/handoff`,
  fresh trace dir. Wall-witnessed boot check BEFORE any hook work:
  `resume_from=/tmp/…/a/handoff verified=True reason=snapshot verified: replay exit 0
  at turn 3`. 13 events / 3 turns / 2 pages; the canonical sidecar's `resumeFrom`
  carries snapshot path + `snapshotDigest: sha256:1ca35687…` + `snapTurn: 3` + sorted
  artifact list — and the digest **recomputes exactly** from the SHIPPED
  `handoff/turn-3/checksums.sha256` (checksum-hex construction), so the evidence chain
  survives the corpus move.

## The new engine law the drop measured: the render tail is knowledge-stateful

The report-worthy finding. The naive proposal check (`diff <pause trace> <package>` →
`a_extends_b`) **does not hold for a mid-session pause with later-declared pages** —
and this is not a bug, it is the v0 derived-composition arithmetic doing what its
tracer comment says (`tally_at` sums the WHOLE table):

- full session-a tail stamps turns 0–6 with `residentTokens: 253` (all six pages —
  post-hoc knowledge at the exit flush);
- the mid-session package honestly stamps turns 0–3 with `93` (three pages — turn-3
  knowledge);
- `diff(full, package)`: shared **pre-tail lifecycle prefix of 10 events**
  (session.open + 3 declares + 3 faults + 3 renders), `firstDivergentEvent: 10`,
  `tallyMismatches` at turns 0–3 (253 vs 93).

The hermes witness chain satisfied full-vs-slice `a_extends_b` only because
`corpus/m2/live-echo.jsonl` declares all its pages by turn 2 — no late pages existed to
revisit. m6 is the first drop to exercise a pause WITH late pages, so the law's
boundary is now characterized: **the shared-prefix counterproof's canonical pair is
`diff(era-as-flushed, package slice) → identical` over all 18 events** — the exact
design §3(3) wording ("source slice on disk" vs trace-N) with the honest source (the
file the export actually consumed). Also measured while characterizing: the post-hoc
`export full --turn 3` keeps `turn.render` rows of ALL later turns in the projection
(29 events; only the `call.meta` rows trim by turn) — the window narrows `call.meta`
but the render tail belongs to the projection, not the window.

Additionally run for the record: `replay` on full-a, package-slice (`--turn 3`), and b
all exit 0; schema PASS 87 + 68 checks; `verify-capture.sh` sidecar CANON MATCH on both
traces. Both replays' violations are the redaction-free cold-entry shape (m5
precedent), not defects.

## The corpus drop (`corpus/m6/`)

Opencode naming per the corpus m5 convention; the proposal's shape executed exactly
(their `handoff/turn-N/` nesting kept, `hermes-*` → `opencode-*` per the harness
ruling):

- `opencode-pause-session-a.jsonl` + `.meta.json` (resumeFrom: null)
- `opencode-resume-session-b.jsonl` + `.meta.json` (resumeFrom: object)
- `handoff/turn-3/` — the package exactly as produced (5 artifacts; `trace-3.jsonl.zst`
  names the slice turn per the T21 law)
- `README.md` (drop description, the knowledge-stateful-tail section, reproduction
  recipes incl. the exact env) + `provenance.json` (m5-style; beats/limitations name
  the new law too) + `checksums.sha256` (12 rows, `sha256sum -c` green; the package's
  own internal birth-checked `checksums.sha256` still verifies separately).

## Gate wiring

`tools/run-ci.sh`: `corpus/m6/*.jsonl` added to the schema FIXTURES list; per-drop
`( cd corpus/m6 && sha256sum -c checksums.sha256 )` added to gate 3.
`04-odps-dataproduct-corpus.yaml`: RE-VALIDATED 2026-10-26 header line,
`latestDrop: corpus/m6`, `productVersion: 0.6.0`, description sentence.
`hub/`: regenerated via `tools/build-hub.sh` (their SDK), `hub/hub.sha256` re-baselined
in the same change (the self-baseline law). Counts unchanged (`ts 13 + 36 / python 59 +
30 + 8` — no test additions; the drop IS the evidence).

## Disclosed

1. **Cross-harness non-executed hermes flow:** the canonical hermes
   `/ctxvm-handoff <dir> [turn]` steps of the proposal remain un-executed by design —
   the handler flush fix is that lane's disclosed item; a hermes-side m6-pair drop can
   follow THEIR fix (page identity transfers across harnesses in principle; the design
   §4 wording does not claim it).
2. The capture-time absolute paths (sidecar `resumeFrom.snapshot`, witness quotes) ship
   in the clear per m1–m3 precedent; the drop README documents the corpus mapping and
   the digest re-derivation.
3. `verify-capture.sh` operates on trace files only; the package's identity proof
   (era-vs-package `diff identical`) is a manual step recorded in the drop README —
   a future kit entry could automate the pair-check.

## Gates

`tools/run-ci.sh` → **ALL GATES GREEN** (rust; release binaries; ts 13 + 36 / python
59 + 30 + 8; schema incl. both m6 traces + per-drop checksum + export round-trip; hub
regen byte-identity at productVersion 0.6.0).

## Lane discipline

Their lane's files untouched (the proposal doc is their artifact; the operator rulings
answer its open questions in MY report + the drop README). Working tree polled; corpus
scratch captures copied with explicit paths; one card commit + one bookkeeping commit;
counts unchanged.

**Status:** UC1-PLUGIN is DONE through B4 — B1 binding, B2 pause (both sides + argv
fix), B3 resume (both sides + golden), §2 mid-session trigger, and now the m6 corpus
beat. Remaining open items are the hermes lane's three disclosed fixes and design §3
v-next (in-module verification checks + the gated `handoff-inject` beat).
