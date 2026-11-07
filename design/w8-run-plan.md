# W8 run plan — model, tasks, and the pilot before the grid

**Status:** plan of record, written 2026-11-06, to be frozen at T0 alongside the task texts and
checkers. It does not amend `design/w8-capture-design.md`; it fills the choices that design left to the
owner (model, task content, tool policy) and records the pilot that gates the grid.

**Scope change the owner made today:** one model, GPT-6 Luna. The multi-model variation discussed
earlier is dropped for this run; DeepSeek and GLM are not run. The frozen design's one-model,
one-factor property therefore holds unchanged — both arms run Luna, differing only in
`context.engine`.

## 1. Model and price row

`OpenAI: GPT-6 Luna` — model id `openai/gpt-6-luna` (confirmed against the provider list), catalogue row
`usdPer1mInput 0.10`, `usdPer1mOutput 0.50`, and `usdPer1mCachedRead 0.01` from the model list's third
column; source `benchmarks/metrics/catalogue-2026-11-06.csv` + `model-list-2026-11-06.txt`, accessed
2026-11-06, owner-supplied.

**Cache pricing changes what the numbers mean.** A cached read costs a tenth of an uncached one. The
naive arm keeps a stable prefix and can accumulate hits; the paged arm rewrites the prefix on every
selection, which forfeits them. A run can therefore cut tokens and still cost more dollars, and the
preregistered gate reads tokens. The ledger carries both columns and the analysis must present both —
token reduction is the gate, cost is the finding.

Why it and not its siblings, at the design's volumes (36 runs = 22.3 M input, 0.5 M output):

| Model | in / out | 36-run grid |
|---|---|---|
| GPT-6 Luna | $0.10 / $0.50 | **$2.48** |
| GPT-6.1 Terra | $1.00 / $5.00 | $24.80 — the cap, no reruns |
| GPT-6 / 6.1 Sol | $2.00 / $10.00 | $49.60 — over |

The cap decides this before capability does. If the owner wants Terra, the grid must shrink to 18 runs.

## 2. What the tasks must satisfy

From the frozen design plus the measured engine behaviour (`RR-ENGINEGAP-20261106`):

1. **Many small pages.** Each tool result at most ~1.5k tokens; 40–60 pages per task; 45–70k declared
   tokens cumulatively. A single 60k-character read pushes the protected floor above `vBudget` and the
   paged arm becomes inert.
2. **Early evidence needed late.** A page read at the start must be re-consulted after the middle, or
   no page is pinned, no fault occurs, and paging is untested.
3. **Mechanical checkers.** Exact JSON, exact ordered list, exact patch, or a test suite. Never a
   model judgement.
4. **Frozen tool set per task.** If a search tool can answer the task in one call, the pressure
   disappears. The tool list is part of the frozen fixture.
5. **A terse system prompt** (~300 tokens, dedicated profile), not the 14k-token default, so the floor
   stays well under the budget.
6. **Real repo content in a disposable workspace** under `/tmp`, per the redaction DQ law; no user
   state, no credential environment, no personal files.

## 3. The six templates

| # | Task | Artefact | Pressure | Check |
|---|---|---|---|---|
| 1 | Binary flag matrix: for each of the six `rust/crates/ctxvm-conformance/src/bin/*.rs`, list every CLI flag and the file defining it | `flags.json` | six sources, no single grep yields binary→flag | exact JSON |
| 2 | Corpus forensics digest: for each `corpus/m1`–`m8`, report sessions, distinct pages, faults by source, checksum status | `drops.json` | eight drops, one command output per drop | exact JSON |
| 3 | Spec-to-code compliance: a spec page states five behaviours; find the modules in `packages/*/src` (20 files) that violate each | `deltas.json` | the spec is read first and re-consulted per module | exact set equality |
| 4 | Release-note reconstruction: the last twelve `reports/LOG.md` rows, in order, with date and track | `release.md` | LOG plus the indexes it cites; ordering forces retention | exact ordered IDs + dates |
| 5 | Test triage in the second repo: three failures, three root causes | working tree | fail log → module → fix → rerun | `pytest -q` exit 0, tests unmodified |
| 6 | Invariant refactor in the second repo: apply a rename rule from a spec across ~12 modules | working tree | many small files; the spec must stay resident to judge each site | tests pass, no old token, tests unmodified |

