# RR-TBSHAPE-20261118 — the surface is now pinned, and with it pinned the shape does not get answered

Owner instruction: "do 1" — close T-B's shape question. The question was open because the wired OpenCode run
passed completeness **with a shell** (196 `shell` declares), which is not the same as the shape being
hand-answerable. This card records the root cause of the surface leak, the fix, the three-prompt probe, and
what the probe does and does not settle. One model call was made; nothing else spent.

## 1. Why the surface was never pinned — the key was the wrong one

Measured, not assumed:

```
$ HERMES_HOME=~/.hermes/profiles/w8cn-naive hermes dump | grep toolsets
  toolsets:           file
$ hermes tools list -p w8cn-naive | head -5
  Built-in toolsets (cli):
    ✓ enabled  web
    ✓ enabled  browser
    ✓ enabled  terminal
    ✓ enabled  file
    ✓ enabled  code_execution
```

A CLI turn binds the **platform** list — "Built-in toolsets (cli)" — not the `toolsets` key. The profile said
`[file]`; the platform enabled `terminal`, `code_execution`, `browser`, `web`, `delegation`, `cronjob`,
`computer_use` and more. Three consequences, all of which bit earlier runs:

1. **The preflight validated the wrong key.** `tools/w8b-run.py` checked `hermes config get toolsets`, which
   answers `[file]` while the turn had a shell. That is why "toolsets pinned" was reported and was false.
2. **`HERMES_HOME` alone did not route the turn.** The client resolved `toolsets: file` correctly and the
   gateway still ran the turn with the platform set; naming the profile on the request —
   `hermes -p <profile> chat …`, flag before the subcommand — is the form that routes it.
3. **Every "DATA-INVALID, shell reached the model" verdict from 16–17 Nov has this cause**, not a model
   behaviour. The model was offered a shell; nothing about the model was being measured.

## 2. What was fixed

- **Both arms, symmetrically** (a pair must differ only in `context.engine`):
  `hermes -p w8cn-{naive,paged} tools disable --platform cli terminal code_execution browser web vision
  image_gen tts session_search connections delegation cronjob computer_use clarify`.
  Effective set now: `file`, `skills`, `todo`, `memory` (+ `context_engine` on the paged arm only).
  `delegation` and `cronjob` were disabled too — a subagent or a scheduled job is an execution route by proxy.
- **`tools/w8-driver.py` now emits `hermes -p <profile> chat …`** on every prompt, with the reason recorded in
  the code, so a turn cannot silently bind the root platform list again.
- **`tools/w8b-run.py` preflight now reads the platform listing** (`hermes tools list -p <profile>`) and fails
  when `file` is absent or `terminal`, `code_execution` or `delegation` is enabled. Proved both ways: it passes
  on the pinned profiles, and it rejects the root list, which enables `terminal`, `code_execution` and
  `delegation`.

These are profile-config and tool changes in lanes that own them (`~/.hermes/profiles/w8-*` and `tools/**` are
the hermes lane's).

## 3. The probe — 3 prompts, naive arm, pinned surface, free tier

`python3 tools/w8b-run.py --task tb --provider w8c --budget 60000 --arms naive --limit 3 --timeout 180
--run-id tb-shape-1` → **timeout at prompt 1**, verdict `NO RECORD`.

The transcript is the finding. The model confirmed the surface itself:

> `'terminal' is not available in this execution context. Don't retry it`

and then spent the entire 180 s looking for another execution route — `tool_search`, `tool_call` with
arbitrary names, the deferred-tool catalog — instead of counting rows. It read `data-01.csv` once and never
answered. The capture flushed on SIGTERM and agrees: **4 events**, one `page.declare`
(`tool:read_file…/fixture/data-01.csv`), `turns: 1`, `residentTokens 3020`, no fault.

So with execution removed, this free model does not hand-aggregate 150 rows; it hunts for a calculator until
the timeout.

## 4. What this settles, and what it does not

- **Settles (for this model):** the wired runs' 191/192 completeness is a *with-code* result. The T-B shape —
  "read N rows and report exact per-category aggregates" — is **not hand-answerable** by `longcat-2.5:free`
  within 180 s, and the earlier 0/48 is explained by the same thing: a model that cannot compute programmatically
  answers the categories it can carry and omits the rest, or looks for a shell.
- **Does not settle:** one model, one prompt, one 180 s cap. A stronger model, or a smaller row count, might
  answer; nothing here proves no model can.
- **Unchanged:** no paging, H3/H4, cost or determinism claim. The probe is a single-prompt `NO RECORD`, and it
  is recorded as one.

## 5. The decision this hands the owner

Two honest options, and no third:

1. **Close T-B as a shape.** Aggregation tasks need execution; paging experiments move to **extraction** shapes
   (T-A v2 style, which measured engagement in W8C), and the programme stops trying to make mental arithmetic
   the workload.
2. **One stronger model, same pinned surface, before closing.** Cheap on a free route, and it would separate
   "this model cannot" from "this shape cannot". The surface is now pinned, so the run would finally measure the
   model rather than the harness.

## 6. Verification

Gate: `bash tools/run-ci.sh` unpiped with `CTXVM_*` cleared → `ALL GATES GREEN`; `check-handoff.sh` ALL PASS;
`git-hygiene.sh` OK. Profile changes are config, not code; the driver and preflight changes are the hermes
lane's own. Nothing pushed.
