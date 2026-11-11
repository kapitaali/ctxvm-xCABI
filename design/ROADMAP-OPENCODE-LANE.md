# ROADMAP — opencode lane (kit, review packets, umpire-development proposals)

State of record: 2026-11-11, HEAD `940a5fb` (the RFC-0.1 compatibility note landing in flight, committing on top).
own task list, not the project board (`08-HANDOFF.md` §5 governs the project board; W workstreams
are defined in `08.1-UPDATE-PROMPT.md` §W). Format law inherited from the family
(`design/ROADMAP-HERMES-LANE.md`): tick a box ONLY when the command under **done when** printed
what the box says; an unticked box is either future work or an owner gate, and says which.

Lane boundaries: this lane owns the kit surfaces it is routed (`handoff/` deltas, `08-HANDOFF.md`
§0 addenda, `reports/` for its cards), reviewer-packet processing, and PROPOSAL-side umpire work.
It does not own `research/**`, `packages/hermes/**`, `corpus/**`, `spec/**`, `AGENTS.md` /
`handoff/AGENT-PROMPT.md` / `handoff/LANES.md` (policy), packet content, or `tools/run-ci.sh`.
Prompts for this lane: `design/OPENCODE-LANE-DEVELOPER-PROMPT.md` (operating law) — keep its §14
pin true every card close.

---

## 0. Standing lane upkeep (machinery that keeps the books honest)

- [x] **R1. Lane master prompt authored and committed.**
  `design/OPENCODE-LANE-DEVELOPER-PROMPT.md` exists, 321+ lines, family format.
  *Done when:* `grep -c '^## ' design/OPENCODE-LANE-DEVELOPER-PROMPT.md` >= 14 and the file is in
  a commit (`git log -1 --format='%h' -- design/OPENCODE-LANE-DEVELOPER-PROMPT.md` → `4326930`).
  *Status:* LANDED 2026-11-10.

- [x] **R2. LOG tail format fault repaired.** The `RR-ENVLEAK-20261110` row had committed with a
  literal backslash-n terminator; repair + erratum row `RR-LOGERR-20261110` + prompt §6/§12 rules.
  *Done when:* `grep -c '^| RR-' reports/LOG.md` prints ≥ 216, the file's final byte is a newline
  (`tail -c 1 reports/LOG.md` prints a blank/`\n`), and no line contains a backslash-n followed by
  `| RR-` (`grep -c 'n| RR-' reports/LOG.md` prints 0).

- [x] **R3. Day files current.** `reports/RR-DAY-20261110.md` carries sections for P5, the gates
  run, the master prompt, and the LOG fault.
  *Done when:* `grep -c '^## ' reports/RR-DAY-20261110.md` >= 5.

- [ ] **R4. `handoff/AGENT-PROMPT.md` §1 session-state refresh.** PROPOSED, not edited — policy
  file (owner gate). The §1 block predates the P4/P5 chain; the proposal is a one-line Done whose
  text lives in the P4/P5 cards.
  *Done when:* owner approves AND `grep -n "0.10.11\|P5 answered" handoff/AGENT-PROMPT.md` shows
  the refreshed line.
  *Owner:* owner D-number/wording approval.

- [ ] **R5. Capture-env leak guard for the deciding command.** PROPOSED (RR-ENVLEAK-20261110):
  `tools/run-ci.sh` warns (or scrubs) when `CTXVM_TRACE_TS` / `CTXVM_HERMES_VERSION` are exported,
  since Actions carries neither and a capture-env shell documented two false reds.
  *Done when:* owner approves AND a red-substitute repro (`CTXVM_TRACE_TS=0 bash tools/run-ci.sh 2>&1 | head -2`)
  prints the guard's warning line.
  *Owner:* owner (the one deciding command).

- [ ] **R6. Paste-budget standing check.** Pre-measure the three pastes BEFORE any PROJECT-STATE
  delta commit; trim CONTEXT-PACK glossary rows (never headings) if any paste exceeds 16,384 B.
  Standing discipline, not a one-shot: the box stays unticked until two consecutive card closes
  pass without a trim.
  *Done when:* on two later cards, `bash tools/check-handoff.sh` + `for n in 1 2 3; do bash
  tools/session-start.sh $n --with-context >/dev/null 2>&1; printf "%s=$? " $n; done` all exit 0
  with no CONTEXT-PACK edit between.

## 1. The review packet board (P1–P8; reviewer's answers → my verify-then-record pipeline)

