# QUESTIONS — running queue for the reviewer

Statuses: queued (packet ready, not yet pasted), sent (owner pasted it), answered (summary copied below).

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + RFC-0.1 normalisation proposal | **answered 2026-11-08** | Split Pillar-1 (replayable + conformance-testable kept; "diffable" behind the consumer profile; "any turn" narrowed) → `design/diff-normalisation.md`; N3 turn unit; paper edits via owner (D13). `RR-DIFFNORM-20261108`. Full: `QUESTIONS-ARCHIVE.md`. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; NOT "illustrative"; R1 3→0 to the RFC-0.1 section; seq 7 located = `page.fault` t2 `identifier_scan` (`RR-P2DEMO-20261108`). Full: `QUESTIONS-ARCHIVE.md`. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Default-on stays in owner-run builds; no registry release ships silent default-on (first-run notice minimum); redaction card proposal-only, sidecar-first; consent paragraph replacement (`RR-P3REDACT-20261109`). Full: `QUESTIONS-ARCHIVE.md`. |
| P4 | umpire `ts` (R4): consumer rule or additive mandate? | **answered 2026-11-09** | (a)+(c): `ts` stays optional; ordering clause DRAFTED proposal-only for umpire 00-SPEC §2 (owner approval + D-number); (b) refused — 0.1 makes `ts` optional, all 4 ledgers are 0.1-stamped without `ts`, v0-only emitters could never comply; no 5-touchpoint card; both UNKNOWNs resolved (0.1 stamping YES; cross-session-ordering consumer NONE today). Full: `RR-P4TS-20261109` + `QUESTIONS-ARCHIVE.md`. |
| P5 | D-U1 calibration transfer: is n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; NO transfer claim until a preregistered equivalence test on ≥5 new label sets (±2 pt, Brier/log-loss primary, cluster bootstrap, n ≈ 180×(h/2)²); point estimates worsened (A1 7.5→12.2, A2 4.9→6.8 ECE); caller sentence proposed. UNKNOWN arms resolved (`design/W9-TRANSFER.md:36-38`); rows-per-scope UNKNOWN half-resolved. Full: `RR-P5CAL-20261110` + `QUESTIONS-ARCHIVE.md`. |
| P6 | D-U3 determinism scope: same-build only or cross-machine? | **queued 2026-11-09** | — |
| P7 | D-U2 baselines: which one must run before a claim ships? | **queued 2026-11-09** | — |

Queue law: every bot-safe one-question format lives in `handoff/packets/P<n>-<slug>.md` (<=3 KB, one specific question); the reviewer's answer is summarized here in one or two lines with the date, and the verdict number it resolves (D13–D17 in PROJECT-STATE) is noted.

## Standing questions (the reviewer asks these of any change)
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Agents apply the five standing questions to their own work BEFORE asking the reviewer; a change that cannot answer (1) or (2) from repo evidence is not ready for review.
