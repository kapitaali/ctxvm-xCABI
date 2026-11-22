# RR-E0RETRY-RESULT-20261122 — E0 retry: Gate L PASS, Gate G FAIL (3/5) → STOP; no full run

Owner "run the gates" on 2026-11-22, under the criteria frozen before any call (`RR-E0RETRY-GATES-20261122.md`).
Single-variable retry on the recommended model `qwen2.5-1.5b-instruct-q8_0` (`d7efb072…`), committed v2 bank
(`cba643d2…` read from `git show HEAD`), $0 local CPU, no provider call. Server stopped (pid 19069); umpire tree
byte-clean; research WIP preserved. No push.

## 1. Verified from `experiments/e0-gate2/retry-gates-20261122.json`

| gate | criterion (frozen) | measured | verdict |
|---|---|---|---|
| **L — logprob + GBNF** | per-token logprobs returned AND forced content byte-exact | baseline_lp=100, forced_lp=101, `forced_byte_exact=True` | **PASS** |
| **G — gradability, 5 items** | PASS ≥4/5 `Var(T)>0`; FAIL ≤3/5 → stop | fb01 0.000, fb02 0.000, fb03 0.360, fb04 0.160, fb05 0.360 → **3/5 gradable** | **FAIL** |

Result object verdict: `STOP — Gate G FAIL (<=3/5); no loosening, no full run`. The bank snapshot used was verified
`cba643d2…` (committed v2), not the working-tree v3 WIP.

## 2. What this means

Gate L PASS confirms the 1.5B model supports E0's teacher-forced logprob + byte-exact GBNF metric — the mechanism
is fine. Gate G FAIL (3/5) means the different model still does not reliably emit the frozen v2 identifier tokens
on 2 of 5 items: the same **gradability precondition** that failed on the 1.7B (12/20) and on the v3 prompt pilot
(2/5) fails again on the 1.5B. The single-variable swap did not fix the instrument. **No full run** — the frozen
FAIL rule was followed exactly: no rule/prompt/bank loosening, no re-scoring, no model switch, no v3 switch.

This is the **third consecutive instrument-precondition failure** for E0 (1.7B v2: 12/20; v3 prompt: 2/5 pilot;
1.5B v2: 3/5 pilot). The pattern is now robust across two models and two prompt/rule variants: the instrument
(a small local model's free-form answer carrying exact identifier tokens) is the binding constraint, not the
paging/touch-count hypothesis. Recorded as a negative precondition finding with equal prominence.

## 3. What is not claimed

No ρ, causal-influence, paging, answer-quality, cost-saving (law 7), or model-quality claim. Nothing pooled with
E0/E2/M1/M2/M3. The published E0 double negative (`RR-E0-NEGATIVE`) stands unchanged; this retry is a separate
failed precondition, not a new E0 result. A further retry (larger model / new acquisition, or a different
identifier scheme) is a **fresh owner ruling** — not started.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261122.md`. No spend,
no push.
