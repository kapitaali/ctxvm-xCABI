# T-B — the second task shape (revision 2): plan of record, preregistered before any cell

**Status:** plan, not run. No cell booked. Nothing here authorises a paid call.
**Revision 2 (2026-11-16), reviewer round.** §0b records what the reviewer found, what was confirmed against
the repo, and what was refused. The reviewer read this plan and the runtime code, not `T-B.md`, the generator
or the captures; three of its findings were verified here before being accepted.
**Supersedes:** `design/w8-tasks/T-B.md` as a *runnable* design (artefact schema, fixture format and
anti-search argument survive; prompt shape and size do not). Precedent: `T-A-v2.md` superseded `T-A.md`.

---

## 0. Why T-B cannot be run as written

**Blocker 1 — one prompt is one turn, and the keep law is turn-granular.** `T-B.md` is a single prompt; the
agent makes ~22 calls inside one user turn. The engine protects `protect_first_n=3` + `protect_last_n=6` turns
+ system prompt + last user prompt + open tool call, so on a one-turn session the protected set is the whole
request and `_plan` returns early at any budget (`design/W8-CLOSURE-20261110.md` claim 1: 9 selections, 0
evictions, peak 63,246 at 24,000).

**Blocker 2 — T-B's arithmetic is inherent, and arithmetic prompts time out.** T-A v1's counting prompt timed
out at 180 s on nvidia and sat silent for 283 s on longcat; `T-A-v2.md` removed the counting for that reason.
T-B cannot remove it, so it is **split**: many small per-file units plus one reconciliation.

**Blocker 3 (new, and the most serious) — the obvious shape does not test accuracy at all.** The engine's
units are tool-result pages (`_classify` pairs a tool call with its result); `_assemble` drops the result and
rewrites out its producing call message, while **assistant prose is scaffold and is never dropped**. Verified
on real bytes: every entry in a 0.13.21 capture's `evictedPages` is a `tool:read_file(…)` ref, with no
assistant text among them. A design whose final prompt needs only the model's own earlier replies therefore
cannot be hurt by paging — the inputs it needs are exactly the ones the policy keeps. T-A v2 has the same
dead-weight property; T-B v1 inherited it.

---

## 0b. The reviewer round

| # | Finding | Verdict here | Evidence |
|---|---|---|---|
| 1 | The shape cannot test accuracy; per-file replies are kept | **accepted** | `context_engine._classify` / `_assemble`; a 0.13.21 capture's `evictedPages` are all `tool:` refs |
| 2 | 40 B/row is ~2.5× too high | **accepted** | a row `1234,epsilon,-500` is 18 B; measured 48×600 = 431 kB |
| 3 | At 20 files the enlarged fixture pushes the protected floor over the budget | **accepted** | F ≈ 5.5k + 9S + 2k; at S ≈ 5.85k, F ≈ 60k against a 60,000 budget ⇒ guaranteed NO-OP |
| 3b | "floor" is used for two different quantities | **accepted** | vocabulary fixed: **C** content total, **F** protected floor |
| 4 | Final correctness multiplies per-file accuracy (0.97²⁰ ≈ 54 %) | **accepted, stronger than stated** | with 48 replies 0.97⁴⁸ ≈ 23 % — so the artefact cannot be the gate |
| 5 | n=1 while free reruns go unused | **accepted** | the prereg promised R=3 alternating; free tier makes it $0 |
| 6 | A one-prompt diagnostic cannot show engagement | **accepted** | the first turns are protected; engagement is a phase-3 fact |
| 7 | P9 and the cost bracket are too tight | **accepted** | P9 widened; cost bracket 0.15–0.45 |
| 8 | Canonical bytes must not fail a cell | **accepted** | the 2026-11-09 parsed-equality ruling; bytes are an observation |
| 9 | The resume key needs more than the fixture digest | **accepted** | plugin build, profile config digest and model id added |
| 10 | H1 (engagement) is already shown | **accepted — the claim moves** | cell-02, cell-03 and the S3 scorer; §1 now tests refetch and per-turn accuracy |
| 11 | My "$1.4075 spent" is superseded | **accepted; my error** | `RR-SPEND-VERIFY-20261110.md`: W8 cost **$7–9**; the provider billed **$7.05–7.14** on the day; the $1.43 table was a short hand ledger |
| 12 | W8B's "0 evictions" may be instrument-blind | **accepted, confirmed** | W8B ran on plugin **0.10.12**; `src/plugin.py:519` there emits `"evictedTokens": 0` as a literal. The reporting arrived in `1de060c` (2026-11-11 20:43, 0.12.2 → **0.13.0**), days later |

