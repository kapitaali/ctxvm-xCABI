# Packet P7: D-U2 baselines — add embedding-NN, logistic, small classifier, larger LLM?
STATUS: answered 2026-11-10 (verdict in handoff/QUESTIONS.md; full record reports/RR-P7BASE-20261110.md:
two cheap baselines first (majority-class + logistic-on-embeddings for accuracy/calibration;
zero-shot embedding similarity for caller-labels); stronger model only before a product claim with
a spend packet; same-split protocol (240 fit / 120 calibration / 120 test, paired bootstrap,
preregistered margin); positioning outcomes preregistered. Both reviewer UNKNOWNs resolved from
the books (480-row = 240/120/120 split at 4 labels of 120; labels still caller-supplied per call) — AND the sweep caught an erratum on the committed P6 card: the
quiescent concurrency-1 recapture already exists (RR-M3V3, attribution CONFIRMED), so Roadmap U4
ticks.

Date: 2026-11-09. Requester: A6. Related decision: D-U2.

## Question (one specific question)

The evaluation lacks embedding-NN, logistic regression, small fine-tuned classifier, and a stronger model (structured output + logprobs). Which baseline, if any, must run before calibration or positioning claims ship?

## Excerpt or diff (only the relevant lines, with file path and line range)

Seed list in adoption prompt §3 A6 (D-U2). umpire `calibration/test_calibration.py` covers only fitted-vs-raw (ECE/Brier).

## Constraints (what must not change)

No spend beyond the reserved budget without a packet. No spec edit. Same 480-row split for fairness.

## Evidence (numbers with the command that produced them; UNVERIFIED marked)

Current: v3 test 120 rows, accuracy 0.7083, ECE 0.0302 (calibrated) vs 0.2473 (raw top) — corpus internal only (README:17-35). No external baselines recorded.

## Output wanted (numbered verdicts, one line each; rewrites only if asked)

1. Run none / one / all baselines first?
2. Same-split protocol in one line?
3. What result would change the positioning brief?
