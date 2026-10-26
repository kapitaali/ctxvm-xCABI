# Corpus drop M6 — first pause/resume pair (OpenCode)

First **mid-session pause + resume drop** for the **ctxvm Trace Corpus**, produced as the
UC1-PLUGIN B4 beat (proposal `reports/B4-PROPOSAL-20261025.md`; operator rulings on its
open questions: **opencode both sides** — design §4 does not claim cross-harness handoff
and the hermes `/ctxvm-handoff` handler shipped without the flush-before-package step its
docstring promises, so the canonical hermes operator flow would pause against a stale
file today; mid-session **turn 3 with real pages** — the design's subject, not the
trivial package-at-flush). Session-a is a real scripted OpenCode 2.1.4 agent run whose
plugged-in adapter (`packages/opencode/live/ctxvm.ts` + the UC1-TRIGGER mid-session
path) fired the turn-shaped handoff trigger at turn 3, packaged the snapshot through the
committed `export` binary, **continued tracing to turn 6** (pause is not teardown), and
flushed the full trace at plugin unload. Session-b is a fresh real run booted with
`CTXVM_RESUME_FROM` pointing at the package: the boot check verified the snapshot before
any hook work and stamped the canonical `resumeFrom` sidecar evidence.

| File | Origin | Tool calls | Turns | Pages | Faults | Events |
|------|--------|------------|-------|-------|--------|--------|
| `opencode-pause-session-a.jsonl` | session-a full trace (turns 0–6; trigger packaged turns 0–3 mid-session at bytes 2671, exit flush = 4573) | 6 (6 ok) | 7 | 6 | 5 | 32 |
| `opencode-resume-session-b.jsonl` | session-b trace, resumed from the package | 2 (2 ok) | 3 | 2 | 2 | 13 |
| `handoff/turn-3/` | the pause package exactly as produced: `trace-3.jsonl.zst`, `page-table-3.json`, `manifest.yaml`, `llms.txt`, `checksums.sha256` (18 events of turn-3 state: 3 pages = `alpha.md` base + edit-new-hash + `beta.md`) | — | — | 3 | — | 18 |

Per-file provenance (harness version, invocation, flush/pause semantics, honest misses)
is in `provenance.json` and the `.meta.json` sidecars. Session-a's sidecar carries
`resumeFrom: null` (not resuming); session-b's carries the full evidence object
(snapshot path, `snapshotDigest: sha256:1ca35687…`, `snapTurn: 3`, artifact list).
Integrity: `checksums.sha256` (covers both traces + both sidecars + all five package
artifacts + `provenance.json`).

## What this capture shows

1. **The mid-session pause chain on real work.** Witnessed 2026-10-26:
   `handoff trigger turn=3 session=ses_e88e3edb… (flush → era copy → package → continue
   unless CTXVM_HANDOFF_STOP=1)` → mid-session flush (2671 bytes) → era copies
   `m6-a-turn-3.{jsonl,meta.json}` → `ctxvm-handoff: exit_code=0 verified=True
   divergences=[]` → **four more context fires** (turns 4–6) → cleanup flush (4573
   bytes). The trigger probed the trace with an idempotent `finish()` (UC1-TRIGGER T17.7
   parity): the in-memory event stream was untouched by the pause.
2. **The package is the era's turn-3 state, replay-deterministically:**
   `diff(era-as-flushed, package slice) → identical` over all 18 events (incl.
   `turn.render` residency 93 at every turn, three declares/faults/renders). This is
   design §3 chain item (3) — "diff source-slice-on-disk vs trace-N" — with the honest
   source being the mid-session flushed file, which is the input the export actually
   consumed.
3. **Resume provenance is verifiable from the drop.** `resumeFrom.snapshotDigest` in
   session-b's sidecar recomputes exactly from the shipped
   `handoff/turn-3/checksums.sha256` (checksum-hex construction, sorted by filename),
   and the boot check ran the full verify chain pre-work: zstd decompress inside the
   snapshot dir → `replay --turn 3` exit 0 → digest.