**Consequence of #12, applied here:** §2 no longer cites W8B's NO-OP as evidence that resident met the budget.
Those verdicts are instrument-blind and support no residency claim in either direction. If the W8B closure
document still asserts them as measurement, that is an erratum owed by the lane that owns it, not by this plan.

---

## 1. What is being tested

Engagement is settled (cell-02 free, cell-03 paid: evictions witnessed, request held at the budget).
Re-proving it on a new shape is not worth a card. This card asks what the shape can actually answer:

| # | Hypothesis | Falsified by |
|---|---|---|
| **H3 refetch** | Paging turns a revisit into a **hard fault**: the model re-reads an evicted file at a measurable token cost, and still answers | the lookup needs an evicted page, yet the paged arm answers correctly **without** re-reading, or re-reads no more than the control |
| **H4 accuracy** | Per-turn accuracy is unaffected by paging at this budget | the paged arm's graded per-reply accuracy falls more than 15 pp below the control's |

Both are answerable on the free tier. Cost is **not**: it needs receipts, so it needs phase 4.

---

## 2. Fixture, and the two numbers that decide whether this can fire

Vocabulary, fixed: **C** = total fixture content tokens; **F** = the engine's protected floor
(≈ system + 9 protected files + scaffold); **budget** = 60,000.

Paging can act only when **F < budget < resident**. A fixture whose per-file size pushes F over the budget is
a guaranteed NO-OP however large C grows — which is what happens if the file count stays at 20 while the rows
grow. So the lever is the **number of files**, not their size.

