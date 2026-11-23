# RR-PARTB-RESULT-20261123 — Part B: silent drop causes a large middle-band accuracy loss (8/8 → 1/8); stub card indicated

Owner authorized Part B accuracy-only (`RR-PARTB-AUTH`, path 1). Both gates passed (C 9/9, E 11/12 middle dropped
@40%), arms ran on the free tier ($0), exact-match readout, recovery pre-downgraded to UNVERIFIED. Review lane,
verify-then-record. No plugin change, no push.

## 1. Run integrity

- Gates: C = 9/9 (3 naive pilot sessions, `RR-PARTB-GATEC`); E = 11/12 middle dropped at ~24k (`RR-PARTA-RESULT`).
- Arms: 8 naive + 8 paged sessions via `tools/w8-driver.py` with our frozen planted-code prompt file
  (`experiments/needle-revisit/partB/`, no `tools/**` edit), 21 prompts each, all rc=0. Stale artefacts archived
  (never deleted) between sessions.
- Paged captures confirm engagement: `arm: paged`, `budgetTokens: 24000`, `trigger: new-page` on the recent sidecars.
  `--assert-engaged` passed all 8.
- Scoring: exact match `<nn>=<code>` per sub-question against the frozen answer key; query echo contains no codes,
  so a match is genuine memory retrieval. Scorer self-tested (green 3/3, red 1/3).

## 2. Result — accuracy by arm × band

| band | naive (n=8) | paged (n=8) | effect |
|---|---|---|---|
| head (part-01) | **8/8** | **8/8** | none — protected control |
| **middle (part-09)** | **8/8** | **1/8** | **−7/8 (−0.875)** |
| tail (part-20) | **8/8** | **7/8** | −1/8 (noise-level) |

The middle needle — the band the keep law drops (Part A: 11/12 at this budget) — collapses from perfect to 1/8
accuracy under paging, while the head control stays 8/8 and the tail 7/8. The 7 of 8 paged middle misses are
`paged-01..05, 07, 08`; only `paged-06` answered correctly. This is a large, band-specific accuracy effect in the
predicted direction, exactly where the engine evicts. Non-overlapping intervals: naive middle 1.00, paged middle
0.125 — far beyond the ~0.3 resolution of an 8-session cell.

## 3. What is / is not established

- **Established (within this shape):** under the real engine's keep law at 24k, silently dropping the middle page
  causes a large hosted-answer accuracy loss on a planted-code retrieval task, with head/tail controls intact. This
  is the first time the paging mechanism has been tied to a measured answer-level effect (all prior E0/E2 attempts
  failed at instrument gates).
- **Recovery: UNVERIFIED.** The mandatory dry check (`RR-PARTB-PREFLIGHT`) showed the final prose question emits no
  `tool_recall` fault; per the frozen rule it is not scored as zero. We cannot say whether the model re-read or not.
- **Not claimed:** cost saving (law 7; free tier `cost 0` is not a receipt), general paging quality, model quality,
  determinism (law 8), or any effect beyond this fixture/budget/route. n=8 per arm; head/tail near ceiling. Nothing
  pooled with E0/E1/E2/M1/M2/M3. The budget caveat stands: live profile 24,000 vs Part A's 24,271–24,414.

## 4. Frozen decision table → change indicated

"Exposed accuracy low AND re-read low → silent drop causes damage → Part C stub card (hermes lane, owner-routed)."
Exposed middle accuracy is low (1/8). The *re-read* half is UNVERIFIED (not "low"), so the table's literal
both-conditions branch is not fully satisfied — but the damage half is strong and band-specific. Per the dev prompt,
this **indicates** Part C (recoverable stub: name, arguments, "re-run to restore") as the next change — a hermes-lane
plugin card requiring a **separate owner ruling**. Not started here.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.
