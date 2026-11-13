# State (updated 2026-11-13, by ctxvm repo agent (opencode); G2/D-U1 applied, D13+D14 routed, W8C+W8D reviewed)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > identical traces > falsifiable metrics > packaging.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`); RFC-0.1 additive landed (`spec/rfc-0.1/`). Corpus: ODPS 0.8.0, m1–m8 checksummed; hub byte-identical. Plugins: hermes 0.13.22 (`packages/hermes/live/__init__.py:94`); node 0.1.0, opencode 0.0.1, ai-sdk 0.0.1.
- Papers: Part I committed + WIP revision; Part II untracked (`RR-WP2REV-20261107`); 6-item bundle routed (`RR-WPROUTE-20261112`). Capture: deepseek-v4.1-flash-1017 on nous; `~/.local/state/ctxvm/traces`; budget 200000.

## Done (last 3 items: one line each, with locators)
1. W8C replay verified (0.13.22 capture): 81 events, 0 divergences, stdout hash `fe27e29c813c4e06` ×3; `export --turn 12` = 21 slots / 86,569 / 0 stubbed (`RR-W8CREPLAY*`).
2. Representation gap confirmed by the provider's receipts: the derived table is turn-invariant (21 slots / 86,569, turns 0–19) and false about the request (12 pages / 47,805 carried); provider ratio 0.563 vs the trace's 0.570 ⇒ removal right, table false (`RR-SHAPEGAP-20261113`).
3. W8D erratum reviewed: five inputs verified, three arithmetic errors (denominator 42 not 41; "0.918" inverted + tokenizers mixed; "16 rewrite events" unsupported ⇒ 9), model check self-contradicting (9 whole-request writes fit within 0.2 %, 16 miss by 1.76×) ⇒ hold-once is a set-level no-op (`RR-W8DERRATUM-20261113`).

## In progress (one item: what, blocker, next command)
- Research lane: apply the routed six-item bundle (`reports/RR-WPROUTE-20261112.md`) to `research/white-paper/white-paper.md`, `index.md`, `white-paper-Part-II.md`. Blocker: the research lane's own edits.
- Hermes lane (ask, zero spend): keep the per-call dropped **identities** beside `callSizes` in the sidecar — the observer computes them (`live/context_engine.py:545-548`), the adapter folds them into a union (`live/__init__.py:1498-1500`) ⇒ W8D §5 step 1 becomes a lookup.

## Next three (ordered, one line each)
1. Owner: rule G4 (`design/redaction-block.md` §4-LIST go/defer) + ratify the release rule at D6/D17.
2. Owner: D17 timing after the routed D13/D14 edits land in `research/**` (G6).
3. Owner: G3 (W9 equivalence-test preregistration before any new held-out capture).

## Decisions made (date, decision, reason)
- 2026-10-30 → 2026-11-10: D3-c OTel layered; D4 adopts RFC-0.1; D8 splits → schemaVersion first; D12 est* keep page-table semantics; W8 vBudget 24,000, W8 ruled FAILED, capture default-on; D13+D14 answered; P4 ts optional + umpire ordering; D-U1 caveat, D-U3 same-build, D-U2 two zero-spend baselines (RR-DECISIONS-20261030 … RR-P7BASE-20261110).
- 2026-11-11: F1–F7 closed; P10+P11 answered; W8B closed negative; D18 RFC-0.1 note (`82f6a03`).
- 2026-11-12: D-U10 (G1) + D-U1 (G2) applied; Prediction-block rule ratified (`685c999`); paid spend stopped after cell-03 ($0.2534, RR-PAIDRESULT-20261112); D13+D14 ratified, bundle routed (G5 closed).
- 2026-11-13: W8C review chain closed — "0 stubs" withdrawn (entailed by the event vocabulary), `evictedTokens` is a lagging cumulative (210,856 = 5.44× the unique 38,764), the W8D erratum corrected three ways, hold-once refused as a set-level no-op; no paid spend (`RR-SHAPEGAP-20261113`, `RR-W8DERRATUM-20261113`).

## Open decisions for the owner (D-numbered, options, your recommendation)
- D13 RATIFIED & ROUTED 2026-11-12: Pillar-1 splits + echo sweep (`design/diff-normalisation.md`, RR-WPROUTE Items 1–2).
- D14 RATIFIED & ROUTED 2026-11-12: capture default-on in owner-run builds; release rule bound at D6/D17; redaction card proposal-only, sidecar-first (`design/redaction-block.md`, RR-WPROUTE Items 5–6). Owner next: §4-LIST go/defer (G4).
- D15 paper structure: keep Part I + II; merge only after D13/D14 edits land. Recommend keep.
- D16 W8 amendment: W8/W8B closed negative; W8C measured, paid spend stopped after cell-03 (0.57x final request, 2.11x cost from 4.49x cache writes); W8D refused on arithmetic — hold-once cannot change the dropped set (already monotone), and the zero-spend gate cannot discriminate ⇒ next policy work is zero-spend only (RR-POLICYCHOICE-20261112, RR-W8DERRATUM-20261113).
- D17 publication: (a) now; (b) after D13–D15; (c) hold. Recommend (b).

## Do not touch (sealed specs, frozen fixtures, plugin defaults)
`spec/rfc-0/` byte-sealed; RFC-0.1 additive law (five touchpoints, ts last); `corpus/` checksums; `design/` plans of record; `08.1-UPDATE-PROMPT.md`; `research/**` (white-paper lane); capture default-on + plugin bumps (card needed); append-only `reports/LOG.md`.

## Evidence rules (the integrity rules, three lines)
1. Every number carries a repo locator + repro command; gate totals from `bash tools/run-ci.sh` are authoritative, never hardcoded (AGENTS.md §2, §5).
2. Unverified claims stay marked UNVERIFIED. No cost-saving claim: none measured on our data; arXiv:2610.22732v1's 18.4–30.9% is an external controller's (AGENTS.md law 7).

## Verification status (gate pointer, UNVERIFIED items and what would verify each)
- Conformance gate: GREEN 2026-11-13 (`run-ci.sh` → ALL GATES GREEN); hosted witness №123 `f16df322` (2026-11-12) green.
- XERJ Hub listing UNVERIFIED (re-check `hub.xerj.org/llms.txt`). openai price row + cache-read nulls UNVERIFIED (`prices.json`). Part II METR secondary figures UNVERIFIED. Hard-fault-recall ≥95% gate UNMEASURED (n=4).
- W8D rewrite-event count: 9 (billed volume) vs 16 (selections) — per-call identities not persisted ⇒ UNVERIFIED until the sidecar keeps them.

## Blocked (item, what it waits for)
- W8 spend: >= $7.14 billed 11-10 + $0.2534 cell-03 (11-12); paid spend stopped until a zero-spend simulation predicts a win; W8D refused on arithmetic (RR-W8DERRATUM-20261113).
- Publication: owner (D17). W12 beyond Steps 0–1: D7 ruled hold. `/tmp/w8` run tree: DESTROYED (`RR-W8INDEX-20261107`); go-forward runs → `~/.local/state/ctxvm/w8-runs`.
