# RR-DATAMININGFIX-20261117 — hygiene fix for the knowledge-discovery note: keyword lists and JSON dump land in research/**, reproduce block corrected

Lane: research (owns `research/**`). Source: `reports/RR-DATAMINING-20261117.md`, suggestion 2.
Action authorized by the owner's "fix them" (2026-11-17). No code change, no model call, no spend.
The reviewer's other five suggestions are acknowledged, not applied here.

## 1. What changed

1. Copied the data-mining script and its JSON output into the repo:
   - `research/datamining/datamining.py`
   - `research/datamining/datamining.json`
   Changed one line in the script: `OUT` now points at the repo copy of the JSON. Verified that
   `python3 research/datamining/datamining.py` runs from the repo root and reproduces the same
   counts (1,061 papers; years 148/179/232/218/137/147).
2. Corrected the reproduce block in the external note
   (`~/research/ctxvm-datamining-knowledge-discovery.md`, §10). It now points at the in-repo
   script, states the `sqlite3` CLI version (3.46.1), and prints the single-term counts with the
   six-term aggregate that produces the note's 80.

No other file was edited. `reports/LOG.md` and `RR-DAY-20261117.md` get the standard kit rows.

## 2. The count discrepancy, resolved

The reviewer's `counterfactual` = 10 is a single-term `LIKE` on `reference`. The note's 80 is the
`CTXVM_CONCEPTS["counterfactual"]` regex, an OR over six terms:

| Term | Papers |
|---|---|
| counterfactual | 9 |
| ablation | 24 |
| intervention | 12 |
| causal | 18 |
| attribution | 24 |
| leave.one.out | 0 |
| **OR-aggregate** | **80** |

Method: word-boundary regex over `title + reference`, case-insensitive. The 9 vs 10 difference
between the script's `counterfactual` and the CLI `LIKE` is the word boundary plus the `title`
field. The `monitor` case is the same pattern: CLI 31, note's "Monitor / view / audit" aggregate 53.

Both numbers are lower bounds from extractive references. Neither is a citation count.

## 3. Repro

```bash
# from the repo root
python3 research/datamining/datamining.py
sqlite3 research/anthropic-papers-reference.sqlite \
  "SELECT COUNT(*) FROM papers WHERE lower(reference) LIKE '%counterfactual%';"   # 10
sqlite3 -header research/anthropic-papers-reference.sqlite \
  "SELECT name,date,title,url FROM papers WHERE lower(reference) LIKE '%monitor%';"  # 31 rows
```

The script's `THEMES` and `CTXVM_CONCEPTS` dicts are the authoritative keyword lists. Every theme
number in the note is reproducible from them and the JSON dump.

## 4. Limits

- The yearly counts, lab table, expert map, co-occurrence table and 431 excluded papers remain the
  note's claims; the reviewer did not verify them and this card does not either.
- The SQLite table has no citation counts. Influence is not measured.
- 38 of 88 author profiles lacked an Anthropic affiliation; some are wrong-person matches.
- The note is external research material. It is not in the repo; only the keyword lists and JSON
  dump are.
- No view registry was built. The reviewer's suggestion 6 stands: that needs an owner-cleared card.
- No Part III route was preregistered or run. Suggestion 1 stands.

## 5. Owner decisions still open

From the reviewer's card, not acted on here: E1 preregistration before any experiment (suggestion
1); D17 positioning of "measurement infrastructure for evaluation and monitoring" (3); no caching
literature chase (4); page-level wire boundary / D19 additive rule (5); view registry only with an
owner-cleared design card and a testable definition of "view version" (6).
