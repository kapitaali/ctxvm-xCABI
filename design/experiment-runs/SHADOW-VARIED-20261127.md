# SHADOW-VARIED-20261127 — varied control-shadow collection plan

Status: **PROPOSED — owner authorization required before any model call.**
Date: 2026-11-27
Owner ruling: pending
Preregistration / design of record: `reports/RR-SHADOW-JOIN-20261126.md`
Current result: `reports/RR-SHADOW-JOIN-RESULT2-20261127.md`

## 1. Hypothesis and scope

Characterize how the fresh control keep law behaves across three workload shapes, using only offline
shadow records. The current n=3 corpus used one forced-pressure shape and produced three dropped pages,
no later observed reuse, and no candidate pins. This batch tests whether those descriptive patterns
persist across different page-count and page-size distributions.

It does not test causal importance, safety, cost saving, paging quality, model quality, determinism,
availability, or redaction. Candidate pins remain offline-only.

## 2. Frozen inputs

- Plugin: Hermes **0.13.37**, profile `w8-shadow`, `engine=compressor`, `budgetTokens=24000`,
  `shadowSelection=true`, fresh mode.
- Model/provider: `tencent/hy4-flash:free` / `nous` (currently working; if unavailable, stop and report).
- Host: Linux x86_64.
- Session path: anonymous one-shot `hermes -z`; no named `--create-if-missing`.
- Sample target: **6 additional sessions** — two per workload shape. Current n=3 becomes n=9 if all pass.
- Hosted output is non-deterministic; no seed or confidence interval is claimed for this small batch.

## 3. Workloads

| Shape | Workspace | Prompt behavior | Purpose |
|---|---|---|---|
| A — many small pages | 12 files, 2–4 KB each | read all files sequentially, then 3 tiny tail files | high page count, small per-page cost |
| B — medium middle pages | 3 files, ~70–90 KB each, then 3 tiny tail files | sequential reads + marker recall | replicate pressure with different page sizes |
| C — mixed sizes | 2 small, 3 medium (~40–60 KB), 3 tiny tail files | sequential reads + marker recall | heterogeneous page distribution |

Each shape uses unique marker lines so later identifier scans can be detected without page bodies entering
the aggregate output.

## 4. Arms and procedure

This is observational shadow collection, not a control/treatment model experiment. Every session runs the
same `w8-shadow` control profile; the live request is unchanged.

For each shape, run two fresh anonymous sessions. Record rc, model, session id, wall time, shadow record
count, persisted drop count, and failures. A session is valid for the join only if all existing gates pass;
a session with no persisted drop is reported but does not satisfy the shape's drop requirement.

## 5. Metrics and denominators

Use `research/shadow-analysis/join.py` unchanged. Report:

- valid sessions and exclusions;
- selections, dropped records/pages, page opportunities;
- later tool_recall and identifier_scan opportunities separately;
- never_observed and ambiguous same-turn counts;
- pressure, floor pressure, drop share, and selection churn with denominators;
- candidate pins only under the existing ≥2-session/≥3-unique-tool_recall rule.

Do not pool the three shapes into a single interpretation without showing per-shape counts. No causal or
safety label is attached to `never_observed`.

## 6. Stop and failure rules

- Any auth/model 404 or provider failure: stop that session, record it, do not silently switch models.
- Any non-zero per-session shadow write failure: exclude the session and report.
- If a shape yields no persisted drop after two attempts, mark it uninformative; do not broaden the prompt
  post hoc to force a drop.
- If fewer than three valid sessions remain overall, join returns `INSUFFICIENT_DATA` and no rates/pins.
- Raw traces and shadow records remain private; only aggregate hashed outputs are committed.

## 7. Claim ceiling

No cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim. `position_band`
and `later_dependency_use` remain UNVERIFIED. Candidate pins are offline nominations only; applying them to a
live profile requires a separate owner ruling and preregistration.

## 8. Receipts and result link

- Private workspaces: `/tmp/opencode/shadow-varied/<shape>/`
- Private traces: `~/.local/state/ctxvm/traces/`
- Aggregate output: `research/shadow-analysis/out/result.json`
- Result card: `reports/RR-SHADOW-VARIED-RESULT-<date>.md`
- Gate/repro: `python3 research/shadow-analysis/test_join.py -v`, shadow schema validator, join, full CI.

## 9. Owner decision needed

Authorize the six free-model calls and the three frozen workspace shapes, or amend the sample/workloads.
No gateway/profile/config edit, restart, publish, or push is included.
