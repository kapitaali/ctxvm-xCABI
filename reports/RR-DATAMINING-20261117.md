# RR-DATAMINING-20261117 — read of the knowledge-discovery note; signals, one count discrepancy, and suggestions

Review lane, verify-then-record. Source: `~/research/ctxvm-datamining-knowledge-discovery.md` (2026-11-17),
outside the repo (read-only here). No code change, no model call, no spend. This card records the read and the
suggestions; it does not endorse the note's counts as verified.

## 1. What the note is

A keyword-matching analysis over a 1,061-row SQLite corpus of papers by 88 named scientists (plus a 159-paper
lab-filtered export), producing theme counts, per-concept coverage, lab comparison, an expert map, and seven
findings with a development order. Its own §9 says the counts are lower bounds from extractive references, that
431 unavailable papers are excluded, that 38/88 author profiles lacked an Anthropic affiliation with
wrong-person matches found, and that no citation counts exist. The note is a **design signal**, not an experiment.

## 2. What I checked

| check | result |
|---|---|
| script and DB exist | `~/.hermes/cache/scratch/datamining.py` (5,450 B), `~/research/anthropic-papers-reference.sqlite` (2.99 MB) |
| corpus row count | **1,061** via Python sqlite3 — matches the note |
| `monitor` over `reference` | **31** — matches the note's targeted count |
| `process supervision` over `reference` | **1** — matches |
| `counterfactual` over `reference` | **10**, not the note's **80** (§3 table "Counterfactual / ablation / intervention" is a different combined keyword set — as is "Monitor / view / audit" = 53 vs the targeted `monitor` = 31). The note does not show the exact per-theme keyword lists, so the 80 and 53 are **not reproducible from the stated command alone** |
| `sqlite3` CLI | absent on this machine; the note's §10 reproduce block will fail as written unless Python sqlite3 is substituted |

The discrepancy is not evidence the note is wrong — the theme table aggregates several terms — but it means a
reader cannot audit the headline theme counts from the printed command. Ask the research lane for the keyword
lists (or a `datamining.json` dump) before using theme numbers in a paper.

## 3. Where the note overlaps work already in the repo

- **Part III Route A** (fault-driven process supervision) matches finding 5; **Route E** (versioned monitor views)
  matches finding 1; **Route D** (metrics as data selectors) matches finding 6. Part III already proposes these as
  designs with falsifiers and explicitly says no route has been run (`RR-PART3-RECORD-20261117`).
- **Page granularity** (finding 3) matches the sealed wire law and the D19 ruling: no sentence-level verb, and the
  omission problem is an open RFC-0.1 extension, not a new v0 verb.
- **Cache instrumentation** (finding 4) matches our measured 2.11× paid result — internal, not from literature.
  No cost-saving claim (law 7).
- **View registry** (the note's priority 1): I found no `MonitorView`/view-registry implementation under
  `rust/`, `packages/`, or `spec/`. Part I §12 defines views conceptually; the registry is a design item, not code.

## 4. Suggestions — what I would do with this knowledge

1. **Treat it as a research-agenda input, not a build order.** The note's priorities 1, 3 and 6 are already Part III
   routes A/E/D. Before implementing anything, preregister one of Part III's E1–E5 experiments; the paper itself
   requires that. The cheapest is E1 (fault labels, no paid calls), which aligns with finding 5.
2. **Fix the evidence hygiene before citing the counts.** Get the keyword lists and the `datamining.json` output
   into the repo's research area with a RR card; correct the reproduce block for the missing sqlite3 CLI. Mark
   theme counts as lower bounds, as the note already does in §9. This is a research-lane task (`research/**`).
3. **Positioning, not product:** finding 7 argues for ctxvm as measurement infrastructure for evaluation and
   monitoring. That is a first-class D17 publication decision — the paper's framing, not a code change. Tie it to
   the P13/P14 corrections already landed and the Part III claim ceiling.
4. **Do not chase the literature on caching** (finding 4). We have a measured internal result and the literature
   barely covers it; keep runner-side instrumentation and the honest 2.11× statement.
5. **Keep the page-level wire boundary** (finding 3). The corpus gap is an argument *for* granularity, not for a
   new verb; any omission extension stays additive and version-gated (D19).
6. **Monitoring is the growth area** (finding 1) — but the repo has no view registry. If the owner wants that
   built, it needs a design card with an owner-cleared placement and a testable definition of "view version";
   I would not start it on the strength of a keyword trend alone.

## 5. Limits of my read

I did not verify the yearly counts, lab table, expert map, co-occurrence table, or the 431 excluded papers; I
spot-checked only the items in §2. I did not read the underlying 159 paper abstracts. The note is external
research material; I did not edit it or copy any of it into `research/**`.

No action is authorized by this card. Kit/gate were green at the last check and this card changes no gate input.
