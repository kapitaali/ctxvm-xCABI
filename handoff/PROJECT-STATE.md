# State (updated 2026-11-10, by ctxvm repo agent (opencode), after the P7 card: D-U2 answered — two zero-spend baselines first, margins preregistered before any run)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > second harness identical traces > falsifiable metrics > packaging. W8: 0 CELL, 3 NO-OP, 1 DATA-INVALID; saving capped 5.3%; next = packet P9.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`, byte-frozen); RFC-0.1 additive landed (`spec/rfc-0.1/`, R0–R5).
- Corpus: ODPS 0.8.0, m1–m8 checksummed; hub ODPC byte-identical.
- Plugins: hermes 0.10.11 (`packages/hermes/live/__init__.py:94`); @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1.
- Papers: Part I committed + the white-paper lane's UNCOMMITTED revision; Part II untracked (`RR-WP2REV-20261107`).
- Everyday capture: deepseek-v4.1-flash-1017 on nous; `~/.local/state/ctxvm/traces`; budget 200000 (RR-WP2REV §Verification).

## Done (last 3 items: one line each, with locators)
1. P7 answered (RR-P7BASE-20261110): two zero-spend baselines first (majority-class + ONE learned); margins preregistered before any run.
2. P6 answered (RR-P6DET-20261110): replay stays SAME-BUILD (option (a)); vocabulary = replay-reproducible with 10 documented exceptions.
3. P5 answered (RR-P5CAL-20261110): calibration WITH the caveat; transfer needs the ≥5-set preregistered equivalence test.

## In progress (one item: what, blocker, next command)
Part II revision (absorbs D13's sentence; `RR-WP2REV-20261107`). Blocker: that lane's WIP + owner routing.

## Next three (ordered, one line each)
1. Owner: ratify D13 + D14 and route the SIX-item white-paper bundle (items listed in full in RR-DAY-20261109) — working-tree bytes, not HEAD.
2. Owner: ratify the release rule + §4-LIST at D6/D17 (placement DONE: `design/redaction-block.md`).
3. Agent: P7 answered; P8 drop-or-keep. Umpire gates: D-ordering (P4), caller sentence (P5), vocab line (P6), protocol+margins (P7).

## Decisions made (date, decision, reason)
- 2026-10-30/31: D3-c = OTel layered mapping, not native; D4 adopts RFC-0.1; D8 splits → schemaVersion first (RR-DECISIONS-20261030, RR-RFC01E1-20261031).
- 2026-11-01: D12 — est* estimates keep page-table semantics (RR-W8PREREG-20261101).
- 2026-11-06: W8 keeps vBudget 24,000; only tasks with a floor below it measure (RR-ENGINEGAP-20261106 rec. 2).
- 2026-11-07: W8 ruled FAILED; capture stays default-on; contract restored (RR-W8CHUNK-20261107-2b + RR-W8INDEX).
- 2026-11-08: D3-c approved (owner); D13 answered (P1); P2 answered + seq 7 located (`identifier_scan` swap-in).
- 2026-11-09: D14 answered (P3 verdicts recorded); consent mends + card-citation rule routed. P4 answered: ts stays optional; ordering clause PROPOSED for umpire §2 (RR-P4TS-20261109), D-number outstanding.
- 2026-11-10: D-U1 (P5) calibration with caveat. D-U3 (P6) same-build. D-U2 (P7) two zero-spend baselines first; margins preregistered before any run (RR-P7BASE-20261110).

## Open decisions for the owner (D-numbered, options, your recommendation)
- D13 (Pkt 1) ANSWERED 2026-11-08: Pillar-1 splits (replayable + conformance-testable kept; "diffable" behind the consumer profile; "reconstructs any turn" narrowed; absence reworded). Card: `design/diff-normalisation.md`. Owner next: ratify + route with the six-item bundle.
- D14 (Pkt 3) ANSWERED 2026-11-08: capture default-on in owner-run builds; release rule bound (no silent-default release; first-run notice minimum, opt-in stronger) — plugin card at D6, timing at D17; redaction card authored proposal-only, sidecar-first (`RR-P3REDACT`; block = assertion; keyed-hash deferred). Card `design/redaction-block.md` (owner-cleared); owner next: §4-LIST.
- D15 paper structure: keep Part I + II; merge only after D13/D14. Recommend keep.
- D16 W8 amendment: (a) reopen with a task set whose floor < 24k; (b) amend arm value/budget + prereg first. Recommend (a) with (b) documented, under `design/W8-PROMPT-SLICE.md` gates.
- D17 publication: (a) now; (b) after D13–D15; (c) hold. Recommend (b).

## Do not touch (sealed specs, frozen fixtures, plugin defaults)
`spec/rfc-0/` byte-sealed; the RFC-0.1 additive law (all five touchpoints, ts last); `corpus/` checksums; `design/` plans of record; `08.1-UPDATE-PROMPT.md`; `research/**` (white-paper lane); capture default-on + plugin version bumps (need a card); append-only `reports/LOG.md`.

## Evidence rules (the integrity rules, three lines)
1. Every number carries a repo locator + repro command; gate totals from `bash tools/run-ci.sh` are authoritative, never hardcoded (AGENTS.md §2, §5).
2. Unverified claims stay marked UNVERIFIED, never asserted; first mention carries a locator.
3. No cost-saving claim: none measured on our data; arXiv:2610.22732v1's 18.4–30.9% belongs to an external controller (AGENTS.md law 7).

## Verification status (gate pointer, UNVERIFIED items and what would verify each)
- Conformance gate: GREEN 2026-11-08 (nine-key `env -u` + `bash tools/run-ci.sh`; proven local, run №90, AND hosted run №94 `42589188792` at `cd43555`, 4/4, 37 s, 2026-11-09); log `/tmp/opencode/otel/gate-d3c.log`. Snapshot dated; totals re-derivable via run-ci.
- XERJ Hub listing UNVERIFIED — live `hub.xerj.org/llms.txt` re-check (RR-XERJ-20261029).
- openai price row + cache-read nulls UNVERIFIED (`prices.json`) — owner source.
- W8 arm-attribution rule SUPERSEDED by plan §4e (`b6aa2a3`: one host gateway, attestation-scope equality); UNPROVEN until a probe runs.
- Part II METR secondary figures UNVERIFIED until a primary locator exists.
- Hard-fault-recall ≥95% gate UNMEASURED (n=4 < 30) — pooled runs.

## Blocked (item, what it waits for)
- W8 reopen: owner go + packet P9. Remaining spend UNVERIFIED (>= $7.14 billed 11-10; store $9.16/3d; RR-SPEND-RECON2).
- Publication: owner (D17). W12 beyond Steps 0–1: D7 ruled hold (`design/runtime-abi/00-reconciliation-and-justification.md`).
- `/tmp/w8` run tree: DESTROYED (a `/tmp` clear; erratum `RR-W8INDEX-20261107` @ `a1d2efb`); go-forward runs → `~/.local/state/ctxvm/w8-runs`.
