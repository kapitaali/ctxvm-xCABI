# State (updated 2026-11-09, by ctxvm repo agent (opencode), after the P3 card's hosted-run witness: run №94 green at cd43555)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > second harness identical traces > falsifiable metrics > packaging. W8 closed FAILED by the owner.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`, byte-frozen); RFC-0.1 additive landed (`spec/rfc-0.1/`, R0–R5).
- Corpus: ODPS 0.8.0, m1–m8 checksummed; hub ODPC byte-identical.
- Plugins: hermes 0.10.6 (`packages/hermes/live/__init__.py:94`); @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1.
- Papers: Part I committed + the white-paper lane's UNCOMMITTED revision; Part II untracked (`RR-WP2REV-20261107`).
- Everyday capture: deepseek-v4.1-flash-1017 on nous; `~/.local/state/ctxvm/traces`; budget 200000 (RR-WP2REV §Verification).

## Done (last 3 items: one line each, with locators)
1. A1–A6 adoption batch (2026-11-09): RR-IMPL2/RR-FRICTION/RR-FINDING/RR-PKG/RR-CHANNELS/RR-UMPIRE + packets P4–P7.
2. P3 (D14) answered; redaction card authored proposal-only, sidecar-first — `design/redaction-block.md` (owner-cleared).
3. P2 answered; seq 7 located — source `identifier_scan`, swap-in cause active (`reports/RR-P2DEMO-20261108.md`).

## In progress (one item: what, blocker, next command)
Part II revision (absorbs D13's sentence; `RR-WP2REV-20261107`). Blocker: that lane's WIP + owner routing.

## Next three (ordered, one line each)
1. Owner: ratify D13 + D14, route the white-paper bundle — SIX paper items: Pillar-1 split; `:635` echo sweep; the P2 demo sentence (`:333`/`:339`, `identifier_scan` cause); the R1 3-to-0 contrast; the consent-paragraph replacement (`white-paper.md:620–623`, index twin, Part II `:368`); Part II's card-citation rule — working-tree bytes, not HEAD.
2. Owner: ratify the release rule + §4-LIST at D6/D17 (placement DONE: `design/redaction-block.md`).
3. Agent: A1 A2 A5 A3 A4 A6 done (RR-IMPL2/RR-FRICTION/RR-FINDING/RR-PKG/RR-CHANNELS/RR-UMPIRE). Owner gates: D13/D14/D17 + umpire (A6) + P4–P7 verdicts.

## Decisions made (date, decision, reason)
- 2026-10-30/31: D3-c = OTel layered mapping, not native; D4 adopts RFC-0.1; D8 splits → schemaVersion first (RR-DECISIONS-20261030, RR-RFC01E1-20261031).
- 2026-11-01: D12 — est* estimates keep page-table semantics (RR-W8PREREG-20261101).
- 2026-11-06: W8 keeps vBudget 24,000; only tasks with a floor below it measure (RR-ENGINEGAP-20261106 rec. 2).
- 2026-11-07: W8 ruled FAILED; capture stays default-on; contract restored (RR-W8CHUNK-20261107-2b + RR-W8INDEX).
- 2026-11-08: D3-c approved (owner); D13 answered (P1); P2 answered + seq 7 located (`identifier_scan` swap-in).
- 2026-11-09: D14 answered (P3 verdicts recorded); redaction card authored proposal-only (sidecar-first); consent mends + Part II card-citation rule routed.

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
- W8 reopen: owner go + `design/W8-PROMPT-SLICE.md` gates + USD 23.8459 left (reports/W8-SPEND.md).
- Publication: owner (D17). W12 beyond Steps 0–1: D7 ruled hold (`design/runtime-abi/00-reconciliation-and-justification.md`).
- `/tmp/w8` run tree: DESTROYED (a `/tmp` clear; erratum `RR-W8INDEX-20261107` @ `a1d2efb`); go-forward runs → `~/.local/state/ctxvm/w8-runs`.
