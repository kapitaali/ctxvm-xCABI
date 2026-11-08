# QUESTIONS — running queue for the reviewer

Statuses: queued (packet ready, not yet pasted), sent (owner pasted it), answered (summary copied below).

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + RFC-0.1 normalisation proposal | **answered 2026-11-08** | Split the Pillar-1 sentence: keep replayable + conformance-testable, qualify "diffable" behind a consumer-side profile, narrow "reconstructs any turn"; absence claim → "we found none in this review" with scope; author the proposal card (done same day: `design/diff-normalisation.md`); rules N1 + N3 (checked: the RFC-0.1 `turn` field defines NO unit — the profile does), OP-N2 open problem — diff on `logical_ref`, hash mismatches = separate class, canonical-hash deferred; fix :635 + sweep "same bytes"/"byte-identically"/"any harness" echoes; paper edit routed to the working-tree revision via the owner. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | queued | — |
| P3 | Redaction block + default-capture decision | queued | — |

Queue law: every bot-safe one-question format lives in `handoff/packets/P<n>-<slug>.md` (<=3 KB, one specific question); the reviewer's answer is summarized here in one or two lines with the date, and the verdict number it resolves (D13–D17 in PROJECT-STATE) is noted.

## Standing questions (the reviewer asks these of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply the five standing questions to their own work BEFORE asking the reviewer; a change that cannot answer (1) or (2) from repo evidence is not ready for review.
