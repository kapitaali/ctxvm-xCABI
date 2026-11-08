# State (updated 2026-11-08, by ctxvm repo agent (opencode), after building the session-continuity kit)

## Goal
Make xCABI an adoptable open trace standard (08.1-UPDATE-PROMPT.md §1). Priority: real data > second harness identical traces > falsifiable metrics > packaging. W8 closed FAILED by the owner.

## Artifacts and versions
- Wire: RFC-0 sealed (`spec/rfc-0/`, v0, byte-frozen); RFC-0.1 additive landed (`spec/rfc-0.1/`, R0–R5; `schemaVersion: "0.1"` emitted).
- Corpus: ODPS manifest productVersion 0.8.0, drops m1–m8, checksummed (`04-odps-dataproduct-corpus.yaml:7–13`); hub ODPC catalog regen byte-identical.
- Plugins: hermes 0.10.5 (`packages/hermes/live/__init__.py:94`); @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1 (packages/*/package.json).
- Papers: Part I committed (`research/white-paper/white-paper.md`, PDF synced) plus an UNCOMMITTED working-tree revision (white-paper lane's). Part II: untracked `research/white-paper-Part-II.md` (v1.0 draft), reviewed in `reports/RR-WP2REV-20261107.md`; no committed Part II.
- Everyday capture contract: deepseek-v4.1-flash-1017, `~/.local/state/ctxvm/traces`, budget 200000 — full verbatim values in `reports/RR-WP2REV-20261107.md` §Verification.

## Done (last 7 items: one line each, with report path)
1. Session-continuity kit: handoff/ files + packets + the two tools (`reports/RR-HANDOFF-20261108.md`).
2. W8 closure index: ruling, chain, money, reopen gates (`reports/RR-W8INDEX-20261107.md`).
3. Books carry plugin 0.10.5 + slice NOT RUNNABLE gates (`reports/RR-W8BOOK-20261107.md`).
4. Record corrected: cell was SEARCH-BOUND, 686/700 declares `search_files` (`reports/RR-W8CHUNK-20261107-2c.md`).
5. W8 halted BLOCKED by owner ruling (`reports/RR-W8CHUNK-20261107-2b.md`).
6. Arm witness recorded construction, not activation (`reports/RR-W8ARM2-20261107.md`).
7. Post-restart prompt is a two-cell slice (`reports/RR-W8SLICE-20261107.md`).

## In progress (one item: what, blocker, next command)
Part II revision applying `reports/RR-WP2REV-20261107.md`'s items. Blocker: another lane's uncommitted WIP + owner decisions D13–D17. Next command: `git status --short research/`.

## Next three (ordered, one line each)
1. Owner answers packets P1–P3 (`handoff/QUESTIONS.md`) — decides D13, D14, D15.
2. Owner: push `3c473fa` (origin at 89ff8e4) and archive `/tmp/w8` before reboot (RR-W8INDEX-20261107 (c)).
3. Agent: next build card W2b provider-reported usage per lane (unblocked per `reports/RR-RFC01E1-20261031.md`); W8 reopen only after owner go under `design/W8-PROMPT-SLICE.md`.

## Decisions made (date, decision, reason)
- 2026-10-30: D3-c — OTel layered mapping, not native switch (RR-DECISIONS-20261030).
- 2026-10-30: D4 — RFC-0.1 adopted; sealed v0 byte-identical (RR-DECISIONS-20261030).
- 2026-10-31: D8 split — schemaVersion emission first (RR-RFC01E1-20261031).
- 2026-11-01: D12 — est* estimates keep page-table semantics (RR-W8PREREG-20261101).
- 2026-11-06: W8 keeps vBudget 24,000; only tasks with a floor below it measure (RR-ENGINEGAP-20261106 rec. 2).
- 2026-11-07: W8 ruled FAILED; capture stays default-on; everyday contract restored (RR-W8CHUNK-20261107-2b + RR-W8INDEX-20261107).

## Open decisions for the owner (D-numbered, options, your recommendation)
Numbering continues the repo's D1–D12; D13–D17 proposed here, not ruled.
- D13 (Pkt 1) cross-harness claim: (a) keep "cross-harness replayable, diffable"; (b) narrow to within-trace byte-identity + W5-classified diffs with a name/args/body/turn-unit normalisation law proposal-only. Recommend (b).
- D14 (Pkt 3) capture + redaction: keep capture default-on (RR-PLUGIN-DEFAULTS-20261101); (a) redaction stays prose; (b) author the §18 session redaction block (policy id, rule-set, stage, replaced-count) as additive proposal-only card. Recommend (b), no unsealing.
- D15 paper structure: (a) keep Part I + II; (b) merge. Recommend (a), merge only after D13/D14.
- D16 W8 amendment: (a) reopen with a task set whose floor < 24k (RR-ENGINEGAP: frozen tool set binds pressure); (b) amend arm value/budget + prereg first. Recommend (a) with (b) documented, only under `design/W8-PROMPT-SLICE.md` gates.
- D17 publication: (a) now; (b) resolve D13–D15 first, publish; (c) hold. Recommend (b).

## Do not touch (sealed specs, frozen fixtures, plugin defaults)
`spec/rfc-0/` byte-sealed; `02-xcabi-events-v0.md`; the RFC-0.1 additive law (new field = all five touchpoints); `corpus/` checksums; `design/` plans of record; `08.1-UPDATE-PROMPT.md`; `research/**` (white-paper lane); capture default-on + plugin version bumps (need a card); append-only `reports/LOG.md`.

## Evidence rules (the integrity rules, three lines)
1. Every number carries a repo locator + repro command; gate totals from `bash tools/run-ci.sh` are authoritative, never hardcoded (AGENTS.md §2, §5).
2. Unverified claims stay marked UNVERIFIED / UNVERIFIED-<date>, never stated as fact; claims carry a locator at first mention (08.1 §2; 08-HANDOFF §4).
3. No cost-saving claim: none measured on our data; arXiv:2610.22732v1's 18.4–30.9% belongs to an external controller (AGENTS.md law 7).

## Verification status (UNVERIFIED items and what would verify each)
- XERJ Hub listing UNVERIFIED — live `hub.xerj.org/llms.txt` re-check (RR-XERJ-20261029).
- openai price row + catalogue cache-read nulls UNVERIFIED (`benchmarks/metrics/prices.json`) — owner source confirmation.
- Pre-restart W8 pair arm attribution UNPROVEN — one 0.10.5 gateway per arm (RR-W8INDEX-20261107 (e)).
- Part II METR secondary figures UNVERIFIED until a primary locator exists.
- Hard-fault-recall ≥95% gate UNMEASURED (n=4 < 30) — pooled runs.

## Blocked (item, what it waits for)
- W8 reopen: owner go + `design/W8-PROMPT-SLICE.md` gates + USD 23.8459 remaining (reports/W8-SPEND.md).
- Publication: owner (D17). W12 > Steps 0–1: D7 ruled hold (`design/runtime-abi/00-reconciliation-and-justification.md`).
- `/tmp/w8` archive: owner action before the next reboot.
