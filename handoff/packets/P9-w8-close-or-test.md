# PACKET P9 — close W8 with a negative result, or buy one mechanism test?

STATUS: OPEN · 2026-11-10 · answer from this packet alone; do not ask for repo access.

## Question

**(A)** Close W8 now with the negative result stated below, or **(B)** spend $2.2–$3.0 on 4–6 paired
cells at budget 60,000 to demonstrate eviction with the artefact unchanged?

One answer, A or B, with a one-line reason. If B, state any condition you would add.

## Evidence

1. **The shape caps the effect.** The keep law protects the system prompt, the first 3 turns and the
   last 6. On a 12-turn session nothing is unprotected until turn 9; the cumulative evictable ceiling
   is 25,404 of 479,076 request tokens — **5.3%**.
2. **A budget cannot fix it.** Eviction requires the budget below floor + middle ≈ 66,600. The
   planned 72,000 evicts zero; 55,000 evicted zero; 24,000 and 28,000 were no-ops (single-turn).
3. **The engine does not rewrite the prefix.** The measured request series is strictly append-only with
   a byte-constant system prompt, and a unit test shows the bytes are unchanged when it does not evict.
4. **The cost is real and unexplained.** 33.5 M cache-write tokens on the day; 46.7 k per call against
   5–9 k of growth. The capture has no per-request cache columns and no scaffold mass, so the cause is
   UNKNOWN.
5. **The cap is smaller than the board says.** ≥ $7.14 billed on one day (819 requests); store estimate
   $9.16 across three; two days have no provider export.
6. **A 10-point non-inferiority gate is unreachable.** With zero failures, the 95% upper bound is 3/n:
   37.5% at n=8, 10% at n=30.

## Constraints

No spend in this packet. Cells are 12 prompts over one session, `-t file`, `agent.max_turns: 12`, a
real seal of parts 01–03, and acceptance is mechanical (CELL / NO-OP / DATA-INVALID). A cell cannot
start without a committed prediction block. No cost-saving claim will be made in any outcome.

## Output wanted

- **A or B**, and why in one line.
- If **B**: the budget (any value other than 60,000 must be justified against the 66,600 threshold), the
  number of pairs, and the exact claim the cells would license.
- Mark UNKNOWN anything this packet cannot decide.
