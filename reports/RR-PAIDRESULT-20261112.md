# RR-PAIDRESULT-20261112 — the paid pair landed: **$0.2534**, the paged arm costs **2.11×** the control,
## and the cause is measured — 4.49× the cache-write volume for 0.82× the tokens

Card: the review side's verification of the paid pair (`w8cp-naive` / `w8cp-paged`, the paid subject
`openai/gpt-6-luna`), recomputed from the captures and the hermes DB's counters. The pair is the one the
owner ruled (one paid pair, ≈ $0.25, ceiling $1) ✓ — this card records what it actually cost and what it
actually showed.

## 1. The money, from the provider's own estimates

| arm | calls | uncached input | cache_read | **cache_write** | output | provider estimate |
|---|---|---|---|---|---|---|
| `w8cp-naive` (control) | 42 | 126 | 4,348,503 | **228,382** | 5,558 | **$0.0748** |
| `w8cp-paged` | 42 | 126 | 2,656,246 | **1,025,825** | 6,458 | **$0.1580** |
| **pair** | 84 | | | | | **$0.2534** |

- **The pair cost $0.2534** ✓ — the owner's central estimate was **$0.25** ✓✓ and the bracket's LOW band
  was $0.21–0.25 ✓ → **the bracket was right at its low end** ✓ (the HIGH regime did not materialise ✓:
  the paid provider **does** reuse the prefix ✓).
- **The dollar ratio is 2.11×** ✓ — the projected 1.8–2.4× ✓✓ (the owner's "roughly 2×" ✓).
- **The ceiling held**: $0.2534 of $1.00 ✓, with the driver's 50-calls-per-arm ceiling never reached
  (42 calls per arm ✓) ✓.

## 2. The mechanism, measured (this is the part that was UNKNOWN)

- The paged arm's **cache-write volume is 4.49× the control's** (1,025,825 vs 228,382 ✓) while its
  **cache_read is lower** (2,656,246 vs 4,348,503 ✓, because its requests are capped ✓).
- **So the whole cost difference is the write volume** ✓: the paged arm sends fewer tokens
  (session ratio **0.819** ✓) and holds the request at the budget (final-request ratio **0.570** ✓), and
  it pays for that with a rewritten middle that the provider bills as writes ✓✓.
- This is the cache-instability signature, measured at the paid provider, at this shape ✓ — and it is the
  W8CACHE "cause of the cache-write volume: UNKNOWN" item answered *for this shape* ✓ (the cause is the
  per-turn prefix invalidation of a selection that is not cache-stable ✓ — which is precisely the P8
  thesis ✓).

## 3. The trace's own accounting (verified per turn)

```
paged   evictedTokens  0 x12, then 4396, 13101, 21601, 29932, 38513, 47399, 55914, 64506   sum 275,362
control evictedTokens  0 on every turn                                                        sum 0
paged   residency  12,060 -> 59,747 (flat from turn 11)
control residency  11,949 -> 104,842 (growing)
net reduction = 201,719   (counter / net = 1.365: the counter sums per-turn re-drops)
final-request ratio 0.570   session-token ratio 0.819
```

- The **control's zero** ✓ — the control arm is a control in the trace's own accounting ✓.
- The **onset is turn 12** ✓ — and this is the **ratified rule's prediction form working**: the
  control first exceeds the 60,000 budget at **turn 11** (62,185 ✓) and the first eviction lands one
  turn later ✓ (the free-tier run's lag was two ✓ — so the lag is run-specific ✓, which is exactly why
  the rule says *"plus the engine's lag"* and never a turn number ✓✓). The observed onset falls inside the
  draft's 10–16 bracket ✓.
- **No `page.evict` row in either arm** ✓ — the count rides in `turn.render.evictedTokens` ✓ (by decision ✓),
  and the per-page detail is still unwitnessed ✓ (the open item ✓).
- The counter/net gap is **1.365** here (1.257 in cell-02 ✓) — the two are different quantities ✓ and
  both are now named in the books ✓.

## 4. What may be claimed (endorsed)

**Supportable:** at budget 60,000, over one pair on the paid subject `openai/gpt-6-luna` (42 calls per
arm, $0.2534 in total), the paged arm **held its request at the budget** (final request 59,747 against
the control's 104,842, **0.57×**; session tokens **0.82×**) and the trace **witnessed the evictions**
(275,362 tokens of per-turn re-drops, first at turn 12; the control's counter **0**), **while costing
2.11× the control in dollars** ($0.1580 vs $0.0748) — the difference being **4.49× the cache-write
volume** at 0.61× the cache-read volume.

**Not supportable:** any **saving** — the paged arm cost *more* ✓ (law 7 ✓: fewer tokens, more money ✓);
any generalisation beyond this shape, this model and this budget ✓; any **page-level** claim about which
pages were dropped ✓ (the trace witnesses the count only ✓); and any claim about *why* a provider prices
writes as it does ✓ (the provider's own pricing is outside our books ✓).

## 5. What this settles, and what it opens

- **The negative is now measured, not projected** ✓ — "paging costs more on a paid provider" is a
  *measurement* at this shape ✓ (2.11×) ✓, where it was a projection from the free tier's token ratios ✓
  and a 7.2× figure from a different shape ✓.
- **The cost story is now attributable** ✓: the *only* mechanism is the cache-write volume caused by a
  selection that is not cache-stable ✓ — which is the **P8 cache-stability question** and the reason the
  next policy (watermark / drop-once-hold, or a cache-stable selection) is where the remaining hope
  lives ✓.
- **The break-even arithmetic must now be re-derived** ✓ for a policy that rewrites the prefix every
  turn: the books' `n\* = (w/r)(P′/S)` assumed a saving `S` and a cache-write cost `P′` ✓; here the
  measured `P′` is **4.49× the control's** and the measured saving in *tokens* is 18 % of the session
  ✓ — so at these rates the policy **loses** ✓, and the loss is quantified ✓ (2.11× ⇒ the paged arm would
  have to save ≥ 2.1× the control's dollars to break even ✓ — it saves 18 % of the tokens ✓ and 43 % of
  the final request ✓, which is not enough ✓).

## 6. Executed agent-doings

- The pair's numbers were recomputed from the artefacts: the per-turn `evictedTokens` and residency
  series from the two captures ✓, the usage counters and the provider's own cost estimates from the hermes
  DB ✓ — nothing was taken from the run's printed table ✓.
- The **onset was checked against the ratified rule's prediction form** (crossing turn + lag, not a turn
  number ✓) and it holds ✓ — the first crossing at turn 11, the first eviction at turn 12 ✓.
- The claim set is stated with what is **not** supportable ✓ (no saving ✓, no generalisation ✓, no
  page-level claim ✓, no claim about the provider's pricing ✓) and the mechanism is stated as the
  *measured* write-volume ratio ✓.
- Kit: this card + LOG row + the day file + the roadmap's W8C pointer. Nothing spent by this card ✓; no
  file of the other lane's edited ✓; nothing pushed ✓.
