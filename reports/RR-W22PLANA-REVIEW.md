# RR-W22PLANA-REVIEW — verified: Plan A landed, the live bar is met, and the replay violation is recorded

Review lane, verify-then-record. Subject: `a2669c9` (ctxvm canonical) and `97711cc1` (DSH checkout sync), plus
`RR-W22-20261116-06.md`. No code change by this lane; the trace stays private under
`~/.local/state/ctxvm/traces/`.

## 1. Verdict

**Plan A is landed and the required live bar is met.** Every claim re-derived from the repo and the trace. The
new trace carries real provider/model and page declarations, validates and replays cleanly on `divergences`,
and reports one `faultOfResidentPage` violation — which the card records honestly. The suite is green with a
named skip. Both copies are byte-identical. Plans B/C/D remain untouched, as stated.

## 2. Evidence re-derived

| claim | command / source | result |
|---|---|---|
| landing | `git log --oneline -3`, `git show --stat a2669c9` | `a2669c9` present; 7 adapter source/test files + card + LOG row |
| fix shape | `packages/deepseek/src/event-data.ts` | one `eventData()` merges `data` payload with envelope metadata (`type, seq, time, surfaceOp, sourceEventSeqs, ignorable`); fallback to the object itself when no `data` — matches the clearance |
| live trace identity | parse the private trace's `session.open` | **`provider=opencode`, `model=hy4-flash-free`**, agentId `dsh:session-1c74…` — the required assertion |
| page declarations | same parse | **3 `page.declare`** rows (required), plus 1 `page.fault`, 1 `turn.render`, 1 `call.meta`; 7 events total |
| permissions | `stat -c %a` | trace `0600`; trace dir precedent `0700` (law 9) |
| schema | `venvs/odps/bin/python spec/rfc-0.1/validate_schema_v0_1.py <trace>` | **exit 0**, OK: all checks passed |
| replay | `./rust/target/release/replay <trace>` | **exit 0**, `"events": 7`, `"divergences": []`, `violations: [{"seq":4,"kind":"faultOfResidentPage"}]` — exactly as the card says |
| suite | `node --test packages/deepseek/test/` | **15 tests / 14 pass / 0 fail / 1 skip** (named replay skip) |
| both copies identical | md5 of 7 files (ctxvm ↔ DSH checkout) | **all IDENTICAL**; DSH HEAD `97711cc1` |
| gates | card's report + my own gate launched during this review | card: `run-ci.sh` rc=0 ALL GATES GREEN (ts 24+62+46+14), kit ALL PASS, hygiene OK, DSH typecheck 0, lint 0/0; my own re-run: rc=0 **ALL GATES GREEN** (2026-11-16, `/tmp/opencode/20261116-plana-ci.log`, ambient `CTXVM_*` cleared) |

## 3. What the violation means, and what it does not

`faultOfResidentPage` at seq 4 is a **ledger violation row, not a replay divergence**: replay exited 0 with
`divergences: []`. The card reports it rather than hiding it, which is the right posture. It does not invalidate
the Plan A bar — identity and page declarations are present — but it is a real observation about this session:
a fault was recorded on a page the derived table considered resident. Do not turn it into a paging claim, and do
not drop it from the record.

## 4. Carry-forward

- Plan B (schemastery peer) stays deferred, Plan C (acceptance #4) held on credential/route, Plan D (lint) with
  the other file's owner. Re-confirm before anyone starts them.
- Reuse the live verification recipe for future adapter changes: named private trace, validator exit, replay
  exit/divergences/violations, suite counts, both trees byte-identical.
- The untracked vendored-peer links are environment setup; the literal `~/` artifact in the DSH checkout remains
  reported and untouched. No recursive delete at a home-resolving path.

No call, no spend, no code change by this lane. Kit/gate status is in the day file.
