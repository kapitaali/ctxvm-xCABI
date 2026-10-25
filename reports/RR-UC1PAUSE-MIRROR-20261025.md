# RR — UC1-PAUSE-MIRROR — opencode UC1 pause (TS mirror + argv-law fix both sides + flush-time handoff)

**Card executed:** UC1-PAUSE-MIRROR — the opencode half of the UC1-PLUGIN B2 row (the
hermes B2 card RR-UC1-PAUSE-20261025 delivered the hermes pause beat; the design §6 B2
text promised both packages, and orchestrator policy approved the argv-law fix crossing
both files in this single card).

## The wire bug this card fixes (probed + proven)

Their landed `UC1Handoff.pause()` assembled the export argv as
`[trace, str(turn), --output DIR, --odps]` — a **bare positional turn**. The real binary
rejects it:

```
$ export /tmp/pauseprobe/probe.jsonl 2 --output /tmp/pauseprobe/mdir --odps
ctxvm export: unexpected second positional `2`
rc=2
```

So EVERY `pause(..., turn=N)` since B2 landed exits 2 — `test_pause_returns_dict`
turn=3 passed only by asserting dict-shape, never success. New hermes test
`test_pause_at_turn_exports_snapshot` pins success (exit 0 + packaging) on the fixed
path, a corpus anchor, turn=2 (with the engine's slice-turn artifact-naming law —
`--turn` beyond the last window slices identity and names by the slice's last turn, so
tests glob `trace-*.jsonl.zst` rather than pin `trace-2`).

