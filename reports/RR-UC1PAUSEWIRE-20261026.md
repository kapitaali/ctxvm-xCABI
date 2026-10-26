# RR — UC1-PAUSE-WIRE — pause counterproof live + flush-before-package + junk arm-but-degrade (both sides)

**Card:** design §2/§6 frontier, UC1-PLUGIN chain — turn the pause counterproof
from reference-dead to evidence, close the `/ctxvm-handoff` flush gap, and
adopt the junk-env arm-but-degrade ruling.

**Attribution:** the three CODE fixes are the hermes lane's work
(`ctxvm <ctxvm@local>`, commit `5e1dcfd`, one commit, 4 files, 125+/24-);
this report and the coverage/bookkeeping below are the opencode lane's
cross-lane backfill (kapitaali) — approved explicitly by the operator after
review showed the commit carried ZERO new tests and no RR/LOG/board/frontier
rows, with retargeted `verified` semantics.

## What their code did (5e1dcfd, reviewed + verified here)

| Fix | Where | Semantics |
| --- | --- | --- |
| 1. counterproof retarget | `uc1_handoff.pause()` + TS `uc1Pause()` | glob the packaged `trace-*.jsonl.zst`, parse the slice turn from the zst FILENAME, decompress to a temp file OUTSIDE the snapshot dir (no package pollution), `replay --turn N`, type-guarded divergence reader (non-dict stdout records no divergences instead of crashing), era-vs-package `_diff_relation`/`shellDiff` expecting `identical` when a turn is set (m6 law: mismatch ⇒ `verified=False`). New `diff_relation` key on `PauseResult` (both sides). |
| 2. flush-before-package | `live/__init__.py` `/ctxvm-handoff` handler | `_flush_traces()` runs before `uc1.pause(...)` — the handler docstring's promise became real (single `pause()` call site, line 756). |
| 3. junk-env arm-but-degrade | `uc1_handoff.pause()` | junk `CTXVM_HANDOFF_TURN` → loud line `CTXVM_HANDOFF_TURN=<value> not an integer — handoff trigger disarmed` to stderr, trigger off (`turn=None`), capture continues; never crashes the call path. |

TS mirror updated in the same commit (pre-cleared by the operator): counterproof
live, `shellDiff` era diff, `diff_relation` added. Their junk DEGRADE law is now
their module's law (ruling C); this lane's ADAPTER junk-witness law stays
separate (below).

## What the backfill added (this commit)

1. **`packages/hermes/test/test_uc1_handoff.py` — `UC1PauseWireTests` (4 tests + 1
   extended):** junk degrade (loud line + `turn=None` + `label="flush"` +
   `diff_relation None`, via `redirect_stderr`), lawful divergent pre-seed
   (`session-thrashing` era + cp -n survival → `verified=False`,
   `diff_relation "divergent"`), type-guard (monkeypatched `replay` returning
   non-dict `[]` → no crash, `divergences == []`, still verified), int env law
   (`"3"` → `turn=3`); the existing happy-path pause test lost its stale
   dead-path comment and now asserts `diff_relation == "identical"`.
2. **`packages/opencode/src/uc1-handoff.ts` — module junk-law convergence:** the
   STALE delta ("the reference crashes; the mirror raises a loud equivalent")
   is gone. `uc1Pause` now CATCHES the `turnFromEnv` throw and prints their
   exact loud line to stderr with the RAW env value, then continues with
   `turn=null` — mirror parity with their Fix 3. The strict `turnFromEnv`
   KEEPS THROWING deliberately: the adapter's arm-time junk witness
   (`live/ctxvm.ts` "trigger not armed (junk CTXVM_HANDOFF_TURN)") keeps its
   own catch — two laws, one truth function, both preserved.
   **This also fixes a latent bug found in review:** the cleanup path's
   `pausePackage()` called `uc1Pause({...})` bare (env fallback), so a junk
   `CTXVM_HANDOFF_TURN` + `CTXVM_HANDOFF_DIR` set would have THROWN out of the
   untried cleanup gate — breaking the "capture never breaks" law on exit. It
   now degrades the same way the module does.
3. **`packages/opencode/test/uc1-handoff.test.ts` (3 new + 1 extended):** junk
   degrade mirrors the python test byte-for-byte (stderr-text assert),
   divergent pre-seed (same anchor, same law), `pauseTurnFromEnv`
   keeps-throwing pin (the adapter law is regression-guarded), and the argv-law
   test asserts `diff_relation === "identical"`.

## Disclosed asymmetry (probed, NOT changed in this card)

The rust `diff` CLI is fail-closed on content: an UNPARSEABLE era/source file
exits 2 with no JSON → `_diff_relation`/`shellDiff` yield `relation=None`.

- **pause() (both sides):** `None` is skipped — the counterproof is BEST EFFORT
  ("never blocks"), so a junk-byte era copy does NOT unverify; `verified` stays
  True and `diff_relation` stays None. Pinned by the junk tests' in-comment
  explanation (both sides use a REAL divergent trace anchor to exercise the
  divergent law).
- **resume() (both sides):** `None` → `exit_code 2, verified False, "diff tool
  failed"` — fail-closed, correctly: resume is the verification gate.

This pause⇄resume asymmetry is pre-existing of their retarget, mirrored
identically on both sides (pause↔pause and resume↔resume parity intact). Left
as-is on theory-of-verification grounds; flagged here for the frontier if the
operator ever wants a loud line at pause for `relation=None`.

## Gates

- hermes: `python3 -m pytest test/ -q` → **74 passed** (was 70; +4 backfill)
- opencode: `node --test test/` → **50 pass** (was 47; +3 backfill)
- count line updated same-card: `ts 13 + 50 / python 74 + 30 + 8`
- their commit re-verified green before the backfill (70/47) — no revert of
  their code; this card only ADDS tests/books and converges the TS module junk
  law.
