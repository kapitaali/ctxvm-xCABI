# State (updated 2026-11-19; E1 approved, G4 done, H12 negative, D17 held)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > identical traces > falsifiable metrics > packaging.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`); RFC-0.1 additive landed (`spec/rfc-0.1/`). Corpus: ODPS 0.8.0, m1–m8 checksummed; hub byte-identical. Plugins: hermes (authoritative: `live/__init__.py:94` + `live/plugin.yaml:2`; **0.13.27** on 2026-11-19, H12 pair live); node 0.1.0, opencode/ai-sdk 0.0.1.
- Papers: P13/P14 applied (`e10d249`); Part III landed (`5ab5d38`); PDF 26pp, recalculated. Live traces private under `~/.local/state/ctxvm/traces`; budget 200000.

## Done (last 3 items: one line each, with locators)

1. (Items 1–2 rotated verbatim 2026-11-15 to `handoff/PROJECT-STATE-ARCHIVE.md`.)
2. H12 NEGATIVE, mode engaged: no hold on read-once sweep; mid-prefix hole defeats cache (`RR-H12RESULT-20261119`).
## In progress (one item: what, blocker, next command)
- Research lane: P13/P14 (`e10d249`), Part III + §9.2 fix (`d10c325`, `99f62f9`), `datamining/` tracked (`97cf743`), E1 LANDED (`a1bd004`), `fixture-bank/` Phase 0 LANDED & VERIFIED (`12a9809`, `RR-FIXBANK-REVIEW`: 242/242; precondition only, E0/E2 $0).
- Hermes lane: free queue DONE & VERIFIED; harnessVersion fixed via canonical resolver (`RR-HVREV-20261119`, verified `RR-FIXBANK-REVIEW`), 0.13.29 synced, suite 229; restart owed.

- **dsh lane (W22):** CLOSED. All 7 acceptance items DONE; T-B capture full run COMPLETE 581/588 (`RR-TBDSHFULL`); counter fix verified (`RR-TBDSHCOUNTER-FIX`). Corpus naming deferred to Phase 2 (`RR-DSHPARK`); Plan D other lane.
- Gateway: pid 4486 (11:13 restart 11-19) holds 0.13.27; paged captures landed (`h12p2`); `enginePlan` live by capture (`RR-H12DIAG-REVIEW`).
## Next three (ordered, one line each)
1. All routed hermes, research, and review queues DONE & VERIFIED (`RR-H16H18-REVIEW`, `RR-E2HOLD-VERIFY`, `RR-FIXBANK-REVIEW`).
2. E0/E2 HELD at $0 (`research/fixture-bank/` Phase 0 landed `12a9809`; E0 route & E2 ceiling owner-gated, `RR-E2HOLD`); W8 parked (`RR-DEFAULTS`).
3. G3 design APPROVED; umpire-side prereg owed in separate repo (owner clearance). D17 held; D19/P11/H19 owner-gated.

## Decisions made (date, decision, reason)
- 2026-10-30 → 2026-11-10: D3-c OTel layered; D4 adopts RFC-0.1; D8 splits → schemaVersion first; D12 est* keep page-table semantics; W8 ruled FAILED, capture default-on; D-U1 caveat, D-U3 same-build, D-U2 two baselines (`RR-DECISIONS-20261030` … `RR-P7BASE-20261110`).
- 2026-11-11: F1–F7 closed; P10+P11 answered; W8B closed negative; D18 RFC-0.1 note (`82f6a03`).
- 2026-11-12: D-U10 (G1) + D-U1 (G2) applied; Prediction-block rule ratified (`685c999`); paid spend stopped after cell-03 ($0.2534, `RR-PAIDRESULT`); D13+D14 ratified (G5 closed).
- 2026-11-13: W8C review chain closed — "0 stubs" withdrawn (entailed by the vocabulary), `evictedTokens` is a lagging cumulative (210,856 = 5.44× the unique 38,764), the W8D erratum corrected three ways, hold-once refused as a no-op; P12 ruled: the wire (`RR-SHAPEGAP`, `RR-W8DERRATUM`, `RR-OMISSIONANSWER`).
- 2026-11-19: E1 LANDED (`a1bd004`); `fixture-bank/` Phase 0 (`12a9809`/`RR-FIXBANK-REVIEW`, precondition only; E0/E2 $0, `RR-E2HOLD`); G4 DONE (`9e755d4`/`056fd94`); H12 NEGATIVE (`RR-H12RESULT`); H13/H15/H16–H18 DONE (`43e46d1`/`93d338d`).

## Open decisions for the owner (D-numbered, options, your recommendation)
- D13 RATIFIED & ROUTED 11-12: Pillar-1 splits + echo sweep (`design/diff-normalisation.md`; RR-WPROUTE 1–2).
- D14 RATIFIED: capture default-on in owner builds; release rule bound D6/D17; redaction sidecar-first (`design/redaction-block.md`). G4 GO 18 Nov (`RR-G4GO`): sidecar assertion only; ROUTED 19 Nov (`RR-G4ROUTE`); IMPL landed 19 Nov (`RR-REDACTIMPL`).
- D15 paper structure: keep Part I + II; merge only after the D13/D14 edits land. Recommend keep.
- D16 W8: W8/W8B negative; W8C measured (0.57x request, 2.11x cost); paid spend stopped; W8D refused — zero-spend policy work only (`RR-POLICYCHOICE`).
- D17 HELD 2026-11-18 (c): packages/registries unreleased until owner judges enough data (no threshold/date). Repo/PDF/hub stay public; D6/D14 consent binds at release (`RR-D17RULING`).
- D19 omission representation: REVIEWER-RULED 2026-11-13 = the wire (optional, omitted-when-unknown, per-call list of removed-page identities; sidecar = documented fallback; per-call fail-closed check; scoped view = an addition under a new name) (`RR-OMISSIONANSWER`); owner: ratify + pick placement, names, D-number.

## Do not touch (sealed specs, frozen fixtures, plugin defaults)
`spec/rfc-0/` byte-sealed; RFC-0.1 additive law (five touchpoints, ts last); `corpus/` checksums; `design/` plans of record; `08.1-UPDATE-PROMPT.md`; `research/**` (white-paper lane); capture default-on + plugin bumps (card); `reports/LOG.md` append-only.

## Evidence rules (the integrity rules, three lines)
1. Every number carries a repo locator + repro command; gate totals from `bash tools/run-ci.sh` are authoritative (AGENTS.md §2).
2. Unverified claims stay marked UNVERIFIED. No cost-saving claim: none measured on our data; arXiv:2610.22732v1's 18.4–30.9% is an external controller's (law 7).

## Verification status (gate pointer, UNVERIFIED items and what would verify each)
- Conformance gate: GREEN 2026-11-13 (`run-ci.sh` → ALL GATES GREEN); hosted witness №123 `f16df322` green.
- XERJ Hub listing UNVERIFIED (re-check `hub.xerj.org/llms.txt`). openai price row + cache-read nulls UNVERIFIED (`prices.json`). Part II METR figures UNVERIFIED. Hard-fault-recall ≥95% UNMEASURED (n=4).
- W8D rewrite-events: 9 vs 16 — mechanism confirmed on 0.13.27 paged capture (RR-UNVERIFIED); counts historical.

## Blocked (item, what it waits for)
- W8 spend: >= $7.14 billed 11-10 + $0.2534 cell-03 (11-12); stopped until a zero-spend simulation predicts a win; W8D refused (`RR-W8DERRATUM`).
- Publication: D17 RULED hold until enough data (2026-11-18, `RR-D17RULING`); no registry/catalog action without a new owner ruling.
