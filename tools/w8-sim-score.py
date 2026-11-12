#!/usr/bin/env python3
"""w8-sim-score.py — score the offline policy simulator against a measured pair. Zero spend.

Declared BEFORE the numbers are read (RR-W8SIM's rule, kept):

  model S   the control arm is the counterfactual. At turn t the unconstrained request is the
            control's measured prompt; the policy keeps the system prompt, the first three turns
            and the last six, and drops the middle until the request fits the budget.
            Predicted eviction(t) = max(0, unconstrained(t) - budget).
            Predicted post-drop request(t) = min(unconstrained(t), budget).

  tolerance onset turn must match exactly; on engaged turns the median relative error of the
            predicted eviction against the observed `turn.render.evictedTokens` must be <= 10 %.
            Outside either, the model FAILS and the card says so.

  inputs    two captures of one pair: the control's and the treatment's. Prompt totals come from
            `call.meta.providerUsage` (inputTokens + cachedInputTokens), one record per turn;
            observed evictions from `turn.render.evictedTokens`.

Usage: w8-sim-score.py CONTROL.jsonl TREATMENT.jsonl --budget 60000

CALL-GRANULARITY MODE (rule declared 2026-11-12, BEFORE the 0.13.3 pair was run)

  model S2  the policy decides once per selection. For each recorded selection k with a measured
            request size `before`, the model predicts
                after_k  = min(before_k, budget)
                drop_k   = max(0, before_k - budget)
            and is scored against the `after` the engine itself recorded. `before` is the only input;
            `after` is the only thing compared.

  tolerance the median relative error of after_k must be <= 5 % on selections where the model
            predicts a drop, and the sign of every prediction must match (drop or no drop). Outside
            either, model S2 FAILS and the card says so.

  why       the turn-level mode failed by 33 % with a +3,200/turn residual because a turn is two
            requests and one `turn.render`. If the reconciliation is right, the call-level model
            closes that gap; if it does not, the keep law itself is wrong and the next card says that.

Usage: w8-sim-score.py --calls TREATMENT.jsonl --budget 60000
"""
from __future__ import annotations

import json
import statistics
import sys
from typing import Any, Dict, List


def load(path: str) -> Dict[str, Any]:
    prompts: List[int] = []
    evicted: List[int] = []
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("type") == "turn.render":
            # The prompt the policy was GIVEN is `prefix.approxInputTokens`. The provider-receipt
            # sum is not it: measured 2026-11-12, call.meta's input+cached runs ~2x the request
            # because it aggregates the turn's calls, so it cannot serve as the counterfactual.
            prompts.append(int((r.get("prefix") or {}).get("approxInputTokens") or 0))
            evicted.append(int(r.get("evictedTokens") or 0))
    return {"prompts": prompts, "evicted": evicted}


def score_calls(trace_path: str, budget: int) -> int:
    side = trace_path.replace(".jsonl", ".coverage.json")
    calls = (json.load(open(side, encoding="utf-8")).get("plugin") or {}).get("callSizes") or []
    if not calls:
        print(f"sim: no callSizes in {side} — the capture predates plugin 0.13.3; nothing to score")
        return 2
    errs = []
    sign_ok = True
    for c in calls:
        before, after = c.get("before"), c.get("after")
        if not isinstance(before, int) or not isinstance(after, int):
            continue
        pred_after = min(before, budget)
        dropped_pred = before > budget
        dropped_obs = after < before
        if dropped_pred != dropped_obs:
            sign_ok = False
        if dropped_obs and after > 0:
            errs.append(abs(pred_after - after) / after)
    median_err = statistics.median(errs) if errs else 0.0
    print(f"sim(S2): {len(calls)} selections, budget {budget:,}")
    print(f"sim(S2): selections with a predicted drop {len(errs)}; median |error| {median_err:.1%}")
    print(f"sim(S2): every prediction's sign matches: {sign_ok}")
    ok = sign_ok and median_err <= 0.05
    print(f"sim(S2): VERDICT {'PASS' if ok else 'FAIL'} (sign exact, median error <= 5 %)")
    return 0 if ok else 1


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    budget = 60000
    if "--budget" in argv:
        budget = int(argv[argv.index("--budget") + 1])
    if "--calls" in argv:
        return score_calls(argv[argv.index("--calls") + 1], budget)
    control = load(argv[0])
    treatment = load(argv[1])
    n = min(len(control["prompts"]), len(treatment["prompts"]), len(treatment["evicted"]))
    if n < 10:
        print(f"sim: only {n} turns with both a prompt and an eviction record — not scoreable")
        return 2

    rows = []
    for t in range(n):
        unc = control["prompts"][t]
        obs = treatment["evicted"][t]
        pred = max(0, unc - budget)
        shown = treatment["prompts"][t]
        rows.append({"t": t, "unconstrained": unc, "observed": obs, "predicted": pred,
                     "shown": shown, "residual": pred - obs})

    onset_obs = next((r["t"] for r in rows if r["observed"] > 0), None)
    onset_pred = next((r["t"] for r in rows if r["predicted"] > 0), None)
    engaged = [r for r in rows if r["observed"] > 0]
    errs = [abs(r["residual"]) / r["observed"] for r in engaged if r["observed"]]
    median_err = statistics.median(errs) if errs else 0.0

    print(f"sim: {n} turns, budget {budget:,}")
    print(f"sim: onset observed {onset_obs}, predicted {onset_pred} "
          f"({'MATCH' if onset_obs == onset_pred else 'MISMATCH'})")
    print(f"sim: engaged turns {len(engaged)}, median relative error {median_err:.1%}")
    print("\n  turn  unconstrained  predicted  observed  residual  shown")
    for r in rows:
        if r["observed"] or r["predicted"]:
            print(f"  {r['t']:>4}  {r['unconstrained']:>13,}  {r['predicted']:>9,}  "
                  f"{r['observed']:>8,}  {r['residual']:>+8,}  {r['shown']:>6,}")
    total_pred = sum(r["predicted"] for r in rows)
    total_obs = sum(r["observed"] for r in rows)
    print(f"\nsim: total predicted {total_pred:,}  observed {total_obs:,}  "
          f"ratio {total_pred / total_obs:.3f}" if total_obs else "")
    ok = (onset_obs == onset_pred) and median_err <= 0.10
    print(f"sim: VERDICT {'PASS' if ok else 'FAIL'} "
          f"(onset exact, median error <= 10 %)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
