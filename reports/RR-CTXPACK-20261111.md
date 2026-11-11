# RR-CTXPACK-20261111 — the 16 KB paste budget repaired: CONTEXT-PACK 7,417 → 6,837 B, so every
# packet's with-context paste fits again (and the P8 question answered: nothing was sent)

Card: the owner pushed, then ran `bash tools/session-start.sh 8 --with-context` and got
"OVER 16 KB: session-start.md is 16617 bytes (limit 16384)" with the tool's own instruction to cut
from CONTEXT-PACK — plus the question "I haven't given P8 to reviewer yet, whats going on here".

## 1. What was actually happening (the owner's question)

Nothing was sent to the reviewer, and nothing selected a packet behind the owner's back.
`tools/session-start.sh` takes the **packet number as its argument**: `session-start.sh 8` assembles
the paste for **packet P8** (`handoff/packets/P8-cache-stable-selection.md`) out of three parts —
PROJECT-STATE + CONTEXT-PACK + that packet (`tools/session-start.sh:19-45`). Running it is a local
paste build, not a dispatch. P8's disposition (the drop-or-keep ruling the roadmap has been
carrying) is still the owner's; this card does not touch it.

The failure was the **paste budget**, and it was wider than P8: with PROJECT-STATE at 6,137 B and
CONTEXT-PACK at 7,417 B, only **2,826 B** remained for the packet inside the 16,384 B paste. Three
packets exceed that — P8 (3,059 B), P11 (3,048 B), P10 (3,045 B) — so **every one of their
with-context pastes was over budget**, not just P8's. The roadmap had already named the cause
("Packet currently at 3,059/3,072 B (13 B margin) — the paste-budget strain driver"); this card
measures the consequence and fixes it.

## 2. The fix — CONTEXT-PACK trimmed per the tool's own instruction

`handoff/CONTEXT-PACK.md`: **7,417 → 6,837 B (-580)**. Glossary rows, excerpt lines and label rows
were dropped or shortened; **no heading was touched** and every dropped fact still lives in the repo
(the "trace" line's white-paper §5.1 quote; the "touch ratio" formula in
`benchmarks/metrics/metrics.py:14`).

- §2 glossary: the `trace` row dropped (the JSONL stream of one capture — self-evident to a
  reviewer session), the `touch ratio` row dropped (it duplicated §4's metric line); `render`,
  `fault` and `stub` rows shortened by dropping their citations only.
- §1: the adapter and measurement-stack rows shortened (package names and the ODPS packaging clause
  kept in §3); the W8 row keeps its verdict and locator.
- §3: the last repo-map line's file enumeration shortened.
- §8: the W8-vocabulary row's arm-witness clause shortened (the 0.10.4→0.10.5 bug detail stays in
  the repo); the LOG-row line keeps two of its four commit locators instead of four.

Nothing else in the kit moved: PROJECT-STATE (6,137/6,144), QUESTIONS (3,055/3,072), the packets
themselves, and the required heading `## 8. Labels (how to read the books)` are all unchanged.

## 3. Verification — every packet, both paste modes

| check | result |
|---|---|
| `session-start.sh <n> --with-context` for **all 11 packets** (P1…P11) | all ≤ 16,384 B; worst is **P8 = 16,037 B** (347 B spare), then P11 16,026, P10 16,023 |
| `session-start.sh <n>` (no context) for P1/P8/P10/P11 | 8,891 / 9,198 / 9,184 / 9,187 B — all fit |
| worst theoretical case (PROJECT-STATE at its 6,144 B cap + a 3,072 B packet + CONTEXT-PACK 6,837) | **16,057 B ≤ 16,384** — the budget holds for any packet the checker would accept |
| `bash tools/check-handoff.sh` | ALL HANDOFF CHECKS PASS (CONTEXT-PACK 6,837/8,192) |
| `bash tools/session-start.sh 1 \| 2 \| 3 --with-context` | exit 0 (the three standing pastes) |

The overflow is gone for P8 **and** for the two packets this lane queued today (P10, P11) — the
paste budget was a standing trip-wire for anything over ~2,826 B, not a P8-specific defect.

## 4. Executed agent-doings

- CONTEXT-PACK trimmed (-580 B) with the sanctioned moves only (glossary rows, excerpt lines, label
  rows; never a heading), and every packet's paste re-measured.
- Roadmap: P8's "paste-budget strain driver" note updated to the measured outcome (the budget now
  holds at 16,057 B worst case); state line re-dated.
- Prompt pin: the paste-budget arithmetic recorded (PROJECT + CONTEXT + packet + 4 ≤ 16,384) so the
  next lane does not rediscover it.
- Kit: card + LOG row + day-file section + 08-HANDOFF frontier 11 addendum 7 + PROJECT-STATE delta
  (own commit). Nothing pushed (the owner pushes).

## 5. Files

- `reports/RR-CTXPACK-20261111.md` (this card); LOG row `RR-CTXPACK-20261111`.
- `handoff/CONTEXT-PACK.md` (trimmed; snapshot in `/tmp/opencode/20261111/`).
- `reports/RR-DAY-20261111.md` (section); `08-HANDOFF.md` §0 frontier addendum 7.
- `design/ROADMAP-OPENCODE-LANE.md` (P8 note + state line);
  `design/OPENCODE-LANE-DEVELOPER-PROMPT.md` (paste-budget pin).
- `handoff/PROJECT-STATE.md` delta in its own commit.

## 6. Verification commands

- `bash tools/session-start.sh 8 --with-context` → `SESSION-START: 16037 bytes` (was: OVER 16 KB at 16,617).
- `for n in $(seq 1 11); do bash tools/session-start.sh $n --with-context; done` → all ≤ 16,384.
- `stat -c %s handoff/CONTEXT-PACK.md` → 6,837 (was 7,417).
- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS.
- `git diff handoff/CONTEXT-PACK.md | grep '^-' | grep -c '^-\-#'` → 0 (no heading removed).

## 7. Limitations

- The trim removes glossary prose, not facts: the two dropped glossary rows keep their definitions
  in the repo (white-paper §5.1; `metrics.py:14`), and the shortened label rows keep the terms a
  reviewer needs.
- PROJECT-STATE is at 6,137/6,144 B, so the paste budget's other term is nearly maxed; a future
  PROJECT-STATE growth of >347 B would need the CONTEXT-PACK trimmed again (the arithmetic is now
  recorded in the prompt pin).
- P8's disposition is untouched: this card made its paste fit, it did not send it or rule on it.
