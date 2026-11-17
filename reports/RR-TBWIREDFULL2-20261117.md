# RR-TBWIREDFULL2-20261117 — fresh wired run: capture flushed, but CEILING at P67

**Lane:** opencode. **Date:** 2026-11-17. **Verdict:** **CEILING**. The fresh wired run produced a
properly flushed xCABI trace, but stopped at prompt 67 with **201 model requests against the
preregistered 198**. The ceiling was not raised and no retry was made. **n = 1** session.

## 1. Authority and setup

Owner authorized a fresh wired run after `RR-TBWIREDFULL-20261117` ended NO RECORD when its server
exited without a flush. The ceiling preregistered **before** this run in
`reports/TB-WIRED-BLOCK-20261117.md` (`5dd1727`) stands at **198**; 579, 451 and 582 were not reused.

Fresh private dir `~/.local/state/ctxvm/w8-runs/tb-wired-full-20261117b/` with the copied fixture,
193-prompt list, lookups key and a project-local shim re-exporting the adapter's default
`{ id, setup }`. Seven `CTXVM_*` keys set deliberately in the server process, including
`CTXVM_TRACE_NAME=tb-wired-full-20261117b` and `CTXVM_BUDGET_TOKENS=60000`. This time the server ran
as a harness-managed background process and stayed alive; the driver used one server and one session
(`ses_e178d6b18ffeeqPj3vTepgFuRP`) for all prompts.

## 2. How it stopped

Prompts 1–66 completed at exactly 3 requests each, reaching 198. Prompt 67 added 3 more, so the
driver recorded `STOP CEILING prompt 67: 201 > 198` and exported both ledgers. The server was then
stopped with `SIGINT`, and the plugin flushed cleanly. No second session, no re-run, no ceiling
change.

## 3. Capture evidence

- Trace (private): `~/.local/state/ctxvm/traces/tb-wired-full-20261117b.jsonl`
- Meta (private): `~/.local/state/ctxvm/traces/tb-wired-full-20261117b.meta.json`
- Coverage sidecar also written; no trace bytes committed.

Witness summary for the session: `context` **203**, `before` **134**, `after` **134**, then
`cleanup entered → flush (168,735 bytes) → retention → finishAll -> 1 tracer(s) → cleanup exit`.
Both hook domains fired across the run and the flush chain is complete — the specific failure of the
previous wired run did not recur.

`session.open` carries real identity: `agentId: tb-wired-full`, `model: opencode-go/hy4-flash-free`,
`provider: opencode-go`, `budgetTokens: 60000`, `schemaVersion: "0.1"`, `environmentId` present,
`ts` last on all 809 events. Meta: `harnessVersion: v2.3.0`, `pluginVersion: 0.0.1`, model/provider
as above, `hookStats` contexts 203 / before 134 / after 134 / completed 134 / errored 0.

Trace census: 809 events — `turn.render` 203, `call.meta` 203, `page.declare` 134,
`page.fault` 134, `page.render` 134, `session.open` 1; 134 distinct page refs, all `tool_result`.
`validate_schema_v0_1.py` exit 0; `replay` exit 0 with `events: 809`, `divergences: []`, and 134
`faultOfResidentPage` waste-class rows. The export's 201 assistant messages versus the trace's 203
contexts are both recorded; the difference arose around the stop/flush boundary.

## 4. Scores (three denominators, separate)

Reply ledger keyed on each prompt's own `fixture/data-NN.csv` reference (D2), never the turn index.
Auth detector used explicit forms only (D3); none fired. From the export: 67 user, 201 assistant,
67 idle; one model (`hy4-flash-free`); cost field 0.

| denominator | result |
|---|---|
| file-exact | **67 / 192 = 34.9 %** (all 67 available replies exact) |
| tuple coverage, files attempted | **536 / 536 = 100 %** (67 files answered) |
| tuple coverage, whole fixture | **536 / 1536 = 34.9 %** |

The artefact and three lookups were not reached (P193 never ran), so they are not scored. The
full-run D1 criterion of ≥192 distinct page refs was not met because the run stopped at P67;
this is a consequence of the ceiling, not a fidelity failure of the prompts that did run.

## 5. Claim ceiling

CEILING is the verdict: 201 > 198, recorded, not repaired. This run witnesses **capture fidelity
over 67 prompts** — valid, replayable traces with real identity and both hook domains — not paging,
H3/H4, eviction, `enginePlan`, cost or model-output determinism. Harness `cost: 0` is not a provider
receipt; no cost or saving claim. Traces stay private (law 9); no trace byte, credential or
unredacted session text was committed. No GO for a Hermes paged cell.

## 6. Files and gates

- Repo: this card, one LOG row, one appended section in `reports/RR-DAY-20261117.md`. No
  `packages/**`, `tools/**`, `spec/**`, `corpus/**`, `research/**` or `design/**` byte changed.
- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS. Repo gate re-run unpiped with ambient
  `CTXVM*` cleared → ALL GATES GREEN.
- Explicit staged paths via a private index; `git read-tree HEAD` afterwards;
  `bash tools/git-hygiene.sh` OK. Never pushed.
