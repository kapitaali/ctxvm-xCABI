# RR-W8CREVIEW-20261111 — review of the W8C plan before the owner's checkpoint: the re-read pin
## already exists in the engine, so the plan needs a falsification set and a stated margin over the
## measured floor

Card: the review side's reading of `design/W8C-PLAN.md` (the other lane's `c466eb7`), before the owner's
first checkpoint. Read at the committed bytes; the engine claims checked at
`packages/hermes/live/context_engine.py`.

## 1. The plan's delta, as stated

> today — demand = a new message text that mentions a page's identifier token (model prose counts, the
> harness re-sending the tool result does not)
> W8C — demand = the model issues a NEW tool call for a logicalRef that was already declared in an EARLIER
> turn

Two things are proposed to change: the **text signal is removed** (`_credit_demand` stops pinning, "not
merely weakened"), and a **new explicit call** `engine.note_refault(logical_ref)` is added, fed by
`pre_tool_call` observations. Everything else — the keep law, the budget mechanism, selection as a pure
function of (page-table state, vBudget), the seven laws, the artefact, the fixture, the pair design —
stays. The signal is available where the plugin already stands (`pre_tool_call` sees every tool call with
its arguments).

## 2. The check that changes the plan's framing: the re-read pin ALREADY exists

The engine has a **second, independent** demand source, and it already implements "pin on a
model-initiated re-read". In `_update_page_state` (`context_engine.py:459-495`):

- a page's **first render** is demand 1 (`:472-478`);
- **the same key arriving on a NEW result message** — i.e. a re-read — is "one more demand", and at
  `demand_count >= 2` it calls `_ensure_pinned` (`:479-488`, deduped per (key, result position) so a
  per-request re-observation cannot double-credit).

So on today's engine, a model that reads the same file twice pins that file — **through the re-render
path, not through prose**. That is exactly W8C's headline rule. W8B's sessions never exercised it
(each file was read exactly once), which is why the mass pinning there came from the text signal alone.

What W8C therefore adds, precisely:

| | today | W8C |
|---|---|---|
| re-read (same file, later turn) | pins at the re-render (result time) | pins at the **tool call** (before the result arrives) — a timing refinement |
| prose naming a file | counts a demand → pins at two | **no demand at all** (signal removed) |
| harness re-sending a tool result | not a demand (`_demand_text` returns `""` for `role in ("tool","system")`) | unchanged |

**The load-bearing change is the removal of the text signal**, which is what pinned 19 of 21 pages in
W8B; the explicit `note_refault` is mostly the *earlier* of the two pin timings. `note_refault` does not
exist yet (grep: no hits in `packages/hermes/live/`) — it is part of the plugin 0.12.0 work.

## 3. What the owner's checkpoint should ask for (two cheap additions)

**(a) A falsification set: which of the four planned tests fail BEFORE the change.** The plan lists
"prose mention does not pin; re-sent tool result does not pin; a second `read_file` in a later turn does;
the existing seven laws still hold". By the reading above, the third test — *a second read_file in a later
turn does pin* — **should already pass on today's engine** (the re-render path, `:479-488`). A test that
passes before and after the change proves nothing about the change, so the set needs its *before*
behaviour stated per test: expected to FAIL before (prose mention must not pin — it does pin today) and
expected to PASS before (re-sent tool result must not pin — it does not; the seven laws still hold). The
discriminating tests are the first two; the third is a **regression guard for the removal** (proving the
explicit signal replaces the removed text signal rather than silently disappearing with it), and it should
be labelled as such — otherwise a reader may take it for evidence of the new mechanism.

**(b) A stated margin over the measured floor in the block.** The plan's falsifier is "with the new
signal and a budget sized from the measured floor, the paged arm still evicts zero tokens ⇒ the floor, not
the signal, is the binding constraint". Decidable ✓. But the *second* horn becomes more likely by
construction the closer the budget sits to the floor: a budget a hair above the floor leaves almost no
room to act, so "zero evictions" would be expected rather than informative. The block should therefore
state the budget as **floor + margin**, with the margin named, and the margin must be large enough that
the measured residency growth of the late turns can cross it. Their own numbers support this: floor
≈ 48,650 (arithmetic checks out: 4,350 + 14,100 + 28,200 + 2,000 = 48,650 ✓), candidate budget 60,000,
measured residency 10,518 → 104,032 with turns above 60,000 at 14–19 — so a floor of 48,650 with a
60,000 budget leaves ~11,350 tokens of room, which is the margin to be stated. Note also that the
measured series is the **pinned** ceiling (with 19 pins nothing was stubbed, so it is an upper bound on
the unpinned residency) — which is exactly why the plan insists the floor be *measured* before the block
is written ✓.

## 4. Two smaller review-side notes

- **"One factor" is close, but name the two deltas.** The plan says "the change, stated as one factor"
  and lists the *signal* as that factor; strictly the delta has two parts (text signal removed; pin
  moved from result-time to call-time). Both parts touch the same mechanism (what counts as a demand), and
  the second is a no-op wherever the re-read produces a result (which is every real re-read). Naming them
  costs one line and keeps the claim checkable.
- **The plan's status line already says "owner approval required before any instrument change"** ✓, and
  it asks for two checkpoints, four tests, one pair and no money. The review side's position: the plan is
  sound, its own falsifier is stated, and the two additions above are enough to make the cell bookable.

## 5. Executed agent-doings

- The plan was read at its committed bytes (`c466eb7`), and every engine claim it makes was checked in
  the code: `_update_page_state` (`:459-495`) for the re-render demand, `_demand_text` (`:151-165`) for
  the excluded surfaces, `_credit_demand` (`:495-521`) for the text signal, and the absence of
  `note_refault` in `packages/hermes/live/` (it is to be built).
- The floor arithmetic was recomputed (4,350 + 14,100 + 28,200 + 2,000 = 48,650 ✓) and the margin
  implied by the proposed 60,000 budget was derived (≈ 11,350 tokens).
- Kit: this card + LOG row + a day-file line + the roadmap's W8C pointer. No file of the other lane's was
  edited; no spec, schema, corpus, vector or umpire byte changed; nothing pushed.

## 6. Outcome (2026-11-11): both asks accepted, the plan's framing corrected — the plan is owner-ready

The other lane's `5c0a8aa` ("W8C plan: the re-read pin already exists, so the change is the text
signal") takes this review's finding and rewrites the plan accordingly. Verified at the committed bytes:

- **The framing is corrected in the plan itself** (its §2 now carries a "Correction (review,
  `RR-W8CREVIEW-20261111`, verified in the code)" paragraph): the re-read pin is **not** a new rule, the
  delta has **two named parts** — *part 1, remove the text signal* (load-bearing: what pinned 19 of 21
  pages) and *part 2, move the re-read pin from result time to call time* (a timing refinement, "it
  fires even if the result never does") — and "both deltas are now named as one mechanism".
- **Ask (a), the falsification set, is in** as a test table with each test's BEFORE behaviour: only
  "prose mention does not pin" **fails today** (discriminating); "re-sent tool result does not pin" and
  "the seven laws still hold" **pass today** (invariant guards); "a second `read_file` in a later turn
  pins" **passes today via the re-render path** and is labelled a **regression guard** for part 2 —
  "proving the explicit signal replaces the removed text signal rather than vanishing with it".
- **Ask (b), the margin, is in** and quantified: "**The budget must be stated as floor + margin, with
  the margin named** … measured growth is ~4,700 tokens per turn, so a margin of two turns' growth is the
  minimum worth running", with estimated floor 48,650, candidate budget 60,000, **margin 11,350 ≈ 2.4
  turns of growth**; "the 60,000 figure is a placeholder for the diagnostic. **The block states floor +
  margin explicitly**, with both numbers derived from the diagnostic capture, and the margin is a
  decision the owner sees at **checkpoint B**."

Their LOG row (`W8C-PLAN-FIX-20261111`) names this review, re-derives the floor arithmetic
(4,350 + 14,100 + 28,200 + 2,000 = 48,650) and agrees with it. **This review's two asks are met, and
the plan is now owner-ready**: checkpoint A is the approval of the plan, checkpoint B is the block with
its measured floor and its named margin. Nothing further is owed by this lane before the owner rules.
