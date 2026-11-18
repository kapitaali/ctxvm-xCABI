# RR-H11-REVIEW — verified: H11 landed, its five laws pass, and H12's budget choice is now decidable

Review lane, verify-then-record. Subject: `9e05548` (H11 implementation) and `39599e1` (floor measurement), both
landed after my T-B closure review. No code change, no model call, no spend, no cell authorized by this card.

## 1. Verdict

**H11's Done condition holds.** The roadmap requires a unit test showing the same selection hash across calls with
an unchanged working set and a different one after a trigger, `should_compress() == False`, and a green gate. All
three verify. The H11 card's "212 passed" reproduces only in a clean environment — with ambient `CTXVM_*` set the
suite shows 11 failures (the known leak, not a regression). This is a state-of-record correction, not a defect in
the implementation.

Note for the books: my T-B closure review (`7196c66`) said "H11 unimplemented" because it was true at `cc7e1dd`.
`9e05548` landed immediately after and supersedes that line. The review stands as written at its time; this card
records the change.

## 2. Evidence re-derived

| claim | how | result |
|---|---|---|
| H11 implementation landed | `git log`, `git show --stat 9e05548` | 8 files: engine, `__init__.py`, plugin.yaml (0.13.25), 5 tests, coverage checker, LOG, day, RR card |
| three triggers in code | `grep` on `context_engine.py` | `new-page` (held key gone / new page), `overflow` on **outgoing** size, `every-B` at B calls (default 4); mode defaults to `fresh` |
| five laws | `pytest -k StableSelection` | **5 passed**: fresh default, held selection with identical hash, new-page replan, every-B trigger, `should_compress()` still False |
| red-before | H11 card §3 | forcing re-plan fails exactly law 2; file restored byte-identical (`sha256`) — recorded, not re-run by me |
| clean suite | `CTXVM_*` cleared, `pytest packages/hermes -q` | **212 passed, 15 subtests** — matches the card |
| ambient leak | same suite with ambient vars | 11 failed / 201 passed — the known `CTXVM_TRACE_TS=0` leak; not a regression |
| plugin version | `live/__init__.py:94`, `plugin.yaml` | both **0.13.25**; installed copy synced per the card, gateway still 0.13.24 (its mode is not live until owner restart) |
| floor measurement | `RR-H11FLOOR-20261118` | free, no model call: at 24k floor 16,714 < budget < resident 80,959 → outgoing 21,163 (under H12's 24,000 target); at 60k outgoing 56,988 > 57,250 break-even → tie at best. Limitation stated: flat single-turn reconstruction; real multi-turn floor was 53,790 on a 12-turn capture |

## 3. What follows

- **H11 is done**; the checkbox in `design/ROADMAP-HERMES-LANE.md` belongs to the hermes lane and should be ticked by them with this verification. H12 (one stable-vs-naive pair, naive
  reference + mode-off cell) is **not** authorized — no cell, no spend, no gateway restart.
- The floor card makes the budget choice decidable but does not prove a 24k cell will act on real traffic: its
  reconstruction is flat, and the real multi-turn floor was larger. The pre-cell check in that card must be run
  before booking H12.
- The gateway still holds 0.13.24, so `selectionMode: stable` is **not live**. A restart is the owner's call and
  ends all active sessions; do not restart "to be safe".

## 4. Remaining owner decisions (unchanged except H11)

H12 budget + cell authorization (after the pre-cell check and a fresh ceiling), gateway restart for 0.13.25,
D17 held (no registry action), D19 ratification, P11 canonicalisation. No paging/cost/determinism claim follows
from H11's unit tests. Kit/gate were green at the last check; this card changes no gate input.
