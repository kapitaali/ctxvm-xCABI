# RR-TBRUNNER-20261116 — T-B phase 0(b): the runner carries a second task shape, and the dry run is green

Phase 0's last item. Free: no model call, no cell, no spend — the first T-B model call stays owner-gated.

## 1. What changed

**`tools/w8-driver.py`** — two additive flags, no change to the T-A v2 path's behaviour:

- `--prompts-file <json>`: a list of prompts for a task shape other than T-A v2. It rebinds the module's
  `PROMPTS`, sets a `PROMPTS_FROM_FILE` flag, and switches `validate_prompts()` to the generic checks
  (≥10 prompts; the last must require `artefact.json`) instead of the T-A v2 ones (`part-0N.txt`,
  `SEALED`).
- `--sealed-parts <list|none>`: sealing is now gated on the set being non-empty, so a shape with no
  sealed parts skips the seal step and its manifest reports `middle_prompts: null`,
  `seal_after_prompt: null` rather than claiming a middle run it never had.

**`tools/w8b-run.py`** — `--task {ta2,tb}` and a `TASKS` table: fixture glob, part count, checker, budget.
The T-B prompts are **built from the fixture** (`build_tb_prompts`), because the revisit lookups have to
name real rows: 48 per-file prompts plus one reconciliation that asks for the artefact **and** three
exact rows from `data-02.csv`, `data-07.csv` and `data-11.csv`. The answer key is written beside the
prompts as `lookups.json`, so the replies can be scored later without re-deriving which row was asked for.

The probe became task-aware too (`PROBE_PROMPTS`): a T-B probe reads `fixture/data-01.csv`, not a
`part-01.txt` that its workspace does not contain.

## 2. A defect the first dry run found

The first T-B dry run reported `48 prompts each` while the workspace held **68 files** — the T-A v2 parts
and the T-B CSVs were sharing `experiments/w8b/ws-{arm}/fixture`. Beyond the count, a T-B run could read
the other task's fixture. Fixed with `workspace_for(task, arm)`: `ws-{arm}` for `ta2` (paths unchanged)
and `ws-tb-{arm}` for `tb`. The contamination was removed from the ta2 workspaces (48 CSVs deleted from
`ws-naive` and `ws-paged`, leaving their 20 parts intact).

## 3. Verification — dry runs only, no model call

| Check | Result |
|---|---|
| `w8b-run.py --task ta2 --provider w8c --budget 60000 --dry-run` | exit 0, **20 prompts**, `ws-{arm}`, unchanged |
| `w8b-run.py --task tb --provider w8c --budget 60000 --dry-run` | exit 0, **48 prompts**, `ws-tb-{arm}`, preflight counts 48 `data-*.csv` |
| driver `--prompts-file … --sealed-parts none --dry-run` | exit 0, `prompts=49 middle=- seal_after=-`, 49 commands printed |
| `lookups.json` | three entries with real ids (`5069`/data-02, `9340`/data-07, `9411`/data-11) |
| budget mismatch is still caught | `ta2 --budget 70000` against the 60000 profile → `PREFLIGHT FAILED`, nothing ran |

The last row is the preflight working: a budget that disagrees with the profile stops the run before
prompt 1, which is what makes the dry run worth running.

## 4. What is still owed before phase 1

- **Lookup scoring** — `tb-check.py` scores the artefact and the per-file replies; the three lookup
  answers arrive in the model's P49 reply text and need a third mode (`--lookups lookups.json <reply>`).
  Small, and needed before phase 3 can report P17.
- **Per-reply capture** — the driver writes `stdout-NN.txt` per prompt, so the replies exist; turning them
  into `tb-check --per-reply` input is a runner-side loop, not yet written.
- **Phase 1 is owner-gated.** Nothing here calls a model.
