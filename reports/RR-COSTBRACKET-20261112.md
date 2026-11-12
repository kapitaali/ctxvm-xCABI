# RR-COSTBRACKET-20261112 — the paid pair's cost bracket, computed from the books: LOW ≈ $0.21, CENTRAL
## ≈ $0.30, HIGH ≈ $0.70 — and the driver's call ceiling that makes the $1 ceiling real

Card: the owner's request — *"about the brackets, give high and low cost estimates"* — answered with the
arithmetic, from the books' own numbers, so the block's bracket is a computation rather than a guess.
Nothing is spent here ✓.

## 1. The inputs, all from the books

| quantity | value | source |
|---|---|---|
| cell-02 control: uncached input / cache_read / output | 224,455 / 4,461,568 / 8,734 | the hermes DB's `sessions` counters (`reports/RR-W8CCELL01-20261111.md` §3) ✓ |
| cell-02 paged: uncached input / cache_read / output | 1,071,090 / 2,870,144 / 6,794 | the same ✓ |
| Luna rates | uncached **$0.10–0.13/1M**, cached read **$0.01/1M**, cache write **~$0.13/1M**, output **$0.50/1M** | the owner's projection, the books' implied rate, and the lane's NOTE ✓ |
| the free tier has **no cache-write row** — writes bill at the input rate | — | `reports/RR-DAY-20261111.md:185` ✓ |
| the earlier paid Luna cell | **$0.1827** for **1.35 M cache-write tokens** (≈ **46.7k per call** over ~29 calls ≈ a whole request per call) | `reports/RR-DAY-20261110.md:156` ✓ |
| the earlier paid pair's dollar ratio | **7.2×** dollars for 3.14× tokens | `reports/RR-LESSONS2-20261109.md` ✓ |
| calls planned | 41 (paged) + 42 (control) | cell-02 ✓ |

## 2. The two regimes, and why they differ by 3×

The cost of each arm is **uncached × $0.10–0.13/1M + cache-write × $0.13/1M + cache-read × $0.01/1M +
output × $0.50/1M** ✓, and the *unknown* is how the paid provider splits each arm's tokens into
**writes** and **reads** ✓ — the free tier did not report writes at all ✓, so this shape has no measured
split ✓.

- **Regime LOW (the free-tier proxy):** the control's tokens are cache **reads** (its prefix is stable),
  the paged arm's uncached tokens are written at the input rate.
  control ≈ 224,455 × $0.10–0.13/1M + 4,461,568 × $0.01/1M + 8,734 × $0.50/1M ≈ **$0.071–0.078**;
  paged ≈ 1,071,090 × $0.10–0.13/1M + 2,870,144 × $0.01/1M + 6,794 × $0.50/1M ≈ **$0.139–0.171**
  → **pair ≈ $0.21–0.25**, ratio ≈ **1.9–2.2×** ✓ (the owner's $0.25 and "roughly 2×" ✓).
- **Regime HIGH (the earlier paid-Luna regime: no cache reuse at all, so every request is written
  whole at ~46.7k tokens per call):** the control's request averages ≈ 55k tokens over the session
  (11k → 108k ✓), the paged arm's ≈ 55k too (11k → 64.7k ✓) → 41 calls × ~55k ≈ **2.25 M written tokens
  per arm** ≈ **$0.29 per arm** ≈ **$0.59 for the pair**, plus output and whatever cache reads still
  land → **pair ≈ $0.65–0.70**, and the **ratio collapses toward 1×** (both arms pay for whole requests;
  the paged arm's total token mass is 0.85× the control's ✓).

**So the bracket's LOW and HIGH ends are not "same model, ±20 %":** the LOW end is *a working cache*, the
HIGH end is *no cache reuse*, and the **dollar ratio moves the other way** in them (1.9× at the low end,
≈1× at the high end) — because the ratio is a function of the **write/read split**, not of the token
mass ✓. The historical **7.2×** sits above both ✓ (the first paid pair: the paged arm's tokens were
writes while the control's were reads ✓ — the maximum-ratio case ✓).

**The bracket to write into the block** (a range, not a point):

```
predicted cost      LOW $0.21   CENTRAL $0.30   HIGH $0.70   (pair, both arms)
predicted ratio     1.0x – 2.4x   with the historical precedent at 7.2x (the first paid pair)
```

and, if the owner prefers a single bracket, the honest one is **$0.20–0.70**, with the note that the
*ratio* bracket is **wider than the cost bracket's** in the tail ✓ (the cost is bounded by the call
ceiling ✓, the ratio is not ✓).

## 3. The call ceiling that makes $1 real

The provider's export is **per day**, so the driver cannot read spend mid-run ✓ → the **call ceiling is
the only live bound** ✓ and the $1 is a backstop ✓.

At the HIGH regime, ≈ $0.0084 per call (≈ 55k written × $0.13/1M + the rest) → **$1.00 ÷ $0.0084 ≈ 119
calls** for the pair. The planned pair is **83 calls** (41 + 42 ✓), and the control arm has already
timed out twice on prompt 20 ✓ (120 s, 180 s ✓ — each retry is another billed request ✓). So:

```
driver ceiling      100 calls for the PAIR (i.e. ~50 per arm), enforced before prompt 1
worst case          100 x $0.0084 = $0.84  -> inside the $1 ceiling
planned             83 calls  -> $0.60-0.70 at the high regime, $0.21-0.25 at the low regime
```

**Recommendation:** the driver enforces **100 calls for the pair** ✓ and the block states that ceiling ✓
and that it is what bounds the spend ✓ (the dollar ceiling being the backstop ✓).

## 4. What this bracket does NOT cover (stated so the block does not imply it)

- **The paid model's token mass.** The arithmetic assumes the paid subject's per-turn token mass is
  within ~±20 % of longcat's ✓; a heavier model scales the *write* term linearly ✓ and moves the pair
  toward the HIGH end ✓ (and a heavier model also raises the **floor** ✓ — the block's own NO-OP branch ✓).
- **The write/read split is UNMEASURED for this shape** ✓ — the bracket spans the two regimes instead of
  pretending to know ✓; the paid run's own split is the measurement ✓, and it is the number the next
  card should predict from ✓.
- **A retry storm.** The $1 backstop covers it only if the call ceiling is enforced ✓ — hence condition 3
  ✓.

## 5. Executed agent-doings

- The bracket was computed from the books' numbers (the DB's usage counters ✓, the implied Luna rates ✓,
  the earlier paid cell's $0.1827 / 1.35 M cache-write tokens ✓, the 7.2× precedent ✓, cell-02's call
  counts ✓) and the two regimes were separated with their arithmetic shown ✓.
- The **call ceiling** was derived from the HIGH regime's per-call cost ✓ and checked against the planned
  83 calls ✓ and the known timeout retries ✓ → **100 calls for the pair** ✓.
- The bracket is offered as a **range with its two regimes named** ✓, not as a point ✓, and the review
  side states what it does not cover ✓.
- Kit: this card + LOG row + the day file + the roadmap's next-cue line; the owner's **ratified** rule is
  now in the rule's home (`reports/W8-SPEND.md` §Prediction ✓) in its own commit ✓. Nothing spent ✓;
  nothing pushed ✓.
