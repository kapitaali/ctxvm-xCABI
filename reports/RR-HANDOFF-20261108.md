# RR-HANDOFF-20261108 — the session-continuity kit: PROJECT-STATE, CONTEXT-PACK, WORKFLOW, QUESTIONS, three reviewer packets, and two POSIX tools

Card: build the session-continuity kit under `handoff/` plus its two POSIX tools under `tools/`,
verify them, and land one report + one LOG row. Editor-facing content only — no code, spec, fixture,
plan, or plugin file touched; the writer scope held to `handoff/**`, `tools/session-start.sh`,
`tools/check-handoff.sh`, this report, the day file, and `reports/LOG.md`. Everything a review session
needs is one paste away: `tools/session-start.sh <n> [--with-context]` prints a single ≤16 KB document
(state + optional brief + one packet) or fails naming which part to cut. All byte counts below come
from `wc -c` on 2026-11-08 on this box; the files carry their own dates, so post-commit drift is
visible at the head of each file.

## Verdict sentence

The kit is complete and green: all eight handoff documents pass their byte limits and required
headings (`bash tools/check-handoff.sh` exit 0), the session-start tool assembles a ≤16 KB paste for
every packet with context (16,320 / 15,900 / 16,312 ≤ 16,384) and fails as designed on a missing
packet (exit 2) and on overflow (exit 1, naming the largest part), the CI gate is green with the nine
`CTXVM_*` keys unset (quoted below as a dated, non-authoritative snapshot), and the owner's five open
decisions are now staged as D13–D17 in `handoff/PROJECT-STATE.md` with a packet per D-number where a
chat answer is needed.

## (a) Files delivered (bytes at commit, `wc -c`)

| File | Bytes | Limit |
|---|---|---|
| `handoff/PROJECT-STATE.md` | 6,025 | 6,144 |
| `handoff/CONTEXT-PACK.md` | 7,677 | 8,192 |
| `handoff/WORKFLOW.md` | 2,845 | 4,096 |
| `handoff/QUESTIONS.md` | 1,139 | 3,072 |
| `handoff/packets/TEMPLATE.md` | 1,116 | 3,072 |
| `handoff/packets/P1-cross-harness-claim.md` | 2,614 | 3,072 |
| `handoff/packets/P2-fault-resident-healthy.md` | 2,194 | 3,072 |
| `handoff/packets/P3-redaction-default-capture.md` | 2,606 | 3,072 |
| `tools/session-start.sh` (+x) | 2,299 | — |
| `tools/check-handoff.sh` (+x) | 2,993 | — |

What the state file carries (the four facts the task pinned): (1) the pager finding — the first
default-capture survey measured approxInputTokens 358,616 against budgetTokens 200,000 with the floor
law = system prompt + protect_first_n=3 + protect_last_n=6 + pins, early-return past 13:21; probes A/B
(`reports/RR-ENGINEGAP-20261106.md`; floor source `packages/hermes/live/context_engine.py:12,287–292`).
(2) Paper versions — Part I committed (`research/white-paper/white-paper.md` + `index.md`, PDF synced)
plus an UNCOMMITTED working-tree revision owned by the white-paper lane; Part II is an untracked v1.0
draft reviewed in `reports/RR-WP2REV-20261107.md`; plugin/emitter versions hermes 0.10.5
(`packages/hermes/live/__init__.py:94`), @ctxvm/node 0.1.0, @ctxvm/opencode 0.0.1, @ctxvm/ai-sdk 0.0.1.
(3) The conformance gate (counts below, with producing command). (4) D13–D17: cross-harness claim
wording, default capture + §18 redaction block, paper structure, W8 budget/task amendment, publication.

Packets: P1 cross-harness claim + RFC-0.1 normalisation (→ D13), P2 the `faultOfResidentPage` line the
healthy-fixture demo prints (paper wording, no D yet), P3 redaction block + default-capture stance
(→ D14). Each packet quotes only the lines needed, carries file path + line range + provenance
(committed HEAD bytes vs working-tree WIP), marks its numbers with the command that produced them, and
asks for numbered one-line verdicts.

## (b) The two tools

- `tools/session-start.sh <n> [--with-context]` (POSIX sh, coreutils only): writes
  `handoff/SESSION-START.md` = PROJECT-STATE + CONTEXT-PACK (with `--with-context`) + packet `P<n>`,
  prints the byte count, deletes its output and exits 1 over 16,384 naming the largest part to cut
  (with the reminder never to drop a required heading), exits 2 on missing packet/input.
- `tools/check-handoff.sh`: existence, byte limits per file class, the required heading set (title +
  the 11 `##` sections = the 12 prescribed headings), per-packet minimum headings, and a secret-shape
  scan (expanded-home-path pattern plus credential-shaped patterns) that prints only the class name,
  never matched bytes. It also scans any regenerated `SESSION-START.md`.

## (c) Verification

1. Gate, nine-key chain (the everyday recipe carries `CTXVM_HERMES_VERSION`, which trips the W17
   `assertIsNone` — `env -u` on all nine is mandatory):
   `env -u CTXVM_HERMES_VERSION -u CTXVM_MODEL -u CTXVM_PROVIDER -u CTXVM_TRACE_DIR -u CTXVM_FEATURES
   -u CTXVM_TRACE_TS -u CTXVM_AGENT_ID -u CTXVM_BUDGET_TOKENS -u CTXVM_TRACE_NAME bash tools/run-ci.sh
   > /tmp/opencode/w8chk/gate-handoff.log 2>&1; echo $?` → exit 0 (`/tmp/opencode/w8chk/gate-handoff.exit`),
   and the log's last line is `[ctxvm-ci] ALL GATES GREEN`. Counts, quoted verbatim as a 2026-11-08
   snapshot — NOT the authoritative totals; production truth is a rerun of the command above:
   "check-node-build: OK — 16 events byte-identical, dist imports resolve without type stripping;
   ts suites green (22 + 62 + 46 tests); python suites green (174 + 66 + 8 tests); positive: 677 event
   lines validated across 27 fixtures; negative: 5 engineered bad cases correctly rejected;
   SCHEMA CONFORMANCE: PASS (682 checks)."
