# QUESTIONS — running queue for the reviewer

Statuses: queued (packet ready, not yet pasted), sent (owner pasted it), answered (summary copied below).

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + RFC-0.1 normalisation proposal | **answered 2026-11-08** | Split Pillar-1 (replayable + conformance-testable kept; "diffable" behind the consumer profile; "any turn" narrowed) → `design/diff-normalisation.md`; N3 turn unit; paper edits via owner (D13). `RR-DIFFNORM-20261108`. Full: `QUESTIONS-ARCHIVE.md`. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; NOT "illustrative"; R1 3→0 to the RFC-0.1 section; seq 7 located = `page.fault` t2 `identifier_scan` (`RR-P2DEMO-20261108`). Full: `QUESTIONS-ARCHIVE.md`. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Default-on stays in owner-run builds; no registry release ships silent default-on (first-run notice minimum); redaction card proposal-only, sidecar-first; consent paragraph replacement (`RR-P3REDACT-20261109`). Full: `QUESTIONS-ARCHIVE.md`. |
| P4 | umpire `ts` (R4): consumer rule or additive mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED proposal-only for umpire 00-SPEC section 2 (owner approval + D-number); (b) refused; both UNKNOWNs resolved. Full: RR-P4TS-20261109 + ARCHIVE. |
| P5 | D-U1 calibration transfer: is n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; no transfer claim until the preregistered >=5-set equivalence test; point estimates worsened (A1 7.5-to-12.2, A2 4.9-to-6.8 ECE); UNKNOWNs resolved. Full: RR-P5CAL-20261110 + ARCHIVE. |
| P6 | D-U3 determinism scope: same-build only or cross-machine? | **answered 2026-11-10** | Keep same-build (register option (a)); vocabulary = replay-reproducible with 10 documented exceptions (page-table softening refused - umpire splits identity 480/480 + strict 470/480); ten classify at quiescent concurrency-1 recapture; cross-machine = preregistered matrix; cross-build = identity only; UNKNOWNs resolved in books. Full: RR-P6DET-20261110 + ARCHIVE. |
| P7 | D-U2 baselines: which one must run before a claim ships? | **queued 2026-11-09** | — |

Queue law: every bot-safe one-question format lives in `handoff/packets/P<n>-<slug>.md` (<=3 KB, one specific question); the reviewer's answer is summarized here in one or two lines with the date, and the verdict number it resolves (D13–D17 in PROJECT-STATE) is noted.

## Standing questions (the reviewer asks these of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply the five standing questions to their own work BEFORE asking the reviewer; a change that cannot answer (1) or (2) from repo evidence is not ready for review.
