# RR-PART3-RECORD-20261117 — Part III landed, but its record rows are missing

Review lane, verify-then-record. Subject: `5ab5d38` ("Land white paper Part III draft (English and Chinese)").
No code change, no model call, no spend. `research/**` is read-never-edit for me.

## 1. What landed

`git show --stat 5ab5d38`: exactly two files —
`research/white-paper-Part-III.md` (530 lines) and `research/white-paper-Part-III.zh.md` (461 lines). Both are in
HEAD. I read the English draft earlier: a design paper with six routes, five experiment designs, an eight-item
agenda, explicit evidence levels and UNVERIFIED marks, and a document control stating "Experiments run: None".

## 2. Record gap

AGENTS.md §6 requires every card to produce (1) an `RR-<CARD>-<date>.md` report, (2) a row in `reports/LOG.md`,
and (3) a section in `reports/RR-DAY-<date>.md`. For `5ab5d38` I checked all three:

- `grep -i 'Part-III|Part III' reports/LOG.md` → **no hit**
- same on `reports/RR-DAY-20261117.md` → **no hit**
- `ls reports/ | grep -i 'PART3|PART-III'` → **no file**
- the commit message contains only the title — no locator, numbers, or limitations

So the artifact is committed but invisible in the ledger and the day index. The LOG is append-only, so the fix is
an erratum row, not a rewrite. This card is the RR; this section plus the new LOG row and a day-file section close
the three-part record.

## 3. What the record must say about the artifact itself

- **Status:** draft for review, version 1.0, 17 November 2026 (Document control). No experiment was run; all
  designs are preregistration candidates.
- **Claim ceiling:** ctxvm supplies the input side of a learning loop — traces, deterministic replay, page-level
  interventions, versioned views. It does not train weights, choose objectives, see internals, judge correctness,
  or prove causation from a render. No cost-saving claim; the 2.11× paid cell is cited as the reason.
- **Evidence hygiene to check before any preregistration:** six §5 sources are marked "Extract — UNVERIFIED", and
  route F's analogy is explicitly UNVERIFIED. The §3 corpus method reports 2,007 scientist-paper rows, 1,495
  unique works, 1,064 PDFs, 1,061 reference rows, and a 159-paper lab filter; 38 of 88 author profiles had no
  Anthropic affiliation in OpenAlex and wrong-person matches were found, so author matching is itself flagged.
- **Not verified by me:** the Chinese draft's fidelity to the English; the corpus counts against the underlying
  SQLite/JSON files; the existence or accuracy of the cited papers. This card records the landing, not a review
  of the paper's claims.

## 4. Carry-forward

The research lane owns `research/**`. Whoever continues Part III should add the RR/LOG/day record at commit time,
and a substantive review card should verify the corpus counts and citations before any E1–E5 preregistration.
No GO, no spend, no model call authorized by this card.

Kit/gate were green at the last check; this card changes no gate input.
