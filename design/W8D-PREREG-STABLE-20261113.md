# W8D — preregistration: does a cache-stable selection pay? (cold-prefix / hold-once)

Status: **prepared, not started.** Owner decision required before any spend. Written 2026-11-13, after
`RR-W8C-CLOSING-20261113` and its confirmation capture. Under the ratified rule (`reports/W8-SPEND.md`
§Prediction): filled, committed and matched by the verifier, or the cell is not booked.

This is a **new experiment**, not a continuation of W8C. It changes the engine, which is the condition
the owner's ruling names ("no further spend until the engine changes").

## 1. The question, in one measurement

W8C measured the whole current policy: the request is held at the budget and the cache pays for it —
0.57× the final request for **2.11×** the dollars, with **72.2 %** of a $0.2534 bill being cache writes.

The question this experiment asks is not "is that true" (it is measured) but: **over what range of
rewrite behaviour does holding the budget pay at all?** The arithmetic below answers it without spending
anything, and it is why the experiment has a falsifier rather than an opinion.

## 2. The arithmetic that gates it (recomputed from cell-03, no new data)

```
unsent content          203,975 tokens        the net request reduction, cell-03
priced at input rate    $0.0204 – $0.0265    at $0.10–0.13 / 1M
measured cost excess    $0.0832              paged $0.1580 − control $0.0748
=> paging pays:         NO                   the rewrite costs 3.1–4.1× the value of what it saves

write volume, measured  16,762 tokens per pair call   (1,408,011 over 84 calls, billed)
rewrite budget allowed  $0.0204–0.0265 → 1,868–2,428 write tokens per call
=> required reduction   ≈ 7–9× in write tokens per call, at this shape
```

So the sign can flip only if the policy stops rewriting the prefix on every turn. That is a property of
the *selection policy*, not of the provider — which is why "try a provider without caching" is the wrong
next experiment: it changes the price of the same mistake.

## 3. The proposed change (one behaviour, not a redesign)

**Hold-once selection**: when a page is evicted it stays evicted for the session; the dropped set is
stable, so the prefix stops changing between turns except when a new page is evicted.

```
today    every turn recomputes the eligible middle and drops it again → a new prefix every turn
hold     the dropped set is monotone within a session; prefix changes only when a page leaves for good
```

Nothing else changes: same keep law (system + first three + last six), same budget, same page granularity,
same report surface. The option is a setting (`selection_mode: hold`), so the current behaviour stays
reproducible and the two cells above remain comparable with each other.

## 4. Predictions — every quantity names its unit

| # | quantity | unit | measured against | predicted | bracket |
|---|---|---|---|---|---|
| H1 | rewrite events | count (turns where the dropped set changes) | `_selections.log` | 9–14 | 5–20 |
| H2 | write tokens per call | tokens (`cache_write` ÷ calls) | provider export | 2,200 | 1,500–3,500 |
| H3 | cost, paged arm | USD (gateway estimate, and the account delta) | run | 0.085 | 0.06–0.12 |
| H4 | dollar ratio | ratio (paged ÷ control), same control as cell-03 | 0.0748 | 1.15 | 0.95–1.60 |
| H5 | final request ratio | ratio (paged ÷ control at turn 19) | both captures | 0.62 | 0.50–0.75 |
| H6 | evicted tokens | tokens (`turn.render.evictedTokens` sum) | trace | 210,000 | 120,000–300,000 |
| H7 | artefact | verdict | `tools/w8-checker-ta.py` | PASS parsed-equal | PASS / FAIL |

The falsifier is **H4**: if the dollar ratio stays at or above 1.6 with write volume above 3,500 tokens
per call, hold-once does not fix the trade and the honest conclusion is that a page-granular clamp cannot
pay at this shape — a publishable negative, not a failure to hide.

## 5. The zero-spend gate, before any money

The simulator is now validated at the granularity the policy decides at (`RR-W8SIM3`, S3: page-granular
bound, both readings on record). So:

