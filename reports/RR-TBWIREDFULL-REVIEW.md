# RR-TBWIREDFULL-REVIEW — verified: the full wired run is COMPLETE at exactly 584 requests

Review lane, verify-then-record. Subject: `f97aa29` / `reports/RR-TBWIREDFULL-20261118.md`. No code change, no
model call, no spend, no retry by this lane. Capture stays private.

## 1. Verdict

**COMPLETE / CAPTURE-FIDELITY PASS**, with the single P192 failure recorded. 193/193 prompts ran in one session,
ending at **exactly 584 requests** — the frozen ceiling from `TB-WIRED-BLOCK-20261118.md` — with **no overrun and
no hard stop**. This is capture fidelity only: no paging, H3/H4, eviction, cost, determinism, or model-quality
claim, and no GO for a Hermes paged cell. The earlier runs stay separate records (NO RECORD P22; CEILING P67;
INCOMPLETE P95).

## 2. Evidence re-derived

| claim | how | result |
|---|---|---|
| completion / ceiling | parse `progress.jsonl` | **193 rows, 0 stops, 0 nonzero rc**; final `calls=584`, `tools=391`; P192 `calls=578` → P193 `584` (6 requests, one more than the assumed A=5, but the total stayed exactly at the frozen ceiling) |
| capture files | `ls` | `.jsonl` 477,474 B; `.meta.json` 630 B |
| flush chain | witness around flush | `cleanup entered` → `flush … bytes=477474` → `cleanup finishAll -> 1 tracer(s)` → `cleanup exit`; both hook domains present in the 584 context / 391 before / 391 after counts |
| trace | parse | **2,339 events**: 1 session.open, 390 page.declare / page.fault / page.render, 584 turn.render / call.meta; identity `opencode-go / opencode-go/hy4-flash-free`; meta pluginVersion 0.0.1, harnessVersion v2.3.0 |
| refs | set match on declared refs | **390 distinct**, covering **192/192** expected `fixture/data-NN.csv` refs; extras are observations (summary/file pages) |
| validator | my own re-run | exit 0, OK: all checks passed |
| replay | my own re-run | exit 0, events 2,339, `divergences: []`, 390 `faultOfResidentPage` rows (waste-class, not divergences or paging evidence) |
| scores | my own `tb-check --per-reply` | file-exact **191/192 = 99.5 %**; attempted coverage **1528/1536 = 99.5 %**, precision 1528/1528; whole-fixture **1528/1536 = 99.5 %**. The single failure is `data-99.csv`: the model replied that `data-9.csv` did not exist and emitted no tuples — a model reading failure, not a ledger/harness fault (the ledger was keyed from each prompt's own filename) |
| artefact / lookups | stored outputs, re-read | artefact PASS with canonical bytes; lookups 3/3 PASS |
| cost | progress rows | `0` harness-reported, not a receipt |

## 3. What the result does and does not support

- **Supports:** a 193-prompt wired run on the authorized Go route produced a valid, replay-clean capture with real
  identity, both hook domains across the run, a complete flush chain, all fixture refs covered, canonical artefact,
  correct lookups, and 191/192 exact per-file replies.
- **Does not support:** paging, H3/H4, eviction, cost/saving, determinism, model quality, or a paged-cell GO.
  `cost: 0` is a harness field; 390 waste-class rows are not paging evidence.
- The single P192 failure is part of the measured score, not an exclusion: it is a model reading error, and the
  runner did not retry. Keep the 99.5 % figure with that cause attached.

## 4. Other commits seen during this review

- `6bd9c89` revised `reports/RR-REDACT-20261118.md` on recorded owner instruction (cross-lane edit by hermes); its
  LOG row `RR-REDACTREV-20261118` is on record. I did not overwrite it.
- `a881dfd` untracked research markdown moved under `research/uncommitted` (Part II stays as PDF). I did not stage
  or restore any of it.

Kit/gate: `bash tools/run-ci.sh` rc=0 **ALL GATES GREEN** (2026-11-18, `/tmp/opencode/20261118-full-ci.log`, ambient `CTXVM_*` cleared); `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.
