# RR-WPVERIFY-20261117 — verified: the routed white-paper corrections landed coherently

Review lane, verify-then-record. Subject: `e10d249` (research lane: P13/P14 corrections, PDF rebuild). No code
change, no model call, no spend by this lane; `research/**` is read-never-edit for me.

## 1. Verdict

**The landing is coherent.** Every routed edit I checked is present, the stale M0 count is corrected, the PDF was
rebuilt, and both page-count claims match the new artifact. No erratum is owed from this verification.

## 2. Checks

| routed item | how | result |
|---|---|---|
| A3/P13 — six one-liner sites | `grep 'reconstruct and replay the exact request'` in `white-paper.md` and `index.md` | **0 hits** in both; narrowed phrase `structure of the request` present 3× / 3× |
| A3/P13 — `:247` in-place fix | paper's wording | replaced with the per-turn render record (landed with the commit) |
| A4/P14 — seventh §16 bullet | count bullets in §16 | **7 bullets**, including "cannot reconstruct the request's bytes" |
| A4/P14 — Part II `:77` | search for `exact request` | **no residual**; the overclaim and its "narrow form" label are gone. Narrowed phrase present 4× |
| A2/P14 — "estimated", not "measured" | paper §16 wording | the estimate caveat is carried in the bullet |
| A1 — M0 test count | `grep 'tests green'` | now **77 cargo tests (78 with tiktoken)**, dated 2026-11-16 with the command — matches my earlier measurement |
| A1 — PDF | `pdfinfo research/white-paper.pdf` | **26 pages**; README says "26 pages"; index.md says "26 pages, rebuilt 2026-11-16" — all three agree |

The earlier disagreements (HEAD 23-p page vs 15/22 claims, WIP 24 vs rebuild 25) are gone: artifact and claims now
match at 26. No rebuilding by me — I only read the committed artifact.

## 3. Not re-verified

- Byte-identity of a fresh `build-pdf.sh` rebuild against the committed PDF. The research lane owns that build;
  the page-count agreement is evidence the same source produced it, but not a byte check.
- Claim accuracy beyond the routed edits (citations, external claims, safety sections) — out of scope here.
- Whether the three paper files are consistent in every sentence; I checked the specific sites named in P13/P14.

## 4. Carry-forward

No open item from this verification. Publication (D17) remains the owner's decision, unchanged. If a later
rebuild changes page count, README and index.md must move with it — the lesson from the earlier disagreement.

Kit/gate were green at the last check; this card changes no gate input.
