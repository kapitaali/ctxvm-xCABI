# ROADMAP — hermes / plugin lane

State of record: 2026-11-09, HEAD `9be5150`. This is the lane's own task list, not the project board.
Tick a box only when the command under **done when** printed what the box says. An unticked box with
a cost is a decision not to spend, not an oversight.

Lane boundaries: this lane owns `packages/hermes/**`, the installed copy, the w8 profiles, and the
plug-in side of `design/`. It does not own `research/**`, `spec/**`, `corpus/**`, `handoff/QUESTIONS.md`,
`08-HANDOFF.md`, or the white paper.

---

## 0. Truth first — the record is behind the code (all free, do these today)

- [x] **H1. (done 2026-11-10, `ab486a6`) Rotate `handoff/PROJECT-STATE.md`.** It says plugin **0.10.6** and "W8 closed FAILED";
  the tree is at **0.10.11** and W8 resumed with 0 cells counted and a session-shape blocker.
  *Why:* every lane reads this file first; a stale version sends the next agent to the wrong code.
  *Fix text:* `Plugins: hermes 0.10.11`; W8 line → `0 cells counted (5 void/no-op), blocker = one-turn
  sessions, next = multi-turn driver`.
  *Done when:* `grep -n "0.10.11" handoff/PROJECT-STATE.md` returns the line and
  `grep -c "0.10.6" handoff/PROJECT-STATE.md` returns 0.
  *Owner:* the lane that next commits PROJECT-STATE (shared file, claim by commit).

- [x] **H2. (done 2026-11-10, `d916212`) Day-file section for today's four cards.** `reports/RR-DAY-20261109.md` has no section
  for `0.10.11` (budget provenance), `RR-DRIFT` (derived counts + version guard), `RR-NOOP`
  (granularity), or the two master prompts.
  *Done when:* the file contains four headings naming those cards and `bash tools/check-handoff.sh`
  still passes.

- [x] **H3. (done 2026-11-10, `d48012e`) Reconcile this lane's uncommitted rows.** Working tree carries other lanes' edits
  (`08-HANDOFF.md`, `handoff/QUESTIONS*.md`, `P4-ts-umpire.md`, `RR-DAY`, `RR-P4TS`) and this lane's
  `reports/RR-W8CELL-20261109.md`, `reports/W8-CHUNKLOG.md`, `reports/W8-SPEND.md`.
  *Done when:* `git status --short` lists only the other lanes' files, and this lane's three are in a
  commit of their own.

- [x] **H4. Confirm the installed copy is the tree's copy.** Verified 2026-11-09: `ok` on all four `cmp` runs (0.10.11). Four files, not three:
  `live/__init__.py`, `live/context_engine.py`, `src/plugin.py` → `plugin.py`, `live/plugin.yaml`.
  *Done when:* sha256 of each repo file equals its installed counterpart:
  `for f in __init__.py context_engine.py plugin.yaml; do cmp -s packages/hermes/live/$f ~/.hermes/plugins/ctxvm-tracer/$f && echo "ok $f"; done; cmp -s packages/hermes/src/plugin.py ~/.hermes/plugins/ctxvm-tracer/plugin.py && echo "ok plugin.py"`

---

## 1. Unblock the experiment (the only path to a countable cell)

- [x] **H5. (done 2026-11-10; code moved to `tools/w8-driver.py`) Write the multi-turn driver.** `experiments/w8/driver/` (gitignored) + a design note in
  `design/`. Requirements, in order: reads in turns 1–3; ≥6 middle turns of other work; a final
  question that needs the early material; deterministic prompts; one named session
  (`--continue <name>`, never unnamed); every prompt through `-p <arm> -t file`.
  *Done when:* a **$0 dry run** (no model call — a stub `-m` or a harness that only records session
  ids) produces a session whose capture would satisfy `len({declare.turn}) >= 10`, and the design note
  states the prompt sequence verbatim.

- [x] **H6. Shape yes, surface no (2026-11-09, `local-8a98048c`).** Twelve distinct turns
  and one session id proved `--continue` works; but 16 `terminal` calls, 2 sealed reads and
  0 evictions made the run VOID (`RR-REVIEW-H6`). Its "T-A is ~19.6 k tokens" note was wrong:
  the fixture is 223,634 B ≈ 55,909 tokens. Cost $0.0030 from the capture's receipts.

- [ ] **H7. First countable cell.** Attempted 2026-11-10, **VOID** (`RR-W8CELL2`): budget 55,000
  sat under floor 53,790 + scaffold, so 0 evictions; prompt 12 never defined `widest_file`, so
  the artefact failed. Fixed: budget 72,000, field definitions in the prompt. Next run is the test.
  *Done when:* checks 1–7 of `design/W8-EXECUTOR-PROMPT.md` §5 pass **and** `evictedTokens > 0`.
  Cells counted goes 0 → 1. Budget: ask first; estimate $0.10–0.20.

- [ ] **H8. Decide the 48-cell grid, with numbers.** After H7: if the cell evicted and the artefact
  held, price a grid from the measured per-cell cost; if it did not, write the negative finding and
  close the card.
  *Done when:* `design/w8-run-plan.md` carries either a costed grid with a preregistered stopping rule
  or a closure paragraph. Owner gate: spend.

---

## 2. Close the engine's observational gap (free to design, small to build)

- [ ] **H9. Record what the engine decided.** The engine emits no record of its own decision, so a
  NO-OP and a real selection look the same from outside. Add an `enginePlan` block to the **coverage
  sidecar** (not the trace): `reason` in {`fits`, `floor_bust`, `evicted`}, `floorTokens`,
  `droppedPages`, `droppedTokens`, `prefixHash`.
  *Why:* the last three cells were diagnosed by arithmetic on `resident` and `headroom`; the reason
  string would have said `floor_bust` in one line.
  *Done when:* a unit test drives `_plan` through all three reasons and asserts the sidecar field; the
  wire schema and `ts` order are untouched; gate green.

