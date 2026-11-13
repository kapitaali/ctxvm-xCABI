# QUESTIONS — running queue for the reviewer

Statuses: queued/sent/answered.

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + normalisation | **answered 2026-11-08** | Pillar-1 split (replayable + conformance-testable kept; diffable behind the consumer profile) -> `design/diff-normalisation.md`. Full: RR-DIFFNORM. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; NOT illustrative; seq 7 = `page.fault` t2 `identifier_scan`. Full: ARCHIVE. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Default-on stays in owner-run builds; no registry release ships silent default-on; redaction card proposal-only. Full: ARCHIVE. |
| P4 | umpire `ts` (R4): consumer rule or mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED for umpire 00-SPEC §2; (b) refused. Full: RR-P4TS. |
| P5 | D-U1 calibration transfer: is n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; transfer waits for the >=5-set preregistered test. Full: RR-P5CAL. |
| P6 | D-U3 determinism scope? | **answered 2026-11-10** | Keep same-build (option (a)); vocabulary = replay-reproducible with 10 documented exceptions. Full: RR-P6DET. |
| P7 | D-U2 baselines: which must run before a claim ships? | **answered 2026-11-10** | Two zero-spend baselines first (majority-class + ONE learned: logistic-on-embeddings; zero-shot for caller-labels). Full: RR-P7BASE. |
| P8 | cache-stable selection? | **answered 2026-11-11** | Ranking adopted (watermark compaction); w/r = 10, evictable 5.3% -> n* ~189 calls; (d) amended (no-op 4.4x control). |
| P9 | close W8 or buy a mechanism test? | **answered 2026-11-10** | A confirmed; the closure ALREADY states the weaker claim; the narrowing ran (H3 unknown cause); one stale phrase routed. Full: `RR-P9CLOSE`. |
| P10 | page-id asymmetry: second-consumer trigger? | **answered 2026-11-11** | Ruling (b)+(a): ONE RFC-0.1 compatibility-note line (type dispatch, never field-sniffing), no field (sealed v0 keeps both shapes); note = new spec/rfc-0.1 file, D-numbered; vector = fixture. Full: `RR-P10ID`. |
| P11 | canonical ordering: who owns the line? | **answered 2026-11-11** | (c) owner, (a) pointer; test FIRST (equal model/page table/report, never bytes), then the note states the fact it enforces; note = compatibility statement only. Full: `RR-P11CANON`. |
| P12 | omission: wire or sidecar? | **queued 2026-11-13** | proposal + measured checker state (`RR-OMISSION-20261113`); owner decision D19 (proposed). |

Queue law: packets live in `handoff/packets/`; answers summarize here with date + decision number; full texts in the ARCHIVE.

## Standing questions
The kit's five, verbatim in `handoff/CONTEXT-PACK.md` §7: what claim does this change support? what evidence
level? what would falsify it? what does it assume about the harness? what is the cost if it is wrong? Own work
answers all five BEFORE review.
