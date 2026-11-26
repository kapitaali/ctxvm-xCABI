# TB-OPENCODE-RUN — proposal: the output-completeness run in OpenCode, with a raised call ceiling

Status: **AUTHORIZED 2026-11-16 / plan of record for a run, not a cell.** Author: review lane, 2026-11-16, at the
owner's request ("plan for a run but in opencode. raise the call ceiling. use the prompt in design/"). The owner
explicitly authorized the re-preregistration and the free run on 2026-11-16 ("yes it is authorized"); recorded in
`reports/RR-TBAUTH-20261116.md`. The plan of record for what T-B measures stays `design/past-experiments/TB-PLAN.md` (rev 2);
`design/past-experiments/TB-FREE-RUN.md` is the Hermes run plan. This card fixes **which harness runs the next shape**. Phase 0 is
verified (`RR-TBPHASE0-20261116`); phase 1 may proceed. No paid call is authorized by this card.

## 1. Why this run exists

The Hermes free run (`RR-TBFREE-20261116` + addenda) answered the capability question and found the real
obstacle: the model emitted **69/69 correct tuples** for the categories it answered, and omitted the rest
because both execution tools were refused in unattended single-query mode, leaving it to aggregate 600 rows by
hand. The experiment lane named the tension: a fixture big enough for residency to cross 60,000 needs many
rows, but a model without code needs a small per-prompt workload; a 150-row variant needs roughly 200 prompts
against **TB-PLAN P1's 150-call ceiling**. The owner chose: **raise the ceiling and run it in OpenCode.**

## 2. What this run can and cannot witness — state it before phase 1

- The OpenCode adapter (`packages/opencode/README.md`) is **mirror-only**: no context engine, no budget, no
  eviction, no `enginePlan`. **This run cannot witness a paged arm, H3, or H4's paging comparison.** It measures
  one thing: whether the smaller per-prompt workload produces **complete, exact per-file replies** on a free
  model when execution tools are available.
- The result is a **capability / shape verdict**, not a cell. A GO means "this shape is now hand-answerable;
  a Hermes paged cell can be preregistered" — not "paging works". A NO-GO means "change the shape again".
- No cost claim: the chosen OpenCode route is zero-cost by its config entry, and any bill ends the run.

## 3. Subject (measured config, not assumed)

`~/.config/opencode/opencode.jsonc` declares 25 models under `explabs`; two are `cost.input = 0.0,
cost.output = 0.0`: **`qwen3-30b-a3b`** and **`qwen3-8b`**. Primary subject: `explabs/qwen3-30b-a3b`;
fallback `explabs/qwen3-8b`. OpenCode CLI v2.3.0 is on PATH. Commands:

```
opencode --version                         # v2.3.0, measured 2026-11-16
opencode run --model explabs/qwen3-30b-a3b --session <id> "<prompt>"
opencode session export <id> --sanitize    # transcript for the reply ledger
```

Zero-cost in config is a local declaration; **the run does not claim $0 until a receipt or the provider's own
endpoint confirms it** (TB-FREE-RUN §4: any charge aborts).

## 4. Fixture — measured, not declared

Generator `tools/gen-tb-fixture.py --seed 7 --budget 60000 --measure`. Measured 2026-11-16 from the repo:

| shape | files | rows/file | fixture tokens C | crossing | pressure turns | digest | verdict |
|---|---|---|---|---|---|---|---|
| current T-B | 48 | 600 | 107,867 | turn 27 | 22 | `f56f61c7…` | kept as the record |
| **proposed** | **192** | **150** | **109,155** | turn **106** | **87 of 192** | `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec` | 1.82× budget; hand-countable rows |
| 240 × 120 | 240 | 120 | (generated, not measured in full) | — | — | `cbcf3659…` | alternative; more prompts, smaller workload |

The proposed shape keeps C essentially the same while cutting per-prompt arithmetic from 600 rows to 150. The
residency crossing moves to turn 106, well inside 192 files; **file-only crossing, so the real onset is earlier**
(same caveat as TB-PLAN §2). F is not printed by `--measure` and is therefore **UNVERIFIED for the new shape**;
the run's phase-0 gate must compute it from the engine tokenizer before prompt 1, as TB-PLAN §8.0 requires
(`F < 60000 < C`).

Reproduce: `python3 tools/gen-tb-fixture.py --out <tmp> --files 192 --rows 150 --seed 7 --budget 60000 --measure`
and `--check` for byte identity. The generator refuses to write into a populated directory; use a fresh temp dir.

## 5. The prompt — verbatim from `design/past-experiments/TB-PLAN.md` §3, no reword

- **P1–P192**, one per file: *"Read `fixture/data-NN.csv`. Reply with one line per category that appears:
  `<category> <count> <sum> <min_id> <max_id>`. Nothing else."* No writes, no prose.
