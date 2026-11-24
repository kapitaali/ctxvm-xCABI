# RR-PAGE-EVICT-PAPER-ROUTE-20261124 — correction: the gitignored paper source is intentional; wording routed to research lane

Owner clarified 2026-11-24: "the .md files were moved to gitignored on purpose. the research lane might not be aware of
this. but you are." My `RR-PAGE-EVICT-IMPL-REVIEW` treated "canonical Part I/II source is not a tracked file here" as a
blocker for the paper wording. That framing was **wrong** — verified from `.gitignore:36–40`:

> "Uncommitted research sources (2026-11-05): two independent safety-research notes were written by different
> models and the owner asked for the SYNTHESIS to be the committed record, not the sources. They stay on disk under
> this folder, tracked by name in `research/synthesis-20261105.md`, never by git."

So `research/uncommitted/white-paper-Part-II_reviewed.md` (and `white-paper_reviewed.md`) are the **legitimate,
intended working sources** — gitignored by design, not missing. The research lane can and should edit them there;
the committed record is the synthesis, not these files.

## 1. What changes in my prior record

- `RR-PAGE-EVICT-IMPL-REVIEW §2` said the paper wording was "owed, not applied (honest blocker)" partly because the
  source "is not a tracked file in this repo." **Corrected:** the source is intentionally gitignored, which is **not**
  a blocker — it is where the research lane works. The wording is still correctly **owed to the research lane**, but
  for the real reason: `research/**` is read-never-edit for me (`LANES.md`), and the change must land **with** the
  hermes emitter so paper and wire agree.
- No claim, no re-score, no push follows from this correction. No law touched — the gitignore is deliberate and
  unchanged.

## 2. Routing to the research lane (exact, now that the source is known)

Apply the design §5 A3/A4 wording to the **gitignored working source**
`research/uncommitted/white-paper-Part-II_reviewed.md` (and `white-paper_reviewed.md` for Part I), at the A3/A4
sentences identified in `reports/RR-PAPER-REVIEW-20261115.md:266–288`:
- from "shipped adapters emit `full` only, once per page, at first reveal" / "adapters do not yet emit stub renders";
- to the format- and adapter-scoped statement that **stub-mode** emits a `page.render(mode=stub)` + `page.evict` per
  dropped result, while **drop mode** still emits neither (the `RR-W8CEVICT` honesty decision).
Land this **in the same change** as the hermes emitter (`design/PAGE-EVICT-HERMES-PROMPT.md`, 0.13.32) so paper and
wire agree; do not edit the files if the emitter is stalled. The research lane owns these paths; I do not write them.

## 3. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`. The prior
"blocker" wording stands corrected by this card, not silently rewritten.
