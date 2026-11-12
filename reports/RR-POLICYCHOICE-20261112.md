# RR-POLICYCHOICE-20261112 — the next policy choice, priced from the paid pair: the negative is about
## the REWRITE, not the eviction; a cache-stable policy's ceiling is ≈ $0.009 (12 % of the control), so
## the only place a materially bigger effect lives is a shape whose content is NOT cached

Card: the review side's analysis of the **next policy choice**, computed from the paid pair's measured
counters (`reports/RR-PAIDRESULT-20261112.md`) — not projected, and not a design proposal. Nothing is
spent ✓.

## 1. What the paid pair settled, precisely

| | control | paged |
|---|---|---|
| transmitted (read + write) | 4,576,885 | 3,682,071 |
| cache_read | 4,348,503 | 2,656,246 |
| cache_write | 228,382 | **1,025,825** (4.49×) |
| dollars (provider) | $0.0748 | $0.1580 (**2.11×**) |
| session tokens (residency) | 1,112,533 | 910,814 (**0.82×**) |

- **Content never sent by the paged arm: 894,814 tokens** ✓
- **Content re-sent by it (the rewritten middle): 797,443 tokens** ✓ — **0.89× the unsent content** ✓,
  i.e. the policy *re-transmitted almost as much as it saved* ✓✓.

**So the negative is about the REWRITE, not the eviction** ✓: eviction works ✓ (the request is held at
the budget ✓, 0.57× the final request ✓), and the *token* claim survives ✓ (0.82× ✓) — what fails is the
*dollar* claim ✓, because the saving is priced at the **read** rate and the rewrite at the **write** rate.

## 2. The decisive constant, and the dollar-optimal policy

At the measured rates, **a cache write costs 13× a cache read** ($0.13/M vs $0.01/M ✓). So:

| | tokens | dollars |
|---|---|---|
| the saving (unsent content, priced as it would have been read) | 894,814 | **$0.0089** |
| the tax (the rewritten middle, priced as writes) | 797,443 | **$0.1037** = **11.6× the saving** |

⇒ **The dollar-optimal policy for a caching provider is: send less, and never change what you already
sent** ✓ — the token saving is real ✓, but it is worth ~$0.009, while *changing the prefix* costs 11.6×
that ✓.

## 3. The candidates, priced

**(a) Cache-stable selection** (evict so that the request's prefix stays intact ✓ — the P8 subject ✓) or
its simpler sibling **(b) the watermark / drop-once-hold** ✓ (drop a page once and keep it out ✓). These
are the **same mechanism** with different triggers ✓: *the evicted set must stop changing* ✓. Priced:
the **first** eviction still invalidates the prefix once (≈ one whole request, 60–105k tokens ≈
**$0.008–0.013** ✓), and thereafter the prefix is stable ✓ → the extra writes ≈ one request ✓ → the net
≈ **−$0.009 ± $0.010** ✓ — i.e. **a tie, inside the noise of one pair** ✓✓. That is exactly the
owner's own reading ("a watermark policy would at best tie at this session length") ✓, and the arithmetic
now says it with measured constants ✓.
> **Design requirement, computable now:** the extra cache-write volume must stay under ≈ **0.13 M tokens
> per session** (≈ **3.2 k per engaged call** ✓) — **an eighth** of what the current policy writes
> (26.6 k per engaged call ✓).

**(c) Stop and publish the negative** ✓ — the claim is now measured (2.11× ✓), attributable (the write
volume ✓) and scoped (this shape, model, budget ✓).

**(d) A different shape — the only place with a materially bigger effect** ✓. The dollar saving is bounded
by the *cached* share of the content ✓: the same 894,814 unsent tokens, priced at the **input** rate
instead of the read rate, are worth ≈ **$0.089** ✓ ≈ 1.2× the control's cost ✓ — a real effect ✓✓. That
is a shape where the content is **not cached** (a cold prefix, or a provider without prefix caching ✓),
and under the W8 reopen's rule it is a **fresh preregistration**, not a continuation ✓.

## 4. The test frame that follows from the arithmetic

- **A paid confirmation of the cache-stable policy is not worth buying** ✓: its whole effect is
  ≈ **$0.009** per session — **3.5 % of the pair's $0.2534 spend** ✓ — and one pair's noise exceeds it
  ✓. The owner's ruling ("one paid pair, then stop") ✓ is therefore *doubly* right ✓.
- **The right test is zero-spend** ✓ (the free tier, or the simulator ✓) with the **cache-write volume
  as the primary metric** ✓ — not the token ratio ✓, because the tokens are not what costs ✓.
- **The simulator can now be scored** ✓: the paid pair measured the constants it lacked ✓ — the write
  cost per re-drop (≈ 26.6 k tokens per engaged call ✓) and the rates ✓ — which is exactly the
  prerequisite the owner's condition named ("the simulator needs scaffold tokens recorded per request
  first", `reports/RR-W8SIM-20261111.md`) ✓.
- **And the two metrics must stay apart in the books** ✓: the *token* claim (0.82× ✓) and the *dollar*
  claim (2.11× against ✓) are different claims ✓ (law 7 ✓) — "paging sends fewer tokens and costs more
  on a caching provider, at this shape" ✓ is the sentence the evidence supports ✓.

## 5. What would falsify each candidate (so the next card is preregisterable)

- **cache-stable / watermark**: falsified if the extra write volume exceeds **0.13 M tokens per session**
  ✓ (≈ 3.2 k per engaged call ✓) — i.e. if the prefix still changes after the first eviction ✓.
- **a different shape (uncached content)**: falsified if the *unsent* volume does not convert to the
  input rate ✓ — i.e. if the provider still serves the content from cache ✓.
- **stop / publish**: falsified only by a measurement that shows a positive dollar effect at a scoped
  shape ✓ (which is the open door ✓).

## 6. Executed agent-doings

- Every number in this card was **computed from the paid pair's measured counters** ✓ (transmitted, read,
  write, unsent, re-sent ✓) and checked against the provider's own estimates ✓ (the model reproduces
  $0.0760/$0.1631 against $0.0748/$0.1580 ✓ — within 3 % ✓).
- The candidates were priced with those constants ✓, and the design requirement for the cache-stable
  variant was derived (≈ 0.13 M extra write tokens per session ✓ ≈ an eighth of today's ✓).
- The zero-spend route and the simulator's new scorability ✓ were identified, with the prerequisite the
  owner's condition named ✓.
- Kit: this card + LOG row + the day file + the roadmap's W8C pointer. Nothing spent ✓; no design
  proposed as settled ✓ (this is the review side's analysis, for the owner to choose from ✓); nothing
  pushed ✓.
