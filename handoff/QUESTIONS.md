# QUESTIONS — running queue for the reviewer

Statuses: queued / sent / answered.

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + normalisation | **answered 2026-11-08** | Pillar-1 split (replayable + conformance-testable kept; diffable behind the consumer profile; any-turn narrowed) -> `design/diff-normalisation.md`. Full: RR-DIFFNORM-20261108 + ARCHIVE. |
| P2 | `faultOfResidentPage` violation shown by the healthy-fixture demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; NOT illustrative; seq 7 = `page.fault` t2 `identifier_scan` (RR-P2DEMO). Full: ARCHIVE. |
| P3 | Redaction block + default-capture decision | **answered 2026-11-08** | Default-on stays in owner-run builds; no registry release ships silent default-on; redaction card proposal-only, sidecar-first (RR-P3REDACT). Full: ARCHIVE. |
| P4 | umpire `ts` (R4): consumer rule or mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED proposal-only for umpire 00-SPEC §2; (b) refused; UNKNOWNs resolved. Full: RR-P4TS-20261109 + ARCHIVE. |
| P5 | D-U1 calibration transfer: is n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; transfer waits for the >=5-set preregistered test; UNKNOWNs resolved. Full: RR-P5CAL-20261110 + ARCHIVE. |
| P6 | D-U3 determinism scope? | **answered 2026-11-10** | Keep same-build (option (a)); vocabulary = replay-reproducible with 10 documented exceptions. Full: RR-P6DET-20261110 + ARCHIVE. |
| P7 | D-U2 baselines: which one must run before a claim ships? | **answered 2026-11-10** | Two zero-spend baselines first (majority-class + ONE learned: logistic-on-embeddings for accuracy + calibration; zero-shot similarity for caller-labels; stronger model only with a spend packet). Full: RR-P7BASE-20261110 + ARCHIVE. |
| P8 | cache-stable selection: bound residency, keep the cache? | **answered 2026-11-11** | Ranking adopted (watermark compaction); w/r = 10 (row-013), evictable 5.3% -> n* ~189 calls; (d) amended (no-op cost 4.4x control). Full: `RR-P8CACHE-20261111` + ARCHIVE. |
| P10 | page-id asymmetry: second-consumer trigger? | **queued 2026-11-11** | Trigger MET (2 consumers branch); options (a) workaround, (b) RFC-0.1 note line, (c) additive field, (d) accept; owner-gated. Full: `P10-page-id-asymmetry.md`. |
| P11 | canonical ordering: who owns the compatibility line? | **queued 2026-11-11** | F9 undocumented; options (a) RFC-0.1 note line, (b) umpire 00-SPEC only, (c) a conformance test, (d) accept; crux: `ts`-last vs sorted keys differ. Full: `P11-canonical-order.md`. |

Queue law: one-question packets live in `handoff/packets/P<n>-<slug>.md` (<=3 KB); answers summarize here with date + decision number; full texts in the ARCHIVE.

## Standing questions
1. What claim does this change support?
2. What evidence level does it have?
3. What would falsify it?
4. What does it assume about the harness?
5. What is the cost if it is wrong?

Own work answers all five BEFORE review is requested.
