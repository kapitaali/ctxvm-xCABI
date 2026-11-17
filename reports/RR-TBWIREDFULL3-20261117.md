# RR-TBWIREDFULL3-20261117 — wired run stopped by operator SIGINT: incomplete, clean flush

**Lane:** opencode. **Date:** 2026-11-17. **Verdict:** **INCOMPLETE RUN (operator shutdown)** — not
NO RECORD (the capture flushed), not CEILING (285 requests against the preregistered 584), and not
a full-run result. **n = 1** session, 95 prompts answered.

## 1. Authority and setup

Fresh full wired run authorized under the new preregistration `reports/TB-WIRED-BLOCK2-20261117.md`
(frozen ceiling **584**; authoritative version `2242220` plus collision erratum `fc6ec90`). Same
fixture, 193 verbatim prompts, one server process and one session, project-local shim, seven
`CTXVM_*` keys, D1–D4 rules. Run dir `~/.local/state/ctxvm/w8-runs/tb-wired-full-20261117c/`,
session `ses_e15d6f27bffep630jx1OniMh8v`.

## 2. How it stopped

The owner asked for status before shutting the machine down at midnight, then asked for a graceful
`SIGINT` to server PID 129064. I sent `kill -INT 129064`; the server exited with status 130 and the
plugin wrote a complete flush. The driver's last progress row records
`STOP API_ERROR prompt 95: HTTP Error 503: Service Unavailable` — that is the stopping server, not
a model fault. The last steady progress rows were P93 = 279 requests, P94 = 282, P95 = 285.

No hard stop from the prereg fired: the ceiling was **584**, and 285 was well below it. No retry,
no second session, no ceiling change.

## 3. Capture evidence

- Private trace: `~/.local/state/ctxvm/traces/tb-wired-full-20261117c.jsonl`
- Private meta: `~/.local/state/ctxvm/traces/tb-wired-full-20261117c.meta.json`

Witness for the session: `context` **285**, `before` **190**, `after` **190**, then
`cleanup entered → flush (204,376 bytes) → retention → finishAll -> 1 tracer(s) → cleanup exit`.
Both hook domains fired and the flush chain is complete.

`session.open` carries real identity: `agentId: tb-wired-full`, `model: opencode-go/hy4-flash-free`,
`provider: opencode-go`, `budgetTokens: 60000`, `schemaVersion: "0.1"`, `environmentId` present,
`ts` last on all 1,046 events. Meta: `harnessVersion: v2.3.0`, `pluginVersion: 0.0.1`,
`hookStats` contexts 285 / before 190 / after 190 / completed 190 / errored 0.

Trace census: 1,046 events — `turn.render` 285, `call.meta` 285, `page.declare` 190 (190 distinct
refs), `page.render` 190, `page.fault` 95, `session.open` 1.
`validate_schema_v0_1.py` exit 0; `replay` exit 0 with `events: 1046`, `divergences: []`, and 95
`faultOfResidentPage` waste-class rows.

## 4. Scores (prefix only)

Reply ledger keyed on each prompt's own `fixture/data-NN.csv` reference (D2), never the turn index.
D3 auth detector used explicit forms only; none fired. Export: 95 user, 285 assistant, 95 idle;
one model; harness `cost: 0` (not a receipt).

| denominator | result |
|---|---|
| file-exact | **95 / 192 = 49.5 %** (all 95 available replies exact) |
| tuple coverage, files attempted | **760 / 760 = 100 %** |
| tuple coverage, whole fixture | **760 / 1536 = 49.5 %** |

P193 was not reached: no artefact, no lookup scores. The full-run D1 criterion of ≥192 distinct
page refs is unmet because the run stopped at 95 prompts, not because a completed prompt failed.

## 5. Claim ceiling

This witnesses **capture fidelity over a 95-prompt prefix**: valid, replayable traces with real
identity, both hook domains and a complete flush. It is not a full-run result, not a ceiling
outcome, and not evidence about paging, H3/H4, eviction, `enginePlan`, cost, model-output
determinism or model quality. Harness `cost: 0` is not a provider receipt; no cost or saving claim.
No GO for a Hermes paged cell. Traces stay private (law 9); no trace byte, credential or unredacted
session text was committed.

## 6. Files and gates

- Repo: this card, one LOG row, one appended section in `reports/RR-DAY-20261117.md`. No
  `packages/**`, `tools/**`, `spec/**`, `corpus/**`, `research/**` or `design/**` byte changed by
  this card. Other lanes' dirt was left untouched and unstaged: modified
  `design/W8-EXECUTOR-PROMPT.md`, `reports/RR-W8B-20261110.md`, `tools/w8-run-env.sh`; deleted
  `research/white-paper-Part-II.md` plus untracked `research/datamining/`,
  `research/white-paper-Part-II.pdf`, `reports/RR-DATAMININGFIX-20261117.md` and other drafts.
- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS. Repo gate re-run unpiped with ambient
  `CTXVM*` cleared → ALL GATES GREEN.
- Explicit staged paths via a private index; `git read-tree HEAD` afterwards;
  `bash tools/git-hygiene.sh` OK. Never pushed.
