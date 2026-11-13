# State (updated 2026-11-12, by ctxvm repo agent (opencode); D13+D14 ratified & routed, W8C S3, plugin 0.13.15

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > identical traces > falsifiable metrics > packaging.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`, byte-frozen); RFC-0.1 additive landed (`spec/rfc-0.1/`, R0–R5).
- Corpus: ODPS 0.8.0, m1–m8 checksummed; hub ODPC byte-identical.
- Plugins: hermes 0.13.15 (`packages/hermes/live/__init__.py:94`); @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1.
- Papers: Part I committed + WIP revision; Part II untracked (`RR-WP2REV-20261107`); 6-item bundle routed (`RR-WPROUTE-20261112`).
- Everyday capture: deepseek-v4.1-flash-1017 on nous; `~/.local/state/ctxvm/traces`; budget 200000 (RR-WP2REV §Verification).

## Done (last 3 items: one line each, with locators)
1. D13 + D14 ratified and the six-item white-paper bundle routed to the research lane; G5 closed (RR-WPROUTE-20261112).
2. Plugin 0.13.15 + `sim(S3)` quantization scorer: uncensored `CALL_LOG`, `plugin.engine` + `evictedPagesCount` confirmed, `upstream/` draft deleted (RR-W8SIM3-20261112, RR-SIM3S3CHECK-20261112).
3. W8C paid cell-03 (`openai/gpt-6-luna`): $0.2534 total, 0.57x final request, 2.11x dollars, 4.49x cache writes; paid spend stopped (RR-PAIDRESULT-20261112).

## In progress (one item: what, blocker, next command)
Research lane: apply the routed six-item white-paper bundle (`reports/RR-WPROUTE-20261112.md`) to working-tree `research/white-paper/white-paper.md`, `index.md`, and `white-paper-Part-II.md`.

## Next three (ordered, one line each)
1. Owner: approve G2 (caller transfer-caveat sentence in umpire `mcp_server.py` + `00-SPEC.md` §3, ratifying into D-U1; pre-verified in RR-UMPIREREADY-20261111).
2. Owner: rule G4 (`design/redaction-block.md` §4-LIST go/defer) and ratify the release rule at D6/D17.
3. Owner: D17 publication timing after the routed D13/D14 white-paper edits land in `research/**`.

## Decisions made (date, decision, reason)
- 2026-10-30/31: D3-c = OTel layered mapping, not native; D4 adopts RFC-0.1; D8 splits → schemaVersion first (RR-DECISIONS-20261030, RR-RFC01E1-20261031).
- 2026-11-01: D12 — est* estimates keep page-table semantics (RR-W8PREREG-20261101).
- 2026-11-06: W8 keeps vBudget 24,000; only tasks with a floor below it measure (RR-ENGINEGAP-20261106 rec. 2).
- 2026-11-07: W8 ruled FAILED; capture stays default-on; contract restored (RR-W8CHUNK-20261107-2b + RR-W8INDEX).
- 2026-11-08: D3-c approved; D13 answered (P1); P2 answered + seq 7 located (`identifier_scan` swap-in).
- 2026-11-09: D14 answered (P3 verdicts); P4 answered: ts stays optional; ordering clause for umpire §2 (RR-P4TS-20261109).
- 2026-11-10: D-U1 (P5) caveat; D-U3 (P6) same-build; D-U2 (P7) two zero-spend baselines first (RR-P7BASE-20261110).
- 2026-11-11: F1–F7 closed; P10+P11 answered; W8B closed negative (`design/W8B-CLOSURE-20261111.md`); D18 RFC-0.1 note (`spec/rfc-0.1/COMPATIBILITY.md`, `82f6a03`).
- 2026-11-12: D-U10 (G1) applied (RR-G1APPLIED-20261112); Prediction-block rule ratified (`685c999`); paid spend stopped after cell-03 ($0.2534, RR-PAIDRESULT-20261112); D13 + D14 ratified and 6-item paper bundle routed (RR-WPROUTE-20261112, G5 closed).

## Open decisions for the owner (D-numbered, options, your recommendation)
- D13 (Pkt 1) RATIFIED & ROUTED 2026-11-12: Pillar-1 splits + echo sweep (`design/diff-normalisation.md`, `reports/RR-WPROUTE-20261112.md` Items 1–2).
- D14 (Pkt 3) RATIFIED & ROUTED 2026-11-12: capture default-on in owner-run builds; release rule bound at D6/D17; redaction card proposal-only, sidecar-first (`design/redaction-block.md`, `reports/RR-WPROUTE-20261112.md` Items 5–6). Owner next: §4-LIST go/defer (G4).
- D15 paper structure: keep Part I + II; merge only after D13/D14 edits land. Recommend keep.
- D16 W8 amendment: W8/W8B closed negative; W8C measured and paid spend stopped after cell-03 (0.57x final request, 2.11x cost due to 4.49x cache writes; cache-stable ceiling ~$0.009/session, RR-POLICYCHOICE-20261112). Next policy work is zero-spend simulation only.
- D17 publication: (a) now; (b) after D13–D15; (c) hold. Recommend (b).

## Do not touch (sealed specs, frozen fixtures, plugin defaults)
`spec/rfc-0/` byte-sealed; the RFC-0.1 additive law (all five touchpoints, ts last); `corpus/` checksums; `design/` plans of record; `08.1-UPDATE-PROMPT.md`; `research/**` (white-paper lane); capture default-on + plugin version bumps (need a card); append-only `reports/LOG.md`.

## Evidence rules (the integrity rules, three lines)
1. Every number carries a repo locator + repro command; gate totals from `bash tools/run-ci.sh` are authoritative, never hardcoded (AGENTS.md §2, §5).
2. Unverified claims stay marked UNVERIFIED, never asserted; first mention carries a locator.
3. No cost-saving claim: none measured on our data; arXiv:2610.22732v1's 18.4–30.9% belongs to an external controller (AGENTS.md law 7).

## Verification status (gate pointer, UNVERIFIED items and what would verify each)
- Conformance gate: GREEN 2026-11-12 (local hermetic `run-ci.sh` + `ci-rehearsal.py --committed` → ALL GATES GREEN); hosted witness №123 `f16df322` (2026-11-12) green.
- XERJ Hub listing UNVERIFIED — live `hub.xerj.org/llms.txt` re-check (RR-XERJ-20261029).
- openai price row + cache-read nulls UNVERIFIED (`prices.json`) — owner source.
- Part II METR secondary figures UNVERIFIED until a primary locator exists.
- Hard-fault-recall ≥95% gate UNMEASURED (n=4 < 30) — pooled runs.

## Blocked (item, what it waits for)
- W8 spend: >= $7.14 billed 11-10 + $0.2534 cell-03 (11-12); paid W8C spend stopped until a zero-spend simulation predicts a win (RR-PAIDRESULT-20261112).
- Publication: owner (D17). W12 beyond Steps 0–1: D7 ruled hold (`design/runtime-abi/00-reconciliation-and-justification.md`).
- `/tmp/w8` run tree: DESTROYED (erratum `RR-W8INDEX-20261107` @ `a1d2efb`); go-forward runs → `~/.local/state/ctxvm/w8-runs`.
