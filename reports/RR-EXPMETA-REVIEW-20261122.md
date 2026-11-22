# RR-EXPMETA-REVIEW-20261122 — verified: cross-experiment diagnosis is sound; two locator/column caveats recorded

Review lane, verify-then-record. Subject: staged `RR-EXP-META-20261122.md` in the DSH sandbox (6,217 B, not in the
repo). Date 2026-11-22. Zero spend, no calls, no commit of another lane's work. This card records the diagnosis in
the review books and flags the two factual slips I found; it does not implement any remedy.

## 1. What I verified

| claim | check | result |
|---|---|---|
| E0 precondition failures 12/20, 2/5, 3/5 | grep the three result cards | confirmed (`RR-E0RESULT`, `RR-E0V3PILOT`, `RR-E0RETRY-RESULT`) |
| E2 pilot 15/15 targeted, 14/15 random, 3/5 repeats | `RR-E2PILOT-REVIEW` + result object | confirmed |
| E0 double negative still published; nothing pooled | `RR-E0-NEGATIVE` present | confirmed |
| DB scale / contaminant claim | read-only sqlite on `~/research/anthropic-papers-reference.sqlite` | **1,061 rows**, **164 distinct `name` strings** — matches the card |
| locator cards exist | `ls` in owning repos | E1 at `research/e1-offline/RR-E1-RESULT.md`; M1/M2 at umpire `reports/RR-M1-20261022.md`, `RR-M2-20261023.md` |

## 2. Two caveats recorded, not glossed

1. **Locator names are shorthand.** The diagnosis cites `RR-M1-RESULT` / `RR-M2-RESULT`, but the actual files are
   `RR-M1-20261022.md` / `RR-M2-20261023.md` in the umpire repo (E1 is correctly at
   `research/e1-offline/RR-E1-RESULT.md`). The references resolve in substance but should carry the real filenames.
2. **Remedy 7 references a non-existent column.** The proposed filter `author_match = confirmed` cannot be applied:
   the DB schema is exactly `name, date, title, url, reference` — there is no `author_match` field. The diagnosis's
   own observation ("164 distinct `name` strings for 88 authors") is the evidence that an author-match signal is
   *needed*, but the field must be **derived** (name-normalization/affiliation check) before any literature-derived
   count can be filtered. As written, remedy 7 is an intent, not an executable step.

## 3. The diagnosis itself — accepted, with scope

The central finding is consistent with everything in the books: **not one of the eight attempts reached a
hypothesis result; every one stopped at an instrument/precondition gate.** Common-method circularity (E0's T and Δ
from the same answer; E1's "close to definitional" 2.4%; E2's change flag from the same stochastic generation),
no independent instrument validation before construct freeze, construct–hypothesis gaps, degenerate controls and
underpowered cells, route properties entering the data, and an unvalidated upstream DB — all match the recorded
cards. The "what you got right" list (preregistration, frozen stop rules that fired, no post-hoc loosening, negatives
published with equal prominence, claim ceilings, hash-frozen inputs) is exactly the discipline the review lane has
enforced. **Integrity sound, construct design failed** — accepted as the state-of-record.

The six remedies are proposals, not authorized work. Remedy 5 ("two precondition failures on one construct →
redesign the construct, not another parameter swap") is the one I'd flag as the governing lesson: the E0 retry
(1.5B swap) was the third swap and failed predictably, precisely as the diagnosis says. I do not implement any of
them without a ruling.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261122.md`. The staged
meta card is left for your copy; `research/**` and other lanes' WIP untouched; no push.