Templates 1–4 run on this repository. Templates 5–6 need the owner-named second repository; the
subtrees are chosen when it is named.

**Rejected task shapes, and why:** any task answered by one `grep` (pressure collapses); any task whose
output needs prose judgement (uncheckable); any task whose fixture is synthetic rather than real repo
content (the design's "real work product" clause); any task that reads one huge file (floor above
budget, arm inert).

## 3b. Review findings (2026-11-07) — five amendments before the freeze

A second lane checked templates 1–4 with throwaway scripts (`RR-W8TPLCHK-20261107`). Five holes, all
of which change the freeze.

**1. The pressure bar is unreachable for three templates.** Measured minimum-read bounds: T1 ≈7k
tokens, T2 ≈19.4k, T4 ≈4.5k, against the 45–70k the design requires. A task that declares 7k cannot
test a 24k budget — both arms behave identically. New freeze rule: every template carries a
**minimum-read bound** computed from its fixture (the tokens of the files a correct solution must
read), and a template that cannot reach 45k is either enlarged or reclassified as a **floor control**:
a task that fits comfortably, where paging must be a no-op and accuracy identical. Floor controls are
reported, never counted toward the NTR gate.

- **T1**: extend from the six `bin/*.rs` to every binary plus the conformance library and the core
  crate's public surface (~25 files), so the minimum-read bound clears the bar.
- **T2**: digest every corpus trace (20+) individually instead of eight drop summaries, with per-drop
  checksum verification.
- **T4**: widen to 60 LOG rows with per-card RR header reads, or replace it with the report-versus-LOG
  audit (every `RR-*.md` has a row and vice versa).

**2. T3's checker can pass on an empty set.** The repository's spec page and the core enum agree
exactly on the nine verbs, so the measured violator set is empty and five empty arrays would satisfy
the checker without any reading. Freeze rule: the expected violator lists are authored, non-empty, and
computed by a stated mechanical rule, with per-file evidence rows. A checker whose expected set is
empty fails the freeze.

**3. Freeze paths, not globs.** `packages/*/src` is exactly 20 files under the strict glob and 53 or 33
under looser rules. Every template's fixture list is an explicit path list at T0.

**4. T2's "sessions" is not derivable from rows.** Only the meta sidecar carries `sessionID`; `m1` has
none, and `ctxvm stream` cannot help because these drops predate `environmentId`. The artefact records
`sessions: n` where a sidecar answers it and `sessions: null` where none does, naming the sidecar.

**5. A DQ trap, reproduced.** Quoting the last twelve LOG rows verbatim trips `tools/dq-secret-scan.py`:
one row quotes the scan's own pattern list, so `path.abs_home` fires and the drop would burn. Expected
artefacts carry ids, dates and tracks, never verbatim rows. Added to §8: **every frozen expected
artefact must pass the scan before the first paid call.**

Two details worth keeping from the same review: T1's USAGE text names `--features tiktoken`, which no
parser arm accepts, so a doc-derived answer is wrong on that binary and the exact vector is the check;
and error strings inside match arms (`--turn:`, `--event:`) need explicit scrub rules in the freeze.

## 4. Pressure arithmetic and expectation

```
per task:  45–70k declared tool-result tokens over 40–60 pages of ~1k
naive:     ~50–70k tokens per request by mid-task
paged:     ~24k per request, if the floor stays under vBudget
expected NTR: 2.0–2.8x  (gate: >= 1.5x)
```

## 4b. Pre-set environment (2026-11-06) — nothing left for the operator to configure

Two profiles and one env contract were created so a run needs no hand-edited setting.

| Path | What it holds |
|---|---|
| `~/.hermes/profiles/w8-naive/config.yaml` | a copy of the global config with `context.engine: compressor` |
| `~/.hermes/profiles/w8-paged/config.yaml` | the same copy with `context.engine: ctxvm` |
| both | `.env` and `plugins` are symlinks to the real ones, so credentials and the plugin are shared, not duplicated |

Verified: `hermes config get context.engine` returns `compressor` and `ctxvm` respectively under
`HERMES_HOME=...`, and `hermes plugins list` shows `ctxvm-tracer 0.10.2 enabled` in both. The two
config trees differ in exactly one key, which is the experiment's one-factor property made checkable.