- [x] **P1 (D13) cross-harness claim.** Answered 2026-11-08;
  `handoff/QUESTIONS-ARCHIVE.md §P1`.
  *Done when (met):* `grep -c '^## P1' handoff/QUESTIONS-ARCHIVE.md` = 1.

- [x] **P2 fault-resident/healthy demo sentence.** Answered 2026-11-08 (seq 7 → `identifier_scan`,
  swap-in cause active); `RR-P2DEMO-20261108`.

- [x] **P3 (D14) redaction default-capture.** Answered 2026-11-08; redaction card authored
  proposal-only sidecar-first (`design/redaction-block.md`, carrier `RR-P3REDACT-20261109`).

- [x] **P4 (R4/`ts`) answered 2026-11-09.** `ts` stays optional; ordering clause DRAFTED
  proposal-only; both UNKNOWNs resolved. Report `reports/RR-P4TS-20261109.md`; commits `89d02b6`
  → `d2b6b1c`.

- [x] **P5 (D-U1 calibration transfer) answered 2026-11-10.** Publish per-corpus WITH caveat; no
  transfer claim until the preregistered ≥5-set equivalence test. Report
  `reports/RR-P5CAL-20261110.md`; commit `43d73bb` (+ `42ed013`, `7f9f4ae`).
  *Done when (met):* `grep -c RR-P5CAL reports/LOG.md` = 1 and QUESTIONS row P5 shows
  `**answered 2026-11-10**`.

- [x] **P6 (D-U3 determinism scope) answered 2026-11-10.** Verify sweep + verdicts recorded in
  `reports/RR-P6DET-20261110.md`: keep same-build (register option (a)); vocabulary tightened to
  "replay-reproducible with 10 documented exceptions"; both UNKNOWNs resolved (RR-M3FULL:19-23;
  local-only serving T14/D-U4).
  *Done when (met):* QUESTIONS row `| P6 |` reads answered and the card exists in a commit.

- [x] **P7 (D-U2 baselines) answered 2026-11-10.** Verify sweep + verdicts recorded in
  `reports/RR-P7BASE-20261110.md`: two zero-spend baselines first; both UNKNOWNs resolved
  (240/120/120 at 4 labels ×120; labels caller-supplied per call); five prereg-positioning
  outcomes; the card carries the P6 U4 erratum.
  *Done when (met):* QUESTIONS row `| P7 |` reads answered and the card exists in a commit.

- [x] **P8 (cache-stable selection) answered 2026-11-11.** The reviewer's packet-only answer is
  recorded in `reports/RR-P8CACHE-20261111.md`: the RANKING is adopted (watermark compaction first —
  evict once on a trigger, hold the set, valid only above break-even; (c) cannot bound residency),
  with TWO corrections from the books — **w/r = 10.0, not 12.5** (the owner's catalogue row-013:
  $0.10 in / $0.50 out / $0.01 cached read, no cache-write row) and the **evictable share 5.3 %
  session-weighted** (`RR-W8SIM` §2; the 12 % is last-request) — so break-even n\* ≈ 189 calls, not
  ~100. **(d) is amended**: the books MEASURED the no-op arm (0 evictions) at $0.0765 vs naive
  $0.0175 = 4.4× (`RR-NOOP-20261109`), so "no worse than control" is falsified — the driver is
  session growth plus output volume, not selection. The no-op byte check the reviewer demands
  already passes (`RR-W8NOOPBYTES`). Q3 was already executed (`design/W8-CLOSURE-20261110.md`,
  owner Option A / packet P9); the replacement run is `design/W8B-FREE-PLAN.md` — and it has now
  run to NO RECORD (both arms, `nous/longcat-2.5:free`, prompt-1 timeout at 120 s, $0.0000;
  `RR-W8B2-20261111`) — and the w8b lane's own erratum (`RR-W8B2-ERRATUM-20261111`) corrects the
  cause: the arms DID run (naive 9 API calls / 21 tool calls, paged 5 / 11, both reaped as
  `ws_orphan_reap` because the driver killed the CLI), so the blocker is the TASK's counting
  questions against a 120 s per-prompt cap, not a model or transport failure. Their lane has landed
  SIGTERM-first termination, a `--limit N` smoke check, `max_turns` 6, prompt rules and
  `--expect-budget any`; the next step is now CONCRETE — rewrite the questions to the values the tool
  reports (`total_lines`, `file_size`) — and the subject choice stays the owner's.
  Q2's five-condition
  metric-replacement rule is adopted as a standing lane rule.
