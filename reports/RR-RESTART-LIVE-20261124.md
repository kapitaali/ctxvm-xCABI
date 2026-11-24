# RR-RESTART-LIVE-20261124 — verified: 0.13.31 is live in the gateway; real sidecar attests stub OFF on operator sessions

Review lane, verify-then-record. Date 2026-11-24. While checking for new landings, I found the "operator restart owed" item from `RR-PARTC-FIX` / `RR-PARTC-FIX-REVIEW` is **already satisfied**. $0, no model call, no push.

## 1. Verified from disk

| claim | check | result |
|---|---|---|
| 0.13.31 files written before gateway start | `stat` repo + installed `__init__.py` (13:23:34), `context_engine.py` (13:22:40); gateway pid 19529 start **13:29:03** | gateway started **after** the files |
| installed build is 0.13.31 | `grep PLUGIN_VERSION` installed copy | `0.13.31` |
| real session flushed under new build | newest coverage sidecars | `local-f913ef…coverage.json` mtime **13:34:45**, `version: 0.13.31`, `harnessVersion: 0.23.4`, `arm: control` |
| stub default-off attested live | that sidecar | `stubDropped: off` on the operator's control session — the default-off condition now has a **real 0.13.31 capture**, closing the earlier evidence gap (which rested on an interpreter probe) |

So the operator restart happened (pid 19529), the shipped 0.13.31 is live, and a real flush attests the stub is off by default on real sessions. The `RR-PARTC-FIX-REVIEW` "owed: operator gateway restart" item is **done**; no agent action was needed.

## 2. What this does / does not change

- **Does:** upgrades the default-off claim from a shipped-code/interpreter probe to a live-capture attestation; confirms the fix is in the running system, not just on disk.
- **Does not:** produce a `recoverable` sidecar — none exists; the stub arm's attestation/re-read remain UNVERIFIED (accepted gap, `RR-PARTC-ARM-RESULT` / `RR-RETRY-BLOCKED`). A future stub arm must still name its own opt-in profile and cite **0.13.31**. No cost/paging/model claim, no `page.evict` (separate owner card), no re-score of Part B.

## 3. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
