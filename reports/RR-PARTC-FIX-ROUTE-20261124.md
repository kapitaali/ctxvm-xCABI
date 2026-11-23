# RR-PARTC-FIX-ROUTE-20261124 — owner forwards bounded stub-seam fix to hermes lane; reviewer answer has no landed card

Owner forwarded 2026-11-24 the bounded fix card saved at `~/.hermes/cache/scratch/PARTC-FIX-LANE-PROMPT.md` (5,426 B, authored 00:21 today), with the instruction "the card to forward" and "not implement it — that's the next work order." Review lane, verify-then-record. This card records and routes; the implementation is hermes-lane work, not mine.

## 1. Verified locator gap (the owner's own opening question)

- The reviewer's answer (checks 1–5, including the §1 measured defect numbers) has **no landed card ID**. Searched `reports/` and the scratch dir: the only artifact carrying the defect numbers (`10,059`-char stub, 101-char instruction echo, `]` frame break) is `PARTC-FIX-LANE-PROMPT.md` itself. No `RR-*` card in the repo cites them.
- Consequence: the implementing lane has no citable locator for "evidence already measured (do not re-derive blindly)" beyond this forwarded prompt. Recorded so the card can name that prompt as the source and, if the owner wants a canonical locator, a reviewer card of record is owed before implementation. I did not write that card — it is the reviewer lane's, not mine.

## 2. The routing (as forwarded)

Hermes lane — bounded fix for the shipped stub seam, scoped to reviewer checks **2, 4, 5**:
- **Fix (`_stub_message`):** cap/escape arguments (newlines, `]`, `[`, control chars); for body-carrying tools omit the argument excerpt; keep the producing call in the carrier.
- **Red-before:** add mutations for gold leak, carrier retention, default-off, and no-env-channel — each proven red then green.
- **Attestation:** two sessions in one gateway (recoverable + off), each sidecar carrying its own `plugin.stubDropped` / `enginePlan.stubDropped`; pin `stubCount` as per-call; presence-gated, version-gated checker rule when `stubDropped=recoverable` and `evictedTokens>0`.
- **Hygiene:** 0.13.30 → 0.13.31 both places, sync, operator restart owed, full test/gate/checker/hygiene bar, own RR card + LOG row + day section, private index, no push.

## 3. Explicitly out of scope (per the card)

`page.evict` emission is a **separate owner-gated card** — not here. No arm, model call, spend, default-on change, D17 action, gateway restart, re-score of Part B, or pooling. The stub-arm preflight cited 0.13.30; a future arm must cite 0.13.31 after this lands.

## 4. My lane's action

Recorded this routing card, the append-only LOG row, and a day-file section for **2026-11-24** (new day file — the 2026-11-21 file stays as the prior day). I did not write the fix card (it is saved in scratch by the owner/reviewer), did not implement, and did not touch `packages/**`, `tools/**`, or `research/**`. Kit/hygiene at entry: check on commit.

## 5. Applied

This card, an append-only LOG row (four pipes), and a new day-file section (`reports/RR-DAY-20261124.md`).
