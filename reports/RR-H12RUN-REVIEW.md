# RR-H12RUN-REVIEW — verified: a clean 24k pair, but stable mode never engaged

Review lane, verify-then-record. Subject: `19ad2c9` / `reports/RR-H12RUN-20261118.md`. No code change, no model
call, no spend, no cell by this lane. The $1 cap stands untouched.

## 1. Verdict

**Accepted as a fresh-mode 24k reference, not as an H12 stable-mode cell.** The pre-cell check passed on measured
numbers; the pair is real and free; the paged arm holds the request at 0.24× and reproduces W8C's cache forfeiture
at a quarter of the budget. But the session's own plan block says `selectionMode: fresh`, so nothing in this run
tests `selectionMode: stable`. The card's own framing is correct — "this is the fresh-mode reference the cell
needs, not the cell". H12 stays open; the diagnostic that distinguishes "policy lacked the key" from "adoption
never ran" needs the gateway restart and one paged prompt.

## 2. Evidence re-derived

| claim | how | result |
|---|---|---|
| pre-cell check | card §1 | control peak **103,648** > 1.3×24k; floor **22,420** computed with the capture's own 24,022-byte system prompt, not the design's assumed 5,483; outgoing 22,756 < 24k. Worth doing: the assumption was wrong and the check still passed |
| pair ran free | arm `summary.md` | control 58 calls / $0.0000 / CONTROL / 651.2 s; paged 41 calls / $0.0000 / CELL / 402.1 s |
| cache signature | card §2, summary in/out | cache share 98.4% → 56.3%; cache-read/call 37,974 → 10,802; uncached 34,697 → 343,759; peak request 103,648 → 24,597 (0.24×). Fewer calls on the paged arm, so the loss is not a call-count artefact |
| checker / replay | card §2 | paged artefact PASS, replay 0 — reproduced from the run record, not re-run here |
| mode defect | card §3 | plan block `selectionMode: fresh`, `trigger: null`, `budgetTokens: 24000/settings`: budget reached the engine, mode did not. Six alternative causes ruled out by check (installed copy `cmp` identical at 0.13.26, profile dirs symlinks, no `CTXVM_*` in gateway environ, `__deepcopy__` copies `__dict__`, direct `policy()` reports `stable/settings`, in-process host emulation adopts with `trigger: held`) |
| diagnostic fields | grep over run sidecars | **`policyMode` / `policyModeSource` / `modeExplicit` are absent from the existing capture** — expected, since 0.13.26 added them after the run. Confirms why one more prompt, not an argument, is needed |
| runner bug | `grep` on `tools/w8b-run.py` | line 536 now compares `task.get("name") == "tb"`; the copy-vs-identity `is` comparison is gone. The 3.5 s failed control cost no model call |
| clean suite | `CTXVM_*` cleared, `pytest packages/hermes -q` | **216 passed, 15 subtests** — matches the card |

## 3. What this supports and what it does not

- **Supports:** at 24k a paged arm holds a T-A v2 session's request at 0.24× with eviction witnessed, parsed-equal
  artefact and replay-clean trace; the cache-forfeiture signature reproduces at that budget. It is now the
  fresh-mode 24k reference for the stable-mode comparison.
- **Does not support:** any claim about stable selection, any saving, any dollar figure (free tier reports 0 and
  cache columns are harness-reported, not receipts), or a paging-quality claim. "CELL" in the runner verdict is
  the tool's label for an engaged paged arm, not a project-level GO.
- The pair differs from the control in the engine *and* two settings; a future stable cell must be read against
  this fresh-paged run, not against the naive control.

## 4. Carry-forward

- One **gateway restart** is owed before the one-prompt diagnostic; it ends active sessions and is the owner's
  call. Then one free paged prompt should say which failure the new fields expose.
- After that, an H12 stable cell can be booked under the existing authorization and **$1 cap** — with a fresh
  ceiling if the run shape changes, and the same four acceptance conditions.
- No cost-saving claim (law 7); no paged-cell GO from this reference. Earlier records stay separate and unrevised.

Kit/gate: the card reports ALL GATES GREEN; my clean pytest confirms 216 passed; hygiene was green at the last check.
