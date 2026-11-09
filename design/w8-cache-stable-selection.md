# W8 — cache-stable selection: the design, and the arithmetic that gates it

Status: proposed 2026-11-09. Source design: research note `ctxvm-cache-stable-prefix-design.md`
(out of tree), derived from Xu et al., arXiv:2606.17016v2, "TokenPilot: Cache-Efficient Context
Management for LLM Agents" (submitted 2026-06-15, revised 2026-08-28). Locator verified at abstract
level; the specific figures quoted by the note ($7.24 → $4.22, cache miss 5.943M → 1.589M) are
**body-level claims and remain UNVERIFIED** until read in the paper.

## 1. What the measurement says

First counted pair, T-A, both arms `-t file`, one gateway, plugin 0.10.10:

```
            calls   input        cache-read   cache-write   peak      reported
naive          5    336,358        227,410      108,933    59,793    $0.0175
paged         14  1,057,053         83,042      973,969    65,488    $0.1264
```

Cost decomposition at Luna rates ($0.10 in, $0.01 cached read, $0.50 out, write billed at input):

```
naive  input $0.0132   implied output ~ 8,662 tok
paged  input $0.0982   implied output ~56,337 tok
```

Two costs, not one: the paged arm rewrote the prefix 14 times, and it also emitted 6.5× the output.

## 2. The arithmetic that decides whether any of this can work

Naive's effective input cost is **13,167 price-units** (cached reads at a tenth, writes at full).
A perfectly cache-stable paged arm writes its prefix once and reads it thereafter, so it ties naive
when `P × (0.10 + 0.01(N−1)) = 13,167`:

| calls N | break-even prefix P |
|---|---|
| 5  | 94,053 |
| 8  | 77,455 |
| 10 | 69,302 |
| **14** | **57,250** |
| 20 | 45,405 |

**The measured paged prefix was 65,488 at 14 calls, so even with perfect caching it would still lose.**
At 24,000 tokens the same cell would cost 42% of naive. Cache stability is necessary and **not
sufficient**: the engine must also make the per-call prefix smaller, and in the measured cell it made
it larger (+5,695 over naive).

That is the same wall as the pilot: the protected floor (system prompt, tool schemas, first 3 and last
6 turns) already exceeds the 24,000 budget, so selection removes nothing and only adds churn.

## 3. The design, accepted in four parts

1. **Canonicalize volatile markers** — timestamps, session ids, cwd, counters replaced by placeholders
   before hashing; cheap and harmless, though it is not what broke the cache here (the selected page
   set did).
2. **Hold the resident set across calls** — emit the same pages in the same order, byte-for-byte,
   until a trigger fires (new page requested, budget overflow, every B-th turn).
3. **Batch-gated eviction** — evict on the B-th turn, not per call; active → completed → evictable;
   single-pass purge, never incremental mutation.
4. **Append-only growth** — history and tool results appended at the tail, never rewritten into
   earlier turns.

Implemented as `selectionMode: stable` with `residentSet`, `lastSelectionHash`, and a per-call
`prefixHash` in the coverage sidecar.

## 4. Acceptance for the one cell that tests it

One change, one cell, naive vs stable — and the cell is only booked if all four hold:

```
1  artefact parsed-equal to the naive artefact
2  per-call prefix <= 24,000 tokens at some point (residency actually reduced; 57,250 is tie, 24,000 is a win)
3  prefixHash unchanged on at least the calls between triggers (the cache is actually preserved)
4  cache-write total below the naive arm's, with cache-read above it
```

If 2 fails, the cell is a **no-op measurement** and must be recorded as one, not as a paging result —
the same rule that retired the pilot.

## 5. What is deliberately not claimed

No cost-saving claim. No statement that paging helps generally. A negative result here would say the
24,000 budget is below the protected floor on this harness, which is a fact about the floor.
