# RR-W8PREFLIGHT-20261107 — chunk 1 stops at pre-flight: the runner never selects the arm's profile

Card: W8 run executor, chunk 1 (`design/W8-RUNBOOK.md` STEP 1). Cells run: **0 of 48**.
API spend: **$0.0000** (no paid call was made). Outcome: **STOP before the first cell**, two
findings, one of them blocking.

## 1. The pre-flight, as run

`python3 tools/w8-run.py --plan` (exit 0, no API call, no ledger row):

```
assert price row: GPT-6 Luna in=0.1 out=0.5 cached=0.01  OK
assert profiles: one differing line = context.engine compressor|ctxvm  OK
assert safe worker: off in both profiles  OK
pending: round 1 t1 naive   ...   pending: round 6 t4 paged
48 of 48 cells pending; 0 already in the ledger
```

The six drift checks from the runbook:

| # | check | expected | measured | verdict |
|---|---|---|---|---|
| 1 | `git log --oneline -1` | record it | `d797002` | recorded |
| 2 | `git status --short` | clean | 4 modified + 3 untracked, all under `research/` | **FAIL** (finding 2) |
| 3 | `model.provider` under both profiles | `nous` | `nous`, `nous` | OK |
| 4 | `model.default` under both profiles | `openai/gpt-6-luna` | `openai/gpt-6-luna`, `openai/gpt-6-luna` | OK |
| 5 | `grep -m1 PLUGIN_VERSION ~/.hermes/plugins/ctxvm-tracer/__init__.py` | `0.10.3` | `0.10.3` | OK |
| 6 | `tail -3 reports/W8-SPEND.md` | running total vs the cap | carried forward `$0.5161`, 0 rows, so running total `$0.5161` of `$25` | OK |

Cap arithmetic (`design/w8-capture-design.md` §8 binding pre-run rule): projection
`48 × 0.3207 = 15.3936` USD; the stop condition `0.5161 + 2 × 0.3207 = 1.1575 < 25` — the
budget stop does not fire.

## 2. Finding 1 (blocking) — the arm's profile does not reach the run

The runner builds the client command with no profile selection
(`tools/w8-run.py:146-148`):

```
hermes -z <prompt> -m openai/gpt-6-luna --provider nous --in <ws> --usage-file <usage> -t file
```

No `-p`, and no per-cell `HERMES_HOME`. Profile resolution is client-side and comes from exactly
those two things (`hermes_cli/main.py:430`: `--profile`/`-p` is pre-parsed and sets `HERMES_HOME`
before imports). Measured on this machine:

```
hermes config get context.engine          -> compressor      (default profile)
hermes -p w8-naive  config get context.engine -> compressor
hermes -p w8-paged  config get context.engine -> ctxvm
```

The shell that launches the runner — and the runner's children — carry
`HERMES_HOME=/home/theb/.hermes`, and `~/.hermes/config.yaml:2125` reads `engine: compressor`.
`hermes gateway list` shows one multiplexer (`PID 160145`) serving `default`, `w8-naive` and
`w8-paged`; its process environment carries `CTXVM_TRACE_DIR=/tmp/w8/traces`,
`CTXVM_TRACE_NAME=w8`, and **no** `CTXVM_VBUDGET`. The gateway log shows the multiplexer does
serve profile-scoped sessions (`gateway.run: ✓ local disconnected (0.00s) (profile: w8-paged)`),
so the mechanism exists; the runner simply never asks for it.

The runner's other arm-specific line does not cover this: `tools/w8-run.py:429` sets
`os.environ["W8_VBUDGET"]` in the *runner* process, and a `-z` turn executes in the gateway
(`hermes_cli/main.py:2844`, measured in `RR-PROVIDER-20261107`). A client-side variable reaches
neither the engine nor the gateway. The same applies to sourcing `tools/w8-run-env.sh` in the
shell that starts the runner.

**Consequence.** Both arms would run under `default` (`compressor`). The paged cell would be a
second naive run: no selection, no faults from selection, and a net-token ratio of about 1.0 that
would read as an arm result instead of as a missing factor. The spend would be real — roughly
half of every chunk — and the data would not be the experiment.

**Consequence for the record.** The capture cannot be re-attributed afterwards. The meta sidecar
of the pilot's captures carries these keys only: `budgetTokens, capturedAt, harness,
harnessVersion, hookStats, model, pluginVersion, provider, resumeFrom, sessionID, traceStats` —
no engine or arm field. `engine=ctxvm registered` is not evidence either
(`RR-W8FREEZE`: `build_engine()` is unconditional; the host activates the engine only from the
profile's `context.engine`).

**What this corrects in the record.** `RR-W8FREEZE` states "the profile config IS per run
(compressor vs ctxvm verified), so the one-factor setting survives". That is true of the two
config files and of `hermes -p … config get`; it is not true of the runner's invocation, which is
what a cell actually executes. The pilot's −1.7 % `requestChars` difference is consistent with two
runs of one engine and was already reported as noise; nothing here upgrades or downgrades it.

**Scope.** This is established from source and settings at zero spend. It is not confirmed by a
paid observation; the disambiguating observation would be one cell per arm, and that spend is not
authorised before the owner ratifies a remedy.

## 3. Finding 2 — the tree is not clean

```
 M research/white-paper.pdf
 M research/white-paper/README.md
 M research/white-paper/index.md
 M research/white-paper/white-paper.md
?? research/ctxvm-ai-safety-research-note.md
?? research/papers/
?? research/white-paper-Part-II.md
```

These are another lane's work in progress: mtimes are 2026-11-06 21:27–23:24, none touched by
this session, and `RR-WP2REV` and `RR-STUBPRO` both name the white-paper draft as that lane's
untracked work. None of the four templates' explicit fixture path lists (`benchmarks/w8/templates/
t*/fixture.json`) includes anything under `research/`, so a task workspace cannot pick them up.

The runbook says a dirty tree stops the pre-flight and the executor does not decide that on its
own. Recorded, not worked around: nothing under `research/` was staged, edited or deleted.

## 4. Other state recorded, no action taken

- HEAD `d797002`; the runbook still cites the runner at `42ce6dd`, three commits back — a stale
  citation in the book, not a change to the instrument.
- The shared capture pool `/tmp/w8/traces` holds earlier sessions' artefacts: `w8.jsonl` (16:53),
  `w8.partial.jsonl` + `w8.partial.meta.json` (17:05), `w8-facd94d7.meta.json` (14:46). Per-cell
  check (f) forbids stray partials from a run; these predate this chunk. Named, not removed.
- No `CTXVM_*` var was exported for a run, no gateway was restarted, no ledger row was written.

## 5. Decision requested (owner)

1. **The blocking finding.** Either (a) ratify a runner change so each cell names its arm's
   profile — the minimal candidate is passing `-p w8-<arm>` in the client command at
   `tools/w8-run.py:146`, which the multiplexer already serves — together with an assertion that
   fails the pre-flight when the two arms resolve the same engine; or (b) halt W8 here as BLOCKED
   and record it as the outcome. The executor does not patch the instrument unratified.
2. **The dirty tree.** Either the `research/` work is committed by its owner before chunk 1, or
   the owner records a waiver for this chunk naming those seven paths.

## 6. What this report does not claim

Nothing about paging. No cell ran; no trace was produced; the grid stands at 0 of 48 with
`$0.5161` of the `$25` cap spent and no new spend from this card.
