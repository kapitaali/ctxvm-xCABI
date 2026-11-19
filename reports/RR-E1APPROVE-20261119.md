# RR-E1APPROVE-20261119 — owner approves E1 (gate open, zero-spend)

Owner decision 2026-11-19, verbatim in response to my next-work list:

> approve E1.

Scope confirmed with the owner at the time of the ruling: **open the gate; the research lane resolves the
specifics.** That is the narrow reading and it is the one recorded here. This card records a ruling and routes it;
the review lane writes no `research/**` byte.

## 1. What the approval authorizes

- **Data freeze** — the research lane copies the 5 development traces (≥1 fault each) plus a `sha256sum` manifest
  into `research/e1-offline/`, records session IDs, and keeps raw prompts/file contents out of every report
  (privacy law 9). Source table: `~/research/plan-E1-smallest-testable-system.md` §2.
- **Prereg** — `research/e1-offline/PREREG.md` with question, view **v1** + hash, arms (control / A fault-label /
  B random-page seeded), metric (faults per turn on the held-out corpus, stratified by source), stop rule (≤10%
  difference ⇒ negative), data digests, falsifier, deviation rule, and an owner sign-off line. Plan §3–§4, §7 step 3.
- **Offline replay** — one script in `research/e1-offline/`, bounded input, per-item `START/OK/FAIL` debug output,
  count printed before any conclusion. Plan §7 step 4.

**Zero-spend by design.** Plan §6 excludes umpire and any model server; §4 is an offline replay over existing traces.
This approval authorizes **no model call, no paid experiment, and no E2**. It does not reopen W8 spend (still
stopped — `PROJECT-STATE.md` §Blocked).

## 2. What it does not resolve

The data-choice blockers named in `RR-PART3REVIEW-CLOSE-20261118.md` are **delegated to the research lane**, not
picked by this ruling:

- **15 corpus paths / 13 filenames** with flat-copy collisions — the research lane decides the naming/layout before
  copying, and records that decision in the prereg.
- **live-count mismatch 247/4 vs the stated 243/5** — the research lane reconciles the counts and records the
  resolution and its locator before the prereg sign-off.

Gate 0 was already closed by owner ruling 2026-11-18 ("close the review", `RR-PART3REVIEW-CLOSE-20261118.md`,
commit `9a679bb`). That closure did not resolve these two blockers; this approval does not pick a specific data
set either — it opens the gate and assigns the resolution. No claim about a data choice exists until the research
lane writes one down.

## 3. Applied by the review lane

- This card, an append-only LOG row (four pipes), and a day section in `reports/RR-DAY-20261119.md`.
- `handoff/PROJECT-STATE.md`: research in-progress line, Next-three item 2, and a Decisions-made line updated to
  show E1 approved and routed.

No `research/**` edit, no code change, no model call, no spend, no push. Mechanism note: no signature artifact —
the owner rules in chat and the review lane records the ruling with date and exact decision (precedent
`RR-W8CSEQ-20261111`). If a file and a chat summary disagree, the file wins.
