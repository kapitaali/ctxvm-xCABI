# ROADMAP — opencode lane (kit, review packets, umpire-development proposals)

State of record: 2026-11-11, HEAD `e716b7b` (the P9 confirmation card in flight, committing on top).
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
  `RR-W8B2-20261111`), so the blocker is a model-side timeout and the subject choice is the owner's.
  Q2's five-condition
  metric-replacement rule is adopted as a standing lane rule.
  *Done when (met):* the packet STATUS reads answered, the card exists in a commit, and the
  QUESTIONS row `| P8 |` reads answered.

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

- [ ] **P10 (page-id asymmetry: flat vs nested page identity) — QUEUED 2026-11-11.** Cut by
  `reports/RR-UGATE-20261111.md` after the umpire gates re-ran against the books. The asymmetry
  (`page.declare` nests `page.id`, the other page-carrying verbs are flat) is inherited from
  SEALED v0 and is NOT in the friction card of record (`design/umpire-friction-vs-rfc01.md`,
  whose residuals are F8 + F9 only). The "second consumer" trigger has ALREADY fired: umpire's
  Python (`ledger_tools.py:85`, `validate_ledger.py:228`) and ctxvm's own OTLP exporter
  (`tools/otel-export.mjs:72-73` nested vs `:86/:96/:106/:116/:125` flat) both branch.
  Options in the packet: (a) workaround + prose, (b) one RFC-0.1 compatibility-note line,
  (c) additive field (five touchpoints; sealed-v0 blast radius = EVERY declare line invalid for
  strict v0 consumers), (d) accept. Agent recommendation: (a)/(b) over (c).
  *Done when:* the owner pastes the ruling; the verdict lands in QUESTIONS + a card.
  *Owner:* paste the packet (D-number in the umpire register).

- [ ] **P11 (canonical ordering: sorted keys vs Rust struct order) — QUEUED 2026-11-11.** Cut by
  `reports/RR-UMRES-20261111.md` to close the gap the umpire-gates card found: F9 is ACCEPTED, but
  its documentation line was proposed as "packet P5" in the friction card while the kit's P5 is the
  calibration question — so no owner existed. Options: (a) one RFC-0.1 compatibility-note line
  (owner + D-number), (b) umpire's 00-SPEC only, (c) a CONFORMANCE TEST instead of a note, (d) accept
  silently. The packet carries the crux: `ts` is the LAST field of every Rust event variant
  (`model.rs:161,:179,:189,:199,:211,:220`) while sorted keys place `ts` BEFORE `type`, so the two byte
  forms differ BY CONSTRUCTION — "both accepted" is the only honest rule, and a normative sorted-keys
  rule would forbid the wire order law 3 requires.
  *Done when:* the owner pastes the ruling; the verdict lands in QUESTIONS + a card.
  *Owner:* paste the packet.

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

- [ ] **G7. W8 reopen.** Ruled FAILED 2026-11-07; reopen conditions recorded
  (`RR-W8CHUNK-20261107-2 §12` + `design/W8-PROMPT-SLICE.md`). Cells are the hermes/W8 lane's to
  run; MY lane's obligations: process any resulting reviewer packets and record day-close lines.
  *Done when:* the owner reopens AND first counted cell lands (or the owner rules it closed for
  good).
  *Owner:* D16/decision.

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
- [ ] **W8 the decisive experiment** — FAILED ruling 2026-11-07, reopen owner-gated (G7). My
  actionable boxes: process results into the review lane when they exist. Landed side-records I
  keep aware of: `RR-W8PAIR-20261109` (first counted pair, negative), `RR-BUDGET-20261109`
  (200,000 vs 24,000 provenance), `RR-DRIFT-20261109` (gate printed numbers it didn't measure),
  `RR-W8H6-20261109` + review follow-up (`shape verified, surface fails`, toolset pinned to
  `[file]`).
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
- [ ] **U2. MCP health re-check before any umpire MCP consumer work.** RE-MEASURED 2026-11-11
  (`RR-UMRES-20261111`): still DOWN — `tools.umpire.health()` returns `urlopen Errno 111` (connection
  refused); the pinned server (`llama-server … --host 127.0.0.1 --port 8081`) has no listener and no
  process, so the MCP CONSUMER path is blocked on the model server, not on the MCP layer. The offline
  surface answers: `pins` OK (default `qwen3-1.7b`), `calibration_info` OK.
  *Done when:* `tools.umpire.health()` returns ok on a fresh session that needs the surface (the
  owner starts the pinned server; this lane does not — it loads ~4.5 GB of weights).

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

- [ ] **U6. The MCP's default calibration artifact is the SUPERSEDED v2 map.** From
  `reports/RR-UMRES-20261111.md`: `calibration_info` (no argument) returns `umpire-cal-v2.json`
  (`cal-v1:aceb881587b3b3a6`, test ECE 0.026684) while the calibration OF RECORD is v3
  (`cal-v1:057a5a35a9d4ec71`, ECE 0.030163, `RR-M3V3`; the umpire repo's own `spec/calibration_ci.py:38`,
  `spec/test_packaging.py:33`, `spec/transfer_eval.py:35` all use v3). The two artifacts are NOT one map
  under two labels: `isotonic.points`, `raw_sha256`, `provenance.git_head`, `selection` and the test
  metrics all differ, so an MCP consumer on the default serves a different map and a different
  data_version stamp than the record — the MCP as configured cannot reproduce the calibration of
  record. The default is NOT in the code (`mcp_server.py:54` has none): the launcher injects it, and
  the hermes gateway config points at v2 (`~/.hermes/config.yaml:2114`; arm profile copy `:2115`).
  *Fix (owner-routed):* point `UMPIRE_CALIBRATION` at `umpire-cal-v3.json` + restart the gateway.
  *Not done here:* `~/.hermes/**` is the hermes lane's machine config; the umpire repo is read-only
  from this lane.
  *Done when:* a fresh MCP session's `calibration_info` (no argument) returns the v3 artifact's
  data_version, and any MCP-decided row carries the record's stamp.

## 6. Owner's next-cue list (what unblocks the most)

1. Paste P10 (page-id asymmetry ruling) — the one friction item still open; its "second consumer"
   trigger has already fired.
2. Rule P8 drop-or-keep (its paste now fits — 16,037/16,384 — after `RR-CTXPACK-20261111`).
3. Ratify G1 (ordering clause, fresh D-number) and G2 (caller sentence, D-U1).
4. Rule the redaction go/defer (G4) and W8's fate (G7); D13/D14 + D17 remain the big gates.

Update law: tick a box only with the command's output in hand; on every card close, re-date the
state-of-record line and revise §14 of the operating prompt (not this file) for volatile facts
(counts, margins). If a chat summary and a book disagree, the book wins.
