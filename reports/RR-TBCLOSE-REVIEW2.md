# RR-TBCLOSE-REVIEW2 — verified: T-B closed as a runnable shape, H11 is the next candidate cell

Review lane, verify-then-record. Subject: `cc7e1dd` (`design/TB-CLOSURE-20261118.md`, `design/TB-PLAN.md` banner,
`reports/RR-TBCLOSE-20261118.md`), plus the surface-pin probe `4552921`. No code change, no model call, no spend.

## 1. Verdict

**Closure accepted.** The one-line reasoning holds: a task that needs a calculator cannot test a context pager —
a model that shells out computes outside the window, so dropping pages cannot hurt it. Three measurements agree
from three sides, and the closure attaches the right verdicts to every earlier run without promoting any of them.

## 2. Evidence re-derived

| claim | source | result |
|---|---|---|
| closure commit | `git show --stat cc7e1dd` | 5 files: closure design, TB-PLAN banner, LOG row, day section, RR card |
| TB-PLAN withdrawn as runnable | `head design/TB-PLAN.md` | banner says CLOSED 2026-11-18, "withdrawn as a runnable design", no further run authorized, reopen needs all three conditions |
| pinned-surface probe | `RR-TBSHAPE-20261118`, closure §1.1 | free model read one file, confirmed *"'terminal' is not available in this execution context"*, spent 180 s hunting for another execution route → NO RECORD at prompt 1. One model, one prompt, one cap — the closure's own limit |
| wired with-code result | my earlier `RR-TBWIREDFULL-REVIEW` §5 | 191/192 came with 193 `read`, 196 `shell`, 1 `glob` declares — with-code, not hand-answerable |
| unwired opposite | closure §1.2 | 0/48 with both execution routes refused — same fact from the other side |
| earlier verdicts preserved | closure §1.3 | CEILING 582 vs 579 (breach), COMPLETE 584 (margin 0), NO RECORD P22 / CEILING P67 / INCOMPLETE P95 — all retained with margins, none re-scored |
| surface root cause | closure §3, `4552921` | CLI turn binds the **platform** toolset list, not the `toolsets` key; `-p <profile>` routes the turn. Driver and profiles now enforce the right key |
| instruments survive | closure §3 | fixture generator (`--check`), checker (`--prove`, three denominators, `--lookups`), task-aware runner (`--task`, `--limit`) |
| unpushed count | `git rev-list --count <remote-head>..HEAD` | **6** against the real remote tip `a881dfd` — matches the report; owner pushes |

## 3. What survives and what moves

Three harnesses' capture fidelity (unwired/wired OpenCode, dsh) remain citable: valid, replay-clean traces with real
identity, populated meta, complete flushes, every fixture ref covered. The platform-toolset root cause and its
fix are durable. The paging question moves to extraction shapes (W8C's engagement and 2.11× dollar negative),
the cache-stable line H11→H12, and a Hermes paged arm that is now runnable because the surface defect is fixed.

**Reopen needs all three**, as the closure says: a no-computation workload, a model demonstrated on three
pinned-surface prompts, and an owner authorization naming the run, its ceiling from a measured rate, and its
claim boundary. None exists today.

## 4. H11 — owner decision routed

The report proposes H11 (`selectionMode: stable`, unimplemented, free) as the next move with a negative to
overturn. I checked `design/ROADMAP-HERMES-LANE.md:97`: H11 is indeed unchecked, with
`design/w8-cache-stable-selection.md` as its design. My recommendation: **clear H11** as a hermes-lane
implementation task (free, no paid cell) before considering H12's pair — it is the prerequisite for turning the
2.11× cache-negative into a testable claim. That is a recommendation, not a ruling; no implementation or cell is
authorized by this card.

Kit/gate: the closure reports ALL GATES GREEN / kit PASS / hygiene OK; this card changes no gate input.
