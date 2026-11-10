# RR-W8NOOPBYTES-20261110 — C2: does a no-op selection preserve the request?

Zero spend, local test. File: `packages/hermes/test/test_context_engine.py`,
class `NoOpByteIdentityTests`. Run:

```
python3 -m pytest packages/hermes/test/test_context_engine.py -q   ->  28 passed
```

## The three cases

1. **Floor above the budget** (`v_budget=1,000`, ten 20 kB results). `_plan` returns early; the
   serialised request is compared byte for byte against its pre-call form.
2. **Request far under budget** (`v_budget=10,000,000`, two small results). Same comparison.
3. **Eviction actually happens** (`v_budget=60,000`, twelve 40 kB results): the system message must be
   the same bytes it was, and every kept message must appear in transcript order.

## What it found

All three pass. Two details matter:

- **The engine can return a list when it drops nothing.** `select_context` returns `None` only when
  `not dropped and not repositioned`; a pinned page makes `repositioned` non-empty even at zero
  evictions, so it returns a freshly assembled list. In both no-op cases the assembled list is
  **byte-identical** to the input (`json.dumps(..., sort_keys=True)` equal), which is the property the
  cache depends on. The docstring's "returns None whenever nothing must be dropped" is therefore
  narrower than the code: nothing is dropped, but a pinned page is repositioned into its block.
- **Nothing is mutated in place.** The input list is unchanged after the call in all three cases.

## Verdict

**A no-op preserves the request in unit conditions, by deep equality and by serialised bytes.** The
engine's message list is not the source of the cache writes. C1 must explain them another way — and it
does not, which is recorded there as UNKNOWN.

## Why this matters for the decision

The reviewer's hypothesis H1 (engine rewrite) was the strongest available explanation for 47 k written
tokens per call. It is now excluded at the unit level and unsupported at the capture level (append-only
request series, constant system prompt). No engine fix is indicated by this evidence.

## Proposal (card only, not applied)

The `None`-versus-list distinction is load-bearing for the host and for `engineSelections`, which
counts calls rather than rewrites. A one-line card: when `repositioned` is non-empty but the assembled
list equals the input, return `None`. That would make "did the engine change the request?" answerable
from the count, which it currently is not.
