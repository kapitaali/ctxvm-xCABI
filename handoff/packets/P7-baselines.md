# Packet P7: D-U2 baselines — add embedding-NN, logistic, small classifier, larger LLM?

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