- **P193**, the reconciliation, in two parts: the aggregate artefact (`artefact.json`: sorted `categories` with
  count/sum/min_id/max_id, `top_category`, `top_file`, `grand_total`) and the **three exact-row lookups** into
  early files, chosen so the looked-up file sits far below the protected window at the final turn.

Changing the file count changes the fixture digest and the prompt count; **that is the re-preregistration this
card asks for.** No other part of the task shape changes.

## 6. Raised call ceiling — new prediction block, to be frozen before phase 3

| # | quantity | old (TB-PLAN) | new (this run) | basis |
|---|---|---|---|---|
| P1 | API calls per run | 105 predicted, **150 ceiling** (49 prompts) | **450 ceiling** (193 prompts) | ~2.3 calls/prompt observed in the Hermes 12-prompt bundle (36 tool files / 12 prompts); 193 × 2.3 ≈ 444, rounded up. Re-measure on the first three OpenCode prompts and freeze before phase 3 |
| P1b | prompts per run | 49 | **193** | 192 files + 1 reconciliation |

Everything else in TB-PLAN §7 is **suspended for this run**, not re-predicted: P2–P17 are paging quantities and
this harness has no engine. P18 (per-reply accuracy) and the lookup scores are the measures this run can take.

## 7. Phases, stops, checkpoints

| phase | cost | work | stop when | checkpoint |
|---|---|---|---|---|
| 0 | $0 | fixture 192×150 generated + `--check`; C and F measured; checker `--per-reply` on a known-good 8/8 reply; prompt list = 193; dry run writes nothing | any perturbation passes; F ≥ 60000; prompt list ≠ 193 | numbers + owner preregistration signed |
| 1 | $0* | **3 prompts** (P1–P3) on one OpenCode session; capture export; `tb-check --per-reply` | fewer than 2 of 3 exact; any billed token; tool refusal | per-prompt call count → freeze the 450 ceiling |
| 2 | $0* | full P1–P192 + P193, one session, raised ceiling | hard stops (§8) | reply ledger (192 replies + artefact + 3 lookups) |
| 3 | $0 | offline: `tb-check <fixture> artefact.json` + `--per-reply` + lookup scoring + schema validation of the exported trace | a capture fails to parse | per-reply exact/tuple coverage/lookup scores |
| 4 | — | **decision only**: if completeness passes, preregister a *Hermes* paged cell on this shape; no cell here | — | GO / NO-GO on the shape |

`*` declared zero-cost on this route; any provider receipt or billed delta is a hard stop, not an explanation.

## 8. Hard stops

A prompt past the timeout; repeated "does not exist" tool errors; auth 401/429; any charge; call count past the
frozen ceiling; NO RECORD (no exported session); a second session serving the run; a trace that fails
`spec/rfc-0.1/validate_schema_v0_1.py`. A refusal, timeout, or billed token is a **result to record**, not a
prompt to retry until green.

## 9. What must be true before prompt 1 (preconditions)

1. **DONE 2026-11-16.** Owner authorized this card's re-preregistration (fixture digest
   `36561425bf57ac156def80a7653ebceccb9a55b24f3c475f585370040156fbec`, 193 prompts, provisional 450 ceiling);
   `reports/RR-TBAUTH-20261116.md`.
2. The OpenCode session driver is shown in a dry run: `opencode run --session <id> --model … "<prompt>"` for
   P1–P3, with `opencode session export <id> --sanitize` producing a parseable reply ledger.
3. The fixture's `F < 60000 < C` gate is printed from the engine tokenizer for the 192×150 shape.
4. The reply parser handles host framing and fused tuples (`tools/tb-check.py::parse_reply`, fixed in `e948b5c`
   and `9f3ee6e`); the known-good reply scores 8/8.
5. The trace surface is identified: if `@ctxvm/opencode` is wired for this run, state whether it emits a capture;
   if it is not wired, say so — **do not present an unwired run as a traced one** (`~/.config/opencode/opencode.jsonc`
   has no `plugin` entry as measured 2026-11-16).

## 10. Out of scope

No cost or saving claim; no model-output determinism; no paged-arm or H3/H4 comparison; no change to
`design/past-experiments/TB-PLAN.md`, the corpus, the specs, `packages/**`, or `tools/**` (this card proposes, it edits nothing
outside its own bytes). No cell until the shape passes and a Hermes paged cell is preregistered.

## 11. Verification of this card

- `wc -c` on this file; LOG row has exactly four pipes.
- Gate re-run during the review of this card: `bash tools/run-ci.sh` rc=0, **ALL GATES GREEN** (2026-11-16,
  `/tmp/opencode/20261116-plan-ci.log`); recorded in `RR-TBOPEN-20261116.md`.
- `bash tools/check-handoff.sh` → ALL PASS; `bash tools/git-hygiene.sh` → OK.
