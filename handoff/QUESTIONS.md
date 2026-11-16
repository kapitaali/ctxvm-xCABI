# QUESTIONS — running queue for the reviewer

Statuses: queued/sent/answered.

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + normalisation | **answered 2026-11-08** | Pillar-1 split (replayable + conformance-testable kept) -> `design/diff-normalisation.md`. `RR-DIFFNORM`. |
| P2 | `faultOfResidentPage` violation in the healthy demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence. `RR-P3REDACT`. |
| P3 | Redaction block + default-capture | **answered 2026-11-08** | Default-on stays in owner-run builds; redaction card proposal-only. `RR-P3REDACT`. |
| P4 | umpire `ts` (R4): rule or mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED; (b) refused. `RR-P4TS`. |
| P5 | D-U1 calibration transfer: n=180 enough? | **answered 2026-11-10** | Publish WITH the caveat; transfer waits for the >=5-set test. `RR-P5CAL`. |
| P6 | D-U3 determinism scope? | **answered 2026-11-10** | Same-build kept; replay-reproducible, 10 exceptions. `RR-P6DET`. |
| P7 | D-U2 baselines: which must run first? | **answered 2026-11-10** | Two zero-spend baselines first. `RR-P7BASE`. |
| P8 | cache-stable selection? | **answered 2026-11-11** | Ranking adopted; w/r = 10, evictable 5.3% -> n* ~189 calls; (d) amended. |
| P9 | close W8 or buy a mechanism test? | **answered 2026-11-10** | A confirmed; weaker claim stated. `RR-P9CLOSE`. |
| P10 | page-id asymmetry: second-consumer trigger? | **answered 2026-11-11** | (b)+(a): type-dispatch note line, no field; D-numbered; vector = fixture. `RR-P10ID`. |
| P11 | canonical ordering: who owns it? | **answered 2026-11-11** | (c) owner, (a) pointer; test FIRST (model/page table/report, never bytes). `RR-P11CANON`. |
| P12 | omission: on the wire or in the sidecar? | **answered 2026-11-13** | the wire (per-call list of removed-page identities, fail-closed check); the scoped view is an addition under a new name. Full answer: archive §P12 + `RR-OMISSIONANSWER`. |
| P13 | paper: the `page.render` sentence | **answered 2026-11-16** | (c) merged+tightened (reviewer's wording); drop the lead-in; scope the table row, the mirror, every other occurrence; optional P12 clause. Archive §P13. |
| P14 | paper: the one-liner "reconstruct and replay the exact request" | **queued 2026-11-15** | Narrow it, or state the limit once in §16: the trace holds no request bytes. Packet: `handoff/packets/P14-paper-oneliner.md`. |
| P15 | W22 CI coverage: clear `design/W22-CI-COVERAGE.md`? | **answered 2026-11-16** | Placement cleared (D-number owed); reword to gate-does-not-run-tests; step owner-directed/hermes-implemented (interim: event-map + named skips; whole dir once (ii) lands); schemastery (ii), (iii) interim. Archive §P15. |

Queue law: packets live in `handoff/packets/`; answers summarize here with date + decision.

## Standing questions
The kit's five are in `handoff/CONTEXT-PACK.md` §7; own work answers all five BEFORE review.
