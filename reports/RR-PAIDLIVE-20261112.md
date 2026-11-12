# RR-PAIDLIVE-20261112 — the paid pair is running and the spend is inside the bracket, at its LOW end:
## the write/read split — the unknown the bracket spanned — is being measured, and the cache is working

Card: the owner started the paid pair ("we are running it now"), and this lane watches the spend against
the bracket it computed (`reports/RR-COSTBRACKET-20261112.md`). **Nothing is spent by this card** ✓ — it
is a live reading of the run in progress.

## 1. The run, as it stands (read from the hermes DB's own counters, 2026-11-12)

The pair runs on **new profiles** `w8cp-naive` / `w8cp-paged` with the **paid subject**
`openai/gpt-6-luna` ✓ (the free-tier subject was `meituan/longcat-2.5:free` ✓).

| arm | calls | uncached input | cache_read | **cache_write** | output | provider's own estimate |
|---|---|---|---|---|---|---|
| `w8cp-naive` | 42 (main) / 49 (profile) | 147 | 4,406,801 | **299,803** | 5,723 | **$0.0748** |
| `w8cp-paged` | 23 (main, **running**) / 30 | 90 | 1,427,826 | **219,557** | 2,043 | **$0.0318** |
| **pair so far** | | | | | | **$0.1272** (plus the probe/diagnostic sessions) |

**The ceiling is live** ✓ — the driver enforces **50 calls per arm** (`tools/w8b-run.py`: `max_calls: 50`
→ `--max-calls`), and the control arm stopped at **42 calls on its own** ✓ (not on the ceiling ✓), with the
paged arm at 23 of its planned 41 ✓.

## 2. The bracket's unknown is being measured — and it is resolving into the LOW regime

The bracket's two ends were "a working cache" (LOW) and "no cache reuse" (HIGH) ✓, because the paid
provider's **write/read split** for this shape was unmeasured ✓. It is being measured now:

- **the naive arm: reads:writes = 14.7 : 1** → the cache is working ✓;
- **the paged arm so far: 6.5 : 1** → still read-dominated ✓ but *less* so ✓ — the signature of a prefix
  being rewritten more often ✓ (exactly what the paged arm does ✓).

So the paid provider **does** reuse the prefix ✓ → the **LOW regime** is the live one ✓, and the pair is
tracking **at or below the LOW estimate ($0.21–0.25)** ✓ — on the provider's own numbers, ≈ $0.13–0.15
projected for the pair ✓ (the control is finished at $0.0748 ✓; the paged arm is at 23 of ~41 calls and
$0.0318 ✓).

**A caution on the projection** ✓: the paged arm's later turns carry *larger* requests and *more*
rewrites ✓ (its request grows to ~64 k and its per-turn re-drops rise to ~43 k ✓), so the run-time share
will grow faster than linearly ✓ — the projected pair could still land higher than $0.15 ✓; the
**50-call ceiling** is what bounds it ✓ (worst case ≈ $0.84 for 100 calls ✓).

## 3. A by-product worth recording: this lane's rate model is validated against the provider's estimate

The bracket's arithmetic used the catalogue rates (uncached $0.10–0.13/1M, read $0.01/1M, write
~$0.13/1M, output $0.50/1M). Against the provider's own estimates for the live run:

| arm | this lane's rate model | the provider's estimate | gap |
|---|---|---|---|
| naive (42 calls) | $0.0859 | $0.0748 | **+15 %** |
| paged (23 calls, partial) | $0.0439 | $0.0318 | **+38 %** (and the run is incomplete ✓) |

**So the model is within ~15 % on the finished arm** ✓ — i.e. the catalogue rates are close to what the
provider actually charges here ✓, which means the bracket's arithmetic was not a coincidence ✓ and the
HIGH estimate (≈ $0.70) was, if anything, conservative ✓.

## 4. What the review side will do with the result

When the pair lands, the verification is the one this lane has been running since cell-01 ✓: the request
series per turn (the naive arm's residency is the *unconstrained* request the paged arm would have sent
✓), the trace's `evictedTokens` counter (per-turn re-drops ✓) against the **net reduction** (the claim's
figure ✓), the control's zero ✓, and — the number this card is really about — the **write/read split and
the dollar ratio**, measured rather than projected ✓ (which is what the owner wanted the pair for ✓:
"turns it from projected to measured" ✓).

**And the standing limit, unchanged** ✓: whatever the ratio is, **no saving may be claimed** unless the
paged arm is *cheaper* on the paid provider ✓ (law 7 ✓), and the claim stays scoped to this shape, this
model and this budget ✓ — "first counted cell" does not become a general claim ✓.

## 5. Executed agent-doings

- The live spend was read from the hermes DB's own counters (calls, uncached input, cache_read,
  **cache_write**, output, the provider's `estimated_cost_usd`) for both arms ✓, and the driver's call
  ceiling was located in the committed tool ✓ (`max_calls: 50` → `--max-calls` ✓).
- The bracket's unknown (the write/read split) was checked against the live numbers ✓ and the regime
  identified ✓; the pair's trajectory against the bracket was stated with the caution that the paged
  arm's share grows faster than linearly ✓.
- The rate model was validated against the provider's own estimate on the finished arm ✓ (+15 % ✓).
- Kit: this card + the LOG row + the day file. Nothing spent by this card ✓; nothing pushed ✓; no file of
  the other lane's edited ✓.
