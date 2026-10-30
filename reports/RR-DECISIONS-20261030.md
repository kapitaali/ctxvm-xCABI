# RR-DECISIONS-20261030 — owner decision session: D1–D7 settled, lanes cleared, riders recorded

**Follows:** `08.1-UPDATE-PROMPT.md` §8 (D1–D7 definitions) ·
`design/rfc-0.1-proposal.md` §8 (the four D4 questions) ·
`design/otel-mapping.md` §5 (D3 options) ·
`design/runtime-abi/00-reconciliation-and-justification.md` (D7 evidence) ·
`reports/RR-DOGFOOD-20261029.md` (D1 evidence) ·
`reports/W4B-PROPOSAL-20261029.md` (W4b scope) ·
`design/packaging.md` §6–§7 + `reports/RR-W10-20261029.md` §5 (W10 blockers)
**Card:** owner decision session (structured question-and-answer, recommendation-first
options; answers recorded verbatim). Session 2026-10-29 → 2026-10-30; record written
2026-10-30. This is a **books-only** record: no code, schema, corpus, package, or
publication change.

---

## 1. Decisions — all seven settled; none outstanding

| ID | Question (source) | Owner answer | Consequence |
|---|---|---|---|
| D1 | Positioning (`08.1` §8) | **D1-c substrate now** | Lead with the replayable trace substrate (capture, replay, measure, diff). Virtual memory stays the roadmap thesis, never a measured claim (W1: zero real evictions, zero true duplicate calls). Revisit after W8. §0's "virtual-memory manager" definition stands — that is the architecture; this is a claims discipline on top of W11's measured-limitations posture, not a pivot. |
| D2 | Umpire (`08.1` §8) | **Demo/reference consumer** | Umpire stays a reference consumer of xCABI. W9 hardening is reproducibility-only: no product commitments, no release/quickstart productization beats. Minting stays a Python mirror of `ident.ts @ 361043e` — "second implementation" remains prohibited. |
| D3 | OTel shape (`design/otel-mapping.md` §5) | **D3-c layered** | JSONL stays canonical; the exporter is a declared lossy projection. The contingency on D4 R4/R5 (clock + turn) is satisfied by the D4 answer. Rider R6 below: drift guard required at exporter promotion. |
| D4 | RFC-0.1 unsealing (`design/rfc-0.1-proposal.md` §8) | **Approve all as proposed** | R1 as a new fault source `intentional_rerun` (not an `intentional` flag — every source-keyed classifier stays correct by default); R2 as a clarification only (`model_pin`/`seed` stay out of the ref); R3–R5 as optional additions behind R0 `session.open.schemaVersion: "0.1"`; scope = exactly the six items. The implementation card is authorized. The sealed `spec/rfc-0/` v0 files stay byte-identical. Riders R4 and R3 below. |
| D5 | W8 budget cap (`08.1` §8) | **USD 25 hard cap** | The preregistration must fit $25; stop and report rather than overspend; scaling needs a new approval. Riders R2 and R3 below. |
| D6 | Names and publish (`08.1` §8) | **Qualified ctxvm family; no publish until W8** | Use the `ctxvm`/`xcabi` names; `umpire` stays local or qualified (bare `umpire` is taken on npm/crates/PyPI/GitHub by unrelated projects). Prepare only — no tags, registry publishes, or index submissions until W8. Accepted risk R7 below. |
| D7 | Runtime ABI (`design/runtime-abi/00-…md`) | **Hold; separate project** | W12 stops at Steps 0–1 until W8. `ctxvm-rt` is a separate consumer project; xCABI remains the trace format, never a C ABI. No `ctxvm_abi.h` and no publication before W8's result. Consistent with Step 1's own conclusion (zero-copy benefit unmeasurable: 5/85 `call.meta` with `latencyMs`, all synthetic). |

## 2. Clearances granted in the same session

- **W10 (`packages/node/**`):** cleared for the JS build + metadata — build step, `files`
  allow-list, `LICENSE`, `repository`, `exports` → built output, `engines` floor
  (`design/packaging.md` §6.2). PyPI strategy: **repo-only until PyO3**. No publish, no tag.
  Coupling check (2026-10-30): the opencode plugin imports the node source by **relative
  path** (`packages/opencode/src/plugin.ts:24` → `../../node/src/index.ts`), not through the
  exports map, so the exports change cannot break any in-repo gate.
- **W4b:** **B1 only** — the `_transcript_texts` live-shape fix (~12 lines) plus its 3 tests,
  including the red-before regression pin (`reports/W4B-PROPOSAL-20261029.md` §2). **B2
  (live-shape generator) DEFERRED — queued immediately after W5** (owner ruling). B3
  (provider usage) and B4 (contract-version provenance) route to W7/RFC-0.1 as proposed.
- **W2b:** all four lanes cleared (ai-sdk, opencode, node, hermes) for the narrow
  provider-usage wiring. Work starts only after the RFC-0.1 schema actually lands —
  `call.meta` is `additionalProperties: false` in sealed v0, so the field cannot exist
  before the v0.1 branch ships.
