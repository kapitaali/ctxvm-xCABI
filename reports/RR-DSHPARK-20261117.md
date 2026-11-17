# RR-DSHPARK-20261117 — owner decision: Phase 1 closed, dsh lane parked, corpus naming deferred

Owner decision 2026-11-17, stated in chat after the review lane asked whether to route the remaining corpus-drop
naming question. The owner declined to route it:

> No — I don't want item 3 routed yet. It's a Phase 2 decision, and routing it now would be premature

The owner's stated reasons, preserved here:
1. `corpus/m1..m8` are frozen with pinned checksums (AGENTS law 5), so there is no place for a dsh trace until a
   specific redacted/synthetic drop is actually proposed.
2. Real dsh traces stay private in the state directory (law 9); nothing from our captures is corpus material
   as-is.
3. A naming decision makes sense only when Phase 2 replay validation or a redaction/fixture card is scoped, with
   the actual artifact and its checksum in hand.

**Preliminary direction, explicitly not a ruling:** a separate `corpus/dsh/` namespace rather than extending the
`m`-series, argued from the frozen-drop rule. Do not record it as decided.

**Status:** Phase 1 is closed; the dsh lane is parked. The owner will assign Phase 2 or another task. Plan D
remains with the other file's owner; the literal `~/` artifact in the DSH checkout stays reported and untouched.

This card records the decision so a future session does not route corpus naming on the strength of the open
question still printed in `RR-W22-20261115.md` §Open questions item 3. That item is a Phase 2 question, not a
pending packet. No code change, no model call, no spend, no push.

Also noted: `bee55c8` corrected the partial-path statement in `RR-TBWIREDFULL-20261117.md` that the review lane
flagged in `RR-TBWIREDFULL-REVIEW` §3 — the named `.partial` files no longer exist, and the card now says so.
