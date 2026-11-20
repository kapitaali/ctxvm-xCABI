# RR-E0ROUTE-VERIFY-20261120 — verified: `f980768` applied the E0 route ruling; one stale banner line routed back

Review lane, verify-then-record. Subject: `f980768` (1 file: `research/e0-proposal/PREREG-E0-DRAFT-20261119.md`,
48 insertions / 23 deletions), applying the owner's `RR-E0ROUTE-20261120` ruling (`af38768`). Date 2026-11-20.
The research lane owes the review lane the LOG row and day section for this commit; this card carries them. No
`research/**` or `umpire/**` byte written by this lane; no model call, server start, spend, or push.

## 1. Evidence re-derived

| claim | verification | result |
|---|---|---|
| commit scope | `git show --stat --oneline f980768` | 1 file, 48+/23− |
| banner now gates on two Phase-0 checks | `sed -n '1,12p'` of the note | `Status: PARKED on the two Phase-0 gates (§8) — owner route ruling RR-E0ROUTE-20261120 (af38768): CPU llama.cpp pinned snapshot, $0 local ceiling. NOT a runnable preregistration until Gate 1 (logprob access) and Gate 2 (gradability pilot, Var(T)>0) pass.` |
| §2 hardware corrected | same file, lines 49–54 | i5-4300M / 4 threads / 15 GiB / Intel integrated only, no NVIDIA; the "GTX 1050 Ti 4 GB" line explicitly retracted as stale |
| §2 route pinned | `harness/pins.json`, binary `--version`, GGUF shas, umpire HEAD | llama.cpp **0.7.0-dev (build 1, commit 620d222)** (source `620d222`, tag `v0.7.0`); binary sha `0f60e048…`; `Qwen3-1.7B-Q8_0.gguf` sha `66a17017…`; `qwen2.5-1.5b-instruct-q8_0.gguf` sha **`d7efb072e7724d25048a…`**; umpire HEAD `519058f` — all match the note |
| Gate 1 locator real | `~/Documents/umpire/reports/RR-M1-20261022.md:65` | records v0.7.0's logprob shape `token`/`logprob`/`top_logprobs` (the old `tok_str`/`prob` shape is gone) — supports "likely to pass", not a substitute for the Phase-0 re-verification |
| §8 two gates added, §9 updated | diff of `f980768` | Gate 1 logprob access (stop → BLOCKED if absent), Gate 2 gradability pilot on 3–5 items (`Var(T)>0`, else escalate); Phase 1 only after both; §9 records the ruling, leaves snapshot-choice and gate-evidence lines blank |
| note still PARKED | banner + closing line | `The note stays PARKED until the gates run; no model call or spend is authorized by the route ruling alone.` |

## 2. Residual defect routed back to the research lane

**Banner line 7** still reads: *"Compute-only by design (no API spend), but it cannot run without an open-weight
model snapshot + a GPU compute route (owner decisions)."* That clause is **stale** — §2 now rules a CPU-only route
and retracts the GPU claim; the banner should read something like *"…but it cannot run until the two Phase-0 gates
(§8) pass and one of the two ruled CPU snapshots is frozen."* This is a prose inconsistency, not a gate input or a
change to the ruling. `research/**` is read-never-edit for the review lane, so I did not edit it; routed to the
research lane as a one-line correction.

## 3. Books closed by the review lane

- Appended the owed LOG row for `f980768` and this verification card to `reports/LOG.md` (four pipes each).
- Added the day-file section to `reports/RR-DAY-20261120.md`.
