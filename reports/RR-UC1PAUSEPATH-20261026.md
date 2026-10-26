# RR — UC1PAUSEPATH — hermes pause-path hardening (m7 frontier)

**Card:** hermes pause-path hardening — m7 frontier (S, one commit). Three
disclosed fixes on the hermes lane plus a doc line for the export wart.

**Attribution:** ctxvm <ctxvm@local>. No push; operator pushes personally.

## What was done

1. **`packages/hermes/live/__init__.py`** — `/ctxvm-handoff` now passes
   `handoff_name=_flush_base()` to `uc1.pause()`, so the flush and the package
   use the same name (the trace name from `CTXVM_TRACE_NAME` / state) instead
   of the default `"handoff"`. This closes the m7 run-1 failure mode: the
   handler flushed/packaged under the default name while the session flushed
   `session-a.jsonl`. New test `test_handoff_passes_trace_name_as_handoff_name`
   pins the m7 shape (mock uc1 records the kwargs).

2. **`packages/hermes/src/uc1_handoff.py`** — `pause()` dir chain made
   ARG-FIRST: `trace_dir or os.environ.get("CTXVM_HANDOFF_DIR")`, mirroring
   the TS ruling in 2bb339a. An env-first line lets a leaked service
   environment override the caller's explicit dir. New law test
   `test_pause_dir_chain_arg_beats_env` sets a junk `CTXVM_HANDOFF_DIR` and
   asserts the explicit dir still wins (exit 0, era copy beside it).

3. **Export wart doc line** (RR-UM7CAPTURE Discoveries 1): one-dir-one-slice
   comment added near the export invocation — rust export writes shared
   generic names (`manifest.yaml`/`llms.txt`/`checksums.sha256`) that the next
   per-turn export into the same dir clobbers; only `trace-N`/`page-table-N`
   carry the turn. Doc/comment fix only; engine filenames unchanged.

## Verification

- Hermes pytest: 76 passed (74 baseline + 2 new).
- `bash tools/run-ci.sh` → ALL GATES GREEN (rust, ts 13 + 51, python 76 + 30 + 8,
  schema 629 checks / 25 fixtures, hub byte-identity).
- Adopted plugin copy synced to `~/.hermes/plugins/ctxvm-tracer/`.

## Counts

`ts 13 + 51 / python 76 + 30 + 8`

## Open (not in this card)

- Gateway tool=None hook-key mapping; verified-boot resume-brief UX; gated
  handoff-inject v-next beat (parked pending orchestrator sign-off).
- T15 (Vercel AI SDK adapter); swap-regen-restore restoration recipe
  (orchestrator call).
- Push to origin/main (owner-only, no PAT on box).
