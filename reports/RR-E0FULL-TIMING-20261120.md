# RR-E0FULL-TIMING-20261120 — full-run timing probe: the $0 CPU route is ~7 h, not hour-order

Owner said "run it" after I proposed chunking the full E0 run into 4 chunks. I started the pinned server
(pid 66992, hashes verified) and ran **validation calls only** — no full run, no results claimed. I stopped the
server and am reporting a material finding before committing hours of CPU, because it contradicts the ruling's
time estimate. $0 spend, no provider call, no `research/**` or `umpire/**` source byte, no push.

## 1. What I measured (pinned build, this machine)

| operation | command shape | wall time |
|---|---|---|
| baseline generation a(τ), one bank item, ~900-token context | `/completion`, `n_predict=96`, `temperature=0` | **58.9 s** (96 tokens, logprobs returned when `n_probs=1`) |
| forced scoring of a short continuation under τ\p | `/completion`, GBNF `root ::= " doc1_value = 107"`, `n_predict=12` | **39.0 s** |
| **forced scoring of a FULL answer under τ** | GBNF literal of the 361-char / 96-token answer, `n_predict=100` | **60.3 s** — reproduced the answer byte-for-byte (`content matches answer: True`) |

Two mechanical facts established:
- Teacher-forced scoring of the **full** baseline answer via GBNF works and reproduces a(τ) exactly — so the Δ(p)
  metric is implementable on this build (consistent with Gate 1).
- But `n_probs=0` omits `completion_probabilities`; `n_probs>=1` is required to get per-token logprobs. This is a
  driver detail, not a blocker.

## 2. The timing problem

Each ablation scoring of a full answer costs ~60 s because it re-evaluates the ~900-token context on CPU
(~19 tok/s prompt eval). Per item, the prereg design needs 1 baseline + 1 baseline-repeat + 10 leave-one-out + 10
matched-random = **22 full-context passes ≈ 22 × ~60 s ≈ 22 min**. For 20 items that is **~7.3 hours of CPU**,
not the "hour-order / ~80–90 min" figure in `RR-E0ROUTE` (which came from Gate 1's 1-token `n_predict=1` probes,
~1.5 s each — those do not apply to scoring a full answer under a full context).

This is not a blocker on correctness — it is a cost/feasibility decision. My earlier chunk plan (4×5 items,
~20 min/chunk) was wrong by ~4×. I did not launch the full run.

## 3. Options for the owner (none executed)

1. **Accept the ~7 h $0 CPU path** — run all 20 items in 4 resumable chunks (~110 min each). Zero spend; multi-hour
   wall time on this laptop; fine if the machine can be left running.
2. **Reduce the ablation burden** — e.g. score a fixed short answer suffix or fewer pages per item; **this changes
   Δ(p) and is a prereg deviation**, needs its own card and must be logged before any run.
3. **Escalate to a rented GPU + 7–8B model** — the $5–10 ceiling already ruled for the *ungradable-pilot* branch;
   using it here would be a new purpose for that ceiling (faster, not just gradability), so I would treat it as a
   fresh ruling, not assume the old one covers it.
4. **Park the full run** — record Gate 1/2 PASS and stop; publish the mechanism/gates without the 440-eval result.

## 4. State

Server stopped (pid 66992, health refused after); umpire tree byte-clean; research lane's staged prereg fold-in
untouched. No model call spend, no full run, no result. Routed to review books: LOG row + day section.