- **W1/W5:** W4b B1 lands first; then the scripted task is prepared and the owner-run
  scheduled in both OpenCode and Hermes; the W1 live capture piggybacks in the same
  window. W5 must still classify hermes user-turn vs opencode/ai-sdk model-request turn
  units as **unit mismatches, never behaviour** (W4 F2 law).
- **W9 (spend bucket):** baselines restricted to **free-tier models** — no paid model spend
  for W9 (owner ruling). The fine-tuned-classifier and stronger-model beats run on free
  tiers or are dropped with the limitation recorded. This closes the un-budgeted spend
  bucket: D5's cap was scoped to W8, and now no card has authorized paid spend except W8.

## 3. Riders recorded with the decisions

1. **W8 inconclusive handling + revisit trigger.** A $25 pilot may not reach the
   preregistered volume for tight CIs; the preregistration must predefine **"inconclusive"**
   as a reportable outcome (reported as inconclusive, never spun). W8's outcome —
   pass / fail / inconclusive — **reopens D5 and D7**.
2. **Paid-model price provenance.** Whichever paid model the W8 pilot uses, its
   `prices.json` row must be filled from the provider's price page with a locator +
   access date BEFORE the run; nulls are never substituted (`priceModelVersion: 1` law;
   openai is UNVERIFIED nulls today, `_template` awaits adoption).
3. **Cache-write blind spot → billed-spend rule.** The D4 scope split leaves cache-write
   unmodeled (v0/v0.1 arithmetic is `hit × cachedRead + miss × input`; the write premium
   field exists for v1). Owner ruling: where the pilot model charges cache-write premiums,
   reports must state **actual billed spend** alongside the model estimate.
4. **RFC-0.1 cross-repo tail.** After the implementation card lands, umpire regenerates
   its four fixture triplets with R1 (the proposal's own §7 list) — a follow-on in the
   umpire repo. The v0 schema file stays byte-identical; only the new v0.1 files, the
   validator branch + negative corpus, the replayer version-branch, fixtures, and the
   `07` §W3 / `02` / RFC-0.1 text updates land.
5. **B2 follow-up.** B1-only leaves the generator-level gap open: the unit-level shape
   matrix (test 3) guards the class, and W5's live run exercises the fixed surface in
   reality, but nothing stops `generate_traces.py` from producing another block-shape-only
   drop. B2 is queued immediately after W5; until then the m4/m7 provenance erratum stays
   the only disclosure.
6. **D3-c drift guard.** When the exporter is promoted to the supported path it gains
   conformance fixtures plus a test keeping its declared-drop list in sync with the
   schema's field set — the known "two things to keep honest" cost, made mechanical. Note
   the synergy: once W2b lands `providerUsage`, the exporter's
   `gen_ai.usage.cache_read` mapping (only when providerReported) gets real inputs.
7. **Accepted naming risk.** The `@ctxvm` npm scope is claimed on first publish (ownership
   UNVERIFIED, org page 403) and the free crates/PyPI names stay unreserved until W8.
   Accepted and recorded, not hidden.

## 4. Next frontier (queue after this record)

1. **W4b B1** (hermes lane, cleared) — 12 lines + 3 tests, one commit.
2. **RFC-0.1 implementation** — `spec/rfc-0.1/` schema, validator branch + negative
   corpus, replayer R1 version-branch, v0.1 fixtures added to conformance only after they
   validate, `07` §W3 + `02` + RFC-0.1 text; sealed v0 byte-identical.
3. **W10 node JS build + metadata** (no publish).
4. **W2b wiring**, all four lanes (after RFC-0.1).
5. **W5/W1 owner-run** (after W4b B1; script prep + owner window).
6. **B2** (immediately after W5).
7. **W8 pilot** ($25 cap; after W2b–W4; preregistration first).
8. **D3-c exporter promotion** (after RFC-0.1; with the drift guard).
9. **W12 Steps 2+** (after W8; D7 holds until then).

## 5. Verification

- Books only: `08-HANDOFF.md` (§0 decisions block, header date, board rows W1/W2/W4b/W6/
  W7/W10/W12), `reports/LOG.md` (one row), this report. Counts unchanged:
  `ts 13 + 58 + 45` / `python 80 + 44 + 8`; rust 59 default / 60 with `tiktoken`.
- The sealed surface is untouched: `git diff --stat` shows no `spec/rfc-0/` and no
  `02-xcabi-events-v0.md` change.
- Full `tools/run-ci.sh` ALL GATES GREEN before the commit; scans (CJK-stray + `||` on
  Markdown, NFC, LOG rows = 4 pipes, §5 rows = 6 pipes) clean.

## 6. Limitations / open questions

- The XERJ Corpus Hub listing remains **pending/UNVERIFIED**; when a public URL appears,
  replace `pending — UNVERIFIED` in `README.md` and record it as a proper update.
- W8's task set, baselines, stopping rule, and threshold are **not yet preregistered** —
  that is W8's first step, inside the $25 cap.
- The W5 owner-run window is unscheduled; the script is prepared once W4b B1 lands.
- The RFC-0.1 implementation card does not exist yet; its exact file list is §4 item 2
  above plus `design/rfc-0.1-proposal.md` §7.
