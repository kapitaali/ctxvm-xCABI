# T-B CLOSED — the shape is withdrawn (owner decision, 2026-11-18)

Owner decision, verbatim: **"close it"** — option 1 of `reports/RR-TBSHAPE-20261118.md` §5. The T-B task shape
("read N rows of a CSV, report exact per-category aggregates") is **closed as a shape**. No further T-B run of
any kind is authorized: not on Hermes, not on OpenCode, not wired or unwired, not on any model.

The plan of record `design/past-experiments/TB-PLAN.md` (rev 2) is hereby **withdrawn as a runnable plan** and kept only as the
record of what was designed and why it failed. Its fixture, checker and prompt machinery remain usable by a
future shape; its claim about "the second task shape" does not.

## 1. What the books support

1. **The shape is not hand-answerable by a free model.** With the CLI surface pinned (no `terminal`, no
   `code_execution`, no `delegation`) `meituan/longcat-2.5:free` read one file, confirmed
   *"'terminal' is not available in this execution context"*, and spent the whole 180 s looking for another
   execution route instead of counting rows — timeout at prompt 1, `NO RECORD`
   (`RR-TBSHAPE-20261118`, trace `local-d70bcd6f…`: 4 events, one read of `data-01.csv`, never answered).
2. **Without a pinned surface the shape looks answerable only because the model computes with code.** The
   wired OpenCode run's **191/192 file-exact, 1528/1536 tuples, 100 % precision** came with **196 `shell`
   declares**: completeness was a with-code result (`RR-TBWIREDFULL-20261118`, verified in
   `RR-TBWIREDFULL-REVIEW`). The unwired run's 0/48 is the same fact from the other side — both execution
   paths refused, so the model aggregated what it could by hand and omitted the rest.
3. **The earlier "shape" results are reclassified, not revised.** The unwired full run stays **CEILING at 582
   against a frozen 579** with its breach attached; the wired run stays **COMPLETE at exactly 584** with zero
   margin; the three earlier wired attempts stay NO RECORD (P22), CEILING (P67) and INCOMPLETE (P95). None of
   them is a paging result and none is now promoted.

## 2. What is not claimed

- **Not** that no model can do it. One model, one prompt, one 180 s cap. A frontier model with a long output
  window might hand-aggregate 150 rows; nothing here tests that, and the closure does not assert it.
- **Not** that aggregation tasks are worthless. It asserts they need *execution*, which makes them the wrong
  workload for a context-paging experiment: a model that shells out computes outside the window, so dropping
  pages cannot hurt it and paging is untestable in that regime.
- No cost, determinism, paging, H3/H4 or `enginePlan` claim of any kind.

## 3. What the T-B line did contribute, and stays

- **Three harnesses' capture fidelity, independently verified:** unwired and wired OpenCode, and the dsh lane's
  run. Valid, replay-clean xCABI traces with real identity, populated `.meta.json`, complete flush chains and
  every fixture ref covered.
- **The surface root cause** (`RR-TBSHAPE-20261118` §1): a CLI turn binds the **platform** toolset list, not the
  `toolsets` key; `HERMES_HOME` does not route the turn, `-p <profile>` does. Every "shell reached the model"
  verdict from 16–17 Nov has that cause, and the preflight, the driver and both experiment profiles now enforce
  the right key.
- **Instruments that outlive the shape:** `tools/gen-tb-fixture.py` (deterministic, `--check`-proven,
  residency-measured), `tools/tb-check.py` (`--prove`, `--per-reply` with three named denominators,
  `--lookups`), and the task-aware runner (`--task`, per-task workspace, `--limit`).

## 4. What replaces it

The paging question does not close with the shape. It moves to a workload that does **not** need execution:

1. **Extraction shapes** (T-A v2 style), where the model reports values a tool already returned. That shape
   measured engagement in W8C — the paged arm held the request at the budget and cost **2.11× dollars** because
   mid-prefix dropping forfeits the provider cache (`RR-PAIDRESULT-20261112`).
2. **The cache-stable line** (`design/past-experiments/w8-cache-stable-selection.md`, H11 → H12), which is the only proposed cell
   that could turn that measured negative positive: a stable prefix should raise `cache_read` and drop the
   dollar ratio below 2.11×. H11 is unimplemented; H12 is one pair behind the owner's $1 cap.
3. **The Hermes paged arm can now be run at all** — the surface defect that invalidated every Hermes cell from
   16–17 Nov is fixed, so a future paged cell measures the policy rather than the harness.

## 5. Reopen conditions — all three required

1. A **workload** whose per-prompt answer does not require programmatic computation (an extraction shape, or a
   row count a model demonstrably handles without code — demonstrated, not assumed).
2. A **model** whose hand-answer is shown on three prompts with the surface pinned — the probe that closed this
   shape, run again and passing.
3. An **owner authorization** naming the run, its ceiling derived from a measured rate, and its claim boundary.

Until all three exist, T-B stays closed, and any document that cites its completeness figures must cite them as
with-code or CEILING results with their verdicts attached.

## 6. Record

This closure; `design/past-experiments/TB-PLAN.md` marked withdrawn; one LOG row; one day-file section; the gate and kit green.
Nothing pushed. No model call was made by writing it.
