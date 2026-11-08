# State (updated 2026-11-08, by ctxvm repo agent (opencode), after the D3-c exporter promotion card)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > second harness identical traces > falsifiable metrics > packaging. W8 closed FAILED by the owner.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`, byte-frozen); RFC-0.1 additive landed (`spec/rfc-0.1/`, R0–R5).
- Corpus: ODPS 0.8.0, m1–m8 checksummed; hub ODPC byte-identical.
- Plugins: hermes 0.10.5 (`packages/hermes/live/__init__.py:94`); @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1.
- Papers: Part I committed + an UNCOMMITTED working-tree revision (`research/white-paper/white-paper.md`, white-paper lane's); Part II untracked draft, reviewed in `reports/RR-WP2REV-20261107.md`.
- Everyday capture: deepseek-v4.1-flash-1017 on nous, `~/.local/state/ctxvm/traces`, `ctxvm-dev`, budget 200000 — full values in RR-WP2REV §Verification.

## Done (last 3 items: one line each, with locators)
1. D3-c exporter promotion: supported surface + field-set drift guard; 2 ci.yml mirror defects fixed (`reports/RR-D3COTEL-20261108.md`).
2. P1 answered; diff-normalisation proposal authored (`design/diff-normalisation.md`; `reports/RR-DIFFNORM-20261108.md`; D13).
3. W8 closure index after the FAILED ruling (`reports/RR-W8INDEX-20261107.md`).

## In progress (one item: what, blocker, next command)
Part II revision per RR-WP2REV-20261107 (absorbs D13's sentence). Blocker: that lane's WIP + owner routing. Next: `git status --short research/`.

## Next three (ordered, one line each)
1. Owner: ratify D13 + route the Part I edit to the white-paper lane (incl. `:635` + echo sweep) — working-tree bytes, not HEAD.
2. Owner: answer packets P2/P3 (`handoff/QUESTIONS.md`) — P2 framing + D14.
3. Agent: un-gated queue is EMPTY (board + frontier 9) — next cards come from owner gates (D16, D17) or P2/P3 verdicts.

## Decisions made (date, decision, reason)
- 2026-10-30: D3-c OTel layered mapping, not native; D4 RFC-0.1 adopted (RR-DECISIONS-20261030).
- 2026-10-31: D8 split — schemaVersion emission first (RR-RFC01E1-20261031).
- 2026-11-01: D12 — est* estimates keep page-table semantics (RR-W8PREREG-20261101).
- 2026-11-06: W8 keeps vBudget 24,000; only tasks with a floor below it measure (RR-ENGINEGAP-20261106 rec. 2).
- 2026-11-07: W8 ruled FAILED; capture stays default-on; contract restored (RR-W8CHUNK-20261107-2b + RR-W8INDEX).
- 2026-11-08: D3-c promotion approved (owner, in-session); D13 answered by the reviewer (P1).

## Open decisions for the owner (D-numbered, options, your recommendation)
- D13 (Pkt 1) ANSWERED 2026-11-08: Pillar-1 splits — replayable + conformance-testable kept; "diffable" behind the consumer-side profile; "reconstructs any turn" narrowed; absence claim reworded (+ scope). Card: `design/diff-normalisation.md`. Owner next: ratify + route the paper edit (echo sweep incl. `:635`).
- D14 (Pkt 3) capture + redaction: keep capture default-on (RR-PLUGIN-DEFAULTS-20261101); (a) redaction stays prose; (b) author the §18 session redaction block additive proposal-only. Recommend (b).
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
- Conformance gate: GREEN 2026-11-08 (nine-key `env -u` chain + `bash tools/run-ci.sh`; otel guard + mirror fixes proven local AND on Actions run 42468046847, 4/4 in 52 s); log `/tmp/opencode/otel/gate-d3c.log`.
- XERJ Hub listing UNVERIFIED — live `hub.xerj.org/llms.txt` re-check (RR-XERJ-20261029).
- openai price row + cache-read nulls UNVERIFIED (`benchmarks/metrics/prices.json`) — owner source confirmation.
- Pre-restart W8 pair arm attribution UNPROVEN — one 0.10.5 gateway per arm (RR-W8INDEX-20261107 (e)).
- Part II METR secondary figures UNVERIFIED until a primary locator exists.
- Hard-fault-recall ≥95% gate UNMEASURED (n=4 < 30) — pooled runs.

## Blocked (item, what it waits for)
- W8 reopen: owner go + `design/W8-PROMPT-SLICE.md` gates + USD 23.8459 left (reports/W8-SPEND.md).
- Publication: owner (D17). W12 beyond Steps 0–1: D7 ruled hold (`design/runtime-abi/00-reconciliation-and-justification.md`).
- `/tmp/w8` archive: owner action before reboot.
