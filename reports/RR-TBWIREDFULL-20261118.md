# RR-TBWIREDFULL-20261118 — full wired OpenCode T-B run: all 193 prompts, capture fidelity PASS, 191/192 exact

**Lane:** opencode. **Date:** 2026-11-18. **Verdict:** **full run completed at the frozen ceiling
(584 requests, no overrun)**. All 193 prompts ran in one session with a clean flush. The capture
passes the D1 fidelity criteria. Scoring is 191/192 file-exact; one prompt failed because the model
misread its filename. **n = 1** session.

## 1. Authority and setup

Fresh run authorized under `reports/TB-WIRED-BLOCK-20261118.md` (prereg frozen before prompt 1,
commit `ae1a550`): ceiling **584** = `ceil(193 × 3.0) + 5`, with A = 5 an UNMEASURED ASSUMPTION for
this wired harness. No ceiling or rule was changed. Run dir
`~/.local/state/ctxvm/w8-runs/tb-wired-full-20261118/`, trace name `tb-wired-full-20261118` (both
fresh for 18 Nov), session `ses_e1297d097ffeC2kbJ99dK7RyD9`. One harness-managed server (PID 8341,
port 4343), one session, project-local shim, seven `CTXVM_*` keys with `CTXVM_BUDGET_TOKENS=60000`
(metadata/`headroom` only). D1–D4 applied.

## 2. Final progress tail and stop

```
prompt 190 calls=570 tools=380 cost=0
prompt 191 calls=573 tools=382 cost=0
prompt 192 calls=578 tools=386 cost=0
prompt 193 calls=584 tools=391 cost=0
STOP None
```

All **193 / 193 prompts** completed. The session ended at **exactly 584 requests** — the frozen
ceiling — with **no overrun**. P193 used 6 requests, one more than the assumed allowance of 5, but
the total stayed at 584. The driver's stop state is `None`; the run was ended normally and the
server was stopped with `SIGINT` (exit 130). No hard stop fired: no timeout, no repeated "does not
exist", no auth/quota, no billed token, no tool refusal, no second session, no unparseable export.

## 3. Witness chain and capture

Witness counts for the session: `context` **584**, `before` **391**, `after` **391**, then:

```
cleanup entered (plugin unload)
flush tb-wired-full-20261118.jsonl bytes=477474 session=ses_e1297d097ffeC2kbJ99dK7RyD9
retention deleted=1 files (max=200, days=30, bytes=536870912)
cleanup finishAll -> 1 tracer(s)
cleanup exit
```

Both hook domains fired across the run and the flush chain is complete.

Private capture (no bytes committed):
`~/.local/state/ctxvm/traces/tb-wired-full-20261118.jsonl` and `.meta.json`.

`session.open`: `agentId: tb-wired-full`, `model: opencode-go/hy4-flash-free`,
`provider: opencode-go`, `budgetTokens: 60000`, `schemaVersion: "0.1"`, `environmentId` present,
`ts` last on all 2,339 events. Meta: `harnessVersion: v2.3.0`, `pluginVersion: 0.0.1`,
`hookStats` contexts 584 / before 391 / after 391 / completed 390 / errored 1.

Trace census: 2,339 events — `turn.render` 584, `call.meta` 584, `page.declare` 390,
`page.fault` 390, `page.render` 390, `session.open` 1; **390 distinct page refs**. Set inclusion
check: all **192/192** expected `fixture/data-NN.csv` read refs appear in `page.declare` (extra refs
are the engine's own summary/file pages, recorded as observations, not failures). The one errored
tool hook is the failed `read` of the misnamed file in the data-99 prompt (§4); it was not repeated.

## 4. Validator and replay

```
python3 spec/rfc-0.1/validate_schema_v0_1.py <trace>
OK: all checks passed                       exit 0

./rust/target/release/replay <trace>        exit 0
{
  "events": 2339,
  "divergences": [],
  "violations": [ … 390 rows of kind "faultOfResidentPage" … ]
}
```

The 390 waste-class rows are ledger observations, not divergences or paging evidence.

## 5. Scores — three denominators kept separate

Reply ledger keyed on each prompt's own `fixture/data-NN.csv` reference (D2), never the turn index
(P192 asks for `data-99.csv`). D3 detector used explicit forms only; none fired. Export: 193 user,
584 assistant, 193 idle; one model; harness `cost: 0` (not a receipt).

| denominator | result |
|---|---|
| file-exact | **191 / 192 = 99.5 %** |
| tuple coverage, files attempted | **1528 / 1536 = 99.5 %** (192 files answered) |
| tuple coverage, whole fixture | **1528 / 1536 = 99.5 %** |
| tuple precision | 1528 / 1528 = 100 % of emitted tuples correct |

The single failure is `data-99.csv`: the prompt correctly asked for `fixture/data-99.csv`, but the
model replied that `fixture/data-9.csv` did not exist and emitted no tuples. This is a model
reading failure on one prompt, not a ledger-mapping or harness fault; it is recorded as a negative
observation. The artefact and three lookups were reached in P193:

- `tb-check fixture artefact.json` → **PASS**, parsed equality, bytes canonical.
- `tb-check --lookups lookups.json p193-reply.txt` → **3/3 PASS** (zeta −264, delta −268, zeta 487).

## 6. Claim ceiling

This witnesses **capture fidelity over all 193 prompts**: valid, replayable v0.1 traces with real
identity, both hook domains, a complete flush, all expected file refs, and scores re-derived from
the same replies. It does **not** witness paging, H3/H4, eviction, `enginePlan`, cost or saving,
model-output determinism, or model quality. Harness `cost: 0` is not a provider receipt. No GO for
a Hermes paged cell. Traces and exports stay private (law 9); no trace byte, credential or
unredacted session text was committed.

## 7. Files and gates

- Repo: this card, one LOG row, one appended section in `reports/RR-DAY-20261118.md`. No
  `packages/**`, `tools/**`, `spec/**`, `corpus/**`, `research/**` or `design/**` byte changed by
  this card. Other lanes' modified `research/white-paper-Part-III*` and untracked drafts were left
  untouched and unstaged.
- `bash tools/check-handoff.sh` → ALL HANDOFF CHECKS PASS. Repo gate re-run unpiped with ambient
  `CTXVM*` cleared → ALL GATES GREEN.
- Explicit staged paths via a private index; `git read-tree HEAD` afterwards;
  `bash tools/git-hygiene.sh` OK. Never pushed.