2. `bash tools/check-handoff.sh` → exit 0; output is the size table above plus "ALL HANDOFF CHECKS PASS".
3. `bash tools/session-start.sh 1 --with-context` → 16,320 bytes, exit 0; `2 --with-context` → 15,900, 0;
   `3 --with-context` → 16,312, 0; plain `1` and `3` → exit 0; missing packet `9` → exit 2. The overflow
   path was demonstrated pre-trim (17,486 and 16,662-byte attempts), printing the parts breakdown and
   "cut from CONTEXT-PACK (largest part…)" before exit 1.
4. `rust/target/release/replay corpus/m1/tracer-healthy.jsonl` → exit 0 (recomputed 2026-11-07, packet P2's
   evidence section): the healthy fixture shows the `faultOfResidentPage` class at seq 7 —
   packet P2 asks how the paper should frame it.
5. CJK sweep over `handoff/**/*.md` → NONE (script in the work note; codepoints scanned: 4E00–9FFF,
   3000–303F, FF00–FFEF). The checker's secret-shape scan ran inside step 2.

## (d) Conflicts and their resolutions

- **Gate counts in a doc.** The task asked for test/conformance counts with the producing command;
  AGENTS.md §5 and §8 forbid hardcoding gate counts. Resolution: the counts line is quoted verbatim as
  a date-stamped snapshot explicitly labeled non-authoritative beside the command that produces it —
  the snapshot is evidence of what the gate printed at commit time, not a substitute for rerunning.
- **The 12 prescribed headings.** Counted as the `# State` title + the 11 `##` sections (Goal;
  Artifacts and versions; Done; In progress; Next three; Decisions made; Open decisions for the owner;
  Do not touch; Evidence rules; Verification status; Blocked). The checker enforces exactly these
  strings.
- **`SESSION-START.md` is a disposable paste artifact.** Regenerated by the tool per run and not part
  of the kit's committed content; the working copy is removed before staging. The checker still scans
  it whenever present.
- **Packet order.** The task listed packets 1–3 as current open items in priority order; ordering kept:
  cross-harness/§18-wording first (D13), then the demo-violation framing, then redaction/default-capture
  (D14).
- **One recommendation resolution declared inside the state file:** D17's wording had to shrink to fit
  the 6 KB limit; the negative-result emphasis is carried in the Evidence-rules section (law 7) and
  packet P3's consent question, so the trim drops no content that is not duplicated elsewhere.

## (e) UNKNOWNs and their resolvers

1. **Which review items of `reports/RR-WP2REV-20261107.md` the uncommitted white-paper working-tree
   revision actually applies** — PROJECT-STATE says only that a revision exists; mapping items→edits is
   the white-paper lane's record, not this lane's. Resolver: that lane's next card.
2. **Official confirmation of the D13–D17 numbering** — D1–D12 exist scattered in the books with three
   usable anchors (D9 ts opt-out, D11 signing law, D12 est* ruling); D13–D17 are this card's proposal.
   Resolver: the owner's next decisions block in `08.1-UPDATE-PROMPT.md`.
3. **Which packet-2 event the paper demo's `seq 7` names** — flagged inside P2 as "will locate on
   request"; kept out of the packet to stay under 3 KB.

## (f) Open decisions staged for the owner (one line each; details in PROJECT-STATE)

- **D13** cross-harness claim (Packet 1): keep the Pillar-1 sentence as-is, or narrow to within-trace
  byte-identity + W5-classified diffs with an authored proposal-only normalisation law — recommend
  (b) narrow.
- **D14** default capture + redaction (Packet 3): keep capture default-on as shipped; author the §18
  session redaction block (policy id, rule-set version, stage, replaced-count) as an additive
  proposal-only card vs stay prose — recommend (b), no unsealing.
- **D15** paper structure: keep Part I + Part II vs merge — recommend keep two, merge only after D13/D14.
- **D16** W8 amendment: reopen with a task set whose protected floor < 24k, and/or amend arm/value +
  preregistration first — recommend (a) with (b) documented, under the NOT RUNNABLE gates of
  `design/W8-PROMPT-SLICE.md`.
- **D17** publication: now vs after D13–D15 with the negative-result law prominent — recommend the latter.

## (g) Standing instruction adopted with this card

Every future work item now leaves, before closing: a ≤150-word state delta applied to
`handoff/PROJECT-STATE.md`, a `handoff/QUESTIONS.md` update when a reviewer question was raised, a
new/updated packet when that question needs a chat answer, and a green `bash tools/check-handoff.sh`
before reporting. This card's own delta is already in place (the header line and Done row 1).

## Limitations

- Byte counts are heavyweight facts only at commit time; the files are dated at the head so drift is
  visible, and the checker enforces the limits going forward.
- The two tools are shell-verified on this box only (POSIX sh, coreutils); no cross-OS claim.
- The kit proves nothing about the trace standard; it is editor infrastructure. All facts inside it
  carry their own locators and were verified at the named dates; their age is the reader's to check.
