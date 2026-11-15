# T-B v2 — the second task shape: plan of record, preregistered before any cell

**Status:** plan, not run. No cell has been booked. Nothing here authorises a paid call.
**Supersedes:** `design/w8-tasks/T-B.md` as a *runnable* design (its artefact schema, fixture spec and
anti-search argument survive verbatim; its prompt shape does not). Precedent: `T-A-v2.md` superseded
`T-A.md` the same way on 2026-11-11.
**Why now:** the W8 family has one task shape (`T-A v2`). The prereg promised six templates
(`design/w8-run-plan.md:53`, `08-HANDOFF.md:1487` "k=6 … R=3 alternating"); one ran. T-B was designed,
reviewed (finding F5 fixed in `design/w8-tasks/REVIEW.md:60`) and never scheduled. A second shape is what
turns one measurement into a replication.

---

## 0. Why T-B cannot be run as written — two measured blockers

**Blocker 1 — one prompt is one turn, and the keep law is turn-granular.** `T-B.md` §Task text is a single
prompt; the agent makes ~22 calls inside one user turn. The engine protects `protect_first_n=3` +
`protect_last_n=6` turns + system prompt + last user message + open tool call, so on a one-turn session the
protected set is the whole request and `_plan` returns early at **any** budget. Already measured:
`design/W8-CLOSURE-20261110.md` claim 1 — 9 selections, 0 evictions, peak 63,246, at 24,000. A single-prompt
T-B would reproduce W8's inertness and measure nothing about paging.

**Blocker 2 — T-B's arithmetic is inherent, and arithmetic prompts time out.** `T-A v1`'s counting prompt
timed out at 180 s on nvidia and sat silent for 283 s on longcat; `T-A-v2.md` removed the counting questions
for that reason. T-B *cannot* remove arithmetic — counts and sums are the task. So the arithmetic must be
made small **per request** rather than dropped.

**Consequence, and the whole design change:** 20 per-file prompts + 1 reconciliation prompt. Multi-turn
restored (the keep law can bite), arithmetic bounded to ~32 numbers per request, and the final answer still
needs every earlier turn — which is exactly the content paging would drop.

---

## 1. What is being tested

| # | Hypothesis | Falsified by |
|---|---|---|
| **H1 mechanism** | On a second task shape, the paged arm at a budget below resident engages and holds the request, while the artefact stays correct | `enginePlan.reason` never reads `evicted` on a call whose `residentTokens > budgetTokens`, or the artefact differs between arms |
| **H2 cost** | Engagement costs more dollars than the control, as it did on T-A v2 (2.11×) | a receipt-priced dollar ratio < 1.0 on the paid pair |

H1 is answerable on the free tier. **H2 is not** — it needs provider receipts, so it needs the paid pair
(phase 4). No dollar claim may be made from a free-tier run.

---

## 2. Fixture (`tools/gen-tb-fixture.py`, to be written in phase 0)

| Item | Value |
|---|---|
| Files | 20 × `data-01.csv` … `data-20.csv` |
| Header | exactly `id,category,value` |
| Rows | 300 data rows per file |
| `id` | integer 1–9999, unique within a file, may repeat across files |
| `category` | one of `alpha beta gamma delta epsilon zeta eta theta` |
| `value` | integer in [-500, 500] |
| Format | no quoting, no embedded commas, no padding, LF endings (F5, `REVIEW.md:60`) |
| Seed | `7`, single documented generator, `--check` re-derives the same bytes |

**Residency target — the number that decides whether this experiment can fire at all.** Paging can only act
when `floor < vBudget < resident`, and T-B's declared fixture is ≈60,200 tokens against a 60,000 budget — which
puts resident and budget in the same place and invites W8B's outcome (43 selections, 0 evictions, at 70k and
90k). So the fixture is sized to a **residency curve**, not to a floor:

