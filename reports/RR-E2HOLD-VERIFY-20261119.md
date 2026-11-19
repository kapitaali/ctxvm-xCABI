# RR-E2HOLD-VERIFY-20261119 — verified: datamining artifacts tracked and RR-E2HOLD routed edits applied

Review lane, verify-then-record. Subject: the three research-lane commits `ff07589` (erratum to
`reports/RR-PART3FIX-20261119.md` §3), `97cf743` (`research/datamining/datamining.{py,json}` tracked under owner
exception), and `99f62f9` (`research/white-paper-Part-III.md:389`, `research/white-paper-Part-III.zh.md:359`, and
`research/e2-proposal/PREREG-E2-DRAFT-20261119.md` landed as a parked design note). Date 2026-11-19. Both
`ff07589` and `99f62f9` left `reports/LOG.md`, `reports/RR-DAY-20261119.md`, and `handoff/PROJECT-STATE.md` to
the review lane. No `research/**` byte, code, model call, spend, or push by this lane.

## 1. Evidence re-derived

| commit | claim | verification command | result |
|---|---|---|---|
| `ff07589` | `RR-PART3FIX-20261119.md` §6 withdraws the "lost / UNREPRODUCIBLE" claim and cites `RR-RESVERIFY-20261119` (`81bbfcb`) | `git show ff07589` | §6 added (+40 lines), preserving original §3 text and recording the gitignored path `research/uncommitted/materials/datamining/` |
| `97cf743` | `research/datamining/datamining.py` and `datamining.json` tracked in git and runnable in-place | `sha256sum research/datamining/datamining.{py,json}`; `python3 research/datamining/datamining.py` + `cmp -s` | `datamining.py` sha256 `c34ea6bec7ea93169d35561101d3677570bfa14bb3eb4f849b8f055d1304c783`; `datamining.json` sha256 `c533af6f86f89e451c28b0a8a61a75a6b26f3c9c88b69dbd3de6108837d23cd2`; in-place run reproduces `datamining.json` **byte-for-byte** (`cmp -s` exit 0: 1,061 papers, years 148/179/232/218/137/147, `counterfactual` 80, `monitor_view` 53) |
| `99f62f9` (Part III §9.2 en + zh) | `:389` en and `:359` zh updated from "6 samples per arm" to "3 samples per arm across 2 arms (leave-one-out and matched random; 6 calls per page)" | `git show 99f62f9 -- research/white-paper-Part-III.md research/white-paper-Part-III.zh.md`; `sha256sum` | 1-line replacement in each file, reconciling §9.2 with Route B's `:232,248` (`1,320` calls); new digests: en `bf597057…`, zh `060d814b…` |
| `99f62f9` (`PREREG-E2-DRAFT-20261119.md`) | landed at `research/e2-proposal/PREREG-E2-DRAFT-20261119.md` as **PARKED / BLOCKED** ($0 spend), recording option (b), 3 samples/arm, and both physical blockers on `corpus/m1`–`m8` | `git show 99f62f9 -- research/e2-proposal/PREREG-E2-DRAFT-20261119.md` | Status banner explicitly states `PARKED / BLOCKED on a content-bearing fixture bank — owner ruling RR-E2HOLD-20261119 (801ef6b), $0 spend. NOT a runnable preregistration`; §0 records option (b) and 3 samples/arm; §2 records Blocker A (0/17 traces carry page/prompt text, Part III §4.1 `:144`) and Blocker B (only 3/17 traces have $\ge 10$ unique pages, 1 `tool_recall` fault among them); §7 sign-off lines remain blank |

## 2. Books closed by the review lane

- Appended the owed LOG rows for `ff07589`/`97cf743` and `99f62f9` plus this verification card
  (`RR-E2HOLD-VERIFY-20261119`) to `reports/LOG.md` (four pipes each).
- Added the day-file section to `reports/RR-DAY-20261119.md`.
- Updated `handoff/PROJECT-STATE.md` to mark the routed Part III §9.2 typo fix, `research/datamining/` tracking, and
  parked E2 design note as LANDED & VERIFIED.