4. **A new law measured precisely: the render tail is knowledge-stateful.** The v0
   derived-composition arithmetic (every declared page resident at every turn;
   `tally_at` sums the whole table) makes `turn.render.residentTokens` depend on
   knowledge at FLUSH time, not session time. Consequence, quantified on this pair:
   - full session-a tail stamps turns 0–6 with 253 (all six pages, post-hoc knowledge);
   - the mid-session package stamps turns 0–3 with 93 (three pages, turn-3 knowledge);
   - `diff(full, package)` therefore shares the **complete pre-tail lifecycle prefix**
     (10 events: `session.open` + 3 declares + 3 faults + 3 renders) and departs exactly
     at the `turn.render` rows (`tallyMismatch` turns 0–3: 253 vs 93 — the late-declared
     `gamma.md`/`shell:cat` pages upgrade the earlier rows in the full tail).
   The m2-style "full ⊇ slice → `a_extends_b`" full-vs-slice law holds only when no
   pages are declared AFTER the pause turn (the hermes witness chain satisfied it
   because `corpus/m2/live-echo.jsonl` declares all three pages by turn 2). m6 exercises
   late pages, so the law's boundary is now characterized by a real drop, covered by the
   identical-era check (item 2).
5. **Resume is observation, not injection (v0 §3).** Session-b continues from its own
   fresh state — 13 events, its own 2 pages — the resume evidence is the boot-check
   verification + provenance stamp, per the gated handoff-inject beat (v-next).

## Validation (witnessed 2026-10-26)

```
$ python3 spec/rfc-0/validate_schema.py opencode-pause-session-a.jsonl
SCHEMA CONFORMANCE: PASS (87 checks)
$ python3 spec/rfc-0/validate_schema.py opencode-resume-session-b.jsonl
SCHEMA CONFORMANCE: PASS (68 checks)
$ rust/target/release/replay opencode-pause-session-a.jsonl   # exit 0, 32 events
$ rust/target/release/replay opencode-resume-session-b.jsonl  # exit 0, 13 events, []
$ zstd -d handoff/turn-3/trace-3.jsonl.zst && \
  rust/target/release/replay trace-3.jsonl --turn 3          # exit 0
$ rust/target/release/diff <era-flush> <package-slice>  → "relation": "identical" (18/18)
$ rust/target/release/diff <full-a> <package-slice>
   → relation "divergent", commonPrefixEvents 10, firstDivergentEvent 10,
     tallyMismatches turns 0–3 (253 vs 93)  # the knowledge-stateful tail — see item 4
$ resumeFrom.snapshotDigest == sha256(checksum hex, sorted)   # MATCHES shipped package
```

The 5 session-a replay violations are the cold-entry double-row shape itself (every
novel page faults once, then renders full next request — m5 precedent), not defects.

## Reproduction

```
# workspace with .opencode/plugins/ctxvm.ts shim re-exporting the repo adapter
export CTXVM_TRACE_DIR=/tmp/opencode/m6-cap/a
export CTXVM_TRACE_NAME=m6-a                    # era turn-3 copies + package land here
export CTXVM_MODEL=opencode/glm-5.3-flash-free
export CTXVM_PROVIDER=opencode
export CTXVM_AGENT_ID=ctxvm-m6
export CTXVM_BUDGET_TOKENS=200000
export CTXVM_OPENCODE_VERSION="$(opencode --version | awk '{print $2}')"
export CTXVM_HANDOFF_DIR="$CTXVM_TRACE_DIR"     # env law: handoff dir resolves env-first
export CTXVM_HANDOFF_TURN=3                     # fires once, right after turn 3
export CTXVM_RESUME_FROM unset                  # session-a is not resuming
opencode run --standalone --auto -m opencode/glm-5.3-flash-free "<multi-file work>"
# … session-b in the same workspace:
export CTXVM_RESUME_FROM=/tmp/opencode/m6-cap/a/handoff
export CTXVM_TRACE_DIR=/tmp/opencode/m6-cap/b ; export CTXVM_TRACE_NAME=m6-b
unset CTXVM_HANDOFF_DIR CTXVM_HANDOFF_TURN
opencode run --standalone --auto -m opencode/glm-5.3-flash-free "<continuation work>"
```

Snapshot era files immediately after the pause and the exit flush (later runs of the
same `CTXVM_TRACE_NAME` overwrite; the drop copies were taken at capture time — the
sidecar paths and witness lines record the capture-time absolute paths per the m1–m3
redaction precedent).
