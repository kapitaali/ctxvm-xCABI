# QUESTIONS — running queue for the reviewer

Statuses: queued / sent / answered.

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + RFC-0.1 normalisation proposal | **answered 2026-11-08** | Pillar-1 split (replayable + conformance-testable kept; "diffable" behind the consumer profile; "any turn" narrowed) -> `design/diff-normalisation.md`; paper edits via owner (D13). Full: RR-DIFFNORM-20261108 + ARCHIVE. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; NOT "illustrative"; R1 3->0 to the RFC-0.1 section; seq 7 located = `page.fault` t2 `identifier_scan` (RR-P2DEMO-20261108). Full: `QUESTIONS-ARCHIVE.md`. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Default-on stays in owner-run builds; no registry release ships silent default-on (first-run notice minimum); redaction card proposal-only, sidecar-first; consent paragraph replacement (`RR-P3REDACT-20261109`). Full: `QUESTIONS-ARCHIVE.md`. |
| P4 | umpire `ts` (R4): consumer rule or additive mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED proposal-only for umpire 00-SPEC §2 (owner + D-number); (b) refused; UNKNOWNs resolved. Full: RR-P4TS-20261109 + ARCHIVE. |
| P5 | D-U1 calibration transfer: is n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; transfer waits for the preregistered >=5-set equivalence test; UNKNOWNs resolved. Full: RR-P5CAL-20261110 + ARCHIVE. |
| P6 | D-U3 determinism scope: same-build only or cross-machine? | **answered 2026-11-10** | Keep same-build (register option (a)); vocabulary = replay-reproducible with 10 documented exceptions; cross-machine = preregistered matrix; cross-build = identity only. Full: RR-P6DET-20261110 + ARCHIVE. |
| P7 | D-U2 baselines: which one must run before a claim ships? | **answered 2026-11-10** | Two zero-spend baselines first (majority-class + ONE learned: logistic-on-embeddings for accuracy + calibration; zero-shot similarity for caller-labels; stronger model only before a product claim with a spend packet); margins PROPOSED; P6 ERRATUM (RR-M3V3) confirmed the attribution, U4 ticks. Full: RR-P7BASE-20261110 + ARCHIVE. |
| P10 | page-id asymmetry (flat vs nested): second-consumer trigger? | **queued 2026-11-11** | Trigger MET (umpire Python + ctxvm OTLP exporter both branch); options (a) workaround, (b) RFC-0.1 note line, (c) additive field, (d) accept; ruling owner-gated. Full: `P10-page-id-asymmetry.md`. |

Queue law: one-question packets live in `handoff/packets/P<n>-<slug>.md` (<=3 KB); answers summarize here with date + decision number; full texts in `QUESTIONS-ARCHIVE.md`.

## Standing questions
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Own work answers all five BEFORE review is requested.
