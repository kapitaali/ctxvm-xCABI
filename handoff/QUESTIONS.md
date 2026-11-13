# QUESTIONS — running queue for the reviewer

Statuses: queued/sent/answered.

| Packet | Title | Status | Answer summary |
|---|---|---|---|
| P1 | Cross-harness claim + normalisation | **answered 2026-11-08** | Pillar-1 split (replayable + conformance-testable kept) -> `design/diff-normalisation.md`. `RR-DIFFNORM`. |
| P2 | `faultOfResidentPage` violation in the healthy demo | **answered 2026-11-08** | Demo keeps + one class-not-failure sentence; seq 7 = `page.fault` t2 `identifier_scan`. Full: `RR-P3REDACT`. |
| P3 | Redaction block + default-capture | **answered 2026-11-08** | Default-on stays in owner-run builds; no release ships silent default-on; redaction card proposal-only. `RR-P3REDACT`. |
| P4 | umpire `ts` (R4): rule or mandate? | **answered 2026-11-09** | (a)+(c): ts stays optional; ordering clause DRAFTED for umpire 00-SPEC §2; (b) refused. Full: `RR-P4TS`. |
| P5 | D-U1 calibration transfer: n=180 enough? | **answered 2026-11-10** | Publish per-corpus calibration WITH the caveat; transfer waits for the >=5-set test. `RR-P5CAL`. |
| P6 | D-U3 determinism scope? | **answered 2026-11-10** | Keep same-build (option (a)); vocabulary = replay-reproducible, 10 exceptions. `RR-P6DET`. |
| P7 | D-U2 baselines: which must run first? | **answered 2026-11-10** | Two zero-spend baselines first (majority-class + ONE learned; zero-shot). `RR-P7BASE`. |
| P8 | cache-stable selection? | **answered 2026-11-11** | Ranking adopted (watermark compaction); w/r = 10, evictable 5.3% -> n* ~189 calls; (d) amended (no-op 4.4x). |
| P9 | close W8 or buy a mechanism test? | **answered 2026-11-10** | A confirmed; the closure states the weaker claim; the narrowing ran. `RR-P9CLOSE`. |
| P10 | page-id asymmetry: second-consumer trigger? | **answered 2026-11-11** | (b)+(a): ONE RFC-0.1 compatibility-note line (type dispatch, never field-sniffing), no field; D-numbered; vector = fixture. `RR-P10ID`. |
| P11 | canonical ordering: who owns it? | **answered 2026-11-11** | (c) owner, (a) pointer; test FIRST (equal model/page table/report, never bytes); note = compatibility. Full: `RR-P11CANON`. |
| P12 | omission: on the wire or in the sidecar? | **answered 2026-11-13** | wire (optional, omitted-when-unknown list of removed-page identities with token counts, per request not per turn; sidecar kept as a documented fallback); check per call (`before − after` equals the sum of removed entries; fail closed when removals exist and the list is absent; provider receipts as a third witness); scoped view is an addition under a new field name, never a change to the recorded `residentTokens`; no `page.evict` reuse. Falsifier: disagreement with provider receipts beyond estimate error, or a second harness that cannot report removals. UNKNOWN: OpenCode capability; trace size; whether R5 suffices for existence at turn N. |

Queue law: packets live in `handoff/packets/`; answers summarize here with date + decision.

## Standing questions
The kit's five are in `handoff/CONTEXT-PACK.md` §7; own work answers all five BEFORE review.
