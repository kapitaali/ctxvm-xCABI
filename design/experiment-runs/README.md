# Experiment runs

Owner-cleared 2026-11-26. This subdirectory is the home for **future authorized experiment execution
plans and preregistrations**. It separates run mechanics from permanent design-of-record files at the
root of `design/`.

## Rules

- One file per run: `<RUN-ID>-<date>.md` or `<RUN-ID>-RUN.md`.
- Every run plan links the owner authorization and the frozen preregistration/design of record.
- Freeze inputs, commands, arms, metrics, denominators, stop rules, and claim ceiling before execution.
- Results belong in `reports/RR-<CARD>-<date>.md`, not here; link receipts from the run plan.
- Never place raw traces, credentials, unredacted session content, or private host paths in this directory.
- Active paging, model spend, gateway restarts, default-on changes, and releases each require their own
  explicit owner ruling.
- Historical run plans at the root of `design/` remain in place so existing links keep working.

Use `TEMPLATE.md` as the starting point. Past/closed experiments live in `../past-experiments/`.
