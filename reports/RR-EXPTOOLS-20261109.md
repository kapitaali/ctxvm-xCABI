# RR-EXPTOOLS-20261109 — tool-surface experiment (Tier 0 only; Tier 1 not run)

**Date:** 2026-11-09. **Budget:** $0.0221 total incl. title-gen. Tier 1 not run per T0.4 (not row B).

## Pair recap (the question)

Prior pair on T-A: naive **5 calls, 73k input, $0.0039** via one `execute_code` (4 declares); paged **7 calls, 448k input, $0.0497** via 28 `read_file` (34 declares) — both checker-PASS but engineSelections 0 on the paged arm. The token ratio measured a *strategy* difference (compute-in-code vs read-everything), not a policy difference. Tier 0 asked whether `-t file` removes the choice.

## Tier 0 result — one pinned naive cell

- Workspace `experiments/w8/t-a/ws-naive-file/fixture/` (14 files, 223,634 bytes ≈ 55,908 tokens floor); task text `experiments/w8/t-a/task-text.txt` (current T-A shape, no `max_line`/`min_line`).
- Session `local-fe1e0932…`, `-p w8-naive -t file`, plugin `0.10.10`, gateway 0.10.8 (PID 112064, since 13:41:59).
- Refs (trace `page.declare`): **search 4, read_file 32, write_file 1**; 37 declares, 1 turn. No `execute_code`, no `terminal`.
- Calls **8** (≤60, ceiling 150), input **667,178** (cache-read 556,058, cache-write 111,096), output 5,127, total incl. auxiliary **$0.0221**. Resident **62,707**, perApiRequest peak **61,939** approx tokens (limit 24,000): pressured as designed.
- Checker: **FAIL (byte-exact) / PASS (values)**. Model wrote every field correctly but per-file objects inline; canonical form expands them. See `design/exp-surface.md` for the decision and why it is row A\*.

## What Tier 0 proves and does not prove

- Proves the surface can be pinned (`-t file` = 4 tools, no `execute_code`) and that with it the model takes the honest read path (32 reads, 62k resident, 8 calls) rather than a single code call.
- Does not prove anything about paging or tokens. This is a scaffold result: the next paid cell (pair, both `-t file`, treatment engineSelections > 0 corroboration) is the measurement.

## Conflicts

None besides the standing experiment-lane ownership: reports/design are new files here; commit is left to the hermes lane per LANES.md.
