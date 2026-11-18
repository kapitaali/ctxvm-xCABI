# RR-TBCLOSE-20261118 — T-B is closed as a shape (owner decision)

Owner decision, verbatim: **"close it"** — option 1 of `reports/RR-TBSHAPE-20261118.md` §5. The closure is
`design/TB-CLOSURE-20261118.md`; `design/TB-PLAN.md` is marked withdrawn as a runnable plan. No model call was
made by this card.

## 1. Why closing is the honest end, not a retreat

The shape was designed to answer "does a model read N rows and report exact aggregates", with the aggregate
answer chosen so `search_files` could not shortcut it. The measurements taken over three days say the answer is
**no, not without code**:

| measurement | what it shows |
|---|---|
| unwired full run, 0/48 | both execution routes refused; the model aggregated what it could carry and omitted the rest |
| wired full run, 191/192 with **196 `shell` declares** | completeness arrived with a shell — a with-code result |
| shape probe, surface pinned, 180 s | the model confirmed no `terminal`, then hunted for another execution route until the timeout |

A task whose answer requires programmatic computation is the wrong workload for a context-paging experiment:
a model that shells out computes outside the window, so dropping pages cannot hurt it, and paging becomes
untestable in exactly the regime the experiment needs.

## 2. What stays true, and stays cited with its verdicts

- The four runs' verdicts are unchanged and are **not** promoted: CEILING 582 vs 579 (breach), COMPLETE at
  exactly 584 (margin 0), NO RECORD / CEILING / INCOMPLETE for the earlier three.
- Three harnesses' **capture fidelity** stands, independently verified: unwired OpenCode, wired OpenCode, dsh.
- The **surface root cause** stands and is fixed: a CLI turn binds the platform toolset list, not `toolsets`;
  `-p <profile>` routes it, `HERMES_HOME` does not.
- The **instruments** survive the shape: `gen-tb-fixture.py`, `tb-check.py` (`--prove`, `--per-reply` with
  three named denominators, `--lookups`), and the task-aware runner.

## 3. What moves instead

The paging question moves to a workload that needs no execution: **extraction shapes** (which measured
engagement in W8C and produced the 2.11× dollar negative) and the **cache-stable line** (H11 → H12), the only
proposed cell that could turn that negative positive. And, for the first time since 16 Nov, the **Hermes paged
arm can be run at all**: the surface defect that invalidated those cells is fixed.

## 4. Reopen conditions

All three, per the closure's §5: a workload whose per-prompt answer needs no programmatic computation, a model
demonstrated on three pinned-surface prompts, and an owner authorization naming the run and its ceiling.

## 5. Verification

Gate `ALL GATES GREEN`; `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK. Two design files and this card, one
LOG row, one day section. Nothing pushed.
