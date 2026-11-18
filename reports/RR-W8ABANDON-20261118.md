# RR-W8ABANDON-20261118 — the stale W8 working-tree state is abandoned, with a reversible copy

Owner instruction, 2026-11-18: abandon the stale W8 paths. They had been dirty in the hermes lane's tree
since 2026-11-09/10, and a dirty tree fails every clean-tree pre-flight — including other lanes' run books,
which is the cost `handoff/LANES.md` rule 3 exists to prevent.

## 1. What was abandoned, and where the copy is

Restored to HEAD (three tracked) and removed (two untracked), after a snapshot to
`~/.local/state/ctxvm/abandoned/w8-stale-20261118/`:

| path | state | what it contained |
|---|---|---|
| `tools/w8-run-env.sh` | tracked, restored | **profile-prefix awareness** (`w8b-naive`/`w8b-paged`) plus free-model defaults — a real improvement, and the skill file still describes that requirement |
| `reports/RR-W8B-20261110.md` | tracked, restored | an **honesty correction**: the naive arm's `artefact.json` is no longer present and its checker PASS was recorded at run time, not re-verifiable |
| `design/W8-EXECUTOR-PROMPT.md` | tracked, restored | a small edit adding the `AGENTS.md` law 10 reference |
| `design/W8C-BLOCK-CELL03-DRAFT.md` | untracked, removed | cell-03 payment-block draft, superseded by the committed `reports/W8C-BLOCK-CELL03-20261112.md` |
| `design/W8C-BLOCK-CELL03-NOTE.md` | untracked, removed | the draft's companion note |

The snapshot holds `tracked-changes.patch` (`git apply` restores all three tracked edits), the two drafts
verbatim, and a README that names each file and what it carried. Nothing is lost; the tree is clean of this
lane's leftovers.

## 2. Two consequences stated rather than buried

1. **`tools/w8-run-env.sh` loses the profile-prefix support.** The script as committed accepts only
   `naive`/`paged`. Any future multi-card W8 run needs that change re-landed as its own card — it was a
   defect fix, not experiment noise.
2. **`reports/RR-W8B-20261110.md` reverts to a claim that is no longer true**: the original text asserts the
   naive-arm artefact exists and was checked, while the file is gone and only the trace attests the write.
   The corrected wording is in the patch. If the report is read before that is re-applied, a reader may
   believe an artefact is available for re-verification. **This is the one I would re-land first**, as a
   docs-only correction, because it is a truthfulness defect and the repo's culture treats those as bugs.

Both are one `git apply` away, and neither was committed, so no history was rewritten.

## 3. Verification

`git status --short` now lists only other lanes' work in flight (`research/**` Part III landing,
`reports/RR-DATAMININGFIX-20261117.md`, `design/DSH-LANE-DEVELOPER-PROMPT.md`) — none of it this lane's,
none of it staged.

Gate: `bash tools/run-ci.sh` unpiped with `CTXVM_*` cleared → `ts suites green (24 + 62 + 46 + 14 tests);
python suites green (207 + 8 + 66 tests)`; **ALL GATES GREEN**. `check-handoff.sh` ALL PASS.

## 4. Not done

No commit of the abandoned material; no attempt to reconstruct what the W8B run would have needed; no claim
about the missing artefact. The W8 line stays closed as a negative result; this card only clears its leftovers.