- [x] **P9 (close W8 or buy a mechanism test) answered 2026-11-10; reviewer confirmed 2026-11-11.**
  Verdict A (close with the negative result) — an independent confirmation, not a new decision; the
  closure (`design/W8-CLOSURE-20261110.md`, owner Option A) stands and needs NO edit: its items 3–5
  and not-claimed list already state the weaker claim (the cache-write cause is UNKNOWN, not
  "selection rewrites the prefix"). The reviewer's four closure-text corrections were checked against
  the artefacts (`reports/RR-P9CLOSE-20261111.md`): the zero-spend narrowing was ALREADY run and
  returned NOT-TESTABLE (the provider export is a per-day/per-key aggregate — no per-request rows,
  no timestamps; call gaps ~18 s; the cache lifetime is UNVERIFIED) ⇒ H1 NOT SUPPORTED, H2 NOT
  TESTABLE, **H3 UNKNOWN cause**; the cap wording stays three-part (billed >= $7.14 / store estimate
  $9.16 / true total UNKNOWN; the 11-07 and 11-09 exports are still missing).
  *ROUTED, not edited:* `design/w8-cache-stable-selection.md` §1 still says "the paged arm rewrote the
  prefix 14 times" — superseded by `RR-W8CACHE` §4 and `RR-W8NOOPBYTES`; that is another lane's plan
  of record, so its owner may append an erratum block. The owner may also ask the w8b lane to adopt
  the reviewer's one-line weaker-claim summary.
  *Done when (met):* the packet STATUS carries the confirmation, the card exists in a commit, and the
  QUESTIONS row `| P9 |` reads answered.

  *Follow-on (2026-11-11):* the owner's T-A classification was applied and verified
  (`reports/RR-W8BBLOCK-20261111.md`): probe/smoke = diagnostic, the 13:46 pair = PAIR ATTEMPT (not
  bookable: block unfilled), and the next block is filled and committed. **Finding A:** at that shape the
  break-even n\* ≈ 34 calls against 41 measured — the first shape where the policy pays back inside a
  session (W8's gave ≈ 189 vs 14–29): a number for a future PAID preregistration, not a cost claim.
  **Finding B:** the open blocker is ARM ATTRIBUTION (`profile "default"` under `w8bn-paged` → that arm
  was not the paged arm), so the one-prompt precondition must assert the profile too.
  (that document's own scope: "new files under `spec/rfc-0.1/` only") carrying a **D-number** (RFC-0.1
  is "Applied (D4 approved 2026-10-30)"); plus a conformance vector making the rule testable — one
  line per shape AND a negative (a `page.declare` with a flat `page.logicalRef`, which a sniffing
  reader would accept and the validator must reject). Falsifiers adopted verbatim (a valid line where
  type-dispatch misreads identity; a verb mixing both shapes; a new verb with a third shape — a v0.2
  *HANDOFF WRITTEN (2026-11-11):* `design/W8B-LANE-PROMPT.md` - a small prompt for that lane with the
  measured state, the owner's ruled decisions (subject order; new subject = new digests = re-commit the
  block first; the arm-attribution precondition) and four items it owes (level-2 assert, the shape
  erratum, the W8SIM 5.3% scoping, the "C3" rename). **PARTLY LANDED (their `6ae0d38`):** their
  master prompt now carries the two-profile rule and a precondition section (probe
  `tools/w8b-run.py --provider nous --probe`; `engineSelections > 0`; READY/NOT READY; the finding that
  the CLI path never calls `select_context` because plugins load in the gateway - `PLG-7`). **THE ONE
  HALF STILL MISSING: the PROFILE attribution** - the precondition must also assert the sidecar's
  recorded profile IS the arm's profile (`w8bn-paged`, not "default"), because that is exactly the
  defect that voided their first pair (`profile "default"` under profile `w8bn-paged`); the arms are
  separated by the profile each was invoked with and by nothing inside the trace.
  *CONTRAST (2026-11-11, `reports/RR-W8BCONTRAST-20261111.md`):* their `57918fd` measured that the
  instrument now engages (READY, first time) AND that both arms are the same arm - every sidecar attests
  `profile: default` regardless of which profile served the session. That CONFIRMS the precondition half
  above: the engine engaging is not the attribution. The umpire side's working analogue: the arms are
  separated by the profile each was invoked with (settings resolved per invocation, not snapshotted per
  process), so the remedy is per-session/per-profile settings inside the plugin (their option 2). A
  no-contrast run is a HARNESS LIMIT, not a result: a closure on that ground claims nothing in either
  direction and is not a negative result about cache-stable selection; the routes left are a fresh
  preregistration of a longer-session paid variant (n\* ~ 34 calls vs 41 measured) or the
  capability-mismatch verdict. The contrast gate should also assert WHICH difference it expects (the
  naive arm's budget vs the paged arm's; the sidecar's profile vs the arm's).
  *OWNER-RULED (2026-11-11):* the subject fallback order - **nvidia** (nemotron-super, the tested path) ->
  **stepfun** -> accept longcat too slow for the 120 s cap only if both fail.
  question; a consumer that cannot dispatch on event type).
  *ERRATUM:* this lane's blast-radius framing for an additive field was overstated (a strict v0 consumer
  already rejects a v0.1 trace at its `session.open` line); the marginal costs are (i) every v0.1-aware
  consumer must be updated, (ii) two identity sources per line, (iii) a consistency rule between them.
  The ruling is unchanged; the reasoning is corrected (erratum block on `reports/RR-UGATE-20261111.md`).
  *Done when (met):* the packet STATUS reads answered, the card exists in a commit, and the
  QUESTIONS row `| P8 |` reads answered.

