# RR-W8BCLOSURE-20261111 — the W8B closure is a PROPER negative (this lane's harness-limit caveat is
## superseded), with one mechanism correction checked against the code, and the next owner decision is
## W8C

Card: the review side's reading of the other lane's W8B closure (`163787a`, card
`design/W8B-CLOSURE-20261111.md`; run cards `e2c7f7b`/`reports/RR-W8B2-RUN3-20261111.md`; the
preregistered block `reports/W8B-BLOCK-CELL02-20261111.md`; the successor plan `c466eb7`
`design/W8C-PLAN.md`). All of it is read at its **committed** bytes.

## 1. What they measured (their closure, verbatim substance)

| budget | paged | naive | verdict |
|---|---|---|---|
| 70,000 | 41 calls, 43 selections, **0 evictions**, parsed-equal artefact | — | NO-OP |
| 90,000 | 41 calls, 43 selections, **0 evictions**, parsed-equal artefact | 41 calls, 0 selections, 0 evictions | NO-OP |

At 90,000 the arms are the same arm *in effect*: per-turn requests within 1 % of each other
(10,481 → 103,262 naive vs 11,030 → 102,204 paged) and provider receipts within 0.2 % (input 181,963
vs 181,632; cached 2,132,608 vs 2,143,872). With zero evictions the engine returns `None` on every
call, so the request is unchanged — the receipts confirm the law rather than the absence of a
treatment. Residency peaks at 102–104 k; the two budgets bracket the protected floor at 90–104 k, so
any budget that could bite leaves at most ~14 k tokens on the last two turns of a 20-turn session (~7 %
of session input, once the session is nearly over).

**The cause, located in the policy rather than the budget**: 21 distinct pages declared, **19 fault**
(every part demanded again after its first declaration). The keep law protects the head (3 turns), the
recency tail (6 turns) and every pinned page; 19 of 21 pinned ⇒ the pinned block alone meets the
budget ⇒ `_plan` returns early on every selection (by design, L5).

**Cost:** $0.00 (both subjects free-tier). **Cells booked: none** — five voids, then two NO-OPs.

## 2. This lane's earlier caveat is SUPERSEDED — and it was the right caveat to write down

This lane recorded on 2026-11-11 (`reports/RR-W8BCONTRAST-20261111.md`) that a **no-contrast** run is a
harness limit and not a result, and that a closure on that ground must claim nothing in either
direction. That caveat applied to the state at the time (`57918fd`: both arms were the same arm). It is
**no longer the case**, and the difference is exactly what the books demanded:

- the instrument **engages** — 43 selections on the paged arm at both budgets, and the control arm
  reports 0 selections under its own profile (`w8bn-naive`, budget 200000/default), so the sidecar
  cannot report the treatment's numbers for the control arm (their per-profile counters);
- the arms **differ by profile and budget** (the contrast probe answers `CONTRAST OK` / `CONTROL OK` /
  `READY`), and the substantive outcome is confirmed **provider-side** (the receipts) and
  **capture-side** (19 `page.fault` events), not by the sidecar's label.

