# RR — UC1-TRIGGER — TS `finish()` idempotency (T17.7 parity) + the mid-session turn-shaped handoff trigger

**Card executed:** the explicit follow-up of UC1-PAUSE-MIRROR — design §2's opencode
mid-session turn-shaped trigger, gated on the TS `finish()` idempotency that the pause
card disclosed as missing (`@ctxvm/node` re-pushed `turn.render`/`call.meta` facts on
every flush, while the hermes port has been idempotent since T17.7).

## The recon finding that widened the card

Planning the mirror from the reference revealed **T17.7's law was never actually pinned**
on either side: `packages/hermes/src/plugin.py`'s `finish()` implements idempotency and
documents it ("the tail is computed per call and never appended to `_events`"), but no
test in their suite exercises a double finish. So the law is pinned BOTH sides in this
one card (§4 enforcement, golden-fixture precedent).

The exact reference law (mirror target — my planning notes had it wrong as
"clear/only-new"): the tail is **recomputed from live state at every call and never
appended to the event stream**; `pending_meta` is **never cleared** and re-renders each
call. Consequences: (a) two flushes without new lifecycle → identical JSONL; (b) a
mid-session flush followed by more lifecycle → the second transcript contains the new
events exactly once plus a freshly regenerated tail; (c) the first flushed transcript is
never retroactively mutated.

## What was built

- `packages/node/src/tracer.ts` — `finish()` no longer `push()`es the tail: it builds
  `tail`, returns `[...events, ...tail]` with the docstring mirrored from the hermes
  reference. `pendingMeta` untouched (never cleared — hermes law).
- **Law pinned both sides:** `packages/node/test/tracer.test.ts` +1
  (`finish() idempotent (T17.7 parity)` — two finishes byte-equal; post-flush lifecycle
  joins the second transcript exactly once; `page.declare`/`turn.render`/`call.meta`
  counts prove no tail duplication; the first transcript unchanged) and
  `packages/hermes/test/test_plugin.py` +1 (`test_finish_idempotent_tail_regenerates` —
  the same three assertions on the reference, restoring the pin the T17.7 card skipped).
- `packages/opencode/src/uc1-handoff.ts` — exports `pauseTurnFromEnv()` so the adapter
  arms the trigger with the SAME env law the module reads (single truth:
  `int(…,"0") or None`; junk raises loudly inside the module).
- `packages/opencode/live/ctxvm.ts` — the mid-session trigger (design §2 trigger law for
  opencode):
  - **Arm:** `CTXVM_HANDOFF_TURN=N` (positive int; `"0"`/unset = the flush-time package
    path). Arm-but-degrade: a junk env value is a loud witness line and capture
    continues — the module's mirrored loud raise stays internal, rather than breaking
    plugin setup (the hermes reference instead crashes its `/ctxvm-handoff` command;
    their lane).
  - **Fire:** in the (now async) context hook, ONCE per session, right after the context
    fire that registered turn N — the probe is `tracerFor(sessionID).finish().stats` (an
    idempotent finish: events untouched). Then the §2 flow: flush through the SAME
    naming law (`flushTraces()`, now shared by trigger and cleanup, one sidecar truth
    incl. the B3 `resumeFrom` LAST slot) → era copy (cp -n, `label=turn-N`) → package
    with `--turn N` via `uc1Pause` (re-reads the env turn itself) → the hermes
    `/ctxvm-handoff` rendering line.
  - **Continue:** tracing continues unless `CTXVM_HANDOFF_STOP=1`, which disposes the
    hook registrations (witness: `handoff stop: hook registrations disposed`) — pause is
    not teardown by default; cleanup still flushes the final trace.
  - **Cleanup gate:** the flush-time package is now the FALLBACK only — skipped when a
    trigger already fired (no double package); runs still when `handoffTurn === null`
    (incl. the `CTXVM_HANDOFF_TURN="0"`-alone recipe, which the env law maps to turn
    None → `label=flush`) or when armed but nothing fired (session ended before turn N —
    still exported with the env turn per the pause() law, slice naming law applies).
- `packages/opencode/test/live-adapter.test.ts` — +2 trigger tests:
  (1) boundary behavior (no package before turn N; era copies
  `hand-test-turn-1.{jsonl,meta.json}` + packaged manifest/checksums/`trace-*.jsonl.zst`
  right AT the boundary; exactly one trigger line; continued tracing NOT lost at the
  final flush; exactly ONE `ctxvm-handoff:` line total — cleanup skipped); (2) STOP=1
  (package + both hook registrations disposed + stop witness + cleanup flush survives,
  re-dispose idempotent-safe).
- `tools/run-ci.sh` — count truth `ts 13 + 36`, `python 59 + 30 + 8`.

## Disclosed deltas

1. **Probe cost:** when armed, every context fire pays one idempotent `finish()` (tail
   regeneration + full JSONL join) — O(turns+meta) per fire. v0 recipes are
   single-session/short-turn; there is no cheap turn-count read without exposing
   private tracer state, and the probe is exactly the law §2 describes (fire right
   after that turn's `turn.render`).
2. **One-fired-suppresses-all:** with multi-session capture and a fired trigger in
   session A, the cleanup fallback package is suppressed even if session B never
   reached turn N. v0 simplification — the design recipes (§2, B4 proposal `7a2d4a0`)
   are single-session; revisit with B4's live m6 run.
3. **STOP double-dispose:** cleanup re-disposes already-disposed registrations
   (idempotent-safe in the v2 promise contract; the test doubles agree).
4. The tracer surface change is engine-adjacent but state-neutral: `finish()`'s return
   shape, JSONL bytes for single-flush usage, event order, and stats are unchanged —
   the 12 pre-existing node tests all pass unmodified (that IS the regression proof).

## Gates

`tools/run-ci.sh` → **ALL GATES GREEN**; suite truths: node 13 (+1), opencode 36 (+2),
hermes 59 (+1 — `test_plugin.py` 24), binding 8/42 subtests, metrics 30; schema + hub
byte-identity. Line before staging everything: see commit message footer.

## Lane discipline

Hermes **source** untouched (T17.7 is their landed reference law); only their TEST file
gains the shared law pin (mirror of the node test, same commit per the both-sides DoD).
Working tree polled (`8fca88c`/`bc399cf` research commits, no overlap); explicit paths
staged; RR + bookkeeping separated.

**Status:** UC1-PAUSE-MIRROR's deferred scope closed. Remaining on UC1: pause counterproof
dead-code retarget + `/ctxvm-handoff` flush-before-package + junk-env loud-raise parity
(hermes lane); B4 m6 corpus offer (orchestrator-gated; drop shape in
reports/B4-PROPOSAL-20261025).