- [x] **P10 (page-id asymmetry: flat vs nested page identity) answered 2026-11-11.** The reviewer's
  ruling: **(b) + (a) — ONE RFC-0.1 compatibility-note line stating the type-dispatch rule, plus prose
  docs, and NO field** — the trigger was met by two codebases in two languages, and (c) is out because
  SEALED v0 traces exist that will not change (every consumer of them keeps the type-dispatch rule
  forever, and a field would add a THIRD shape without removing either old one); (d) is out (a third
  consumer would find the rule only in code comments); (a) alone is weaker (a workaround in two repos
  does not tell a new implementer the rule exists).
  **The rule is verified WORD FOR WORD against both schemas**: sealed v0's `page.declare.page` ->
  `$defs/pageRef` = `{id: pageId{logicalRef,contentHash}, kind, tokens}` (nested) while
  `page.render`/`page.evict`/`page.fault`/`page.pin`/`page.unpin` -> `$defs/pageId` =
  `{logicalRef,contentHash}` (flat); RFC-0.1 keeps the same `$defs` and the same nine verbs, so the
  asymmetry is inherited and unchanged; **no verb carries both shapes**. Two of the reviewer's three
  UNKNOWNs resolved from the books: `schemaVersion` is on the `session.open` line ONLY and optional
  (RFC-0.1:8), so their "if every v0.1 line carried schemaVersion" premise is false; and a
  conformance vector is a FIXTURE (`rust/crates/ctxvm-conformance/vectors/`), not a spec edit.
  **C3 ENFORCED (2026-11-11, `reports/RR-C3FIX-20261111.md`):** the review found C3 was FALSE for
  ctxvm itself - `ident.ts:20` sorted by UTF-16 code units while Python sorts by code points, so the
  same input canonicalises differently in the two implementations (silently). Fixed with a code-point
  comparator + two TS tests + a 12-case Python-generated vector file
  (`rust/crates/ctxvm-conformance/vectors/canonical-form-cases.jsonl`: input text + expected canonical
  bytes + expected digest; NFC vs NFD differ; reject cases beyond 2^53 / integral float / -0 / lone
  surrogate); `validateHashInput` added (exported, not wired into the minting path - owner-routed, blast
  radius named). No digest moved: 44 hashed input files scanned, 0 non-BMP keys, 0 astral values; CI
  ALL GATES GREEN after the change (`check-node-build: OK - 16 events byte-identical`).
  **LANDED 2026-11-11 (D18):** the note is `spec/rfc-0.1/COMPATIBILITY.md` — a new file under
  `spec/rfc-0.1/` (that document's declared scope: "new files under `spec/rfc-0.1/` only"), carrying
  **C1** the type-dispatch rule, **C2** the key-order compatibility statement plus its pointer to the
  conformance test (one line per shape AND a negative — a `page.declare` with a flat `page.logicalRef`,
  which a sniffing reader would accept and the validator must reject), and **C3** the canonical form
  for hash inputs (code-point ordering, integers only) — the reviewer's own conditional, triggered by
  umpire's ref digest and the two measured divergences. No field, no sealed byte, no gate moved (CI
  ALL GATES GREEN with it present). The D-number is renumberable by the owner.
  **ERRATUM:** this lane's blast-radius framing for an additive field was overstated (a strict v0
  consumer already rejects a v0.1 trace at its `session.open` line); the marginal costs are (i) every
  v0.1-aware consumer must be updated, (ii) two sources of identity per line, (iii) a consistency rule
  between them. The ruling is unchanged; the reasoning is corrected (erratum block on
  `reports/RR-UGATE-20261111.md`).
  **Falsifiers adopted verbatim** (a valid line where type-dispatch misreads identity; a verb mixing
  both shapes; a new verb with a third shape — a v0.2 question; a consumer that cannot dispatch on
  event type).
  *Done when (met):* the packet STATUS reads answered, the card exists in a commit, and the QUESTIONS
  row `| P10 |` reads answered.

