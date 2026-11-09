# QUESTIONS — running queue for the reviewer

Statuses: queued (packet ready, not yet pasted), sent (owner pasted it), answered (summary copied below).

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + RFC-0.1 normalisation proposal | **answered 2026-11-08** | Split the Pillar-1 sentence (replayable + conformance-testable kept; "diffable" behind the consumer-side profile; "reconstructs any turn" narrowed; absence claim reworded with scope); card `design/diff-normalisation.md` (N1 + N3 unit rule; OP-N2 open); `:635` + "same bytes"/echo sweep; paper edits via owner (D13 bundle). Full record: `RR-DIFFNORM-20261108`. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + ONE class-not-failure sentence ("healthy" = divergence-free, not violation-free); NOT "illustrative" (recomputed 2026-11-07); R1 3→0 contrast goes to the RFC-0.1 section. Verdict-3 locate DONE: seq 7 = `page.fault` turn 2, source `identifier_scan` (cause swap-in activates), target `tool:read_file({"path":"src/auth/session.ts"})` @ `sha256:d5bf10dd` — declared seq 2, rendered full seq 5, never evicted (`RR-P2DEMO-20261108`; byte-twin `50593d98…`). Sentences route via owner; `:333`/`:339`, working tree. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Keep capture default-on in owner-run builds; no registry release ships silent default-on — first-run notice minimum, opt-in stronger; consent plugin card bound at D6 (covers publish), D17 = timing. Author the redaction card proposal-only, sidecar-first: stage list (capture/flush/export) with policy id + rule-set version + replaced-field count, "absent = unknown", ref-policy entry (raw/keyed-hashed/dropped), and the block is an assertion without tamper evidence; keyed-hash emission deferred until a rule passes the golden vectors (consistent with `page_id` = `(logical_ref, content_hash)` minting within an artifact; breaks cross-drop joins and the N1 raw-ref diffs); falsifiers: seeded-canary recall; the no-docs user blind to the trace. Mend the consent paragraph (stored contents, discoverability, the 0700 limit) — replacement text in `RR-P3REDACT-20261109`; Part II cites the card id until the field name is ratified. Card: `design/redaction-block.md` (owner-cleared 2026-11-09). |

Queue law: every bot-safe one-question format lives in `handoff/packets/P<n>-<slug>.md` (<=3 KB, one specific question); the reviewer's answer is summarized here in one or two lines with the date, and the verdict number it resolves (D13–D17 in PROJECT-STATE) is noted.

## Standing questions (the reviewer asks these of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply the five standing questions to their own work BEFORE asking the reviewer; a change that cannot answer (1) or (2) from repo evidence is not ready for review.
