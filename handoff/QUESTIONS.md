# QUESTIONS — running queue for the reviewer

Statuses: queued (packet ready, not yet pasted), sent (owner pasted it), answered (summary copied below).

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + RFC-0.1 normalisation proposal | **answered 2026-11-08** | Split the Pillar-1 sentence: keep replayable + conformance-testable, qualify "diffable" behind a consumer-side profile, narrow "reconstructs any turn"; absence claim → "we found none in this review" with scope; author the proposal card (done same day: `design/diff-normalisation.md`); rules N1 + N3 (checked: the RFC-0.1 `turn` field defines NO unit — the profile does), OP-N2 open problem — diff on `logical_ref`, hash mismatches = separate class, canonical-hash deferred; fix :635 + sweep "same bytes"/"byte-identically"/"any harness" echoes; paper edit routed to the working-tree revision via the owner. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Keep the demo as-is, add ONE sentence explaining that `violations` is a logged class, not a failure, and that "healthy" means divergence-free; locate seq 7 and name its fault source in the sentence; show the R1 3-to-0 contrast in the RFC-0.1 section instead of replacing the demo. Locate DONE same day: seq 7 = `page.fault` turn 2, source `identifier_scan` (the conditional swap-in "the model named an identifier whose page was still resident" ACTIVATES), target `tool:read_file({"path":"src/auth/session.ts"})` at `sha256:d5bf10dd` — page declared seq 2, rendered full seq 5, never evicted; replay exit 0 / divergences empty / violations exactly the one entry; byte-twin verified (`corpus/m1/tracer-healthy.jsonl` == `packages/node/fixtures/tracer-healthy.jsonl`, sha256 `50593d98…`). Owner routes the sentence edit to the white-paper lane with the D13 bundle (`:333`/`:339` has the line; working tree, not HEAD). |
| P3 | Redaction block + default-capture decision | queued | — |

Queue law: every bot-safe one-question format lives in `handoff/packets/P<n>-<slug>.md` (<=3 KB, one specific question); the reviewer's answer is summarized here in one or two lines with the date, and the verdict number it resolves (D13–D17 in PROJECT-STATE) is noted.

## Standing questions (the reviewer asks these of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply the five standing questions to their own work BEFORE asking the reviewer; a change that cannot answer (1) or (2) from repo evidence is not ready for review.
