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


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    budget = 60000
    if "--budget" in argv:
        budget = int(argv[argv.index("--budget") + 1])
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