`tools/w8-run-env.sh <naive|paged> <trace-dir> <trace-name>` is the only place a run's settings live.
It exports `HERMES_HOME`, `CTXVM_FEATURES`, `CTXVM_TRACE_DIR`, `CTXVM_TRACE_NAME`, the write-through
pair, `CTXVM_MODEL` (default `openai/gpt-6-luna`, to be confirmed at P0) and `CTXVM_BUDGET_TOKENS`;
it sets `CTXVM_VBUDGET=24000` for the paged arm only and leaves it UNSET for naive, because the
virtual budget is a paged-arm concept and exporting it for both would blur the factor. `CTXVM_PROVIDER`
is left alone on purpose: the plugin records `unknown` rather than guessing.

Defaults now fixed, so no decision blocks the start: `vBudget` 24,000 (the T0 lock may raise, never
lower), `R = 3`, budget tokens 200,000, and the second repository `~/Documents/umpire` (clean at
`d383255`).

The global `context.engine` was returned to `compressor`. The experiment never reads that value — it
reads the profile — and leaving it on `ctxvm` would have put everyday sessions into the measured no-op
regime with compaction disabled.

## 4c. Where a run's settings must land (2026-11-07)

`hermes -z` does not execute the turn in the client process. `hermes_cli/main.py:2844` states it:
every `hermes` / `-q` / `-z` / TUI turn runs in the **gateway**. Measured consequence: a probe
exporting `CTXVM_TRACE_DIR=/tmp/w8/probe` wrote nothing there and landed in the gateway's own
directory instead.

So the runner is two steps, not one:

1. source `tools/w8-run-env.sh <arm> <dir> <name>`, then start (or restart) **that profile's
   gateway** under it — the gateway is the process that captures;
2. send prompts with `hermes -z … -m "$W8_MODEL" --provider "$W8_PROVIDER"` to that gateway.

One gateway per arm, because the arms differ by profile (`context.engine`) and a shared gateway
writes both arms into one directory and one name — the seventeen `w8-run-<hex>` files were exactly
that: one name, many sessions, collision suffixes.

Provider: `nous` (both profiles). The earlier `nvidia` values were stale copies and routed
`openai/gpt-6-luna` to another vendor's free tier, which answered 429. `session.open.provider` stays
`unknown` until the gateway serving the run is started after the identity fix; the payload for that
hook carries no provider, so settings are the only source.

## 5. The pilot before the grid

One task (template 1), both arms, one round. On Luna this costs about $0.14. It answers what no design
document can:

- can the model solve the task at all (if both arms fail, non-inferiority is unmeasurable);
- does the paged arm actually select (watch `requestChars` fall toward the budget);
- does the checker fire on a real artefact;
- what the protected floor measures on a task-shaped session, which decides whether `vBudget` stays at
  the preregistered 24,000 or is raised at the T0 lock (raising is allowed; lowering is not).

If the pilot shows the floor above the budget, or a task the model cannot solve, the grid does not
start and the pilot is reported as the outcome.

## 6. Grid and budget

6 tasks × 3 rounds × 2 arms = 36 runs, alternating naive, paged per task. Estimated **$2.48** at the
pinned row, so R = 6 (~$5) or R = 9 (~$7.4) would still fit the $25 cap if the intervals need
tightening — a decision to take before run #1, never after.

The ledger (`reports/W8-SPEND.md`) opens in the capture commit and records, per run: date, arm, task,
round, model, provider receipts, USD from the pinned row, running total. Cache reads are unpriced in
the catalogue; pricing them at the input rate is an upper bound and must be named as such.

## 7. Freeze list at T0

- six task texts and their checkers;
- the per-task tool set and the terse system prompt;
- the model row (GPT-6 Luna) and `priceModelVersion 2`;
- `vBudget`, confirmed or raised (never lowered);
- R and the stopping rule as already frozen;
- the ledger's projected-cost assumption for the first run;
- each template's minimum-read bound and its family (pressure task or floor control);
- the explicit fixture path list per template.

## 8. Acceptance before run #1

1. Pilot green on template 1, both arms.
2. `tools/dq-secret-scan.py` exits 0 on the pilot's drop set.
3. The ledger exists with its first row.
4. The runner asserts safe-worker mode is off and that `context.engine` differs only between arms.
5. `ctxvm replay` is byte-identical on every captured trace.
6. The task texts and checkers are committed before the first paid call.
7. Every frozen expected artefact passes `tools/dq-secret-scan.py` with zero matches.
