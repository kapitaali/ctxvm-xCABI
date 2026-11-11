# QUESTIONS — running queue for the reviewer

Statuses: queued/sent/answered.

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + normalisation | **answered 2026-11-08** | Pillar-1 split (replayable + conformance-testable kept; diffable behind the consumer profile) -> `design/diff-normalisation.md`. Full: RR-DIFFNORM + ARCHIVE. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; NOT illustrative; seq 7 = `page.fault` t2 `identifier_scan`. Full: ARCHIVE. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Default-on stays in owner-run builds; no registry release ships silent default-on; redaction card proposal-only. Full: ARCHIVE. |
| P4 | umpire `ts` (R4): consumer rule or mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED for umpire 00-SPEC §2; (b) refused. Full: RR-P4TS + ARCHIVE. |
| P5 | D-U1 calibration transfer: is n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; transfer waits for the >=5-set preregistered test. Full: RR-P5CAL + ARCHIVE. |
| P6 | D-U3 determinism scope? | **answered 2026-11-10** | Keep same-build (option (a)); vocabulary = replay-reproducible with 10 documented exceptions. Full: RR-P6DET + ARCHIVE. |
| P7 | D-U2 baselines: which must run before a claim ships? | **answered 2026-11-10** | Two zero-spend baselines first (majority-class + ONE learned: logistic-on-embeddings for accuracy + calibration; zero-shot for caller-labels). Full: RR-P7BASE + ARCHIVE. |
| P8 | cache-stable selection? | **answered 2026-11-11** | Ranking adopted (watermark compaction); w/r = 10, evictable 5.3% -> n* ~189 calls; (d) amended (no-op cost 4.4x control). Full: `RR-P8CACHE` + ARCHIVE. |
| P9 | close W8 or buy a mechanism test? | **answered 2026-11-10** | A confirmed; the closure ALREADY states the weaker claim; the narrowing ran (H3 unknown cause); one stale phrase routed. Full: `RR-P9CLOSE-20261111` + ARCHIVE. |
| P10 | page-id asymmetry: second-consumer trigger? | **queued 2026-11-11** | Trigger MET (2 consumers); options (a) workaround, (b) RFC-0.1 note line, (c) additive field, (d) accept; owner-gated. Full: `P10-page-id-asymmetry.md`. |
| P11 | canonical ordering: who owns the line? | **queued 2026-11-11** | F9 undocumented; options (a) RFC-0.1 note line, (b) umpire 00-SPEC only, (c) a conformance test, (d) accept; crux: `ts`-last vs sorted keys. Full: `P11-canonical-order.md`. |

Queue law: packets live in `handoff/packets/P<n>-<slug>.md`; answers summarize here with date + decision number; full texts in the ARCHIVE.

## Standing questions
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Own work answers all five BEFORE review.