- [ ] **H10. State the engine's floor in the report.** Once H9 lands, add the measured floor for the
  T-A session to `reports/RR-NOOP-20261109.md`.
  *Done when:* the report contains `floorTokens` and the turn spread that produced it.

---

## 3. Cache-stable selection — the hypothesis the data actually supports

- [ ] **H11. Implement `selectionMode: stable`.** Design: `design/w8-cache-stable-selection.md`.
  Hold the resident set verbatim between triggers; re-select only on residency change, budget
  overflow, or every B-th turn; canonicalise volatile markers before hashing; emit `prefixHash` per
  call.
  *Done when:* a unit test shows the same `prefixHash` across calls with an unchanged working set and
  a different one after a trigger; `should_compress` still returns False; gate green.

- [ ] **H12. One cell, stable mode, same task.** Compare against the naive reference **and** against
  the mode-off cell.
  *Done when:* `prefixHash` is unchanged between triggers, `cache_read` rises above the naive arm's
  share, and parsed artefacts match. Otherwise the finding is "stability alone is not sufficient" and
  that is written up as such.

- [ ] **H13. Answer the reviewer's P8 with the numbers from H11–H12.** Packet
  `handoff/packets/P8-cache-stable-selection.md` asks the exact question; its answer should cite a
  measured run, not an argument.

---

## 4. Deployment hygiene (small, prevents the class of bug that cost today)

- [ ] **H14. Write `tools/sync-plugin.sh`.** Copies the four files and verifies by hash, failing loudly
  if any differs; prints the installed and repo `PLUGIN_VERSION`.
  *Why:* three of today's false conclusions came from a running process older than the file, or a
  partially synced copy.
  *Done when:* the script exists, is run after a version bump, and its exit code is 0; it is referenced
  from `design/HERMES-PLUGIN-DEVELOPER-PROMPT.md` §5.

- [ ] **H15. Clean the installed directory.** Remove `live/`, `src/`, `test_plugin.py`,
  `BUG_REPORT.md`; keep `ctxvm.py` (the T17 re-export).
  *Done when:* `ls ~/.hermes/plugins/ctxvm-tracer/` shows exactly
  `__init__.py context_engine.py ctxvm.py plugin.py plugin.yaml __pycache__` and a probe still captures.

- [ ] **H16. Add a capture smoke test to the gate.** One synthetic session, assert the triple exists,
  `coverage_check` exits 0, and the sidecar carries `budgetTokens` + `budgetSource`.
  *Why:* the sidecar fields are new and currently unpinned by any gate step.

---

## 5. Test gaps (each is a hole someone will fall into)

- [ ] **H17. Retention with suffixed trace names.** Retention prunes oldest-first and must never prune
  the file it just wrote; suffixing (`-2`, `-3`) was added for collisions and has no test.
  *Done when:* a test creates N suffixed files, forces a prune, and asserts the newest survives and the
  count matches the byte budget rule.

- [ ] **H18. Budget precedence is pinned (done) — extend to the sidecar.** Five tests cover
  `_budget_from_settings`; none asserts the sidecar actually carries `budgetSource`.
  *Done when:* one test flushes a synthetic trace with a profile setting and asserts both fields.

---

## 6. Docs and layout

- [ ] **H19. `docs/quickstart.md` placement.** It is a top-level directory that `AGENTS.md` §3 does not
  list. Either add it to the layout section or move it under `design/`. Owner call; the lane supplies
  the one-line diff either way.
  *Done when:* `AGENTS.md` §3 lists `docs/` **or** the file moved and the reference updated.

- [ ] **H20. Keep the two master prompts current.** `design/HERMES-PLUGIN-DEVELOPER-PROMPT.md` and
  `design/W8-EXECUTOR-PROMPT.md` name versions, paths and open items. Re-read them at every card close;
  a prompt that describes a version two releases old is the drift this lane keeps fixing.
  *Done when:* `grep -n "0.10.11" design/HERMES-PLUGIN-DEVELOPER-PROMPT.md` still matches the installed
  version.

---

## 7. Not this lane's to start (owner-gated; listed so they are not forgotten)

```
W19 tier-2 interventions      E1/E2/E3 need a spend decision
W20 trace-surface extensions  four owner calls on the decision table
W9 baselines                  rerun scope + cost
W16 causal edges              design only
D1 positioning, D6 publish, D17 release rule
umpire >=3.10 floor           no job of its own; umpire lane
docs/quickstart (H19)         owner layout call
```

---

## Critical path

```
H4 (installed copy true)  ->  H5 (driver)  ->  H6 (shape verified, $0.01)  ->  H7 (first cell)
H9 (engine records reason) ------------------------------------------------^ cheapest alongside H5
H11 -> H12 -> H13          after H7, and only if H7 evicted at all
H1/H2/H3                   today, because they mislead the next agent
```

If H6 shows the capture still collapses to one turn, **stop** the experiment line and write the
finding: on this build, a single-turn agent session cannot exercise a turn-granular keep law, and
that is the paper's result rather than a failure to obtain one.

## Definition of done for the lane

- `bash tools/run-ci.sh` green and `bash tools/check-handoff.sh` PASS at every commit.
- No version string in the tree that disagrees with the installed copy.
- Every number in a report traceable to a command in the report.
- Every claim about an arm attributed runner-side, never to a capture.
- The experiment either produces one countable cell or a written reason why it cannot.