**Measured** (`tools/gen-tb-fixture.py --measure` (see `tools/gen-tb-fixture.py`), the engine's own tokenizer):

| candidate | S (tok/file) | C | C/budget | crossing | F | verdict |
|---|---|---|---|---|---|---|
| **48 × 600 rows (chosen)** | ≈2,247 | **107,867** | **1.80×** | turn **27** (file-only) | ≈**27.7 k** | 32 k of droppable room |
| 36 × 900 | ≈3,364 | 121,122 | 2.02× | turn 18 | ≈35.8 k | 900 rows of arithmetic per prompt |
| 60 × 450 | ≈1,687 | 101,236 | 1.69× | turn 36 | ≈22.9 k | ~121 calls brushes the 150 ceiling |
| 20 × 1,400 | ≈5,247 | ≈105 k | 1.75× | turn 11 | ≈**54.7 k** | F close to the budget; one more file size step and it is a NO-OP |

The choice prefers **many small files over few large ones**: S sets F, and per-prompt workload sets the
timeout risk. Crossing is computed from *file* tokens only; the model's replies add resident mass, so the real
onset is **earlier** than 27 — the estimate errs toward more pressure, not less.

Fixture spec (unchanged, F5-pinned): 48 files `data-01.csv`…`data-48.csv`, header `id,category,value`, 600
data rows, ids 1–9999 unique per file, 8 fixed categories, values −500…500, no quoting, LF endings, seed 7.
Generator `tools/gen-tb-fixture.py`; `--check` re-derives byte-identically; digest
`f56f61c75e3b40636c646176307041e2b9941f0cdeffc5cd8c0d9431f303d6a8`.

T-B.md's "≈60,200 tokens" was a hand estimate at 40 B/row and is off by about 2.5×; **C is measured, never
declared**, and F is computed from it, never assumed.

---

## 3. Task shape (v3): per-file units, then a reconciliation that *revisits*

- **P1–P48**, one per file: *"Read `fixture/data-NN.csv`. Reply with one line per category that appears:
  `<category> <count> <sum> <min_id> <max_id>`. Nothing else."* No writes, no prose.
- **P49**, the reconciliation, in two parts:
  1. the aggregate artefact (`T-B.md:25-37`: sorted `categories` with count/sum/min_id/max_id, plus
     `top_category`, `top_file`, `grand_total`) written to `artefact.json`;
  2. **three exact-row lookups into early files** — *"give the `category` and `value` of the row with `id` = X
     in `data-NN.csv`"* — chosen so that `data-NN`'s result sits far below the protected window at turn 49.

Part 2 is the fix for Blocker 3. A reply carries per-category aggregates, not individual rows, so the lookup
cannot be answered from the model's own earlier prose and cannot be inferred from the fixture's construction.
A dropped page makes the answer wrong; a re-read makes it right at a measurable cost — the first honest
refetch measurement this project can take.

---

## 4. Checker and per-reply scoring

`tools/tb-check.py <fixture-dir> <artefact>`: both paths as arguments, **refuses defaults**, prints
`checker: fixture=<path> artefact=<path>` on PASS, **recomputes** from the fixture bytes (never a stored
expected file), exit 0/1/2.

- **Parsed equality is the gate**; canonical bytes are reported as an observation and never fail a cell
  (2026-11-09 ruling).
- **Six perturbations must be shown red** in phase 0: one `count`, one `sum`, `top_category`, two keys swapped,
  `min_id` off by one, trailing newline removed.
- **`--per-reply`**: for each of P1–P48, recompute that file's eight `category → (count, sum, min_id, max_id)`
  tuples and score the reply exactly. This is the measurement H4 needs, and it does not multiply out.
- **Lookup scoring**: the three exact rows are checked one by one.

---

## 5. Arms, profiles, model, budget

| Item | Value |
|---|---|
| Control | `~/.hermes/profiles/w8cp-naive` — `context.engine: compressor`, toolsets `[file]` |
| Treatment | `~/.hermes/profiles/w8cp-paged` — `context.engine: ctxvm`, `budgetTokens: 60000`, toolsets `[file]` |
| Profiles | reused, never created (the runner refuses; owner rule) |
| Model | free tier first; phase 1b decides whether it can do the arithmetic at all |
| Budget | 60,000, one direction only: if resident never exceeds it, **enlarge the file count**, never lower the budget |
| Paid rates (phase 4) | the W8C row: input 0.10–0.13/1M, cached 0.01/1M, output 0.50/1M |

---

## 6. Runner and the resume key

`tools/w8b-run.py --task tb`: fixture glob `data-*.csv`, the 49-prompt list, checker path, artefact name. One
runner, two shapes — the arm isolation, key sync, preflight and bundle logic are already verified there.

The cell key carries **four** digests: fixture (sha256 over sorted per-file hashes), **plugin build**
(`PLUGIN_VERSION`), **profile config digest** (both arms), and **model id**. A key on the fixture alone marks
a cell done after an engine or model change — the 33→13 rewrite lesson applied to the other three axes.

---

## 7. Prediction block (draft after phase 0, frozen before phase 3)

| # | quantity | unit | measured against | predicted | bracket |
|---|---|---|---|---|---|
| P1 | API calls per arm | calls | `sessions.api_call_count` | 105 | 85–130 (150 = CEILING) |
| P2 | control crossing 60,000 | turn | control `turn.render.prefix.approxInputTokens` | 24 | 22–28 |
| P3 | engine lag | turns | first non-zero paged `evictedTokens` − P2 | 2 | 1–3 |
| P4 | onset | turn | first non-zero paged `evictedTokens` | 26 | 23–31; none ⇒ **NO-OP outcome** |
| P5 | net request reduction | tokens | Σ over turns (control − paged `approxInputTokens`) | ≈1.6 M | 0.8–2.5 M |
| P6 | per-turn re-drop sum | tokens | Σ paged `turn.render.evictedTokens` | ≈2.2 M | 1.2–3.2 M |
| P7 | final-turn request ratio | ratio | paged ÷ control, last turn | 0.60 | 0.50–0.70 |
| P8 | cache-read share, control | ratio | `call.meta.providerUsage` | ≥85 % | 75–98 % |
| P9 | cache-read share, paged | ratio | same | 60 % | **55–80 %** (cell-03's receipts imply ≈72 %) |
| P10 | artefact, both arms | verdict | `tools/tb-check.py` | PASS parsed-equal | observation, **not** the gate |
| P11 | control evictions | tokens | control capture | **exactly 0** | non-zero ⇒ INSTRUMENT-BUG |
| P12 | selections | count | session-keyed sidecar | control 0, paged > 0 | — |
| P13 | plan reason, paged | calls | `plugin.enginePlanTally` | ≥15 `evicted` | 10–25 |
| P14 | plan reason, control | calls | same | 0 `evicted` | exactly 0 |
| P15 | plan/eviction agreement | count | tally vs `callSizes` rows with `after < before` | equal | mismatch ⇒ INSTRUMENT-BUG |
| P16 | **refetch on the lookups** | faults | `page.fault`, source `tool_recall`, on the three looked-up files | paged ≥2 of 3, control 0 | 0 ⇒ H3 unproven |
| P17 | **lookup answers** | correct/3 | checker recomputation | paged ≥2, control 3 | — |
| P18 | **per-reply accuracy** | ratio | `tb-check --per-reply` | paged ≥ control − 5 pp | a drop > 15 pp falsifies H4 |
| P19 | dollar ratio (phase 4) | ratio | receipt-priced | 2.1 | 1.5–3.5 |
| P20 | pair cost (phase 4) | USD | receipt-priced + billed delta | 0.30 | **0.15–0.45** |

---

## 8. Preconditions — any failure stops the run before prompt 1

```
0  fixture generated; --check byte-identical; C, S and F printed with the engine tokenizer;
   gate: F < 60000 < C
1  checker PASS on a correct artefact; six perturbations FAIL; --per-reply scores a known-good reply 8/8
2  plugin >= 0.13.24 on disk AND loaded (installed mtime vs gateway start, plus a flush after the restart
   attesting 0.13.24 — a manifest reading is not a loaded-build reading)
3  THE INSTRUMENT IS NOT BLIND: one diagnostic capture carries plugin.enginePlan with a reason in the closed
   set and a non-null enginePlanTally. Without this, P13–P15 measure nothing — the W8B lesson, applicable
   because that field was a literal zero for four versions
4  probe --arm both -> control 200000/default + 0 selections; paged 60000/settings + > 0
5  exactly one gateway serves both arms (two = stop; attribution is runner-side)
6  --dry-run writes nothing: profile config digests identical before and after
7  free-tier credential valid against the provider's own endpoint, not merely present
```

---

## 9. Phases, each with a stop and a checkpoint

| Phase | Cost | Work | Stops when | Checkpoint |
|---|---|---|---|---|
| 0 | $0 | generator, fixture, C/S/F, checker + six reds + `--per-reply`, runner `--task tb`, dry-run | a perturbation passes; F ≥ 60,000; the known-good reply scores < 8/8 | **numbers, owner reads** |
| 1 | $0 | capability probe, 2 prompts, paged arm | no `read_file` in the trace | probe verdict |
| **1b** | $0 | **three files on the NAIVE arm, replies scored** | fewer than 2 of 3 replies exact | **shape-vs-model verdict: a control that cannot do the arithmetic buys no paged cell** |
| 2 | $0 | attestation only: one prompt per arm; assert P11/P12/P14 and a plan reason | `enginePlan` absent or mistyped | instrument verdict |
| 3 | $0 | **R=3 interleaved rounds** of the full pair, plus one naive-vs-naive pair for variance | a hard stop (§10) | the cell set or its NO-OP / ARTEFACT-FAIL verdict |
| 4 | **owner gate**, cap $1.00 | one paid pair for receipts | 401/429, unexpected charge | the dollar claim or its refusal |
| 5 | $0 | offline verify (coverage_check + replay + checker) before any number is written | a capture fails to parse | RR + ledger + LOG + day section |

Phase 3 runs **three rounds** because the preregistration promised R=3 alternating and the free tier makes the
replay costless; one pair cannot separate an effect from sampling noise.

---

## 10. Verdict taxonomy

NO RECORD (no capture — not evidence) · DATA-INVALID (multiple sessions, shell/code tool, sealed-part read,
budget mismatch, coverage or replay non-zero — out of the denominator) · **NO-OP** (sound record, zero
evictions — an outcome, stays in) · ARTEFACT-FAIL · CEILING · CELL (engaged, held, and the claim's own
condition met).

Hard stops: prompt past the timeout cap; repeated `does not exist` errors; 401/429; any charge on a free run;
NO RECORD on either arm; context refusal near 90k (reduce the file count, never the budget).

---

## 11. What this cannot prove

- One model, one shape: k=2 with T-A v2, against the six the prereg named.
- Free-tier phases give mechanics **and** accuracy; they give no dollar claim.
- A correct artefact is not a paging result: with 48 replies the final check multiplies out (0.97⁴⁸ ≈ 23 %),
  which is why P16–P18 carry the claim and P10 does not.
- Truncated search dumps remain a route (`REVIEW.md` F6): classify a failure as *truncated data* or
  *arithmetic error* before reporting it as a result about the model.

---

## 12. Deliverables

`tools/gen-tb-fixture.py` (landed), `tools/tb-check.py` (+ `--per-reply`, + `--prove`; landed
2026-11-16 — six perturbations and a trailing-newline observation proved, and its arithmetic cross-checked
against an independent awk implementation on all eight categories), `tools/w8b-run.py --task tb` (**still
owed**), a prediction block `reports/TB-BLOCK-CELL01-<date>.md` carrying the phase-0 numbers, a card report
`reports/RR-TB-<date>.md`, one LOG row, a day-file section, and the verdict either way. **A NO-OP or a
falsified H4 is the deliverable, not a failure of the card.**
