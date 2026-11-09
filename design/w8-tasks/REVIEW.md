# Review of the W8 task designs (lane review, 2026-11-09)

Verdict: **shape accepted, four defects fixed in place, one correction of claim.** Both tasks are
runnable after the fixture is generated and its floor measured against real bytes. Nothing here
needs a paid call to settle.

## F1 — T-A shipped its own arithmetic, uncorrected

The floor paragraph read:

> ≈ 22,400 bytes ≈ 112,000 bytes total ≈ **28,000 tokens** at 4 bytes/token. Wait — recompute:
> 14 × 200 × 80 = 224,000 bytes ≈ **56,000 tokens**.

Three different numbers for one quantity, with the correction left in the text. A design document
that argues with itself is how a fixture gets built to the wrong size; the lane that implements it
would have had to decide which number was meant.

**Fixed:** one computation, one number, with the mean of the draw stated.

## F2 — T-A measured lines with the newline included

`max_line` counted the terminating `\n`, while the repo's existing definition
(`lineShape.maxLineBytes`, T1, the frozen expected vector) excludes it. Two definitions of the same
word in one repository is a trap: the checker would be right by its own spec and wrong by every
reader's assumption, and a 4–9-byte disagreement — the exact failure that took a day to diagnose on
2026-10-07 — becomes plausible again.

**Fixed:** newline excluded, and the task text says so explicitly, citing T1.

## F3 — `short` was a field that could not vary

The fixture drew lengths uniformly from [40,120] while `short` counted lines under 10 bytes. The
value was therefore always `0`: a field a model cannot get wrong, tested by a checker that always
sees zero. It would have padded the artefact and taught the analysis nothing.

**Fixed:** lengths now draw from [5,120] so both tails exist, and each file carries 250 lines
instead of 200 to keep the floor above 45,000:
`14 × 250 × 62.5 bytes = 218,750 B ≈ 54,700 tokens`.

## F4 — the anti-search claim was overstated, and the claim is load-bearing

The README said search *cannot* shortcut: "No grep can compute how many lines exceed 100 bytes."
True of grep, and beside the point — `search_files` returns the matching **lines**, and a broad
enough pattern returns most of a file. The material can reach the context through search instead of
through `read_file`, so the shortcut exists.

That does not sink the design, but the reason has to be stated correctly or the experiment rests on
a claim that is false. The corrected argument, now in the README:

- calls stay low (16 and 22 against 150), so a competent agent finishes;
- context still grows past the 24,000 budget (54,700 / 60,200 tokens) whichever route the content
  takes, so the paged arm is exercised rather than idle;
- the answer is still a computation — no search returns a count, sum, maximum or per-file
  contribution — so the failure mode is a wrong number the checker catches, not an infinite loop.

**Consequence for the run:** a search-heavy route is acceptable to the experiment, and only the
686-search thrash was not. The metric that decides a cell's fate is calls and completion, not the
tool mix.

## F5 — T-B did not pin the CSV format

No quoting rule, no embedded-comma rule, no whitespace rule. A fixture generator is free to emit
`"a,b"` and the parser question becomes the task. **Fixed:** plain format stated — header exactly
`id,category,value`, no quoting, no embedded commas, no padding, LF endings.

## What the pilot still has to watch

`search_files` truncates at `limit`. An agent that searches for everything may hold part of the
data, compute a wrong aggregate, and fail for a reason that has nothing to do with paging. When a
cell fails, the analysis must distinguish **truncated data** from **arithmetic error** — the first
says the task allowed a bad route, the second says the model mis-measured, and only the second is a
result about the model.

## Not changed

The call estimates (16 / 22), the artefact schemas, the tie-break rules, the checker philosophy
(byte-exact, perturbation-tested), and the honest note that a weak model can submit a wrong
artefact quickly. Those are sound.
