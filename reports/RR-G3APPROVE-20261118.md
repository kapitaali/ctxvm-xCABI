# RR-G3APPROVE-20261118 — owner approves G3 (W9 equivalence-test preregistration)

Owner decision 2026-11-18, verbatim:

> approve g3

## What this approves

G3 in `design/ROADMAP-OPENCODE-LANE.md` and `handoff/PROJECT-STATE.md` §Next three item 3: the **design** for an
equivalence test of umpire's calibrated confidence transfer. The roadmap's *Owner* line is "approve the design +
fund the run"; this ruling supplies the approval. The *Done when* rule is stricter: a preregistration card must
exist, umpire-side, referee-checkable, with frozen thresholds and parse code, **dated after this approval**. So G3
stays open until that card lands; it is not marked done by this ruling.

## Frozen design carried forward from `RR-P5CAL-20261110`

- margin **±2 points**; **Brier/log-loss primary**, ECE secondary;
- **≥5 held-out NEW label sets**, the set being the generalisation unit (not the row);
- cluster bootstrap across sets, cross-fitting;
- sizing `n ≈ 180 × (h/2)²` from the existing rows' paired bootstrap half-width (h=4 → ~720; h=6 → ~1,620);
- callers must keep saying "treat it as an uncalibrated score" until the transfer claim is checked and established.

**Boundary:** no new capture run may start before the prereg card exists. Umpire is a separate repo and lane;
editing it still needs owner clearance for the specific change, and the review lane does not write there. The
model server start script and the D-U1 transfer caveat remain on record. No spend from this ruling alone beyond
the owner's "fund the run" (the run itself still needs the prereg).

## Applied

- Roadmap G3 line: owner approval dated 2026-11-18 with a pointer here; task still open until the prereg exists.
- `handoff/PROJECT-STATE.md` §Next three item 3 and D19/umprie-related lines updated within the byte cap.
- This card, an append-only LOG row (four pipes), and a day-file section.

No code change, no model call, no push. Mechanism note: no signature artifact — the owner rules in chat and the
review lane records the ruling with the date and exact decision (precedent `RR-W8CSEQ-20261111`).
