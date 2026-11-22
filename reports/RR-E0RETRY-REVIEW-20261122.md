# RR-E0RETRY-REVIEW-20261122 — verified: E0 retry plan coherent; single-variable model swap with frozen gates, awaiting owner sign-off

Review lane, verify-then-record. Subject: staged `RR-E0RETRY-PLAN-20261121.md` (owner's draft, design-only, also
landed in the repo as `reports/RR-E0RETRY-PLAN-20261121.md`). Verified from disk on 2026-11-22; the plan is dated
20261121 (authored the prior day) — I did not rewrite that date. No call, spend, model swap, or commit of another
lane's WIP by this lane.

## 1. Verified anchors

| claim | command | result |
|---|---|---|
| candidate models on disk with claimed hashes | `sha256sum ~/Documents/umpire/models/*.gguf` | `qwen2.5-1.5b-instruct-q8_0` → `d7efb072e7724d25048a…`; `Qwen3-0.6B-Q8_0` → `9465e63a22add5354d9b…` — both match the plan |
| committed v2 bank sha | `git show HEAD:research/fixture-bank/bank.json \| sha256sum` | `cba643d2ef105d744786…` — matches the plan's frozen bank |
| pinned runner | `sha256sum …/llama-server` | `0f60e0483ee8aa394f2f…` — matches the plan's pinned binary |
| E0 double negative still published | `ls reports/RR-E0-NEGATIVE-20261121.md` | present — nothing pooled, no claim re-opened |

## 2. Coherence assessment (not an authorization)

- **The single-variable design is sound:** bank (v2 `cba643d2…`), v2 identifier rule, prompt, seed, and 440-eval
  structure all stay frozen; **only the GGUF changes** — so a Gate G result would be attributable to the model.
- **The metric-preservation argument is right on the local side:** E0's Δ(p) needs teacher-forced per-token
  logprobs under τ vs τ\p, which the pinned llama.cpp provides (Gate 1 PASS, `RR-E0GATE1`; full-answer GBNF forcing
  byte-exact, `RR-E0FULL-TIMING`). A hosted free API would change the metric to answer-change = E2, which already
  closed as an instrument failure — so a local GGUF swap is the correct shape for a retry. **Evidence boundary:**
  I verified the local mechanism but did not test any hosted API's logprob primitive; the plan's claim that hosted
  APIs lack forced continuation is a design rationale, not a measured fact from this lane.
- **Anti-fishing is frozen before any run:** Gate L (logprob + byte-exact GBNF, make-or-break) and Gate G
  (5 items, PASS ≥4/5 `Var(T)>0`, FAIL ≤3/5 → stop, no rule/prompt/bank loosening). A Gate G PASS still needs a
  separate go-ahead for the ~7.3 h chunked full run.

## 3. Recommendation (for the owner's ruling, not executed)

Take the recommended candidate `qwen2.5-1.5b-instruct-q8_0` (`d7efb072…`) — different architecture/instruct tuning
than the failed 1.7B, same $0 CPU logprob+GBNF mechanism, on disk (no download). Keep the backup Qwen3-0.6B in
reserve. But decide this with open eyes: both E0 and E2 failed on **instrument** properties, not the hypothesis;
a different 1.5B model may simply reproduce the same "no identifier tokens" failure. The gates are what make a
negative cheap and honest — run Gate L then Gate G, and stop at FAIL exactly as frozen.

## 4. State and applied

The plan's §5 sign-off remains blank (model choice, frozen-gate acceptance, full-run go-ahead, deviation authority,
decision/date/owner) — **no model call or spend is authorized by this card**. E0 stays published as a double
negative; E2 stays closed; D17 held. Research v3 WIP, staged prereg fold-in, and untracked E2 cards are other lanes'
work, preserved. Applied: this card, an append-only LOG row (four pipes), and a day-file section
(`reports/RR-DAY-20261122.md`). No push.
