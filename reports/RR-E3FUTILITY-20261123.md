# RR-E3FUTILITY-20261123 — verified: E3 Stage 0 verdict is already fixed (G0a/G0c unreachable); recommendation STOP now

Review lane, verify-then-record. Subject: hermes lane's analysis (delivered 2026-11-23) that the E3 needle-revisit
Stage 0 run has already failed arithmetically and the remaining ~9 h cannot change the verdict. I verified every
decisive claim from disk before recording. No code change, model call, spend, or process action by this lane — the
stop/finish decision is the owner's.

## 1. The decisive arithmetic — verified

Gates require ≥0.90 of **9** tasks; 8/9 = 0.889 < 0.90, so **9/9 required**. From the 3 checkpointed tasks
(`stage0-checkpoint.json`, bank `bank-pilot9.json`, 9 items):

| gate | observed in nd01–nd03 | best possible with 6 remaining | verdict |
|---|---|---|---|
| G0a full top-1 ≥90% | 0/3 True | 6/9 = **0.667** | **unreachable** |
| G0c random-removal <0.5 nats ≥90% | 1/3 pass (nd02 1.046, nd03 1.355 fail) | 7/9 = **0.778** | **unreachable** |
| G0b needle drop ≥3 nats AND flips top-1 | 3/3 but **vacuous** | — | passes, proves nothing |
| G0d determinism | repeat_delta=0 on all 3 | — | passes |

Confirmed from the harness: `g0a`, `g0b`, `g0c` use `/ 9` and `>= 0.90`; `g0b` is
`d_needle >= 3.0 and not needle_removed.top1` (`stage0-instrument.py:113`) — since `needle_removed.top1` is False on
every task, the "flips" conjunct is always True and G0b is vacuous. The paste's claim that G0b fails was wrong per
the code; hermes corrected this, and I confirm the correction.

**Conclusion: STOP is fixed regardless of nd04–nd09.** ~6 tasks × ~88–95 min ≈ 9 h would be spent confirming a
negative already settled by nd01–nd03. The design had no futility rule — "a failed gate stops the run" was
implemented as "stops at the end."

## 2. Underlying causes — verified where checkable

1. **Model never had the answer at baseline.** 5-digit gold ≈ chance e^−11.41. Full-context logprobs: nd01 −10.48
   (2.8e−5, ~2.5× chance), nd02 −11.73 (8.1e−6, below chance), nd03 −14.01 (8.2e−7, ~14× below chance). The 13–17
   nat needle drop is real but measures "this page shifts the distribution," not "the model retrieved the value."
   With 24 pages × 26 near-duplicate lines (~8.3k tokens), a 1.5B model can't pinpoint one key — the design's own
   risk list predicted this, but placed it as a hard gate rather than routing to an easier construct.
2. **Binary flag smuggled back in.** The rationale says "graded, not binary," but G0a/G0b use a binary first-token
   flag from a separate *unforced* `n_predict=1` call, while the graded number comes from a *GBNF-forced* call —
   two decoding regimes, checking only `gold[:1]` against the first token (`:97–101`). Verified in code.
3. **Thresholds guessed, not calibrated.** G0c's 0.5-nat bound assumed random removal inert; measured 1.0–1.4 nats
   is the real noise floor with 600 near-duplicate lines. And 0.90 over n=9 permits zero failures — the prereg
   flagged "power the cell or label it a pilot" then applied a confirmatory gate to a labeled pilot.

## 3. Verified supporting facts

- GBNF forcing reproduces gold byte-exactly (`forced_byte_exact=True` on all 3), repeat_delta=0 (gate mechanism
  sound); probe call 662.1 s, 9-task bank, as stated.
- `stage1-policy-damage.py` does drive the real `select_context` (`kept_engine.select_context(...)` at `:104`,
  `ce.build_engine()` at `:141` with the host-ABC stub) — the "product code path" claim is accurate.

## 4. Recommendation (owner's decision, not executed)

**STOP the run now** — no new spend either way. Rebuild Stage 0 with: a retrieval-capable gold (e.g. 1-of-4 token
value or far fewer distractors), top-1 demoted to diagnostic (not a gate), G0c calibrated from a shrunken $0 pilot
*before* freezing, and a **futility rule**: if remaining tasks cannot change any gate, STOP immediately. This is
the fourth instrument-level failure (E0 gradability, E2 specificity, E0 retry, E3 readout) — the construct-validity
gap the meta-diagnosis named. No hypothesis result has been reached in any of them.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`. No process
was stopped by this lane; no claim/push/spend.
