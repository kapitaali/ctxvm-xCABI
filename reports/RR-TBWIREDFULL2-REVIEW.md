# RR-TBWIREDFULL2-REVIEW — verified: clean flush and CEILING at 201 vs 198

Review lane, verify-then-record. Subject: `9def6b2` / `reports/RR-TBWIREDFULL2-20261117.md`. No code change, no
model call, no spend, no retry by this lane. The capture stays private under `~/.local/state/ctxvm/traces/`.

## 1. Verdict

**CEILING is the correct verdict.** P67 took the session to 201 requests against the preregistered 198. The
ceiling was not raised, no retry was made, and every completed prompt's reply was exact. Unlike the earlier
NO RECORD run, this one has a **complete flush chain** and a valid final capture. The earlier CEILING run
(unwired, 582 vs 579) and the NO RECORD run (66 vs 198, no flush) are separate records; nothing was re-scored.

## 2. Evidence re-derived

| claim | command / source | result |
|---|---|---|
| ceiling stop | `progress.jsonl` tail | P65 195, P66 198, P67 **201** with `STOP CEILING prompt 67: 201 > 198`; no raise |
| final capture | `ls` both files | `.jsonl` 168,735 B; `.meta.json` 629 B — both exist (contrast with the NO RECORD run) |
| flush chain | witness around the flush | `cleanup entered` → `flush … bytes=168735` → `cleanup finishAll -> 1 tracer(s)` → `cleanup exit`, with retention note; both hook domains present in `hookStats` (203 contexts, 134 before/after) |
| identity / meta | parse `session.open` + meta | `opencode-go / opencode-go/hy4-flash-free`; `pluginVersion 0.0.1`, `harnessVersion v2.3.0` |
| trace | parse events | **809**: 203 `turn.render`, 203 `call.meta`, 134 `page.declare`, 134 `page.fault`, 134 `page.render`, 1 `session.open` |
| validator | `validate_schema_v0_1.py` | **exit 0**, OK: all checks passed |
| replay | `rust/target/release/replay` | **exit 0**, events 809, `divergences: []`, 134 `faultOfResidentPage` rows |
| scores | stored per-reply tail, re-read | file-exact **67/192**; attempted coverage **536/536 = 100 %**; whole fixture **536/1536 = 34.9 %**. All available replies exact |
| P193 not reached | progress + scores | artefact/lookups unscored; the ≥192-ref full-run fidelity criterion is unmet **because of the ceiling stop**, not a completed-prompt failure |
| cost | progress rows | harness-reported `0`, not a receipt |

## 3. What this does and does not support

- **Supports:** 67 prompts on the wired route produced a schema-valid, replay-clean capture with real identity,
  both hook domains firing, and a complete flush — capture fidelity on the completed prefix.
- **Does not support:** a full-run completeness verdict, paging/H3/H4/eviction, cost or saving, model-output
  determinism, or a GO for a Hermes paged cell. The 134 `faultOfResidentPage` rows are waste-class ledger rows,
  not replay divergences; they are not paging evidence.
- The NO RECORD run had no final capture; this one does. Keep them as separate records with separate verdicts.

## 4. Owner decision routed

A further wired run would need a newly preregistered ceiling under a fresh authorization. The review lane's
recommendation: do not treat 201 > 198 as evidence about the shape — the completed prompts were all exact. If
the owner wants the full 193-prompt capture, preregister a ceiling from the measured rate (201/67 ≈ 3.0 per
prompt plus a P193 allowance) before any new run, and do not reuse 198, 579, or 451. That is the owner's call;
this review makes no GO.

Kit/gate: `bash tools/run-ci.sh` rc=0 **ALL GATES GREEN** (2026-11-17, `/tmp/opencode/20261117-full2-ci.log`, ambient `CTXVM_*` cleared); `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.
