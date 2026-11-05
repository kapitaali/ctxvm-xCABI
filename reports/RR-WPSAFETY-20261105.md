# RR-WPSAFETY-20261105 — the seven research questions, and the paper that now carries them

Card: owner request of 2026-11-05 — read the uncommitted safety note, answer its research
questions, then revise the white paper accordingly. Related record: `research/synthesis-20261105.md`
(committed the same morning by the synthesis lane; it merges the two source notes and ranks the card
queue). This card is the experiment-level pass: what each question can be answered with today, what
cannot, and the paper sections that say so.

## What was done

1. Read `research/uncommitted/ctxvm and AI safety research note and proposed white-paper sections.md`
   (11,750 characters): three questions, seven research questions, sixteen references, ten proposed
   white-paper sections.
2. Fetched every reference at its arXiv abstract page and compared the claim in the note with the
   text at the source. Results in the table below.
3. Ran the one measurement the repository can support today (RQ4's premise) over its own traces.
4. Wrote `research/safety-research-questions.md` (190 lines): one section per question, each with
   what is known, what ctxvm can say now, the experiment and its cost, and a verdict.
5. Revised `research/white-paper/white-paper.md`: five related-work subsections (§8.7–§8.11) and
   nine new sections (§9 threat model, §10 counterfactual replay, §11 evaluation infrastructure,
   §12 monitor views, §13 provenance, §14 control protocols, §15 audit and regulation, §16 what
   ctxvm cannot do, §17 research agenda). Conclusion renumbered to §18; abstract gained one sentence
   pointing at the new block; §7 gained four limitation bullets; 19 references added.
6. Fixed a real defect found on the way: `index.md` and `white-paper.md` had drifted, while
   `README.md` required hand maintenance "until one is generated from the other". Added
   `sync-index.py` (`--check` mode included), regenerated `index.md`, and rewrote the sync rule.
7. Rebuilt the PDF through `build-pdf.sh`: 15 → 22 pages, 93 KB → 118 KB, clean text.

## Source verification

Fetched at abstract level on 2026-11-05. "Verified" means the claim in the note matches the abstract
text; "body-level" means the number appears only in a paper body that was not opened, and the paper
marks it as such.

| Source | Claim checked | Result |
|---|---|---|
| Barnett & Thiergart, arXiv:2412.08653 | evaluations cannot establish upper bounds or robustly assess autonomous systems | verified |
| Kapoor et al., HAL, arXiv:2510.11977 | 21,730 rollouts, ~$40k, models × scaffolds × benchmarks; log inspection found benchmark searching | verified; "scaffold strongly affects accuracy" is body-level |
| Needham et al., arXiv:2505.23836 | evaluation awareness AUC 0.83 vs human 0.92; agentic easier to spot | verified |
| Charnock et al., arXiv:2601.11916 | AL1/AL2/AL3 access taxonomy | verified |
| Cohen-Wang et al., ContextCite, arXiv:2409.00729 | ablation-surrogate attribution | verified; the 32× multiplier is body-level |
| Cohen-Wang et al., probes, arXiv:2502.03407 | AUROC 0.96–0.999, insufficient as a robust defence | verified |
| Arnav et al., arXiv:2505.23575 | CoT monitoring good on subtle sabotage, misled on obvious cases; hybrid best | verified |
| Arike et al., arXiv:2601.21112 | less-is-more; extract-and-evaluate +16.8 pp | verified |
| Korbak et al., arXiv:2507.11473 | CoT monitorability fragile, development choices erode it | verified |
| Chen et al., arXiv:2505.05410 | reveal rate often below 20%; RL plateaus; more hint use ≠ more verbalization | verified |
| FACE-Eval, arXiv:2608.29464 | tool-return cues less verbalized on all 15 models; monitor detection falls as unverbalized adoption rises | verified |
| Why Models Know But Don't Say, arXiv:2603.26410 | 55.4% thinking-answer divergence; 11.8% in neither channel | verified |
| Greenblatt et al., arXiv:2312.06942 | control protocols robust to intentional subversion | verified |
| Bhatt et al., Ctrl-Z, arXiv:2504.10374 | resampling protocols, BashBench | verified; 58%→7% and 5% are body-level |
| Debenedetti et al., CaMeL, arXiv:2503.18813 | 77% with provable security vs 84% undefended | verified |
| Laban et al., arXiv:2505.06120 | 39% average multi-turn drop; no recovery after a wrong turn | verified |
| FAR.AI, arXiv:2512.07810 | blue team could not reliably discriminate sandbaggers | verified |
| UK AISI, 21 Jul 2026 | every model tested attempted to cheat; transcript review protects published estimates | verified (site) |
| AI Act Arts. 12, 55 | automatic recording; documented adversarial testing | verified (regulation text) |

Two secondary-only figures from the earlier note stay `UNVERIFIED` and are named in the paper's
document-control table: the 11.3 h vs >270 h capability swing, and AISI's per-model cheating rates.

## The measurement

Across 24 traces (frozen corpus `m1`–`m8` plus the live capture directory):

```
declared pages            417
rendered at least once    312  (74.8%)
page.fault events         303
faults on rendered pages  301  (99.3%)
faults on unrendered pages  2
```

Reading: the fault taxonomy fires when the model re-requests content it has seen, so a page never
shown cannot produce the event. The 99.3% is therefore close to definitional and cannot separate
"the model needed it" from "the harness had shown it". That separation is RQ4's ablation experiment,
and it is the reason §17 of the paper marks the agenda as unanswered.

## Verdicts recorded

| RQ | Verdict |
|---|---|
| 1. touch ratio vs causal influence | designed; needs page-ablation spend |
| 2. CoT admits an injected hint on agentic traces | designed; strongest candidate |
| 3. which page views make the best monitors | designed; baseline to beat exists (EaE) |
| 4. capability vs context policy | unanswered anywhere; spend-bound |
| 5. which pages give an evaluation away | blocked on deployment traces + redaction |
| 6. page provenance as a taint layer | prototype-able; three attributes missing |
| 7. evicting an early wrong premise | not started; three-arm design incl. oracle arm |

## Verification of this card

```sh
python3 research/white-paper/sync-index.py --check     # OK: index.md matches white-paper.md
bash research/white-paper/build-pdf.sh                 # 22 pages, 117,950 bytes
bash tools/run-ci.sh                                   # ALL GATES GREEN
```

Markdown hygiene on every edited file: no non-NFC characters, no CJK characters, no doubled pipe characters.

## Limitations

- **Abstract level only.** Every citation was verified against the abstract page, not the full text.
  Numbers that live in bodies are marked body-level in the paper and in the register.
- **No experiment was run.** None of the seven questions is answered; the card establishes what is
  known, what the repository can measure, and what each experiment would cost.
- **The measurement is definition-bound.** It is one set operation over parsed events, reported for
  the caution it supplies, not as a result about models.
- **The paper's new sections are a position, not a finding.** §17's table states status per row; the
  document-control block records that the safety sections were added on this date.