**The fix, both sides, one card (09 §6 DoD):**
- hermes `packages/hermes/src/uc1_handoff.py` — argv assembly patched to the documented
  CLI form the module's own comment already promised: `["--turn", str(turn)]
  + [--output DIR, --odps]` (surgical 2-line insert; the rest of pause() untouched).
- opencode mirror emits the same fixed form (see below).
- Rust engine untouched (the engine was always right; the caller was wrong).

## What was built

- `packages/opencode/src/uc1-handoff.ts` (NEW) — the full `uc1_handoff.py` mirror:
  **pause()** — env/arg law (`CTXVM_HANDOFF_DIR` wins over the passed trace dir; name
  chain arg > `CTXVM_HANDOFF_NAME` > `"handoff"`; turn from env `CTXVM_HANDOFF_TURN`
  when the arg is None; `"flush"` label when unset), era-snapshot with cp -n semantics
  (never clobbers; snapshot records the era paths even when the copy was skipped),
  `export <trace> --turn N --output <dir>/handoff/ --odps`, the reference-dead replay
  counterproof mirrored verbatim (checks a literal `trace-N.jsonl.zst` that never
  exists → `verified` stays True — disclosed, retarget pending), result shape
  `{exit_code, snapshot, report, stderr, verified, divergences, witness}` with the
  exact early-failure 4-key shape and the values-order witness quirk (`artifacts` =
  the snapshot dict's VALUES: era copies, then handoff_dir, label, turn). **resume()**
  — moved verbatim from the superseded `uc1-resume.ts`; the module consolidates under
  the §1.2 file-naming law `uc1-handoff.{ts,py}`. Flush is the caller's duty (mirror of
  the reference design; the opencode caller happens to run pause AFTER its flush, so
  the design §2 ordering holds by construction).
- `packages/opencode/live/ctxvm.ts` — the flush-time handoff path (design §2 "unset
  turn = package at flush"): with `CTXVM_HANDOFF_DIR` and/or `CTXVM_HANDOFF_TURN` set,
  cleanup calls `uc1Pause({traceDir, handoffName: CTXVM_TRACE_NAME})` after the flush
  loop and re-emits the hermes `/ctxvm-handoff` witness rendering verbatim
  (`ctxvm-handoff: exit_code=N verified=True|False|None divergences=[…]`,
  `ctxvm-handoff stderr: …` — Python-cased booleans/None). Env recipes documented:
  `CTXVM_HANDOFF_DIR` equal to `CTXVM_TRACE_DIR` (the handoff dir resolves env-first
  per reference law); mid-session turn-shaped triggers need the follow-up card (below).
- `packages/opencode/test/uc1-handoff.test.ts` (NEW; supersedes uc1-resume.test.ts) —
  11 tests: the 5 resume tests (incl. the golden deep-equal vs the hermes-generated
  fixture) + 6 pause tests: argv law (turn rides `--turn N`, exit 0), missing-trace
  law (`cannot read` prefix), era never-clobber + records-paths-regardless + export-on-
  original, **byte-compare of the packaged tree vs a direct export CLI run** (this
  closes the design §6 B2 "byte-compare the packaged dir against a direct CLI run" TODO
  — same argv bytes, zstd frame-stable), witness values-order quirk, name OR-chain law.
- `packages/opencode/test/live-adapter.test.ts` — env-hygiene keys
  (+`CTXVM_HANDOFF_DIR`/`_TURN`), `CTXVM_RESUME_FROM` boot test import rewired, NEW
  flush-time handoff test: real capture → cleanup → era copies exist, the package
  carries manifest/checksums/llms + trace/*.zst/page-table, and the witness log passes
  the `/ctxvm-handoff` line with exit 0.
- `packages/hermes/test/test_uc1_handoff.py` — `test_pause_at_turn_exports_snapshot`
  (success pin; TemporaryDirectory-scoped asserts) + `test_pause_era_copy_never_clobbers`
  (cp -n law + records-paths quirk). Existing shape/missing-binary tests untouched.
- `09-plugin-parity.md` — §4 enforcement bullet updated (mirror path + argv law); §5
  gains the pause-mirror and flush-time-handoff kit rows; the resume fixture row's
  mirror path updated to `uc1-handoff.ts`.
- `design/uc1-plugin.md` §6 — B2 LANDED paragraph (hermes card + this mirror card; the
  B2 TODO byte-compare landed; disclosures).
- `tools/run-ci.sh` — count truth: `ts 12 + 34`, `python 58 + 30 + 8`.

## Disclosed deltas & findings (pre-existing, unpatched unless stated)

1. **argv law** — FIXED both sides here (above). This was the only wire bug fixed; the
   engine never had it.
2. **Dead pause counterproof (NOT patched):** pause's replay block checks the literal
   name `trace-N.jsonl.zst` (no f-string) while the binary writes
   `trace-<sliceTurn>.jsonl.zst` — the branch never executes, `verified: True` is
   unproven at pause time, `divergences: []` always. Their lane's to retarget (resume(),
   by contrast, computes the path correctly). Mirrored verbatim in TS until then.
3. **`/ctxvm-handoff` never flushes (NOT patched):** the docstring says "flush live
   tracers → era snapshot", the handler calls `pause()` immediately — no
   `_flush_traces()` — so the era copies a STALE file unless the operator flushed
   beforehand. Opencode's flush-time path has the ordering right by construction
   (cleanup flushes, then pauses). Their lane to fix.
4. **TS `finish()` non-idempotency (NOT patched):** hermes T17.7 made the python
   port's `finish()` idempotent + re-callable (subsequent events included again, turn
   facts not duplicated); the TS tracer re-pushes `turn.render`/`call.meta` facts on
   every call (no `finished` guard, `pendingMeta` never cleared). Any mid-session
   flush-then-continue would poison the trace with duplicates → the design §2
   turn-shaped opencode trigger is EXPLICITLY deferred to a follow-up card that lands
   the T17.7 parity on `@ctxvm/node` first.
5. **Junk `CTXVM_HANDOFF_TURN`** crashes the reference (`int()` uncaught); the TS
   mirror raises a loud typed equivalent instead of silently mis-parsing.
6. **`paused_at` precision:** python microseconds vs JS milliseconds (both Z-suffixed).

## Gates

`tools/run-ci.sh` → **ALL GATES GREEN** (run twice incl. after the count-line edit):
rust cargo test; release binaries; TS suites `12 + 34`; python suites `58 + 30 + 8`
(hermes 56+2 in the handoff file — the pause tests pin the fixed argv; binding 8/42
subtests; metrics 30); schema 515; hub byte-identity. Direct witnesses: pause runs
greed on a real corpus anchor with the FIXED argv both sides; the flush-time adapter
test drives a real capture → era copies → successful package; byte-compare green.

## Lane discipline

- Their module file `uc1_handoff.py` edited EXACTLY for the argv fix approved by the
  orchestrator this card (2 lines + comment); their `live/__init__.py`,
  `test_plugin.py`, `uc_registry.py` untouched. Cross-lane fix disclosed here + in the
  design/contract text + board row.
- Working tree polled before staging (`git log -1` + `status --porcelain`); no
  `git add -A`; one card commit + one bookkeeping commit; `||` typo-scan on every
  ledger edit.

**Status:** UC1-PLUGIN B2 opencode half LANDED; the UC1-PLUGIN row is DONE on both
sides for B1/B2/B3. Open follow-ups: TS finish() idempotency + mid-session turn
trigger (design §2); pause counterproof retarget + handler flush (hermes lane); B4 m6
corpus offer (orchestrator-gated).
