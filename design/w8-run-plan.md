# W8 run plan — model, tasks, and the pilot before the grid

**Status:** plan of record, written 2026-11-06, to be frozen at T0 alongside the task texts and
checkers. It does not amend `design/w8-capture-design.md`; it fills the choices that design left to the
owner (model, task content, tool policy) and records the pilot that gates the grid.

**Scope change the owner made today:** one model, GPT-6 Luna. The multi-model variation discussed
earlier is dropped for this run; DeepSeek and GLM are not run. The frozen design's one-model,
one-factor property therefore holds unchanged — both arms run Luna, differing only in
`context.engine`.

## 1. Model and price row

`OpenAI: GPT-6 Luna` — catalogue row, `usdPer1mInput 0.10`, `usdPer1mOutput 0.50`, basis `in-out`,
source `benchmarks/metrics/catalogue-2026-11-06.csv`, accessed 2026-11-06, owner-supplied (not
web-verified by this repository).

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
- the ledger's projected-cost assumption for the first run.

## 8. Acceptance before run #1

1. Pilot green on template 1, both arms.
2. `tools/dq-secret-scan.py` exits 0 on the pilot's drop set.
3. The ledger exists with its first row.
4. The runner asserts safe-worker mode is off and that `context.engine` differs only between arms.
5. `ctxvm replay` is byte-identical on every captured trace.
6. The task texts and checkers are committed before the first paid call.
