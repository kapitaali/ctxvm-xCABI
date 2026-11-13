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
    """S3: the policy drops WHOLE PAGES, so the honest model is a bound, not a point.

    Declared 2026-11-12 after the review lane showed that a 5 % point tolerance is tighter than one
    page (~4,400 of 60,000 ≈ 7.3 %), which made the earlier PASS depend on how many calls fell either
    side of a page boundary.

      predicted   budget - slack  <  after_k  <=  budget
      slack       one page when the capture records `dropped` per call (0.13.14+), so a single-page
                  drop is identifiable: slack = max(before - after | dropped == 1). On older captures
                  it is two minimum-drops, because one drop can overshoot a page by a few tokens.
      PASS        every call inside the interval; the median relative error is reported as a
                  diagnostic and is not the verdict, because it cannot resolve below one page
    """
    side = trace_path.replace(".jsonl", ".coverage.json")
    calls = (json.load(open(side, encoding="utf-8")).get("plugin") or {}).get("callSizes") or []
    if not calls:
        print(f"sim: no callSizes in {side} — nothing to score")
        return 2

    dropping = [c for c in calls if isinstance(c.get("before"), int) and isinstance(c.get("after"), int)
                and c["after"] < c["before"]]
    if not dropping:
        print(f"sim(S3): {len(calls)} selections, none dropped — the budget never bound")
        return 2

    # Page size from the DATA, not from a per-call ratio: consecutive `after` levels differ by one
    # dropped page, so the median gap between sorted distinct levels estimates it without needing the
    # `dropped` count (absent in captures written before 0.13.14).
    # Two modes, chosen by what the capture actually records:
    #   0.13.14+  `dropped` is stored per call, so a ONE-page drop is identifiable and the interval is
    #             exactly one page wide:  budget - page_max < after <= budget
    #   older     no `dropped`, so the smallest observed drop stands in for one page and the interval
    #             widens to two of those, because a single drop can overshoot one page by a few tokens
    #             (measured: call 10 dropped 4,473 while the smallest drop was 4,424, 1.029x).
    one_page = [c["before"] - c["after"] for c in dropping if c.get("dropped") == 1]
    if one_page:
        page_max = int(max(one_page))
        slack = page_max
        basis = "one-page drops (dropped == 1)"
    else:
        page_max = int(min(c["before"] - c["after"] for c in dropping))
        slack = 2 * page_max
        basis = "smallest drop (no per-call dropped count: pre-0.13.14 capture)"
    page_est = page_max
    lo = budget - slack
    outside = [c for c in dropping if not (lo < c["after"] <= budget)]
    errs = [abs(c["after"] - budget) / budget for c in dropping]
    print(f"sim(S3): {len(calls)} selections, {len(dropping)} dropped, budget {budget:,}")
    print(f"sim(S3): page ~{page_est:,} tokens from {basis} -> interval ({lo:,}, {budget:,}]")
    print(f"sim(S3): median |after-budget|/budget {statistics.median(errs):.2%} "
          f"(diagnostic; resolution is one page = {page_est / budget:.1%})")
    if outside:
        # Report the overshoot as a fraction of one page. The verdict stays FAIL: widening the margin
        # until the data passes is the sin the review lane named, so the size of the violation is
        # stated and the bound is left as declared.
        for c in outside[:5]:
            slack_used = budget - c["after"]
            print(f"sim(S3): OUTSIDE before={c['before']:,} after={c['after']:,} "
                  f"dropped={c.get('dropped')} slack={slack_used:,} "
                  f"= {slack_used / page_est:.3f} pages")
    ok = not outside
    print(f"sim(S3): VERDICT {'PASS' if ok else 'FAIL'} "
          f"(every dropped request inside {slack:,} tokens of the budget)")
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
