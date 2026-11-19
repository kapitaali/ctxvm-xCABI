# RR-H12DIAG-REVIEW — verified: the mode now engages; the H12 control arm is running

Review lane, verify-then-record. Date 2026-11-19. The gateway was restarted by the owner at 11:13 local; a one-prompt
diagnostic then ran. A second pair (`h12c2`) is **in progress** as I write — I did not touch it or its artefacts.

## 1. What the diagnostic established

The sidecar `~/.local/state/ctxvm/traces/local-7e52ceed…coverage.json` (paged arm, budget 24,000, capture
`local-7e52ceed….jsonl`, 4 events) carries:

| field | value | meaning |
|---|---|---|
| `policyMode` | **`stable`** | the policy dict now has the key — the shadowing defect is gone |
| `policyModeSource` | `settings` | it came from the profile setting, not a forced env var |
| `modeExplicit` | `false` | consistent with a settings-sourced value |
| `selectionMode` | `stable` | the engine adopted it |
| `trigger` | `new-page` | on the first turn a new page is a plan trigger, not a hold |
| `harnessVersion` | `null` | not populated on this build — worth flagging, not a blocker for identity |

This is the answer the previous card asked for. The `new-page` trigger on a **one-prompt** diagnostic is expected:
the held set is empty on the first call, so the first plan is a plan. A `held` trigger requires a second call with an
unchanged working set — which the one-prompt identity check does not provide. I do not treat `trigger: held` as
established from this capture; it was established earlier by `StableSelectionTests` law 2 at 0.13.25
(`RR-H11-REVIEW`), and the loader change does not touch that law.

**The diagnostic verdict is VOID, correctly:** `verify.txt` reports two FAILs — turn spread ≥10 (1 distinct turn)
and evictions > 0 (0 tokens) — with every other check OK, including single session, budget from settings, engine
entered and engaged, no code/shell tools, no sealed part read after seal, and coverage_check/replay exit 0. That is
the right label for an identity probe: it is not a cell, and the gate refused to promote it.

## 2. The in-progress cell — observed, not reviewed

Processes started 11:39: `python3 tools/w8b-run.py --task ta2 --provider w8c --budget 24000 --arms naive … --run-id
h12c2` and the driver on arm `naive`. The run dir has command/stdout/stderr files up to prompt 07; no `summary.json`
yet. This is the control half of the H12 pair under the existing authorization and **$1 cap**. I have not read its
reply content or interfered; it is not evidence until it finishes and its RR lands.

## 3. What follows and what is not yet claimed

- The mode fault is closed by capture, not by inference: `policyMode: stable` is in the sidecar after the restart and
  the by-path loader fix.
- No H12 stable result exists yet. When `h12c2` finishes, review must check both arms, the four acceptance
  conditions from `design/w8-cache-stable-selection.md` §4, the $1 cap, and the diagnostic trio in the plan blocks —
  then record CELL / NO-OP / negative with its margin.
- The `harnessVersion: null` field is a metadata gap on this build; a later capture should populate it if the
  plugin recipe requires it (the m5 erratum is the precedent). It does not change the identity verdict.
- No cost-saving, paging, determinism, or model-quality claim follows from this card. No restart, spend, or cell
  action is authorized by it.

Kit/gate: `check-handoff.sh` ALL PASS and `git-hygiene.sh` OK at the last check; this card changes no gate input.
