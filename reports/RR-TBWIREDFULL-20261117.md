# RR-TBWIREDFULL-20261117 — full wired run: NO RECORD, server exited without flush

**Lane:** opencode. **Date:** 2026-11-17. **Verdict:** **NO RECORD** for the capture. The run stopped
at prompt 22 when the OpenCode server process exited without a cleanup/flush; there is no final
`.jsonl` or `.meta.json`, only a write-through partial. **No ceiling breach** (66 requests against
the preregistered 198). No retry, no second session, no ceiling change.

## 1. Authority and preregistration

Owner authorized the full 193-prompt wired run on 2026-11-17. The ceiling was preregistered and
committed **before** the run in `reports/TB-WIRED-BLOCK-20261117.md` (commit `5dd1727`):
`ceil(193 × r_smoke=1.000) = 193` plus a stated P193 allowance of 5 = **198**. 579/451 were not
reused; 582 remained an observation. D1–D4 applied as authorized.

## 2. What ran, and how it stopped

Fresh private run dir `~/.local/state/ctxvm/w8-runs/tb-wired-full-20261117/` with the copied
fixture, `prompts.jsonl`, `lookups.json`, and a project-local shim re-exporting the adapter's
default `{ id, setup }`. Seven `CTXVM_*` variables were set deliberately in the server process
(`CTXVM_TRACE_NAME=tb-wired-full-20261117`, `CTXVM_BUDGET_TOKENS=60000`, model/provider
`opencode-go/hy4-flash-free` / `opencode-go`). One server process and one session
(`ses_e17d63b4affezmm1j39F120zHZ`) served all prompts.

Prompts 1–21 completed normally (63 assistant messages). Prompt 22's poll then failed with
`<urlopen error [Errno 111] Connection refused>`: the server process was gone. `serve.log` contains
only the listening and password lines — no shutdown reason. The driver recorded
`STOP API_ERROR prompt 22` and exported both ledgers. No second session was created; nothing was
retried to get a green result.

## 3. Why this is NO RECORD

- The trace directory holds only
  `~/.local/state/ctxvm/traces/tb-wired-full-20261117.partial.jsonl` and
  `.partial.meta.json` (write-through after hook fires), **not** the final
  `<name>.jsonl`/`.meta.json` pair.
- `hooks-witness.log` for this session ends with `context`/`before`/`after` lines and has
  **no `cleanup entered`, `flush`, `finishAll` or `cleanup exit`** for it. The flush discipline from
  the plan was not completed: the slice was not gracefully flushed.
- Therefore none of the full-run D1 fidelity criteria can be claimed. Diagnostic-only facts about
  the partial bytes are stated in §4 and are not a capture verdict.

## 4. Diagnostic observations (not a result)

- Exports parse: 22 user, 66 assistant, 22 idle; one model only (`hy4-flash-free`); 44 tool parts;
  harness `info.cost: 0` (harness-reported, not a receipt). 66 requests is well below 198, so the
  preregistered ceiling was not reached.
- The partial witness does show **both** hook domains (`session.context` and
  `tool.execute.before`/`after`) across the 21 completed prompts — evidence the v2.3.0 domains fire
  under load, but not a substitute for the final flush.
- Partial trace: 220 events (`turn.render` 60, `call.meta` 60, `page.declare` 40, `page.render` 39,
  `page.fault` 20, `session.open` 1), 40 distinct page refs. `validate_schema_v0_1.py` exit 0;
  `replay` exit 0 with `divergences: []` and 20 `faultOfResidentPage` waste-class rows. Both checks
  are diagnostics on a partial file, not full-run gates.
- Reply ledger keyed by each prompt's own `fixture/data-NN.csv` reference (D2), never the turn
  index. `--per-reply` on the 22 available replies: 22/22 file-exact, 176/176 tuples correct over
  files attempted, 176/1536 whole fixture. The artefact and three lookups were not reached (P193
  never ran), so they are not scored.

## 5. Claim ceiling and next decision

NO RECORD is a harness/infrastructure outcome, not evidence about the shape, the model, paging,
H3/H4, eviction, cost, or model-output determinism. Even a completed wired run would witness only
capture fidelity (mirror-only adapter, no engine). Traces stay private; no trace bytes, server
password or session text were committed.

The owner must decide whether to authorize a fresh wired run with a server that is kept alive and
flushed gracefully. This card does not restart it, raise or reinterpret the ceiling, or issue a GO
for a Hermes paged cell.

## 6. Files and gates

- Repo: this card, one LOG row, one appended section in `reports/RR-DAY-20261117.md`. No
  `packages/**`, `tools/**`, `spec/**`, `corpus/**`, `research/**` or `design/**` byte changed.
- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS. Repo gate re-run unpiped with ambient
  `CTXVM*` cleared → ALL GATES GREEN.
- Explicit staged paths via a private index; `git read-tree HEAD` afterwards;
  `bash tools/git-hygiene.sh` OK. Never pushed.

## 7. Erratum (2026-11-17, review `RR-TBWIREDFULL-REVIEW`) — partial path statement

Sections 2–4 state that `~/.local/state/ctxvm/traces/tb-wired-full-20261117.partial.jsonl` and
`.partial.meta.json` exist. That is no longer true: a later check found **no files at those paths
anywhere**. What remains is the in-run `partial-replay.json`, the per-reply outputs and the witness
log (155 lines for the session, both hook domains, zero cleanup/flush lines). Consequently the
220-event validator/replay result in §4 cannot be re-run from bytes. The **NO RECORD** verdict does
not depend on those files — it rests on the absent final capture and the absent cleanup chain in the
witness log — so the verdict stands. Why the server exited remains UNVERIFIED (`serve.log` has no
shutdown reason).