So the closure is a **negative result about this policy on this shape**, and the wording they used
("This is a statement about this policy on this shape. It is not a general result about paging, and it
says nothing about the external controller in arXiv:2610.22732v1") is the correct scope. That sentence
must not be softened upward into a general claim about paging, and must not be borrowed downward as one.

## 3. The negative was PREREGISTERED — the strongest form available here

`reports/W8B-BLOCK-CELL02-20261111.md` (committed before the run, as the rule requires) did not merely
predict evictions at turns 18–19 (~5,200 and ~14,000 tokens); it **pre-registered the reading of a
zero-eviction outcome**:

> "If the verifier shows `evictions == 0` again, the floor is above 90,000 too — that would be a second
> measured data point pointing at (c) in `RR-W8B2-RUN2-20261111.md` §Options (the policy cannot tell a
> page the model needs from one the harness re-sent), **not a reason to raise the budget again**."

That is why the outcome is bookable as a finding rather than as an instrument bug: the block said in
advance what a zero would mean, and the run produced a zero. (The block's generic verdict line —
"a mismatch means the instrument is wrong" — is a *rule of the instrument*, and it was discharged
separately: the engine engaged 43 times, so the zero evictions were the policy's decision, not a
broken instrument. The two must be kept apart in the ledger: a prediction error about a policy is not
an instrument bug. Their run card makes that distinction for the reader — the runner's own table called
the arm VOID because the verifier was handed 70,000 while the run used 90,000, a plumbing bug that was
fixed and re-verified offline against the same capture.)

## 4. ONE mechanism correction, checked against the code

The closure's explanatory sentence reads:

> "In a read-once workflow the harness re-sends every tool result on every call; the policy reads that
> re-send as a demand and pins the page. **'Pin on re-demand' is equivalent to 'pin nearly everything'
> when the harness is the one re-demanding.**"

**The code does not do that, and the correction matters for W8C's implementation.** Two facts in
`packages/hermes/live/context_engine.py`:

1. **Tool-result bodies are not a demand surface at all.** `_demand_text` (`:151-165`) returns `""` for
   `role in ("tool", "system")` — by design, and the docstring says why ("a tool result demanding
   another page's path would let the harness write infer demand"). A re-sent tool result therefore
   **cannot** be a demand, let alone a second one.
2. **Identical text is credited once.** `_credit_demand` (`:508-511`) skips any message whose text
   digest is already in `_credited_texts`. So even on the eligible surfaces a *verbatim* re-send is not
   a second demand.

What actually pins a page is **new prose that names it**: the assistant's own text and its tool-call
argument payloads (both eligible surfaces) and the user's prose — e.g. the model's answer "part-01.txt
is 16,602 bytes" is demand one, and the next prompt's prose naming the file again is demand two, at
which point `_ensure_pinned` fires (`:513-521`). Their **W8C plan states this correctly** ("a demand is
a `pre_tool_call` for a `logicalRef` already declared in an earlier turn … Prose pins nothing; a
re-sent tool result pins nothing"), so the successor design is unaffected.

Why the correction is worth writing down: the closure's sentence would send the next implementer to
change the wrong thing (the tool-result re-send) instead of the right one (prose naming a page). The
closure's *conclusion* survives and sharpens — the policy cannot tell "the model needs this page
again" from "somebody mentioned the file again" — but the sentence as written attributes the pinning
to a mechanism that the code explicitly excludes. This is recorded here as a review-side note; their
cards are theirs to amend.

## 5. The ledger's honest reading, and the two ceilings that must not be conflated

- **No cell is booked.** Five voids, then two NO-OPs, $0.00. The record therefore holds a **negative
  cause**, not a counted result — the W8B chapter closes as "no cell; the policy's demand signal was
  located". No cost-saving claim is available (law 7): the free tier has no cache price to break even
  against, and with **zero** evictions there is nothing to save at this shape at all. The paid
  break-even (n\* ≈ 10 × (98,934 / 28,934) ≈ **34 calls** against the 41 measured, P8's arithmetic)
  stays on record but does not apply to a policy that evicts nothing here.
- **Two different ceilings.** W8's scoped sentence — "no policy can save more than 5.3 %" — holds only
  for policies that keep the first three turns, the last six and the system prompt
  (`reports/RR-W8SIM-20261110.md`). W8B's finding is a *different* number about a *different* policy on a
  *different* shape: at a read-once shape, **this** policy's evictable share is ~0, because the demand
  signal pins nearly every page before the budget can bite. 5.3 % is not W8B's ceiling and must not be
  quoted as if it were; and W8B's ~0 is not a general statement about paging.

## 6. The residual attribution risk stands (this lane's `reports/RR-W8BARMSTATE-20261111.md`)

The arm fields are **still** written into the tracer's process-global state — `st["serving_profile"]`,
`st["budget_tokens"]`, `st["budget_source"]`, `st["arm"]`, `st["engine_setting"]`
(`packages/hermes/live/__init__.py:1173-1177`) — and read back at flush time (`:646-650`); there is no
per-session keying. Their counters moved to **per profile** (`context_engine.py:307, 390, 412`), not per
session, so the cross-session window my card named is unchanged for two sessions of one profile (a
control sidecar cannot report the treatment's numbers ✓, but a *concurrent* session of the same profile
could still overwrite the arm fields between an arm session's hook and its flush).

**The closure does not depend on this**: its evidence is provider-side (receipts), engine-side (43
selections that returned `None`) and capture-side (19 `page.fault` events). It remains a known
limitation for any future run that interleaves sessions — and the fix is still one dict
(`state["arms"][session_id]`).

## 7. The next owner decision: W8C (`design/W8C-PLAN.md`, `c466eb7`)

The plan is **proposed; owner approval is required before any instrument change**, and it is a
*different question* from W8's: not "does paging save tokens" but **"does the keep law have purchase
once the fault signal means what it claims to mean?"** Concretely: demand becomes an explicit
`pre_tool_call` for a `logicalRef` declared in an earlier turn; prose pins nothing and a re-sent tool
result pins nothing; everything else (keep law, budget mechanism, the seven laws, task, fixture) stays.
Its own falsifier is stated: **with the new signal and a budget sized from the measured floor, the
paged arm still evicts zero tokens ⇒ the floor, not the signal, is the binding constraint**, and the
next question becomes head/tail protection rather than paging. Their floor estimate without pins is
~48,650 tokens with residency passing 60,000 on turns 14–19, so the candidate budget is 60,000 — but
the block "will be written from a measured floor, not from that estimate".

The plan asks for two owner checkpoints, four tests, one pair and no money.

## 8. Executed agent-doings

- The closure, the run cards, the prediction block and the successor plan were read at their **committed**
  bytes (`163787a`, `e2c7f7b`, `c466eb7`), not from the working tree.
- The mechanism was checked against the code (`_demand_text` `:151-165`; `_credit_demand` `:495-521`;
  the digest set `:508-511`) before any correction was written, and the correction was compared with
  the successor plan's own description, which is already right.
- The closure was checked against this lane's earlier caveat (superseded), against the preregistration
  rule in `reports/W8-SPEND.md` §Prediction, and against law 7 (no cost claim).
- Kit: this card + LOG row + a day-file line + the roadmap's W8B/W8C pointers + the owner's next-cue
  list. No file of the other lane's was edited; no spec, schema, corpus, vector or umpire byte changed;
  nothing pushed.
