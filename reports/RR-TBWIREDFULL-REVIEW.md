# RR-TBWIREDFULL-REVIEW — verified: NO RECORD is correct; one artefact-path discrepancy to correct

Review lane, verify-then-record. Subject: `67650a8` / `reports/RR-TBWIREDFULL-20261117.md`. No model call, no
code change, no spend by this lane. Private artefacts stay under `~/.local/state/ctxvm/w8-runs/`.

## 1. Verdict

**NO RECORD is the correct verdict.** The run stopped at P22 with the server gone, the witness has no
cleanup/flush/finishAll line, and no final capture was written. No ceiling breach: 66 requests against the
preregistered 198. The card's diagnostic numbers check out. One correction is owed: the card names partial trace
paths in the trace dir that are **no longer present** (see §3).

## 2. Evidence re-derived

| claim | command / source | result |
|---|---|---|
| stopping point | `progress.jsonl` tail | P21 `calls 63`; P22 `STOP API_ERROR … Connection refused`, `calls 66` |
| server exit without reason | `serve.log` | only listening + password lines; no shutdown reason (password not reproduced here) |
| one session / model | `export-full.json → info` and message counts | `ses_e17d63b4affezmm1j39F120zHZ`; 22 user, 66 assistant, 22 idle; all 66 assistant on `hy4-flash-free`; cost 0 (harness-reported) |
| no flush | `hooks-witness.log`, grep on that session | 155 lines, both hook domains (context + before/after), **`grep -ci 'cleanup\|flush\|finishAll'` = 0** |
| no final capture | `ls ~/.local/state/ctxvm/traces` | no `tb-wired-full-20261117.jsonl` or `.meta.json`; smoke trace from the earlier run is present |
| partial diagnostics | `partial-replay.json` | 220 events, `divergences: []`, 20 `faultOfResidentPage` rows — matches the card |
| replies | `per-reply-partial.txt` | 22/192 file-exact, 176/176 attempted tuples, 176/1536 whole fixture — matches |
| no breach | progress + prereg | 66 < 198; 579/451 not reused; ceiling unchanged |
| gates | card + my own re-run | card: kit ALL PASS, gate ALL GATES GREEN; my own re-run rc=0 **ALL GATES GREEN** (2026-11-17, `/tmp/opencode/20261117-norec-ci.log`, ambient `CTXVM_*` cleared) |

## 3. Record discrepancy — partial trace paths named by the card are absent

The card §3 states that `~/.local/state/ctxvm/traces/tb-wired-full-20261117.partial.jsonl` and
`.partial.meta.json` exist. I searched the trace dir and the whole home tree: **no `*.partial.jsonl` or
`*.partial.meta.json` exists now**. What remains are the in-run diagnostics (`partial-replay.json`,
`per-reply-partial.txt`, `replies-partial.jsonl`) and the witness log. So the *evidence* for the partial trace's
220-event validator/replay checks cannot be re-run from bytes today — only the stored `partial-replay.json`
result remains. The NO RECORD verdict does not depend on those files (it depends on the absent final capture and
the missing flush), but the card's path statement is stale or was written about files later removed. Corrected
here; the owning lane should not re-run a validator on a file that is gone.

## 4. Carry-forward

- A fresh wired run needs the server **kept alive and flushed gracefully**. The driver's poll got Connection
  refused because the process exited; `serve.log` gives no reason, so the cause of that exit is UNVERIFIED.
- The 198 ceiling **stands**. A fresh run may reuse it only if the owner's fresh authorization says so; do not
  reinterpret "NO RECORD" as a breach or a pass.
- Both hook domains firing under load (witness) is a useful diagnostic for the next attempt, but never a
  substitute for the flush.
- The 22/22 exact replies are observations from a NO RECORD run; no completeness, paging, H3/H4, cost, or
  determinism claim follows from them.

No GO for a Hermes paged cell, no ceiling change, no retry from this lane.
