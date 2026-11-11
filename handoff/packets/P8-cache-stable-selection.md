# PACKET P8 — cache-stable selection

STATUS: answered 2026-11-11 (card RR-P8CACHE-20261111.md; ranking adopted, w/r = 10).

## Question

**Q1.** Given cached input billed at roughly a tenth of uncached, is there a page-selection strategy
that bounds residency **without forfeiting the provider's prefix cache**? Rank these and say what each
costs: (a) reselect only when the resident set changes, never per call; (b) select once and hold the
set; (c) keep the head byte-identical and mutate only near the tail; (d) abandon selection on any
cache-billed provider.

**Q2.** If the answer is (c) or "not with this structure", should the primary metric move from tokens to
dollars? They agree on this result but would diverge under a cache-stable policy. The token ratio is
pre-registered; changing it after a negative result is the move we would call fishing in someone else.

**Q3.** We hold 2 of 48 cells and $1.36 of a $25 cap. The open question is engine structure, not arm
behaviour. Abandon the grid for a re-preregistered single-cell test of (a)/(c), or keep it as a
measurement of the current engine, which is already known to forfeit the cache?

## Evidence

First counted pair, one task, surface `file`, one gateway, both cells complete:

```
            calls   input        cache-read   cache-write   peak     cost
control        5    336,358        227,410      108,933    59,793   $0.0175
treatment     14  1,057,053         83,042      973,969    65,488   $0.1264
```

`NTR = -2.14`: 3.14× input tokens, 7.2× dollars. Both artefacts are correct and identical after
parsing, so accuracy is not the difference. The treatment selects a page set on **every** call, so the
request prefix changes every call and the prefix cache — which hits on the longest common prefix —
misses from the first changed page onward. Cache reads fell to a third; writes rose ninefold.

Break-even from the naive receipt: a perfectly stable arm ties control only below **57,250** tokens per
call at 14 calls (94,053 at 5; 45,405 at 20). The measured paged prefix was 65,488 — caching alone
would still have lost. At 24,000 the cell would cost 42% of control. The engine currently makes the
prefix larger: the protected floor exceeds the budget, so selection removes nothing and adds churn.

## Constraints

Fixed: corpus, task, surface, model row, budget gate. The engine is ours and may
change. We publish no cost-saving claim and will state none from these data. Arm attribution is
runner-side, not in-capture: a plugin in the shared plugins directory is one module for every profile,
so the arms are separated by the profile each was invoked with and by nothing inside the trace.

## Output wanted

- **Q1:** a ranked candidate and its falsifier — a run where the common prefix stays maximal and the
  dollar ratio is still worse than control kills that candidate.
- **Q2:** a rule for when a pre-registered metric may be replaced, stated so it would also bind a
  result we liked.
- **Q3:** one instruction. Mark UNKNOWN what the packet cannot decide.