- [x] **P11 (canonical ordering: sorted keys vs Rust struct order) answered 2026-11-11.** The ruling
  stands: **(c) as the owner, with (a) as a short POINTER — and the ORDER is test-first**: write the
  conformance test, then the note can state a fact the test enforces (F9 is otherwise a claim nobody
  can falsify). The test belongs to ctxvm (its replay makes the acceptance claim) and asserts, in order
  of strength, equal parsed model -> equal page table -> equal replay report, NEVER equal bytes, with a
  trace WITH `ts` and one WITHOUT plus a numeric case, in BOTH places (a vector pair in
  `rust/crates/ctxvm-conformance/vectors/` + a Rust unit test). The note's line is a COMPATIBILITY
  STATEMENT ONLY (parsing and replay; the codec stays strict). Resolved from the books: `ts` coverage
  (6 lines in `events-v0-1.jsonl`), a vector is a FIXTURE not a spec edit, and the note's route (a
  D-number + a NEW file under `spec/rfc-0.1/`, bundling the P10 line and this one under one D-number).
  **MEASURED TODAY, and it TRIGGERS the reviewer's third falsifier:** umpire's Python `canonical_json`
  and ctxvm's TS `canonicalJson` agree on ascii, non-ASCII values and nested keys but DIFFER on
  astral-plane KEY names (code point vs UTF-16 code-unit ordering) and on number text forms in four of
  six cases — and umpire's ref digest IS a digest over serialised bytes, so the note needs a normative
  canonical form FOR HASH INPUTS ONLY. Duplicate keys: accepted by the validator, unspecified anywhere.
  *GAP (2026-11-11, `reports/RR-P11GAP-20261111.md`):* the landed test asserts THREE levels in
  prose but only TWO in code — `ctxvm_core::ReplayReport` carries events/divergences/violations only,
  so no page table is derived or compared; the one-call fix is
  `ctxvm_core::render::derive_projection(events, turn)` (a pure function of the decisions fed) per
  turn, or the two comments are corrected and the claim dropped. The test file is the owner's
  in-flight work → theirs to make.
  *LANDED (2026-11-11, verified by this lane):* the conformance pair — four vectors under
  `rust/crates/ctxvm-conformance/vectors/` (`order-{struct,sorted}-{ts,nots}.jsonl`) plus
  `rust/crates/ctxvm-conformance/tests/key_order.rs`; the pairs are true byte-order twins (parsed equal,
  bytes differ), `ts` is LAST in the struct form and BEFORE `type` in the sorted form (law 3's divergence
  exercised), and `cargo test -p ctxvm-conformance` → 3 passed, 0 failed. *Still owner-routed:* the note
  file (two lines, one D-number) and the canonical-form choice for its C3 clause. *Done when (met):* the packet STATUS reads answered, the card exists in a commit, and the
  QUESTIONS row `| P11 |` reads answered.

## 2. Owner-gated proposals this lane authored (ratification turns text into bytes)

- [ ] **G1. Umpire ordering clause (from P4).** The one-clause rule (line order governs; absent
  `ts` = unknown, never zero; no cross-ledger order) — verbatim text in
  `reports/RR-P4TS-20261109.md`; insertion point `umpire/00-SPEC.md` §2, after the L1–L5 block,
  documentation-only. Needs owner approval + a FRESH D-number (the A6 D-U register has no ts
  candidate).
  *Done when:* the clause is IN a committed `umpire/00-SPEC.md` §2 AND the new D-number appears in
  the umpire decision register.
  *Owner:* approval + D-number.

- [ ] **G2. Calibrated-confidence caller sentence (from P5).** Verbatim text in
  `reports/RR-P5CAL-20261110.md`; insertion point: wherever `calibrate()`'s contract text lives
  (MCP tool description / umpire spec). Ratifies INTO registered D-U1.
  *Done when:* sentence committed into the umpire books AND `handoff/QUESTIONS-ARCHIVE.md` P5
  updated with the ratification locator.
  *Owner:* approval (D-U1 exists already).

