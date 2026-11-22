# RR-E0RETRY-GATES-20261122 — owner "run the gates": frozen Gate L + Gate G on the recommended 1.5B model

Owner decision 2026-11-22, verbatim: **"run the gates"**. Interpreted as: use the plan's **recommended** candidate
`qwen2.5-1.5b-instruct-q8_0` (`d7efb072…`), apply the **frozen** Gate L and Gate G criteria from
`RR-E0RETRY-PLAN-20261121.md`, and **not** proceed to the ~7.3 h full run (that needs a separate go-ahead on a PASS).
This card fixes that interpretation and the decision rules **before** the calls — anti-fishing discipline. Review
lane, no spend (local CPU $0 route), no push.

## 1. Frozen inputs (written before call 1)

- **Model:** `qwen2.5-1.5b-instruct-q8_0.gguf`, sha256 `d7efb072e7724d25048a…` (on disk, verified); pinned via
  `UMPIRE_MODEL_ID=qwen2.5-1.5b` → `harness/pins.json` entry (sha `d7efb…`, binary `0f60e048…`).
- **Bank:** **committed v2** read from `git show HEAD:research/fixture-bank/bank.json` (sha `cba643d2ef105d744786…`),
  **not** the working-tree v3 WIP (sha `86adb25…`). The runner snapshots v2 to a file and verifies its sha before use.
- **Identifier rule:** v2 frozen (`doc<j>_value` + `<topic>-doc-<j>`, whole-token case-insensitive) — unchanged, so
  gradability is comparable to the published 12/20. v3's value-robust rule is not used.
- **Prompt / seed / arms:** v2 prompt from the frozen bank, `temperature 0`, `seed 7`, `n_predict` as in the v2 runner.

## 2. Gate L — logprob + byte-exact GBNF (make-or-break)

One bounded `/completion` with `n_probs>=1` and a GBNF-forced full answer.
**PASS** only if `completion_probabilities` returns per-token logprobs **and** the forced content matches the
baseline answer byte-for-byte. **FAIL** → stop: the new model cannot support E0's metric; record, do not substitute
a hosted model.

## 3. Gate G — gradability pilot, criterion frozen NOW

- 5 items fb01–fb05, baseline a(τ) under the v2 prompt, `Var(T(p))>0` under the v2 rule.
- **PASS = ≥4/5 gradable.** On PASS: stop and report; the ~7.3 h chunked full run needs a **separate** go-ahead.
- **FAIL = ≤3/5 → stop.** No rule loosening, no prompt/bank change, no v3 switch, no re-scoring, no model switch.
- No post-hoc re-labeling; bank/rule/model hashes frozen before call 1.

## 4. Scope

No hypothesis/ρ/answer/cost/model-quality claim from a gate. E0 stays published as a double negative; E2 closed;
D17 held. On either FAIL the result is a negative precondition finding, recorded with equal prominence, and the
retry stops. No full run authorized by this card. No push.
