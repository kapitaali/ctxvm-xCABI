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
  *ARM RECORDING (2026-11-11, `reports/RR-W8BARMSTATE-20261111.md`):* their `3455f01` (plugin
  0.11.0) is the right DESIGN - the arm is resolved per CALL from the gateway's per-turn contextvar and
  the engine declines to select when the profile says `compressor` - but the RECORDING is still
  process-global: the resolved arm is written into the tracer's `sys`-held state at hook time and read
  back at flush time, so another session in the same gateway (the operator's own chat) can overwrite
  it, and the engine's counters are cumulative over every session the instance served (a paged arm's
  sidecar can show `skippedControl > 0` from another session's declines). Three changes, each with an
  existing precedent in the file: key the arm fields by `session_id`; report the counters as a
  per-session delta; gate on the ARM fields (`arm`, `engineSetting`, `budgetTokens`+`budgetSource`,
  `skippedControl`) and never on `engine` (process-level by design, reads `ctxvm` in both arms). With
  the new fields the PROFILE half of the precondition can become a gate rather than a reading.
  *CELL READY (2026-11-11, their `4566c4b`, LOG row `RR-W8B-CONTRASTOK-20261111`):* **CONTRAST
  OK** - after the 0.11.0 restart the probe reports the two arms as two arms: `w8bn-naive` engine
  null, **0 selections**, profile `w8bn-naive`, budget **200000/default**; `w8bn-paged` engine `ctxvm`,
  **2 selections**, profile `w8bn-paged`, budget **70000/settings** - the first time in this card the
  control arm IS a control. Digests re-verified against the committed prediction block (prompt
  `eac8b37b1602`, fixture `e9e587e60f1f`), so `w8b-cell-01` may run as written (the block:
  `reports/RR-W8B2CLASS-20261111.md` §3 - evictions ~29,000 tokens, first at turn 13-14, cost $0.00 on
  the free tier, artefact PASS parsed-equal, mismatch = INSTRUMENT-BUG and the cell is not booked).
  **ONE REVIEW-SIDE PRECONDITION IS STILL UNMET** (`reports/RR-W8BARMSTATE-20261111.md`): the arm
  fields are still written into the tracer's PROCESS-GLOBAL state, so the probe's correct attribution
  comes from the arms running sequentially with no other session in between - a 20-prompt pair is a
  much longer window, and the operator's chat (default profile) fires hooks in the same gateway.
  Before a pair counts as a CELL, the recording must be keyed per session (and the counters reported as
  a per-session delta), or the pair is a pair attempt again.
  *CLOSURE (2026-11-11, their `163787a` + `c466eb7`, card `reports/RR-W8BCLOSURE-20261111.md`):*
  **W8B is CLOSED NEGATIVE — a PROPER negative, not a harness limit.** The paged arm made 43
  selections at BOTH budgets (70,000 and 90,000) and evicted **zero** tokens, with a parsed-equal
  artefact; the naive arm made 0 selections under its own profile; provider receipts agree within
  0.2 % (input 181,963 vs 181,632). The cause is in the **policy**, not the budget: 21 pages
  declared, **19 fault** (each part demanded again after its first declaration) => 19 pinned => the
  pinned block alone meets the budget => `_plan` returns early on every selection (L5). **This lane's
  earlier caveat is SUPERSEDED** (`reports/RR-W8BCONTRAST-20261111.md` said a no-contrast run is a
  harness limit): the instrument now engages, the arms differ by profile and budget, and the outcome
  is confirmed provider-side and capture-side, not by the sidecar's label. The negative was
  **preregistered**: the committed cell-02 block pre-registered the reading of a zero-eviction outcome
  ("a second measured data point pointing at (c) - NOT a reason to raise the budget again"). **No cell
  is booked** (five voids, then two NO-OPs, $0.00) and no cost claim is available. **One mechanism
  correction, checked in code:** tool-result bodies are NOT a demand surface at all
  (`_demand_text`, `context_engine.py:151-165`) and identical text is credited once
  (`_credit_demand`, `:508-511`), so the pinning comes from NEW PROSE NAMING THE PAGE (the model's
  reply and the next prompt), not from the harness re-sending tool results — their W8C plan already
  states it correctly. **Two ceilings must not be conflated:** W8's scoped 5.3 % (policies keeping
  the first three turns, the last six, the system prompt) is not W8B's ~0 evictable share at a
  read-once shape. **Next owner decision: W8C** (`design/W8C-PLAN.md`, proposed, approval required
  before any instrument change; its falsifier: with the new signal and a floor-sized budget the paged
  arm still evicts zero => the FLOOR is binding, not the signal).
  *W8C REVIEW (2026-11-11, `reports/RR-W8CREVIEW-20261111.md`):* the plan is sound and its own
  falsifier is stated, but two cheap additions should be asked for at the owner's first checkpoint:
  **(a) a falsification set** - the plan's test "a second `read_file` in a later turn DOES pin" should
  ALREADY pass on today's engine, because `_update_page_state` treats a re-render as a demand and pins
  at two (`context_engine.py:479-488`); it is therefore a regression guard for the removal, not evidence
  of the new mechanism, and each test's BEFORE behaviour must be stated. The load-bearing change is the
  REMOVAL of the text signal (what pinned 19 of 21 pages); the explicit `note_refault` mostly moves the
  pin from result-time to call-time. **(b) a stated margin** over the measured floor in the block:
  floor ~48,650 (arithmetic checks out), candidate budget 60,000 => ~11,350 tokens of room, and a
  budget a hair above the floor would make "zero evictions" expected rather than informative.
  **BOTH ASKS ACCEPTED (their `5c0a8aa`):** the plan now carries the correction itself (a "Correction
  (review, `RR-W8CREVIEW-20261111`, verified in the code)" paragraph), names the delta as TWO parts
  (remove the text signal - load-bearing; move the re-read pin to call time - a timing refinement),
  states each test's BEFORE behaviour (only "prose mention does not pin" fails today), and requires
  the block to read floor + margin with the margin NAMED (candidate 60,000 against an estimated 48,650
  floor = 11,350 ~ 2.4 turns of growth). **THE OWNER RULED THE SEQUENCE (2026-11-11,
  `reports/RR-W8CSEQ-20261111.md`)**: instrument -> **checkpoint A = the probe's verdict** (CONTRAST OK
  + paged READY) -> profiles (exactly two, budget on the paged arm only) -> diagnostic (one prompt per
  arm) -> block (floor + margin, committed) -> checkpoint B -> pair (~20 min, $0.00). **The diagnostic
  should assert `page.fault == 0`** - that single number IS the change (19 of 21 faulted under the text
  signal) - but it CANNOT measure the floor: a one-prompt run never reaches the late turns, so the
  floor is DERIVED from the measured W8B series (4,350 + 3x4,700 + 6x4,700 + 2,000 = 48,650) and the
  diagnostic verifies the pins and the growth. **The block should carry the bound**: the six-turn window
  (14-19) comes from the PINNED CEILING, so under the new instrument it is an UPPER BOUND, not a
  promise - state the predicted volume as a range so a narrower window is not read as a falsification.
  *ERRATUM ON THIS LANE'S NOTE 1 (2026-11-11, their `f14db07`, `reports/RR-W8CERRATUM-20261111`)*
  **:** `page.fault` is emitted by the plugin **observer** (`packages/hermes/src/plugin.py`:
  `tool_recall` `:349-352`, `identifier_scan` `:426-434`), not by the engine (which pins in
  `packages/hermes/live/context_engine.py`, `_credit_demand`) - and the count is ENGINE-INDEPENDENT:
  the W8B **control arm ran no engine and recorded the same 19 faults**. So "assert `page.fault == 0`"
  was wrong in its measurement choice; the discriminating observable is the **engine's pin count by
  source** (`pins_by_source.text == 0`, which the plan's section 4 already requires). The **observer must
  be aligned in the same change** or the capture cannot be compared before/after - and if it is not
  aligned, the capture's fault count stays 19 after W8C **by design**, so before/after comparisons must
  be made on the engine's pin count. The W8B closure's outcome is untouched; only its evidence line is
  read more sharply (19 pages were prose-demanded, visible as faults in the control arm too, and the
  engine pinned those pages).
  *STEP-1 VERIFICATION LIST (2026-11-11, `reports/RR-W8CSTEP1-20261111.md`):* a fixed six-item list for
  the instrument commit, each item with the command that checks it (text signal removed not weakened;
  `note_refault` exists and is fed by `pre_tool_call`; **pins by source** reported; the observer aligned;
  the four tests carry their before-behaviour; the gate green with a CLEAN env - `CTXVM_BUDGET_TOKENS`
  must be unset, or `ArmPolicyTests` fails for an unrelated reason). **The frozen-fixture hazard is
  CLEARED by measurement**: the committed live fixture is reproduced ts-stripped byte-identical by the
  in-flight code (18 events, fault source `tool_recall`), the two m3 sources are protected by the
  generator's own refusal, and the test suite never regenerates them - so no law-5 exposure. Two watch
  items: the healthy fixture's turn count moved ([0,1,2,3] -> [0,1,2,3,4]), so the W8C capture may not
  be shape-comparable with W8B's and the block must be written from the diagnostic's capture; and the
  mention telemetry must stay in the SIDECAR/engine status, never inside a v0 event.
  *STEP-1 VERIFIED (2026-11-11, their `7e0f2df`, `reports/RR-W8CVERIFY-20261111.md`):* the
  six-item list run against the committed bytes - **five PASS, one GAP**: the text signal is removed not
  weakened (prose is telemetry only, `context_engine.py:496-525`); `note_refault(args)` exists and is fed
  from `pre_tool_call` (`live/__init__.py:1216`) using the SAME tokenisation as the page table; the
  sidecar carries `faultsBySource`; the observer is aligned (mentions kept as telemetry); the four tests
  carry their before-behaviour; and **the gate is ALL GATES GREEN** (exit 0, TS 24+62+46, python
  196+8+66, schema 682, node-build 16 byte-identical, hub green). **THE GAP: the prose-mention count is
  invisible in the capture** (`prose_mentions`/`refaults` are engine-internal), so a capture can no longer
  distinguish "the scan sees the prose and does not pin" from "the scan is blind" - the B1-class death
  the identifier_scan fault used to expose. **Recommendation: report the mention count in the SIDECAR**
  (never inside a v0 event), so the diagnostic can assert both halves. **GAP CLOSED (their `366e693`,
  `reports/RR-W8CVERIFY-20261111.md` section 5):** the sidecar now carries `proseMentions` +
  `proseMentionsTotal` (`live/__init__.py:680-685`) and `tools/coverage_check.py` makes it a GATE -
  every key must name a page the trace declared, and the total must match the sum; sidecar-only, no v0
  event gains a field; the key format was checked here (the observer's `_declared` key IS the trace's
  `logicalRef`). Gate green at that commit. This lane's earlier
  "byte-identical" fixture claim is corrected by an appended erratum (the comparison used the working
  tree, not HEAD: the committed fixture had 20 lines with two identifier_scan faults and needed the
  regeneration their commit carried; the no-law-5-exposure conclusion survives because the package
  fixture is not checksum-pinned and the two frozen ones are protected).
  *HOSTED CI RED (2026-11-11, `reports/RR-CIRED-20261111.md`):* the hosted gate failed for three
  pushes (`97c4902`, `70df8d5`, `0ba4f8f`; the last green was `52b09a9`) - the `ts` job's hermes step,
  2 failures, **one file**: the committed `packages/hermes/test/generate_traces.py` still asserts the
  pre-0.12.0 behaviour (the live-shape trace must carry an `identifier_scan` fault) and the observer is
  now aligned, so the generator trips that guard. The other lane has the fix written and uncommitted;
  this lane does not stage another lane's path. **THE TOOLING GAP IS NOW CLOSED:**
  `tools/ci-rehearsal.py --committed` rehearses the COMMITTED tree alone (what actions/checkout gives the
  runner) and reproduces the hosted failure in one command - the default mode overlays the dirty tree
  ("what would be pushed"), which is why it was green while the hosted run was red.
  **THE STANDING RULE: a green local gate is evidence about the WORKING TREE; the gate that decides the
  PUSHED COMMIT is `ci-rehearsal.py --committed`.**
  *CHECKPOINT A PASSED - AND THE ATTRIBUTION IS A PROPERTY OF THE LAST FLUSH (2026-11-11, their
  `cf7fdbe`, `reports/RR-W8CATTR-20261111.md`):* the probe on the 0.12.1 gateway returns CONTRAST OK and
  EVERY arm field matches this lane's checklist (naive: engine null, 0 selections, `w8cn-naive`,
  200000/default; paged: engine ctxvm, 8 selections, `w8cn-paged`, 60000/settings), and the liveness is
  now on live bytes (a two-prompt diagnostic: `proseMentions` 1, total 1, `faultsBySource` all zero,
  sidecar key byte-identical to the trace's `logicalRef`). **One correction to this lane's checklist:** a
  ONE-PROMPT PROBE CANNOT SHOW MENTIONS (the final reply never enters a later request, so no
  `pre_llm_call` scans it) - liveness is observable on the two-prompt diagnostic only. **THE FINDING:
  THE PAGED ARM'S OWN CAPTURE ON DISK RIGHT NOW ATTESTS THE CONTROL ARM** (profile `default`, arm
  `control`, `engineSetting compressor`, 0 selections, 200000/default) although that session ran in the
  paged profile (20 log hits there, 0 in the naive profile's) - because the arm fields are still
  PROCESS-GLOBAL and are read AT FLUSH TIME: the probe read the sidecar at ~20:04 (right after the
  flush, so its verdict was right), and at 20:05:44 a gateway restart's re-flush rewrote ALL SIX
  captures with the then-current global values. **Consequences: the attribution evidence must be read
  at RUN TIME and copied into the record** (their LOG row does), and any later reading of a capture's
  `plugin` block can see another session's arm and call a correct cell VOID - the still-open fix
  (key the arm fields by session id, `reports/RR-W8BARMSTATE-20261111.md`) is now observably
  load-bearing for step 5 (the block) and step 6 (the pair).
  *CELL-01: THE TREATMENT ACTS (2026-11-11, `reports/RR-W8CCELL01-20261111.md`):* the first run in the
  card where the policy visibly acts, **independently recomputed from the captures**: the paged arm's
  request **flattens at ~61 k from turn 11/12** (sum 922,911, final 60,781) while the control keeps
  growing (sum 1,108,214, final 102,967) - ratios 0.833x / 0.590x, exactly their numbers. But the
  **trace cannot see it** (0 `page.evict` rows, `evictedTokens` 0 in both arms) so the verifier says
  NO-OP, the control is labelled VOID by a check that does not know the control arm, and the block's
  rule makes it INSTRUMENT-BUG - **no cell is booked**. **The cost consequence, from the DB's own usage
  counters**: the paged arm's uncached input is **4.77x** the control's (1,071,090 vs 224,455) and its
  **cache_read 0.64x** (2,870,144 vs 4,461,568) - it sends fewer tokens and pays with cache misses on
  BOTH sides of the cache, which is the cache-stability question the P8 packet raised; no saving may be
  claimed (law 7). **This lane's attribution finding extends to the budget**: the paged arm's capture
  attests `200000/default` while the run used 60,000, so a capture's `plugin` block is not a record of
  the arm's configuration - take it from the run, never from the capture afterwards. Both arms show
  `proseMentions` 190, which is the strongest statement yet that the prose signal was REMOVED rather
  than DISABLED. Two instrument fixes are prerequisites for the next pair: engine -> observer
  reporting (evict rows + `evictedTokens`) and an arm-aware verifier.
  *NO page.evict, AND THAT IS RIGHT (2026-11-11, `reports/RR-W8CEVICT-20261111.md`):* the other lane's
  agent declined to emit `page.evict` for the cell's fix, because **this policy removes the dropped
  messages rather than substituting stubs** and RFC-0's `page.evict` REQUIRES `stubText` - so emitting
  one would describe a wire that was not sent. **Verified and endorsed**: the hermes engine's path is
  `_plan` -> `_assemble(..., dropped, repositioned)` with **no stub substitution anywhere** (the stub
  mechanism belongs to the rust core's page table), and the sealed schema gives `page.evict`
  `required: [type, turn, page, stubText]` + `additionalProperties: false`. The count therefore belongs
  in `turn.render.evictedTokens` (a v0 required field that does not presuppose substitution), the
  detail in the **sidecar**, and `page.evict` stays for policies that really stub. **This lane's earlier
  request for "page.evict per dropped page" was wrong for this engine** - an erratum on the ask, not
  on the decision. **The rule it establishes: a missing event is a gap, a wrong event is a falsehood.**
  **The sidecar's detail must be checkable against the trace** (the `proseMentions` precedent): every
  dropped page keyed by the trace's `logicalRef` and naming a declared page; the per-page totals summing
  to the trace's `evictedTokens`; a control arm reporting none; `repositioned` kept separate. And the
  engine -> observer payload should carry the **logicalRef**, not the identifier tokens, so the rule can
  be stated at all. The verifier's `evictions > 0` gate is now satisfiable by the trace without a
  fabricated event - which is what makes the next pair bookable.
  *CELL-02's BLOCK (2026-11-12, `reports/RR-W8CCELL02-20261112.md`):* the block takes this lane's three
  additions (the **attribution clause** - read the arm/profile/budget from the RUN, never from a capture
  afterwards; the digests; the instrument version 0.13.0) and keeps the named floor + margin, five
  checkable preconditions and the no-saving-claim clause - **but one number is stale by an order of
  magnitude**: it predicts evictions "first at turn 14 or later; volume 5-20 k", while cell-01's own
  measurement (the arms' residency difference, recomputed from the captures) gives **turn 4** and a
  **session total of 185,303 tokens** (peak 42,186 at turn 19) - 9x to 37x the stated upper bound, and
  the block's own preamble cites that measurement. **Consequence if unfixed:** a correct run at ~185 k
  would MISS the block's range, and by the block's own verdict line be classified INSTRUMENT-BUG and not
  booked - sending the lane to re-fix a working instrument. Two honest fixes (the measured prediction
  with a three-way outcome rule, or the range restated as a THRESHOLD with the expected volume
  alongside) - the freeze discipline allows either, since the prediction must be committed before the
  run (it is) and a new cell is a fresh preregistration.
  *CELL-02 IS A CELL (2026-11-12, their `e6863f4`, `reports/RR-W8CCELL02RUN-20261112.md`):* the first
  **counted cell in the W8 family** — verified from the captures digit for digit: paged
  `evictedTokens` 0 x13 then 4,396…55,914 (**210,856**, first non-zero at **turn 13**), residency
  63,014 -> **64,733** vs the control's 62,999 -> **107,794** (ratio **0.60x**), the control's counter
  **0 on every turn**, and **no `page.evict` row in either arm** (the count rides in
  `turn.render.evictedTokens`) — so **the trace witnesses the policy engaging for the first time**.
  **The unit lesson (their rule): a block's volume column must name its unit** — the trace sums
  *per-turn re-drops*, this lane's ~185 k was the *net residency difference* (12% apart, and this
  lane's "turn 4" onset was wrong: **the onset is the first turn the unconstrained request exceeds
  the budget**, plus a two-turn engine lag). **Booking despite the mismatch was defensible** (the
  instrument was verified; the cause was the block's own specification error) — but the rule's text
  was not followed literally, so it needs the owner's refinement: units named; a *specified* mismatch
  is a recorded deviation, an unexplained one stays INSTRUMENT-BUG. **The attribution items are
  CLOSED** (`cc8f833`, 0.13.1: the budget is session-keyed too) — the capture is self-describing now.
  Still open: the payload's logicalRef + the sidecar's per-page detail + a checker rule (the *count*
  is witnessed; the *set* of dropped pages is not). **No saving may be claimed** (4.73x the uncached
  input, law 7).
  *CELL-03 DRAFT REVIEWED BEFORE COMMIT (2026-11-12, `reports/RR-W8CCELL03-20261112.md`):* the
  paid-pair draft's arithmetic **checks out** (cell-02's own net reduction **167,793**, turns 12–19
  **168,447**; counter/net = **1.257**), and the other lane is **right** that this lane's "12 % apart"
  compared **two different runs** — within cell-02 the gap is 26 % (net = 0.80 × counter) ✓ (erratum
  appended). **Three things to settle before the block is committed:** (a) the **refined rule must be
  RATIFIED first** (it is in front of the owner, `reports/RR-SPEND-20261112.md` §4) — a block committed
  under an unratified rule repeats cell-02's defect in a milder form; (b) the **widened brackets**
  ($0.15–0.50, 1.5–4.0× vs the owner's $0.20–0.30, 1.8–2.4×) are a **deviation that needs the owner's
  word** — the reason is sound (the subject moves to Luna; ~46.7k cache-write tokens per call were seen
  on earlier paid Luna cells) — carry the owner's brackets as the expectation and the widened ones as the
  tolerance, or carry the widening with its reason ✓; (c) the **claim set must be cost-only** (the
  draft reuses cell-02's shape, so the accuracy PASS stays near-guaranteed — acceptable here, because
  this pair's purpose is to make the cost claim *measured*; the revisit task belongs to the cache-stable
  card). Plus: the cache-write share is a **PROXY** (the ledger's uncached input is prompt minus both
  cache buckets) → name it, mark it UNVERIFIED, and predict the receipts' observable ✓; and the **floor
  must be re-derived for the paid subject** (48,650 carries longcat's scaffold and system prompt) ✓.
  *THE PAID PAIR LANDED (2026-11-12, `reports/RR-PAIDRESULT-20261112.md`):* **$0.2534** for the pair
  (the owner's central estimate $0.25 ✓, the bracket's LOW end ✓), the **paged arm costs 2.11× the
  control** in dollars ($0.1580 vs $0.0748) ✓ — inside the projected 1.8–2.4× ✓ — and **the cause is
  measured**: the paged arm's **cache_write is 4.49× the control's** (1,025,825 vs 228,382 ✓) at
  **0.61× its cache_read** ✓, while it sends **0.82× the tokens** ✓ and holds the request at the budget
  (**0.57×** the final request ✓). The trace witnessed the evictions (275,362 per-turn re-drops, first at
  **turn 12** ✓; the control's counter **0** ✓) — and the onset landed exactly where the **ratified
  rule's** form puts it (the control crosses 60,000 at turn 11, the eviction follows one turn later —
  the lag is run-specific ✓, which is why the rule says *plus the lag* and never a turn number ✓).
  **So: no saving may be claimed** (law 7 ✓ — fewer tokens, more money ✓), the claim stays scoped to this
  shape/model/budget ✓, and the **break-even must be re-derived** for a policy that rewrites the prefix
  every turn (the measured `P′` is 4.49× and the token saving is 18 % of the session ⇒ the policy
  **loses** at these rates ✓). The cause of the cache-write volume is now answered **for this shape** ✓
  — it is the per-turn prefix invalidation of a selection that is not cache-stable ✓, i.e. the **P8**
  thesis ✓, and therefore where the remaining hope lives ✓.
  *THE NEXT POLICY CHOICE, PRICED (2026-11-12, `reports/RR-POLICYCHOICE-20261112.md`):* the paid
  pair's negative is about the **REWRITE, not the eviction** ✓ — the paged arm **never sent 894,814
  tokens** ✓ and **re-sent 797,443** of them ✓ (0.89× the unsent content ✓): the token claim survives
  (0.82× ✓) and the dollar claim fails (2.11× against ✓) because **a cache write costs 13× a cache
  read** ✓ → the saving is **$0.0089** ✓ and the tax **$0.1037** = **11.6×** it ✓. Hence the
  dollar-optimal policy is **send less, and never change what you already sent** ✓. Priced candidates:
  cache-stable selection / watermark (the same mechanism — the evicted set must stop changing ✓) net
  ≈ **−$0.009 ± $0.010** ✓ = **a tie inside one pair's noise** ✓ (the owner's own reading ✓), with the
  design requirement now computable: **extra write volume < ~0.13 M tokens per session** (≈ 3.2 k per
  engaged call ✓ — an eighth of today's 26.6 k ✓); stop-and-publish ✓; and **a different shape** — the
  only place with a materially bigger effect ✓ (the same unsent tokens priced at the input rate are
  worth ≈ **$0.089** ✓ ≈ 1.2× the control ✓), i.e. content that is **not cached** ✓ — a fresh
  preregistration under the W8 reopen's rule ✓. **So: no paid confirmation is worth buying** ✓ (the
  effect is 3.5 % of the pair's spend ✓) — the next test is **zero-spend** with the **cache-write volume
  as the primary metric** ✓, and the simulator can now be **scored** ✓ (the paid pair measured the
  constants it lacked ✓).
  *THE FREE PAIR AFTER THE PAID ONE IS A VOID (2026-11-12, `reports/RR-VOIDPAIR-20261112.md`):* the
  scoring run on the free tier **never engaged the engine** on the treatment arm (`engine: null` ✓ —
  which in 0.13.x means *select_context() was never called* ✓ — 0 selections ✓, 0 evictions ✓, empty
  `evictedPages`/`callSizes` ✓) while the profile asked for it (`engineSetting: ctxvm` ✓,
  `60000/settings` ✓) ✓ → **a void by instrument fault, not a policy result** ✓, nothing spent ✓ ($0 ✓),
  and **not booked** ✓ (the ratified rule + their own precondition ✓). The engine code did **not** change
  ✓ (`git diff 2b6c950..HEAD` on `context_engine.py` is empty ✓) → a **runtime** cause ✓: the gateway was
  not restarted after the `w8cn-*` profiles were recreated ✓ (the PLG-7 behaviour ✓), while the paid pair
  used fresh `w8cp-*` homes **with** a restart ✓ → the contrast identifies it ✓. **The sharp edge:** the
  verifier's new CONTROL verdict (*"a control asked to select nothing has not done nothing"* ✓) is **not
  arm-conditioned** ✓, and a **paged** arm with 0 selections has exactly the shape it would accept ✓ →
  booked, it would be a **false cell** ✓; the sidecar already carries the evidence ✓, so a **third**
  verdict is cheap ✓ — `arm == paged and engine == null` → **VOID** ✓. **And 0.13.3 carries the two open
  instrument items** ✓: `evictedPages` (the per-page detail ✓) and `callSizes` (the per-call sizes ✓ —
  the simulator's prerequisite ✓) ✓, so the simulator's blocker is implemented ✓ and the next scoring run
  can produce a scoreable capture ✓ — provided the gateway is restarted ✓ and the probe's READY is a
  precondition of the run ✓.
  *THE ENGINE-LAYERS DIAGNOSIS, REVIEWED (2026-11-12, `reports/RR-W8CENGINE-20261112.md`):* **sound** ✓ —
  every exclusion is a file-level fact ✓ and only the third `agent_init` path survives ✓, so the
  disagreement is **inside the agent build** ✓ (the registry is empty *at construction time* ✓) and this
  is the **fourth form** of the failure class ✓ — the first three were configuration/ordering faults with
  a known fix ✓, this one is a **host-side ordering property** no ctxvm-side configuration controls ✓.
  **This lane's own card is corrected** ✓ (erratum): `engine: null` establishes *no selections* ✓, not
  *"never called"* ✓ (the implementation is `_engine_activated_for` ✓ = null iff selections == 0 ✓) — the
  conclusion stood ✓ but the right evidence is the **agent's behaviour** ✓ (the built-in compressor ✓).
  **Their two commits already close this lane's sharp edge** ✓: the arm-conditioned verdict ✓
  (`450b9bd` ✓ — *a treatment that never acted is void, not a control that behaved* ✓) and the three layer
  fields ✓ (`93ff8ab` ✓) so the sidecar can **name the failing layer** ✓. **The cheap insurance left:**
  the VOID capture was avoidable ✓ — the probe's READY runs in a **different process** than the 42-call
  run ✓, so "probe first" cannot guarantee the run's activation ✓; with the new fields the run should
  **assert engagement on its first prompt and abort** ✓ (naming the layer ✓) → a host-side regression costs
  **one prompt** ✓, and on a paid run **$0.00** ✓. **On the two options:** option 1 (a one-line host
  diagnostic ✓) is the right first move ✓ — it answers *what order* ✓ in one free prompt ✓, and the
  consent framing is right ✓ (the agent runtime is outside both lanes ✓). Option 2 (bypass the host slot ✓)
  is endorsed with their own caveat ✓ — it changes the activation path ✓, so the booked cells would be on
  a different mechanism than any future one ✓: a **new experiment**, not a fallback ✓. **A third option
  the arithmetic supports** ✓: file the host defect and **close the W8C line** ✓ — the remaining measurable
  upside is ≈ **$0.009/session** ✓ (3.5 % of one paid pair ✓) against a **host-side** blocker ✓, so if
  option 1 does not name it in one free prompt ✓, closing with the defect filed is the honest end ✓.
  *THE HOST'S SOURCE COMPLETES THE DIAGNOSIS (2026-11-12, `reports/RR-W8CTRANSPORT-20261112.md`):*
  read in the host's tree, read-only ✓ — the per-turn selection hook has **exactly one** production
  call site (`agent/turn_request_assembly.py:145` ✓), its **only** guard is `_engine_overrides_hook` ✓
  (true iff the engine overrides the ABC's no-op ✓ → our engine does ✓ → the gate passes ✓), and the
  one-shot CLI is **not** a separate fast path ✓ (`_run_oneshot_from_args` → `launch_gateway_chat` ✓) →
  it *should* reach the same assembly ✓ ⇒ **the request in the one-shot path is not assembled through
  `assemble_api_request`** ✓✓ — a precise, file-and-line reproducible statement ✓ (not the hypothesis
  "the difference is in how the host assembles this path" ✓) ✓ and upstream's to fix ✓. **Their
  `_entered.log` evidence is durable** ✓ (the prune globs only `*.jsonl` ✓ → it cannot have removed it ✓,
  and the file is absent ✓) ✓, and the durable witness going forward is the sidecar's **`engineEntered`** ✓
  (0.13.7 ✓ — the void runs were 0.13.3 ✓ and predate it ✓). **The one free check left** ✓: one
  session, reading all three witnesses **from the same run** ✓ (the host's `CONTEXT-ENGINE-DIAG` lines ✓,
  `engineEntered` ✓, `_entered.log` ✓) — **$0.00** ✓ — which turns the upstream report from *"the hook
  is not called here"* into *"…and here is the path"* ✓✓. **On the two options: they are not exclusive**
  ✓ — option 1 (report upstream ✓) is warranted ✓, and option 2 (the desktop transport ✓) is the
  **scoring remedy**, not only a test ✓✓ (a scoreable capture with no upstream patch ✓ and no change to
  the instrument ✓✓) — with the honest caveat that a desktop-path pair is a **different transport** ✓ →
  fine for scoring ✓, not for a comparable cell ✓. **And a third step, ours and reusable** ✓: when the
  transport never calls the hook ✓, the run's refusal should **say so** ✓ (*"this transport does not
  assemble the engine"* ✓) instead of producing a void ✓✓ — it would have said this on 11 November ✓.
  *ENGINE AUDIT: THE PLAN NEVER RAN (2026-11-12, `reports/RR-W8CAUDIT-20261112.md`):* the counter is
  incremented **before** the plan ✓ — `select_context` increments `self._meter["select"]` at `:443` ✓ and
  only then classifies (`:451` ✓) and plans (`:456` ✓) — and the only earlier return is the **control-arm
  branch** (`:428-431` ✓) ⇒ **`engineSelections 0` means every call returned there** ✓✓ ⇒ **the plan never
  ran** ✓✓ ⇒ **(a) and (b) are both premature** ✓✓ (both assume the engine planned ✓) — and (a)'s *second*
  half is right ✓✓: with no selection the request grows to the **host's** limit ✓✓, so the ~62 k plateau is
  the host's compaction ✓✓ ⇒ the run's honest statement is *"the paged arm was not a paged arm"* ✓✓.
  **The two resolutions of the same policy disagree** ✓✓ — the sidecar's `engineSetting: ctxvm` ✓ (hook
  time ✓) vs the engine's call-time resolution ✓ (compressor ✓) ✓ — and `policy()`'s fallback is
  `engine or "compressor"` ✓✓ ⇒ **a missing/unreadable home silently reads as the control arm** ✓✓✓
  (the profiles were recreated ✓✓, so a stale contextvar home ✓✓ would resolve to nothing ✓✓) — ⇒ **the
  fix is ours** ✓✓ (pass the hook-time resolution into the engine's per-call resolution ✓✓) ⇒ **the
  upstream report is not warranted** ✓✓ (the hook path works ✓✓ — 67 entries ✓✓) **and the desktop
  transport is unlikely to help** ✓✓ (the contextvar would be missing there too ✓✓; no worker executions
  anywhere ✓✓). **The `_decision.log` needs the call-time resolution's HOME and ENGINE** ✓✓ (its current
  fields cannot say *which* resolution failed ✓✓) ✓✓. **And the unit point is the next block's blocker** ✓✓:
  the budget is **60,000 apx4-char tokens** ✓✓ (≈240,000 chars ✓) while every quoted request size is in
  **provider** tokens ✓✓, and the books' floor (48,650 ✓) **mixes the two** ✓✓ ⇒ the next block must name
  the unit ✓✓ and compare the keep law's floor in **apx4** ✓✓ ✓.
  *CALL-GRANULARITY SCORER VERIFIED PASS (2026-11-12, `reports/RR-SIM3CHECK-20261112.md` on `78cc6e9`):*
  reproduced from `local-b7d235587eef…jsonl` (`w8b-20261112-201127`, plugin 0.13.13, $0.00): 41
  selections (`engineEntered: 47`), 16 dropping selections in `callSizes`, **median |error| 1.2%**, sign
  exact → **PASS** against the preregistered rule (`2b6c950`), `turn.render.evictedTokens` sum
  **227,963** across 7 turns ✓. Confirms the zero counters were instance-identity splits fixed by
  module-global `OBSERVER`, `ACTIVATIONS['select']`, and `CALL_LOG` (`1af40e7`, `bf6fcb1`), and default
  home `~/.hermes` is now forced to `compressor` (`1af40e7`) ✓. Two non-blocking sidecar residuals
  located: `plugin.engine: null` (`_engine_activated_for` still checks instance `_engine_selections_for`)
  and `plugin.evictedPagesCount: 0` (`context_engine._value_tokens` splits on `.` while
  `plugin.identity_tokens` keeps `.txt`) ✓.
  *CRITICAL AUDIT OF W8SIM3 & UPSTREAM DRAFT (2026-11-12, `reports/RR-SIM3CRITIQUE-20261112.md`):*
  (1) The 2-calls-per-turn diagnosis holds even on `sim(S)`'s `drop_k` denominator (median error **8.63%
  ≤ 10%**, mean 8.71%, max 17.44% across the 16 dropping calls) ✓. (2) However, `RR-W8SIM3`'s physical
  explanation of the residual (*"the protected-set/scaffold gap"*) is wrong: both `before` and `after`
  sum `_tokens_for(m)` over the full request (`context_engine.py:495-496`), and the residual is
  **whole-page quantization** (~4,400-token pages ≈ 7.3% of budget) — calls 1–9 have errors
  `0.28%–1.21%` (`after = 59,283..59,834`), while calls 10–16 cross a page boundary by 91 tokens and
  have errors **`6.01%–8.21%`** (`after = 55,449..56,599`, **7 of 16 above the 5% threshold**; the
  16-sample median is `1.16%` only because the 8th/9th sorted values are `1.06%/1.11%` while the 10th
  jumps to `6.01%`) ✓. (3) `CALL_LOG.append` (`:495`) sits *after* `if not dropped and not
  repositioned: return None` (`:492-493`), censoring the 25 non-dropping calls so `score_calls()`'s
  sign check is one-sided ✓. (4) `upstream/hermes-context-engine-hook.md` (`e430322`) should be
  **deleted** (`git rm`), not edited, and `RR-W8CTRANSPORT-20261112` §1–§2 carries an explicit erratum
  (the absent `_entered.log` in 0.13.7 `f1879a3` was an unimported `Path` / undefined `ENTERED`
  swallowed by `except Exception: pass`, fixed in `22404cd`) ✓.
  *VERIFIED 0.13.14 & SIM(S3) BOUND (`d491912`, `reports/RR-SIM3S3CHECK-20261112.md`):* `upstream/hermes-context-engine-hook.md`
  deleted ✓; §8 retraction appended directly to `reports/RR-W8CTRANSPORT-20261112.md` ✓; `CALL_LOG`
  moved before the L7 return (`context_engine.py:494-505`) ✓; `_engine_activated_for` and stem-joined
  `refs_for_identity_tokens` verified in-process (201 hermes tests green) ✓; `sim(S3)` bound
  `(51,152, 60,000]` verified on the 16 dropping calls ✓.
  *OPENCODE VS HERMES TURN-ACCOUNTING REVIEW (`78b3382`, `reports/RR-OCDIFFREV-20261113.md`):* confirms
  the 6 vs 13 `turn.render` / 12 vs 13 request measurement on `longcat-2.5` (free, $0.00) and the `m7`
  premise correction (`m7` = Hermes, `m2/m5/m6` = OpenCode, `m8` = AI-SDK) ✓. Four added findings:
  (1) prompts 2–6 on OpenCode made 2.0 requests/prompt (batching `read` + `shell`), so the 13 vs 12
  request difference is a single sequential `shell` call on prompt 1 ✓; (2) `@ctxvm/opencode` emits
  `0/N` `providerUsage` because `plugin.ts` only hooks pre-request `session.context` and never calls
  `noteUsage()` (even though OpenCode assistant messages carry `.tokens`), while Hermes emits `6/6`
  last-write-wins per user turn (dropping call 1 of 2 from `call.meta`) ✓; (3) `@ctxvm/opencode` still
  emits v0 `identifier_scan` `faultOfResidentPage` rows (`12` vs `0` on Hermes 0.12.0+) ✓; (4)
  `README.md:114,116` can cite `RR-OCDIFF-20261113` and `m5` vs `m7` ✓.
  *REVIEW OF W8C CLOSING (`7ca4672`, plugin `0.13.19`, `reports/RR-W8CCLOSINGREV-20261113.md`):*
  empirical results and trace `evictedTokens > 0` proof stand ✓; however, the reason `0.13.18` lost
  `evictedPagesCount` (`0`) and `callSizes` (`0`) was **not** policy re-attribution — in both `0.13.18`
  (`3f0f7a0`) and `0.13.19` (`7ca4672`), `packages/hermes/live/__init__.py:1465` uses `_target` **15
  lines before `_target = _sid` is assigned at `:1480`**, raising `UnboundLocalError: cannot access
  local variable '_target' where it is not associated with a value` on every call and swallowing it in
  `except Exception: pass` (`:1485`) ✓. Also `_coverage_manifest` (`:790`) still writes
  `"engineSelections": _selections_total()` (only `_write_live_stamp` at `:405` writes
  `engineSelectionsProcess`) ✓.
  *CONFIRMATION CAPTURE VERIFIED (`2d9f6cf`, `reports/RR-W8CCONFIRMEDREV-20261113.md`):* the run
  bundle, the sidecar, and the scorer all re-run and PASS ✓ (`w8b-20261113-150420-paged`: CELL, 41 calls,
  210,856 evicted, `engineSelections 16`, `evictedPagesCount 9`, `callSizes 16`, scorer PASS median 0.92%) ✓
  — two caveats: (1) `_selections.log` holds **81** lines, 39 of them from the plugin's own pytest suite
  (no `CTXVM_TRACE_DIR` in `test_context_engine.py` ⇒ the engine writes into the live trace dir; reproduced
  offline: 81 → 121 lines) ✓, so the file must be filtered by the run's timestamp window, not counted ✓;
  (2) `_swallowed.log` covers **2 of 23** swallow sites in `live/__init__.py` and **0 of 12** in
  `context_engine.py` ✓ ⇒ its absence proves nothing for the other 33 ✓.
  *W8D PREREGISTRATION REVIEWED (`3d91fb9`, `reports/RR-W8DREVIEW-20261112.md`):* the refusal to spend is
  RIGHT ✓ and stronger than stated ✓, but three arithmetic seams are open ✓ — (1) “unsent content 203,975” is
  the net request reduction, not the unsent content (894,814 ✓), and the input rate belongs to the cold-prefix
  shape ✓, so the measured penalty is **11.6×** ✓ (the books' ratio ✓), not 3.1–4.1× ✓; (2) §9's “36 rewrite
  events” has no locator ✓ and the pair's own billed write volume is **1,254,207** ✓ (not the export's
  1,408,011 ✓, which includes 14 non-pair requests ✓); (3) the decisive measured number is **24,424 write
  tokens/call** ✓ (DB ✓) against a 1,868–2,428 allowance ✓ ⇒ **~10× over allowance today** ✓ — and §5 step 1
  cannot run as written (cell-03 has no `_selections.log` ✓) while the 0.13.22 capture already answers it:
  its dropped-set sizes are **monotone** ✓, so hold-once is a set-level no-op ✓ and falsifier H4's bracket
  admits its own falsifier ✓.
  *CAPTURE REPLAY VERIFIED (`reports/RR-W8CREPLAY-20261112.md`):* replay of `local-d60a50c4…` re-runs exactly ✓ —
  81 events ✓, 0 divergences ✓, 0 violations ✓, exit 0 ✓, stdout hash `fe27e29c813c4e06` three times ✓ ✓, and
  `export --turn 12` gives 21 slots ✓, 86,569 resident tokens ✓, **0 stubbed** ✓, slot 0 = `part-01.txt` ✓ — one
  qualifier ✓: the page table is derived by `ctxvm-core` from the trace alone ✓, but `turn.render.evictedTokens`
  is a **plugin-written field** the replay reads rather than re-derives ✓, so *“both are independently
  derived”* overstates the eviction half ✓ (86,569 ✓ derived, 4,396 ✓ carried) ✓.
  *THE TURN-12 PROJECTION IS TURN-INVARIANT (`reports/RR-W8CREPLAY2-20261113.md`):* `export --turn 12/15/19`
  each give 21 slots ✓ / 86,569 resident ✓ / **0 stubbed** ✓ / 0 violations ✓ — because the trace's
  `residentTokens` is pinned to the **whole-table** residency ✓ (`packages/hermes/src/plugin.py:229` ✓), and
  the trace carries **no `page.evict` row at all** ✓ (0 of 81 events ✓) ⇒ the 0-stub result witnesses the
  **removal** semantics ✓ but is **not a per-turn observation** ✓, and there is **no contrast case** to measure
  against ✓ (`corpus/m1`'s 4 `page.evict` events are synthetic ✓; the live captures have none ✓).
  *REPRESENTATION GAP CONFIRMED BY THE PROVIDER'S OWN RECEIPTS (`reports/RR-SHAPEGAP-20261113.md`):* the
  reviewer's four points verified against code and captures ✓ — **"0 stubs" is entailed by the event
  vocabulary** ✓ (the hermes engine has no stub concept ✓ and the adapter never emits `page.evict` ✓), the
  replay agreement is a **determinism + internal-consistency** witness ✓ (not vacuous ✓ — mutating
  `residentTokens` or a render mode trips a divergence ✓), the plateau cannot separate removal from
  substitution ✓, and the **representation gap is real and larger than stated** ✓: the projection is
  **turn-invariant** ✓ (21 slots / 86,569 at turns 0–19 ✓) because the flush tail is **positional** ✓, so at
  turn 0 it already claims 21 pages that exist only at turn 19 ✓. **The reviewer's falsifier, run on the
  paid capture, does not fire** ✓: provider receipts put the paged request at **0.563** of the control's at
  turn 19 ✓ (trace's own ratio 0.570 ✓) ⇒ the model **did not** see all 21 pages ✓ ⇒ the removal
  measurement is right ✓ and the **derived table is the false part** ✓. Also: `turn.render.evictedTokens` is a
  **lagging cumulative** ✓ (session sum 210,856 = **5.44×** the unique removed content 38,764 ✓) ⇒ the W8D
  prereg's "36 rewrite events" is unsupported ✓ (measured: **9** pages ever removed ✓, **16** dropping
  selections ✓) and its write-volume per event must be re-derived ✓ — zero-spend, from the capture ✓.
  *THE W8D ERRATUM REVIEWED (`ceb15d2`, `reports/RR-W8DERRATUM-20261113.md`):* five of §11's inputs verified ✓
  (16 dropping selections ✓, 75 page-drops ✓, 9 distinct pages ✓, 1,254,207 pair writes ✓, and the withdrawal of
  "0 stubs" ✓), but three arithmetic errors ✓ — the denominator is the paid arm's **42** calls ✓ (not the free
  capture's 41 ✓), the "0.918" ratio is **inverted** ✓ (the sentence it supports needs 1.090 ✓) and mixes **two
  tokenizers** ✓ (apx4 vs provider ✓, factor 1.92–1.94 ✓), and "**rewrite events, today 16**" is unsupported ✓
  (the dropped-set *sizes* take 9 distinct values ✓ and change 9 times ✓) ⇒ the like-for-like comparison is
  **9 → 9 = 1.0×** ✓, not 16 → 9 = 1.8× ✓. **The model check contradicts itself** ✓: 16 whole-request writes
  would cost 1,804,703 provider tokens against the measured 1,025,825 ✓ (1.76× ✓), while **9** whole-request
  writes fit with a residual of **0.2 %** ✓ ✓ — and the provider's receipts witness the whole-request write ✓
  (the paged arm's cached prefix collapsed to 14,504 ✓ — the turn-0 cached prefix was 14,554 ✓ — so no message content was
  reusable ✓). ⇒ **The refusal stands and is stronger** ✓: today's own **24,424** write tokens/call against the
  1,868–2,428 allowance ✓ ≈ **10× over** ✓ — and hold-once does not touch it ✓, because **the dropped set is
  already monotone** ✓ (the union of pages ever dropped = 9 ✓ equals the final set's size ✓ ⇒ the policy never
  un-drops ✓ ⇒ hold-once's premise already holds ✓). ⇒ **The zero-spend gate's step 1 cannot discriminate** ✓
  (H1 predicts 9–14 ✓; today's run already yields 9 ✓) ⇒ the one missing measurement is the per-call dropped
  **identity** list ✓ (the observer computes it ✓; the adapter folds it into a union ✓) ⇒ one sidecar field would
  make step 1 a lookup ✓ at zero spend ✓.
  *OMISSION REPRESENTATION, PROPOSED (`reports/RR-OMISSION-20261113.md`):* the reviewer's open item 3, closed as a
  **proposal** ✓ (no spec, no adapter, no `design/` file ✓ — the owner clears new ones ✓), and item 4 measured ✓.
  The measured gap ✓: the derived table claims 21 pages / 86,569 tokens ✓ (`export --turn 0/5/12/19` ✓,
  turn-invariant ✓) while the request carried 12 pages / 47,805 ✓; v0 has **no omission verb** ✓ (`page.evict`
  requires `stubText` ✓); the count is **unchecked in v0** ✓ (OPEN T-OVICT ✓) and is in fact a **lagging
  cumulative** ✓ (210,856 = **5.44×** the unique 38,764 ✓); the derived table is **not turn-scoped** ✓ (the cut
  is positional ✓); the corpus has **no contrast case** ✓ (the only 4 `page.evict` rows are synthetic ✓) ⇒ a
  trace-only reader cannot say which pages a request omitted ✓. **Why now** ✓: the second consumer already
  exists in the paper's own design ✓ — Part I §12 makes a view *"a pure function of a trace"* ✓
  (`white-paper.md:549` ✓) ⇒ "leave it unrepresented" would contradict a claim the same paper makes ✓ ⇒ the
  decision cannot wait for Part II's view claims ✓. **Recommended shape: count + identity + checked** ✓ —
  four parts, **two of them free** ✓: the **count** exists ✓ (`turn.render.evictedTokens` ✓) but needs a
  per-turn meaning ✓ and a check ✓; the **identity** must be **on the wire** ✓ (an RFC-0.1 per-turn
  dropped-page list ✓) or Part I §12's "pure function of a trace" must become "of a trace and its sidecar" ✓;
  the **check** is **three** parts ✓, not one ✓ — the shape rule already exists ✓ (`tools/coverage_check.py` ✓,
  version-gated ✓) but is **dormant** on the capture that needs it ✓ (the sidecar's plugin block carries **no
  `evictedTokens` key** ✓), and the "sum" cannot be checked against the trace's cumulative counter ✓ ⇒ it must
  be checked **per call** ✓ ⇒ blocked on the per-call identities ✓ (the routed ask ✓); and the **turn-scoped
  projection** is a **derivation fix with no wire change** ✓ — RFC-0.1 **R5** already gives `page.declare` its
  own `turn` ✓ ⇒ the export can cut on it ✓ (v0 traces keep today's projection ✓) ⇒ **D19 (proposed)** is on the
  owner's table ✓.
  *LOG REWIND (2026-11-11, `reports/RR-LOGREWIND-20261111.md`):* the working-tree `reports/LOG.md`
  had been rewound by ten committed rows (279 in HEAD vs 271 in the tree) and one committed row's text
  reversed; restored to the committed bytes. The rule now in force: append to the working tree AND
  commit a blob anchored at HEAD, re-sync the tree after the commit (`git checkout HEAD --
  reports/LOG.md`), and before staging, the diff against HEAD must show only ADDED rows.
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
  **GAP CLOSED (2026-11-11, owner-ruled "do those", `reports/RR-P11LEVEL2-20261111.md`):** the test
  now derives the page table per turn (`derive_projection`), asserts both byte forms project to the
  SAME `TurnProjection`, and asserts both equal a PINNED projection
  (`vectors/order-expected-projection.json`, produced by the committed tool
  `ctxvm replay <vector> --turn N`) — the pin is what makes the level independent of level 1. The two
  overstating comments are corrected (the report carries events/divergences/violations only). The
  pin was falsified (one token → `derived page table differs from the pinned projection at turn 0`)
  and restored; `cargo test -p ctxvm-conformance --test key_order` → 4 passed. **The pair is now
  COMMITTED** (test + five vectors + two goldens + the vectors README, one commit because the
  golden is `include_str!`d), so the RFC-0.1 note's C2 pointer names a committed file and the
  clause's inference is executed rather than assumed. The note's TEXT is deliberately unchanged:
  its status line binds content changes to a new D-number (the owner's to grant).
  *LANDED (2026-11-11, verified by this lane):* the conformance pair — four vectors under
  `rust/crates/ctxvm-conformance/vectors/` (`order-{struct,sorted}-{ts,nots}.jsonl`) plus
  `rust/crates/ctxvm-conformance/tests/key_order.rs`; the pairs are true byte-order twins (parsed equal,
  bytes differ), `ts` is LAST in the struct form and BEFORE `type` in the sorted form (law 3's divergence
  exercised), and `cargo test -p ctxvm-conformance` → 3 passed, 0 failed. *Still owner-routed:* the note
  file (two lines, one D-number) and the canonical-form choice for its C3 clause. *Done when (met):* the packet STATUS reads answered, the card exists in a commit, and the
  QUESTIONS row `| P11 |` reads answered.

## 2. Owner-gated proposals this lane authored (ratification turns text into bytes)

- [x] **Umpire side — how it is currently used (noted 2026-11-12).** `reports/RR-UMPIREUSE-20261112.md`:
  the mechanism as it stands (MCP proxy → pinned model server → calibration artifact + ledgers; the
  pins make drift a hard error; the calibration of record is bound to the pin's hashes), this lane's use
  of it (an **instrument, not a decision-maker**: health, pins, calibration_info, one decide, and the two
  output gates `validate` / `replay`), and the limits that travel with every umpire number (the transfer
  caveat is still missing = **G2**; determinism is scoped to one machine/build; `calibrated.confidence` is
  a fitted P(key is correct), not a guarantee; the model is 1.7B and local, ~6 s and free). The umpire
  repo's own `README-MCP.md` now names the runner's start script and the artifact of record
  (`umpire-cal-v3.json` = `cal-v1:057a5a35a9d4ec71`), and the runner dependency's failure mode.
- [x] **G1. Umpire ordering clause (from P4) — APPLIED 2026-11-12.** The one-clause rule (line order governs; absent
  `ts` = unknown, never zero; no cross-ledger order) — verbatim text in
  `reports/RR-P4TS-20261109.md`; insertion point `umpire/00-SPEC.md` §2, after the L1–L5 block,
  documentation-only. Needs owner approval + a FRESH D-number (the A6 D-U register has no ts
  candidate). **READY TO APPLY (2026-11-11, `reports/RR-UMPIREREADY-20261111.md`):** the insert point
  is re-verified (L1–L5 at `00-SPEC.md:37-43`, the next heading at `:45` → the clause lands at `:44`;
  the P4 card's `:45` citation has drifted by one line) and **the fresh D-number is `D-U10`** — the
  register (`design/umpire-design-choices.md`, in this repo) holds D-U1–D-U9. No contradiction to fix:
  the umpire spec has **no** ordering/`ts` statement at all (only `canonicalJson`'s key-sorting at
  `:47`, a hash-input rule = the note's C3 domain), so the clause lands without touching the D18 note.
  *Done when:* the clause is IN a committed `umpire/00-SPEC.md` §2 AND the new D-number appears in
  the umpire decision register. **APPLIED (owner-approved 2026-11-12,
  `reports/RR-G1APPLIED-20261112.md`):** the clause IS in `umpire/00-SPEC.md` §2 (after L1–L5, before
  "### Identity minting") ✓ and **D-U10** IS in the register (`design/umpire-design-choices.md`) ✓;
  the owner's wording change applied — the dated repo-facts parenthetical moved OUT of the clause into
  D-U10, leaving the clause timeless ✓; no validator change, no negative, no ledger or fixture byte
  changed ✓ (umpire commit `1f7eae8`; umpire gate ALL GATES GREEN ✓). **MET.**
  *Owner:* approval + D-number — **given 2026-11-12** ✓.

- [x] **G2. Calibrated-confidence caller sentence (from P5) — APPLIED (2026-11-12, `reports/RR-G2APPLIED-20261112.md`).**
  Verbatim text from `reports/RR-P5CAL-20261110.md` committed into `umpire/mcp_server.py`
  (`INSTRUCTIONS` at `:74–77` and `TOOLS[0]["description"]` for `decide` at `:85–88`) and
  `umpire/00-SPEC.md` §3 (`:116–118`) (umpire commit `64b97fb`, `reports/RR-G2CALLER-20261112.md`;
  umpire gate `ALL GATES GREEN` ✓). Ratified into **D-U1** (option (a)) in
  `design/umpire-design-choices.md` with the timeless-spec / dated-register split ✓, and
  `handoff/QUESTIONS-ARCHIVE.md` P5 updated with the ratification locator ✓.
  *Done when:* sentence committed into the umpire books AND `handoff/QUESTIONS-ARCHIVE.md` P5
  updated with the ratification locator. **MET.**
  *Owner:* approval — **given 2026-11-12** ✓.

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

- [x] **G5. D13/D14 ratification + white-paper bundle routing — DONE (2026-11-12, `reports/RR-WPROUTE-20261112.md`).**
  The six paper items (Pillar-1 split; `:635` echo sweep; the P2 demo sentence; the R1 3-to-0 contrast;
  the consent-paragraph replacement; Part II's card-citation rule + `RR-FIELDAUD-20261107` audit pointer)
  plus the W8/W8B/W8C empirical update are ratified and routed in `reports/RR-WPROUTE-20261112.md`
  with exact working-tree file paths (`research/white-paper/white-paper.md`, `index.md`, `white-paper-Part-II.md`),
  line numbers, before/after text, and verification commands (`research/**` untouched per `handoff/LANES.md`).
  *Done when:* PROJECT-STATE Next-three line 1 rotates away (done 2026-11-12).
  *Owner:* ratified + routed.

- [ ] **G6. Publication (D17).** W10 prepare-only; publish/submit/tag only with approval.
  *Done when:* an orchestrated publication task appears with D17 resolved.
  *Owner:* D17.

- [x] **G7. W8 reopen — CLOSED (2026-11-10): W8 closed NEGATIVE, owner Option A** (packet P9,
  `design/W8-CLOSURE-20261110.md`; the 2026-11-07 FAILED ruling and its reopen conditions
  `RR-W8CHUNK-20261107-2 §12` + `design/W8-PROMPT-SLICE.md` are superseded). The reopen question is
  now answered by the P8/P9 answers: a different shape (longer session, more unprotected middle) or a
  different keep law is a **FRESH preregistration, not W8** — and at the measured shape the break-even
  is n\* ≈ 34 calls against 41 measured (`RR-W8BBLOCK-20261111`), so a paid cell at this shape is
  preregistrable while W8 itself is not. The live thread moved on: **W8B is closed negative** (their
  `163787a`; `reports/RR-W8BCLOSURE-20261111.md`), and the successor question is **W8C**
  (`design/W8C-PLAN.md`) — owner-gated, no money, four tests.

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
   the calibration of record). **Two loose ends in that note's own pointer:** the P11 pair + test are
   still STAGED, NOT COMMITTED (0 `order-*` vectors in `HEAD`), so the note's C2 locator names an
   uncommitted file, and the test's third level (the derived page table) is still unasserted - the
   one-call patch is in `reports/RR-P11GAP-20261111.md` §7.
2. **W8B is closed NEGATIVE** (their `163787a`; `reports/RR-W8BCLOSURE-20261111.md`): the policy's
   demand signal pins nearly every page on a read-once shape (19 of 21 fault), so nothing is ever
   eligible; no cell was booked and no cost claim exists. The live thread is **W8C**, and its sequence
   is OWNER-RULED (2026-11-11, `reports/RR-W8CSEQ-20261111.md`): **1** instrument (remove the text
   signal; add `note_refault(ref)`; plugin 0.12.0; four tests - one discriminating, three guards) -
   **2** **checkpoint A** = `--probe --arm both` returns CONTRAST OK and paged READY - **3** profiles
   (exactly two: `w8cn-naive`, `w8cn-paged`; budget on the paged arm only) - **4** diagnostic (one
   prompt per arm; read the real floor from the capture) - **5** block (floor + margin, written and
   committed) then **checkpoint B** - **6** pair (one run, ~20 min, $0.00). **CORRECTED HERE: this
   board had said checkpoint A was a plan approval - the plan's own section 8 says it is the PROBE's
   verdict, and the file wins over a summary.** The other lane's remaining items stand
   (`design/W8B-LANE-PROMPT.md`): the shape erratum in `design/W8B-FREE-PLAN.md`, the W8SIM "5.3%"
   scoping, and the "C3" rename (the P11 third level is done - `reports/RR-P11LEVEL2-20261111.md`).
3. **G1 (`D-U10`) and G2 (`D-U1`) are both applied** ✓ (G1: the ordering clause in `umpire/00-SPEC.md`
   §2, `1f7eae8`; G2: the caller transfer-caveat sentence in `umpire/mcp_server.py` `INSTRUCTIONS` +
   `decide` description and `umpire/00-SPEC.md` §3, `64b97fb`; both ratified in
   `design/umpire-design-choices.md`, `reports/RR-G1APPLIED-20261112.md`, `reports/RR-G2APPLIED-20261112.md`).
   **The spend ruling** (`reports/RR-SPEND-20261112.md`): one paid pair completed (`$0.2534` in cell-03,
   `reports/RR-PAIDRESULT-20261112.md`), paid spend stopped, and the owner's **refined prediction-block
   rule is RATIFIED** in `reports/W8-SPEND.md` §Prediction ✓.
4. **G5 (D13/D14 ratification + six-item white-paper bundle routing) is DONE** (`reports/RR-WPROUTE-20261112.md`).
   Remaining owner gates: **G4** (`design/redaction-block.md` §4-LIST go/defer), **G3** (W9 equivalence-test
   preregistration before any new transfer capture), and **G6 / D17** (publication timing). W8's fate is
   settled (G7 closed: negative, 2026-11-10).

Update law: tick a box only with the command's output in hand; on every card close, re-date the
state-of-record line and revise §14 of the operating prompt (not this file) for volatile facts
(counts, margins). If a chat summary and a book disagree, the book wins.
