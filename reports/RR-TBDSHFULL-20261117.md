# RR-TBDSHFULL-20261117 — verified: dsh full run COMPLETE, capture-fidelity pass within ceiling

Review lane, verify-then-record. Subject: dsh handoff 18. No code change, no model call, no spend, no retry by
this lane. All artefacts remain private/workspace-local.

## 1. Verdict

**COMPLETE / CAPTURE-FIDELITY PASS accepted.** 193/193 prompts, rc 0, no hard stop, 581 requests against the
frozen 588 ceiling, 193 valid replay-clean traces, all 192 fixture refs covered, artefact and lookups PASS.
This is a capture-fidelity result only — 193 short traces, not one 193-turn trace; no cost, paging, H3/H4,
eviction, determinism, or model-quality claim, and no GO for a Hermes paged cell.

## 2. Evidence re-derived (not taken from the handoff on trust)

| claim | how | result |
|---|---|---|
| completion | parse `progress.jsonl` | **193 rows, 0 nonzero rc, 0 stops, 0 trace anomalies**; P193 rc 0, 47 s |
| request count | decompress the *correct* session dir (workspace-named) and count `assistant/message` | **581** — matches the handoff. Note: my first attempt used the DSH-checkout-named session dir and got 0; the run's session lives under the workspace-named dir. The number stands |
| external ceiling watch | handoff's `ceiling-watch.log` (six rows) | last row 193 rows / 581 calls; 581 < 588, no CEILING. `ceil(193×3)+9` double-counts P193's base; frozen integer unchanged |
| traces | `new-traces.txt` | **193 paths**; parsed all: 193 `session.open` with provider opencode / model hy4-flash-free, 582 `page.declare`, 0 parse failures |
| no meta | glob `session-9fd394a3*.meta.json` | **0** — the dsh adapter emits JSONL only; no meta path invented |
| flush chain | grep all 193 prompt logs | `session/disposed` **193**, `trace written` **193**, `effect cleanup` **193**, `flushTracer FAILED` **0** |
| detectors | handoff scan | 401/429, insufficient_credits, FreeUsageLimitError, authentication_error, MissingSessionID — all 0 |
| scores | re-ran `tools/tb-check.py` against the workspace fixture and corrected `replies.jsonl` | **file-exact 192/192**, attempted coverage **1536/1536**, whole fixture **1536/1536**, exit 0; artefact check exit 0 (parsed equality) |
| lookups / P193 | handoff + tb-check stored output | 3/3; P193 4-key artefact, 47 s, one trace, 5 requests; no retry |

## 3. Corrections accepted from the handoff

1. **Driver `calls: 0`** — the field is unusable; the authoritative count is the persisted session log,
   externally watched. My earlier `RR-TBDSHCOUNTER-20261117` named a double-prefix glob as the cause; the
   handoff calls it a flush race. Both agree on the effect (counter stuck at 0, ceiling enforced externally).
   The exact root cause remains UNVERIFIED; fix belongs to the dsh lane's workspace driver.
2. **First verifier's spurious 191/192** — it keyed P193's reconciliation reply to `data-02.csv`. Excluding P193
   from the per-file ledger (it is scored by `--lookups`) gives 192/192. Corrected outputs authoritative; the
   first `verification.txt` is an audit trail.
3. **`call.meta` is a turn-level flush**, not a request counter. Request counts come from session-log assistant
   messages.
4. **No `.meta.json`** from this adapter — unlike the OpenCode lane. Do not validate a nonexistent file.

## 4. Repo record

This card + one LOG row (four pipes) + a day-file section. No gate input changed. My gate re-run rc=0 **ALL GATES GREEN** (2026-11-17, `/tmp/opencode/20261117-dshfull-ci.log`, ambient `CTXVM_*` cleared); `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.

## Handoff back to the dsh lane

Roger on handoff 18 — accepted as COMPLETE / CAPTURE-FIDELITY PASS. I re-derived the load-bearing numbers
(193 rows/no stops, 581 assistant messages from the workspace-named session, 193 traces with correct identity,
193× each flush line, 192/192 + 1536/1536 + 1536/1536 via my own tb-check run). The four corrections are
accepted, with the driver-counter root cause left UNVERIFIED — don't assert a cause you haven't proven. No
cost/paging/H3/H4/determinism claim; no paged-cell GO. Plan D and the corpus naming remain parked. Do not
re-run anything until the owner assigns a new task. The separate prompt for fixing the counter bug follows in
my reply to the owner.