- [ ] **G3. Equivalence-test preregistration (W9 follow-on).** BEFORE any new capture run:
  margin ±2 points; Brier/log-loss primary, ECE secondary; ≥5 held-out NEW label sets with cluster
  bootstrap; cross-fitting; sizing n ≈ 180×(h/2)² from the existing rows' paired bootstrap
  half-width. Criteria recorded in `RR-P5CAL-20261110`; nothing is preregistered yet, and nothing
  runs before it is.
  *Done when:* a preregistration card exists (umpire-side, referee-checkable, with frozen
  thresholds + parse code) dated AFTER the owner approves the design.
  *Owner:* approve the design + fund the run.

- [ ] **G4. Redaction carrier.** `design/redaction-block.md` (owner-cleared placement,
  sidecar-first, P3's D14 answered) — build starts only at the owner's word; the silent
  default-on release rule stays bound at D6/D17.
  *Done when:* implementation card exists (`RR-REDACT*` with a passing kit+CI gate) OR the owner
  rules it further-deferred in writing.
  *Owner:* go/defer.

- [ ] **G5. D13/D14 ratification + white-paper bundle routing.** The six paper items
  (Pillar-1 split; `:635` echo sweep; the P2 demo sentence; the R1 3-to-0 contrast;
  the consent-paragraph replacement; Part II's card-citation rule) live in
  `reports/RR-DAY-20261109.md`; they are owner-routed white-paper lane work.
  *Done when:* PROJECT-STATE Next-three line 1 rotates away (i.e., the bundle is routed/executed).
  *Owner:* ratify + route.

- [ ] **G6. Publication (D17).** W10 prepare-only; publish/submit/tag only with approval.
  *Done when:* an orchestrated publication task appears with D17 resolved.
  *Owner:* D17.

- [x] **G7. W8 reopen — CLOSED (2026-11-10): W8 closed NEGATIVE, owner Option A** (packet P9,
  `design/W8-CLOSURE-20261110.md`; the 2026-11-07 FAILED ruling and its reopen conditions
  `RR-W8CHUNK-20261107-2 §12` + `design/W8-PROMPT-SLICE.md` are superseded). The reopen question is
  now answered by the P8/P9 answers: a different shape (longer session, more unprotected middle) or a
  different keep law is a **FRESH preregistration, not W8** — and at the measured shape the break-even
  is n\* ≈ 34 calls against 41 measured (`RR-W8BBLOCK-20261111`), so a paid cell at this shape is
  preregistrable while W8 itself is not. The live thread is the W8B free-model replacement
  (`design/W8B-FREE-PLAN.md`), the other lane's to run.

## 3. W workstreams — the board as it bears on THIS lane

(Their definitions live in `08.1-UPDATE-PROMPT.md` §W; statuses quoted from `08-HANDOFF.md` §5
row lines, noted per item. Boxes below are MY lane's actionable obligations, not other lanes' work.)

- [x] **W1 dogfood** — dry-run landed (`RR-DOGFOOD-20261029`, §5 :1057). My part: none open;
  live runs are the capture lanes'.
- [x] **W2 real tokenization** — v0 landed; W2b cleared on all four lanes; emitter chain closed
  (§5 :1056, frontier 3).
- [x] **W3 metrics falsifiability** — landed (`RR-W3-20261029`, :1058).
- [x] **W4 / W4b hermes adapter + capture-surface fix** — landed per :1059–:1060; plugin lane owns
  the rest (their roadmap).
- [x] **W6 OTel decision** — D3-c landed and promoted to the supported path 2026-11-08
  (`RR-D3COTEL-20261108`), drift guard in place (frontier 9).
- [x] **W7 RFC-0.1 chain** — closed 2026-10-31 (:1065).
- [x] **W10 packaging (prepare-only)** — node build + CI wiring landed (:1067, W10NODE); anything
  beyond is D17 (§2 G6).
- [x] **W11 + W11b scope discipline + external correction** — done (:1063, :1068).
- [x] **W13 `turn.render.prefix` / W14 environment key / W15 `toolEffect` / W17 coverage manifest
  / W18 monitor replay tier 1 / W21 collide-proof filenames** — LANDED 2026-11-05…07
  (AGENTS §9). My part: regression upkeep via the gates; nothing open.
- [x] **W12 Steps 0–1** — done; Steps 2+ are D7 hold (:1064, :110 of frontier 9). My part:
  none until D7 lifts.
- [x] **W8 the decisive experiment** — CLOSED NEGATIVE 2026-11-10 (owner Option A, packet P9;
  `design/W8-CLOSURE-20261110.md`; G7 closed). My actionable box is discharged: the results were
  processed into the review lane (P8 and P9 answered, both cards + LOG rows). Side-records kept
  aware of: `RR-W8PAIR-20261109` (first counted pair, negative), `RR-BUDGET-20261109` (200,000 vs
  24,000 provenance), `RR-DRIFT-20261109` (gate printed numbers it didn't measure), `RR-W8H6-20261109`
  (`shape verified, surface fails`), and from the close-out: `RR-W8SIM-20261110` (the simulator cannot
  validate; the 5.3% session-weighted ceiling), `RR-W8CACHE-20261110` (the cache-write cause is
  UNKNOWN; H1 excluded, H2 untestable), `RR-W8NOOPBYTES-20261110` (a no-op selection preserves the
  request byte for byte), `RR-W8B2CLASS-20261111` + `RR-W8B2-ERRATUM-20261111` (the free run's
  classification: diagnostics and a pair attempt, not a cell).
- [ ] **W9 umpire hardening/positioning** — alive on the umpire side; THIS lane's named pieces are
  exactly G1–G3 above. Nothing else until owner route.
- [ ] **W16 causal edges / W19 tier-2 interventions / W20 trace-surface extensions** — design
  notes only, owner-gated (`design/causal-edges.md`, W19/W20 sections in `08.1`).
  *Done when:* owner opens one → first touchpoint-touching card follows the five-touchpoint law
  (prompt §8) BEFORE any wire change.
  *Owner:* open/defer per workstream.

## 4. The pre-W board (T0–T25 + support rows) — closed before the workstreams existed

- [x] **T-board verified DONE.** T0–T25 (incl. the umpire-side T13/T14, T15/T22–T24 adapter
  chain, T17 hermes chain) plus W11b and SUPPORT-1: all `| T`-rows and the two support rows read
  DONE/LANDED/CLOSED.
  *Done when (met):* `grep -c '^| T' 08-HANDOFF.md` = 33 and
  `grep '^| T' 08-HANDOFF.md | grep -ciE 'DONE|LANDED|CLOSED'` = 33; every
  `open|undone|queued`-matching row is a false positive on the substring "Open" inside DONE rows
  (T7/T9/T12 "OpenCode", T22/T24/T25 "gated/inject" prose). No pre-W work remains on my ledger;
  anything resurfacing enters as a NEW card, never a reopened T row.

## 5. Umpire-repo hygiene (sibling repo, read/proposal lane)

- [x] **U1. Artifact + books identity verified.** `cal-precision-v3.json`
  (schema `umpire-calibration-precision/0.1`, `cal-v1:057a5a35a9d4ec71`, corpus sha `54e39733…`,
  bootstrap n=2000 seed 42, 10-bin ECE, test n=120, committed `47e0ee0`) verified on disk during
  P5.
- [x] **U2. MCP health re-check — VERIFIED LIVE 2026-11-11.** With the pinned server started,
  `tools.umpire.health()` returns ok (200) on 127.0.0.1:8081, and a real `decide` returns key
  `billing` with calibrated confidence 0.905882 at `data_version: cal-v1:057a5a35a9d4ec71` — the record's
  map applied end-to-end (U6 verified where it matters), latency 5.3 s, ledger + records written
  (`reports/RR-U2LIVE-20261111.md`). The only environment tail is the gateway-scoped MCP: its wrapper
  still holds v2 until a gateway restart (the owner's timing — a restart reaps gateway sessions and the
  w8b lane has runs in flight).
- [ ] **U3. Umpire-side lane tools.** The umpire repo has its own AGENTS.md books; if the owner
  routes a dev card there, its pipeline mirrors §4 of my prompt with uom-per-card kit rules in
  that repo. Standing: proposals only until a D-number lands.
  *Done when:* first routed card lands with its own `RR-*` row in the umpire repo's books.

- [x] **U4. D-U3 falsifier run: quiescent (concurrency-1) recapture + ten-row classification.**
  RAN ALREADY by the books: `RR-M3V3-20261024` = the quiescent FULL 480 recapture (6,060.5 s,
  zero MCP decide writes in-window, same pin/seed/corpus sha) where the ten suspect rows relaxed
  to the replay-path values (splits 5/4/1 train/validation/test) and the capture-time page-table
  came out byte-identical — "**capture-time-concurrency attribution CONFIRMED**" (the locator
  printed by `grep -n 'CONFIRMED' ~/Documents/umpire/reports/LOG.md`). Discovered while
  processing P7; the committed P6 card's Limitations wrongly said it hadn't run — erratum block
  appended there, U4 ticks here.
  *Done when (met):* the box's snake-locator command prints the RR-M3V3 row; falsifier outcome =
  recapture-clean.

- [ ] **U5. Page-id asymmetry ruling (the one friction item still open).** From
  `reports/RR-UGATE-20261111.md`: the asymmetry is real and sealed-v0-inherited; TWO in-repo
  consumers already branch on it, so the standing "revisit if a second consumer hits it"
  recommendation's trigger has fired. What U5 needs from the owner: the ruling among (a)/(b)/(c)/
  (d) and, if (c), which side gets the field plus acceptance of the blast radius. The agent's
  recommendation is (a)/(b) over (c): sealed v0 rejects unknown fields under
  `additionalProperties:false`, so a declare-side field invalidates EVERY declare line for
  strict v0 consumers, against R1's rerun-only addition. Packet P10 carries the question.
  *Done when:* P10 is answered in QUESTIONS + a card lands; if (b), the RFC-0.1 compatibility-note
  line is drafted proposal-only for the owner.
  *Owner:* paste P10 (D-number in the umpire register).

- [x] **U6. The MCP's default calibration artifact was the SUPERSEDED v2 map — FIXED 2026-11-11.** From
  `reports/RR-UMRES-20261111.md`: `calibration_info` (no argument) returns `umpire-cal-v2.json`
  (`cal-v1:aceb881587b3b3a6`, test ECE 0.026684) while the calibration OF RECORD is v3
  (`cal-v1:057a5a35a9d4ec71`, ECE 0.030163, `RR-M3V3`; the umpire repo's own `spec/calibration_ci.py:38`,
  `spec/test_packaging.py:33`, `spec/transfer_eval.py:35` all use v3). The two artifacts are NOT one map
  under two labels: `isotonic.points`, `raw_sha256`, `provenance.git_head`, `selection` and the test
  metrics all differ, so an MCP consumer on the default serves a different map and a different
  data_version stamp than the record — the MCP as configured cannot reproduce the calibration of
  record. The default is NOT in the code (`mcp_server.py:54` has none): the launcher injects it, and
  the hermes gateway config points at v2 (`~/.hermes/config.yaml:2114`; arm profile copy `:2115`).
  *APPLIED 2026-11-11 (`reports/RR-U6FIX-20261111.md`), owner-approved:* the MCP's environment comes
  from opencode's OWN config as well as the hermes gateway's, so THREE files changed
  (`~/.config/opencode/opencode.jsonc:20`, `~/.hermes/config.yaml:2114`, and the arm-profile copy
  `~/.hermes/profiles/w8bo-paged/config.yaml:2115`), each now naming `umpire-cal-v3.json`; verified
  LIVE — `calibration_info()` reports `cal-v1:057a5a35a9d4ec71` with test ECE 0.030163 (the record),
  where before it served the v2 map (ECE 0.026684). The gateway's own wrapper still holds v2 until a
  **gateway restart** (the owner's timing: it reaps gateway sessions and the w8b lane has runs in
  flight); `health` stays DOWN until the pinned model server runs, so U2 stands.
  *Done when:* a fresh MCP session's `calibration_info` (no argument) returns the v3 artifact's
  data_version, and any MCP-decided row carries the record's stamp.

## 6. Owner's next-cue list (what unblocks the most)

1. NO packet paste is pending: P1-P11 are all answered, the RFC-0.1 compatibility note has LANDED
   under D18 (with C3 now enforced in code), and U2 + U6 are verified live (the MCP is alive and serves
   the calibration of record).
2. The W8B lane's four items, written up in `design/W8B-LANE-PROMPT.md`: assert the P11 test's third
   level (one-call `derive_projection` patch), the shape erratum in `design/W8B-FREE-PLAN.md`, the W8SIM
   "5.3%" scoping, and the "C3" rename.
3. Ratify G1 (ordering clause, fresh D-number) and G2 (caller sentence, D-U1).
4. Rule the redaction go/defer (G4); D13/D14 + D17 remain the big gates. W8's fate is settled (G7
   closed: negative, 2026-11-10).

Update law: tick a box only with the command's output in hand; on every card close, re-date the
state-of-record line and revise §14 of the operating prompt (not this file) for volatile facts
(counts, margins). If a chat summary and a book disagree, the book wins.