- target: cumulative resident crosses 60,000 at **turn 10–13** of 21, so the arm has ~8 turns of pressure;
- that needs total fixture tokens ≈ **1.6–2.0 × budget**, i.e. 96,000–120,000 tokens ≈ 384–480 kB of CSV;
- 20 files × 300 rows ≈ 240 kB ≈ 60k tokens is therefore **too small** and must be enlarged (≈480–600 rows per
  file, or 30+ files) — decided by phase 0's measured curve, not by this paragraph.

**Measured 2026-11-15 (`tools/gen-tb-fixture.py --measure`, engine tokenizer):** 48 files × 600 rows,
seed 7 — 431 kB, **107,867 tokens = 1.80× budget**, residency crosses 60,000 at **turn 27 of 48**, leaving
**22 pressure turns**, and ≈97–110 calls against the 150 ceiling. Rejected in the same measurement: 36 × 900
(2.02×, crossing at turn 18, but 900 rows of arithmetic per prompt) and 60 × 450 (1.69×, crossing at turn 36,
but ~121 calls brushes the ceiling). The choice prefers **smaller arithmetic per request** over a shorter run,
because arithmetic is what timed out on T-A v1, while a long free-tier run costs only time.

The curve counts *file* tokens only, so the real crossing is earlier than turn 27 (the model's own replies and
call messages add resident mass) — the estimate errs toward more pressure, not less.

**The floor is measured, never declared.** `T-B.md:57` computes 60,200 tokens by hand at 40 B/row; the
generator's real bytes decide. Phase 0 prints per-file bytes, the total, and tokens under the engine's own
`apx4-char` rule (and `tiktoken` if available). Gate: **floor ≥ 45,000 tokens** and **floor + scaffold <
budget**. A fixture that fails either is enlarged before any prompt, and the number that decided it goes into
the block.

---

## 3. Task shape (T-B v2)

- **P1–P20**, one per file: *"Read `fixture/data-NN.csv`. Reply with one line per category that appears:
  `<category> <count> <sum> <min_id> <max_id>`. Nothing else."* — no writes, no prose.
- **P21**, reconciliation: restate the `artefact.json` schema from `T-B.md:25-37`, and require the aggregate
  over all 20 files: `categories` (sorted) with `count/sum/min_id/max_id`, plus `top_category` (largest sum,
  tie-break name ascending), `top_file` (most rows in `top_category`, tie-break basename ascending),
  `grand_total`. Write `artefact.json`.
- Prompt digests for all 21 go into the prediction block, so a changed prompt invalidates a resumed run.
- **The retention dependence is the point:** P21's numbers exist only in P1–P20's replies. If paging drops an
  early reply, P21 must either be right from what survived (then the arm's reduction is real) or wrong (then
  the artefact fails and the cell is an ARTEFACT-FAIL outcome, not a void).

---

## 4. Checker (`tools/tb-check.py`, phase 0)

1. Takes `<fixture-dir> <artefact>` as arguments and **refuses to run on defaults**; prints
   `checker: fixture=<path> artefact=<path>` on the PASS line.
2. **Recomputes** the expected result from the fixture bytes — no stored expected file, no author-side
   reference copy. A checker that agrees with its own reference proves nothing.
3. Compares exact: parsed equality, then canonical bytes (2-space indent, single trailing newline, sorted
   category keys).
4. Prints `PASS` / `FAIL: <reason>`, exit 0 / 1 / 2.

**Perturbation set — all six must be shown red in phase 0, transcript kept in the run bundle:** one `count`
changed; one `sum` changed; `top_category` changed; two category keys swapped; `min_id` off by one; trailing
newline removed.

---

## 5. Arms, profiles, model, budget

