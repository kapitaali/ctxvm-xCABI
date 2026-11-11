# State (updated 2026-11-11, by ctxvm repo agent (opencode), U6 applied; RFC-0.1 note + C3 enforced (D18)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > identical traces > falsifiable metrics > packaging. W8 CLOSED negative (design/W8-CLOSURE-20261110.md).

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`, byte-frozen); RFC-0.1 additive landed (`spec/rfc-0.1/`, R0–R5).
- Corpus: ODPS 0.8.0, m1–m8 checksummed; hub ODPC byte-identical.
- Plugins: hermes 0.10.11 (`packages/hermes/live/__init__.py:94`); @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1.
- Papers: Part I committed + the white-paper lane's UNCOMMITTED revision; Part II untracked (`RR-WP2REV-20261107`).
- Everyday capture: deepseek-v4.1-flash-1017 on nous; `~/.local/state/ctxvm/traces`; budget 200000 (RR-WP2REV §Verification).

## Done (last 3 items: one line each, with locators)
1. U2 + U6 verified live (RR-U2LIVE): health ok; a decide runs on the record's map (cal-v1:057a5a35a9d4ec71); the gateway wrapper awaits a restart.
2. RFC-0.1 note + C3 enforced (D18): code-point comparator + vector; no digest moved; CI green.
3. P11 gap (RR-P11GAP-20261111): the pair asserts TWO levels; level-2 patch drafted.

## In progress (one item: what, blocker, next command)
Part II revision (absorbs D13's sentence; `RR-WP2REV-20261107`). Blocker: that lane's WIP + owner routing.

## Next three (ordered, one line each)
1. Owner: ratify D13 + D14 and route the SIX-item white-paper bundle (items listed in full in RR-DAY-20261109) — working-tree bytes, not HEAD.
2. Owner: ratify the release rule + §4-LIST at D6/D17 (placement DONE: `design/redaction-block.md`).
3. Agent: NO paste pending (P1-P11 answered); owner-routed: hub $ref, T-A arm precondition. Umpire gates: D-ordering (P4), caller (P5), vocab (P6).

## Decisions made (date, decision, reason)
- 2026-10-30/31: D3-c = OTel layered mapping, not native; D4 adopts RFC-0.1; D8 splits → schemaVersion first (RR-DECISIONS-20261030, RR-RFC01E1-20261031).
- 2026-11-01: D12 — est* estimates keep page-table semantics (RR-W8PREREG-20261101).
- 2026-11-06: W8 keeps vBudget 24,000; only tasks with a floor below it measure (RR-ENGINEGAP-20261106 rec. 2).
- 2026-11-07: W8 ruled FAILED; capture stays default-on; contract restored (RR-W8CHUNK-20261107-2b + RR-W8INDEX).
- 2026-11-08: D3-c approved (owner); D13 answered (P1); P2 answered + seq 7 located (`identifier_scan` swap-in).
- 2026-11-09: D14 answered (P3 verdicts recorded); consent mends + card-citation rule routed. P4 answered: ts stays optional; ordering clause PROPOSED for umpire §2 (RR-P4TS-20261109), D-number outstanding.
- 2026-11-10: D-U1 (P5) caveat; D-U3 (P6) same-build; D-U2 (P7) two zero-spend baselines first (RR-P7BASE-20261110).
- 2026-11-11: F1–F7 closed; P10+P11 answered.
- 2026-11-11: subject fallback APPROVED: nvidia (tested) -> stepfun -> accept longcat too slow.
- 2026-11-11: D18 — RFC-0.1 note applied (`spec/rfc-0.1/COMPATIBILITY.md`): C1 dispatch, C2 key-order + test, C3 canonical form for hashes; C3 then enforced in code (no digest moved; CI green).

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
- Conformance gate: GREEN 2026-11-11 (local, HEAD `f8e063c`; env-correct run-ci.sh → ALL GATES GREEN); hosted witness №94 `42589188792` (2026-11-09) stands.
- XERJ Hub listing UNVERIFIED — live `hub.xerj.org/llms.txt` re-check (RR-XERJ-20261029).
- openai price row + cache-read nulls UNVERIFIED (`prices.json`) — owner source.
- W8 arm-attribution rule SUPERSEDED by plan §4e (`b6aa2a3`: one host gateway, attestation-scope equality); UNPROVEN until a probe runs.
- Part II METR secondary figures UNVERIFIED until a primary locator exists.
- Hard-fault-recall ≥95% gate UNMEASURED (n=4 < 30) — pooled runs.

## Blocked (item, what it waits for)
- W8 spend: >= $7.14 billed 11-10; store $9.16/3d; remaining UNKNOWN (RR-SPEND-RECON2).
- Publication: owner (D17). W12 beyond Steps 0–1: D7 ruled hold (`design/runtime-abi/00-reconciliation-and-justification.md`).
- `/tmp/w8` run tree: DESTROYED (a `/tmp` clear; erratum `RR-W8INDEX-20261107` @ `a1d2efb`); go-forward runs → `~/.local/state/ctxvm/w8-runs`.
