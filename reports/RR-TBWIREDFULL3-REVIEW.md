# RR-TBWIREDFULL3-REVIEW — verified: operator-stopped wired run is INCOMPLETE with a clean prefix capture

Review lane, verify-then-record. Subject: `c513144` / `reports/RR-TBWIREDFULL3-20261117.md`. No code change, no
model call, no spend, no retry by this lane. Capture stays private.

## 1. Verdict

**INCOMPLETE is the correct verdict** — 95 of 193 prompts, stopped by the owner's SIGINT at 20:21Z during server
shutdown. It is **not NO RECORD** (a final capture exists with a complete flush chain) and **not CEILING** (285
requests against the preregistered 584). All 95 available replies exact; the stop is an operator decision, not a
model or harness result. P193/artefact/lookups were not reached.

## 2. Evidence re-derived

| claim | how | result |
|---|---|---|
| stop | `progress.jsonl` | 95 rows; last `STOP API_ERROR prompt 95: HTTP Error 503: Service Unavailable` during shutdown; `calls` 285 < 584 |
| server exit | handoff | PID 129064 exit 130 on `kill -INT` — consistent with SIGINT; not independently re-observable after the fact |
| flush chain | witness around flush | `write-through after 10 hook fires` → `cleanup entered` → `flush … bytes=204376` → `cleanup finishAll -> 1 tracer(s)` → `cleanup exit` — complete |
| final files | `ls` | `.jsonl` 204,376 B and `.meta.json` 628 B both exist |
| trace | parse | **1,046 events**: 1 session.open, 190 page.declare (190 distinct refs), 95 page.fault, 190 page.render, 285 turn.render, 285 call.meta; identity `opencode-go / opencode-go/hy4-flash-free`; meta pluginVersion 0.0.1, harnessVersion v2.3.0 |
| validator | my own re-run | exit 0, OK: all checks passed |
| replay | my own re-run | exit 0, events 1,046, `divergences: []`, 95 `faultOfResidentPage` rows |
| scores | stored per-reply tail | file-exact **95/192**, attempted coverage **760/760 = 100 %**, whole fixture **760/1536** — all available replies exact |
| not reached | progress/scores | P193, artefact, lookups unscored; no exact-reply failure exists for the completed prefix |

## 3. What this supports and what it does not

- **Supports:** an operator-stopped 95-prompt prefix produced a valid, replay-clean capture with real identity and
  a complete flush chain — capture fidelity on the completed prefix.
- **Does not support:** a full-run completeness verdict, paging/H3/H4/eviction, cost or saving, determinism,
  model quality, or a GO for a Hermes paged cell. The 95 waste-class rows are ledger rows, not divergences or
  paging evidence. `cost: 0` is harness-reported, not a receipt.
- The three wired runs stay separate records: NO RECORD (P22, no flush), CEILING (P67, 201 > 198, clean flush),
  INCOMPLETE (P95, operator stop, clean flush). None was re-scored or retried.

## 4. Carry-forward

A fresh full run needs a new owner authorization and ceiling preregistration. The 584 prereg
(`TB-WIRED-BLOCK2-20261117.md`) governed this run; its integer was not reached and remains unraised. Do not
treat 285 < 584 as evidence about the shape — only 95 prompts ran. My recommendation: if another full run is
wanted, budget the real wall time (the owner's 5–6 h estimate), keep the graceful-flush driver, and preregister
before prompt 1. That is the owner's call; this review issues no GO.

Kit/gate: `bash tools/run-ci.sh` rc=0 **ALL GATES GREEN** (2026-11-17, `/tmp/opencode/20261117-full3-ci.log`, ambient `CTXVM_*` cleared); `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.