```
step 1  replay cell-03's `_selections.log` under hold semantics and count rewrite events (H1)
        expected 9–14 out of 41 entries; if it is above 20, the change does not buy what H2 assumes
step 2  price the predicted write volume at the rates above and compare against the measured excess
        if the predicted ratio is above 1.6, STOP — do not run a paid pair to learn what arithmetic says
step 3  only if steps 1-2 pass: one paid pair, ceiling stated below
```

Step 1 and 2 cost nothing and are the reason this document exists before the code.

## 6. Ceilings and preconditions for the paid pair (only if steps 1–2 pass)

```
calls        50 per arm, enforced by tools/w8-driver.py --max-calls (worst case ~$0.26/arm at the
             measured $0.00259 per request; the $1.00 ceiling is a backstop, not the control)
USD          1.00 per pair, owner-gated; the account delta is read afterwards, one credential
budget       60000, unchanged from cell-03 so the comparison is like-for-like
subject      openai/gpt-6-luna via nous, unchanged
instrument   the next plugin version, verified in all four arm homes, gateway restarted
before-run   probe --arm both → CONTRAST OK; preflight green; block committed before any call
```

## 7. Claim ceiling

May support: "one pair, this subject, 20 prompts, budget 60,000: hold-once selection produced <x> rewrite
events and <y> write tokens per call, and the paged arm cost <z>× the control."

May not support: any saving (law 7); any claim about a cold-prefix provider (untested here); any
generalisation past this shape; any statement that the policy is "better" — only cheaper or dearer at a
measured ratio.

## 8. What the owner is being asked to decide

```
a  implement hold-once as an option and run the zero-spend gate          cost $0.00
b  if the gate passes, authorise one paid pair under the ceilings above  cost ≤ $1.00
c  or stop the line here, and publish the W8C negative as it stands      cost $0.00
```

Nothing in (a) spends money and nothing in (b) happens without a separate word from the owner.

## 9. The zero-spend gate, computed — and why it says do not spend

Run before writing a line of engine code, from cell-03's own billed write volume and its
`_selections.log`.

```
rewrite events, today          36   (every dropping selection rewrites the prefix)
rewrite events under hold        9   (the dropped set is monotone: it grows, never repeats)
billed writes, today     1,408,011 tokens -> 39,111 per rewrite
hold, scaled by events     352,003 tokens -> 4,191 per call
break-even allowance       1,868-2,428 per call
=> hold reduces writes 4.0x; the sign needs 6.9x.  FAIL by 1.7x.
```

Bounds for completeness: if a rewrite only wrote the newly evicted pages, hold would be 328 tokens per
call (a pass); if it wrote the whole post-rewrite request, 4,362 (a fail by 1.8x). The scaled estimate
(4,191) sits at the conservative end, and it is the only one anchored in a **billed** number rather than
an assumption about cache-write granularity.

## 10. Recommendation to the owner

**Do not authorise the paid pair.** The arithmetic answers the question the pair would ask: a
cache-stable policy of this kind buys a 4× reduction where 7× is needed. Spending up to $1.00 to confirm
a ratio we can already bound is the purchase this line has learned to refuse.

Two honest ways forward, both zero-spend:

```
a  publish the negative as it stands: at this shape a page-granular clamp holds the request at
   0.57x and costs 2.11x, and no cache-stable variant of it reaches break-even
b  change the shape, not the policy: the arithmetic says the sign flips only where the rewritten
   prefix is cheap or absent — a provider without prefix caching, or a session whose content is
   never reused. That is a different experiment with its own preregistration, and it needs a
   provider we have not yet measured.
```

What would reopen (a): a measured write volume per rewrite below ~7,000 tokens (the point at which 9
rewrites × 7,000 ÷ 84 calls lands inside the allowance). That is a *measurement* on a different provider,
not a redesign of this policy.

The falsifier H4 in §4 therefore stands unused: the experiment it was written for is not worth running,
and its being skipped is the result.