| Item | Value |
|---|---|
| Control | `~/.hermes/profiles/w8cp-naive` — `context.engine: compressor`, toolsets `[file]` |
| Treatment | `~/.hermes/profiles/w8cp-paged` — `context.engine: ctxvm`, `budgetTokens: 60000`, toolsets `[file]` |
| Profiles | **reused, never created** (the runner refuses to create them; owner rule) |
| Model | free-tier candidate first (precedent: nous free tier via the owner's gateway). The capability probe decides; a model that cannot drive `read_file` never gets a cell |
| Paid rates (phase 4 only) | the W8C row, reused not invented: input 0.10–0.13/1M, cached 0.01/1M, output 0.50/1M |
| Budget | **60,000 provisional** — precondition is floor + scaffold < 60,000 < resident at late turns |

Budget rule, one direction only: if `perCall.residentTokens` never exceeds 60,000 the task is too small and
the cell is void at turn 0 — **enlarge the fixture, never lower the budget**. The residency target in §2 is how
the fixture is enlarged *before* the run instead of after it. A budget that can shrink after
the fact is not preregistered.

---

## 6. Runner change

Extend `tools/w8b-run.py` with `--task {ta2,tb}`: fixture glob (`part-*.txt` / `data-*.csv`), the 21-prompt
list, the checker path, and the artefact name. One runner, two shapes — not a fork, because the arm
isolation, key sync, preflight and bundle logic are already verified there and a second copy would rot.

The resume key gains a **fixture digest** (sha256 over sorted per-file hashes). The 33→13 part rewrite taught
this: a cell keyed on `(round, task, arm)` marks itself done after its fixture changed, and the next pair then
compares a paged run on the new fixture with a naive run on the old one.

---

## 7. Prediction block (committed twice: a draft after phase 0, frozen before phase 3)

Values marked `?` are filled from phase 0's measurements — the floor and resident are not yet measured for
this fixture, and inventing them is how a block becomes decoration.

| # | quantity | unit | measured against | predicted | bracket |
|---|---|---|---|---|---|
| P1 | API calls per arm | calls | `sessions.api_call_count` | 45 | 38–50 (50 = ceiling ⇒ CEILING outcome) |
| P2 | control crossing 60,000 | turn index | control `turn.render.prefix.approxInputTokens` | ? | ? ± 2 |
| P3 | engine lag | turns | paged first non-zero `evictedTokens` − P2 | 2 | 1–3 |
| P4 | onset | turn index | first non-zero paged `evictedTokens` | P2 + P3 | no non-zero turn ⇒ **NO-OP outcome**, never a void |
| P5 | net request reduction | tokens (sum over turns) | control − paged `approxInputTokens` | ? | wide; computed from P2/P4 |
| P6 | per-turn re-drop sum | tokens | sum of paged `turn.render.evictedTokens` | ? | ≤ P5 × (turns after onset) |
| P7 | final-turn request ratio | ratio | paged ÷ control at the last turn | 0.57 | 0.45–0.75 |
| P8 | cache-read share, control | ratio | `call.meta.providerUsage` | ≥ 85 % | 75–98 % |
| P9 | cache-read share, paged | ratio | same | ≤ 65 % | 35–80 % |
| P10 | artefact, both arms | verdict | `tools/tb-check.py` | PASS parsed-equal | PASS / FAIL |
| P11 | control evictions | tokens | control capture | **exactly 0** | non-zero ⇒ INSTRUMENT-BUG |
| P12 | selections | count | sidecar, session-keyed | control 0, paged > 0 | — |
| P13 | **plan reason, paged** | count of calls | `plugin.enginePlanTally` | ≥ 8 calls `evicted` | 4–14 |
| P14 | **plan reason, control** | count of calls | `plugin.enginePlanTally` | 0 calls `evicted` | exactly 0 |
| P15 | **plan/eviction agreement** | count | `enginePlanTally.evicted` vs calls with `after < before` in `callSizes` | equal | mismatch ⇒ INSTRUMENT-BUG |
| P16 | dollar ratio (**phase 4 only**) | ratio | receipt-priced per arm | 2.1 | 1.5–3.5 |
| P17 | pair cost (**phase 4 only**) | USD | receipt-priced + billed delta | 0.25 | 0.10–0.28 |

P13–P15 are only possible because `plugin.enginePlan` landed today (`RR-ENGINEPLAN-20261114`). On the old
build the onset had to be inferred from `resident` and `headroom` arithmetic; now the engine states it, and a
disagreement between the plan tally and the per-call sizes is an instrument bug rather than a mystery.

---

## 8. Preconditions — any failure stops the run before prompt 1

```
0  fixture generated; --check re-derives identical bytes; floor printed and ≥ 45,000
1  checker PASS on a correct artefact; all six perturbations FAIL (transcript in the bundle)
2  plugin ≥ 0.13.24 on disk AND loaded: installed mtime vs gateway start, plus a flush after the
   restart attesting plugin.version 0.13.24 (a manifest reading is not a loaded-build reading)
3  probe --arm both -> control 200000/default + 0 selections; paged 60000/settings + > 0 selections
4  exactly one gateway serves both arms (two = stop, attribution is runner-side)
5  --dry-run writes nothing: hash both profile configs before and after
6  workspace fresh: 20 CSVs present, artefact.json absent, no stale .partial.jsonl in the trace pool
7  free-tier credential valid against the provider's own endpoint, not merely present
```

---

## 9. Phases, each with a stop and a checkpoint

| Phase | Cost | Work | Stops when | Checkpoint |
|---|---|---|---|---|
| 0 | $0, no model call | generator + fixture, checker + perturbation reds, floor measurement, runner `--task tb`, dry-run | a perturbation passes; floor < 45,000 | **numbers here, owner reads before phase 1** |
| 1 | $0 | capability probe, 2 prompts, paged arm | no `read_file` in the trace | **probe verdict, owner reads** |
| 2 | $0 | diagnostic: 1 prompt per arm at 60,000 | P12/P14 fail (no engagement, no control silence) | **instrument verdict** |
| 3 | $0 | full pair, 21 prompts | any hard stop in §10 | **the cell or its NO-OP/ARTEFACT-FAIL verdict** |
| 4 | **owner gate**, cap $1.00, expected $0.25 | paid replicate pair for receipts | 401/429, any unexpected charge | **the dollar claim or its refusal** |
| 5 | $0 | verify offline (coverage_check + replay + checker), re-verify before any number is written | a capture fails to parse | RR + ledger row + LOG row + day section |

Phases 0–3 are free. Nothing in this plan spends without phase 4's separate gate.

---

## 10. Verdict taxonomy (from `references/verdict-taxonomy.md`)

| Verdict | Meaning | Counts? |
|---|---|---|
| NO RECORD | no capture, no sidecar | no — not evidence |
| DATA-INVALID | multiple sessions, shell/code tool used, successful sealed-part read, budget mismatch, coverage/replay non-zero | no — stays out of the denominator |
| NO-OP | sound record, `evictedTokens == 0` | **yes — an outcome** |
| ARTEFACT-FAIL | paged or control produced a wrong artefact | yes |
| CEILING | hit the call ceiling | yes |
| CELL | engaged, request held, artefact correct | yes |

Hard stops mid-run: a prompt exceeding the timeout cap; repeated `does not exist` tool errors; auth 401/429;
**any charge on a free-tier run**; NO RECORD on either arm; context refusal near 90k (reduce parts, never
shrink the budget).

---

## 11. What this cannot prove

- One model, one task shape. Two shapes is k=2, not the six the prereg named.
- Free-tier phases give **mechanics only**; the 2.11× cost result does not transfer without phase 4's receipts.
- The task is an aggregation exercise: a model that is bad at arithmetic fails for a reason unrelated to
  paging, which is why the control arm's artefact result gates the claim (a control FAIL means the shape is
  too hard for this model, not that paging hurt).
- Truncated search dumps remain a route (`REVIEW.md` F6): a failure must be classified as *truncated data* or
  *arithmetic error* before it is reported as a result about the model.

---

## 12. Deliverables

`tools/gen-tb-fixture.py`, `tools/tb-check.py`, `tools/w8b-run.py --task tb`, a prediction block
`reports/TB-BLOCK-CELL01-<date>.md`, a card report `reports/RR-TB-<date>.md`, one LOG row, a day-file
section, and the verdict either way. **A negative or NO-OP result is the deliverable, not a failure of the
card.**
