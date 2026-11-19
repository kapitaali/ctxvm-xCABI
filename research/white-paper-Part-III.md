# Part III — What a context trace offers a self-improvement loop

**Author:** Kapitaali · **Version:** 1.1, 18 November 2026 · **Status:** draft for review
**Part I:** *Virtual memory for LLM agent context: the xCABI standard and the ctxvm engine.*
**Part II:** *What a context trace can and cannot show about AI safety.*

---

## Abstract

This paper asks what a context trace contributes to a self-improvement loop. The answer is narrow.
ctxvm does not train weights. It has no reward model and no access to model internals. It supplies the
input side: a portable record of the harness request, deterministic replay of the page-table
projection, and page-level counterfactual intervention with the provenance a causal claim needs.
The loop still needs a generator, an evaluator, a selector and an update step. ctxvm strengthens two
of them — the **evaluator** (a versioned view) and the **training-data selector** (causal labels from
page ablation). It does not strengthen the generator or the weight update. We describe six routes,
each with a mechanism, a changed object, a falsifier and an experiment. No route has been run.
Claims that rest on snippets are marked UNVERIFIED and carry no argument.

---

## 1. Scope and vocabulary

### 1.1 Defined terms

| Term | Meaning in this paper |
|---|---|
| Self-improvement | A loop that changes a system so a later version scores better on a held-out task. The change may be in weights, in a policy outside the model, or in data. |
| Loop | Generate, evaluate, select, update, repeat. |
| Changed object | The thing a route updates: policy, ranker, training data, evaluator or weights. |
| Page | A context unit with identity `(logical_ref, content_hash)`, kind and token count. |
| Intervention replay | A run that changes one thing in a recorded trace and calls the model again. The engine is deterministic; the model is not. |
| Monitor view | A versioned function of a trace **joined with its sources and the omission record**, giving the data a monitor sees (Part II §1.1). |
| Omission gap | A removal policy's dropped pages are not on the sealed v0 wire; the trace declares them full and they are absent from the request (Part II §2.4). |
| Flush-tail capture | A trace whose `page.declare` and `page.render` rows all precede its `turn.render` block, so a positional turn cut includes declarations from later turns. The derived table is then not turn-scoped (Part II §2.4). |
| Budget term | The cost part of a context objective. Without it, "keep everything resident" trivially minimises faults. |
| Noise floor | The answer-change rate between two unchanged runs. |

### 1.2 Evidence levels — Part II vocabulary

| Level | Meaning |
|---|---|
| **Read in full** | The whole paper was read. |
| **Abstract** | The abstract was read; body figures are not used. |
| **Snippet** | A search excerpt or summary was read. The claim is marked UNVERIFIED. |
| **Secondary** | A third party reports the claim. UNVERIFIED. |

Statuses are Part II's: Answered, Partly answered, Designed, Prototype-able, Blocked, Not found.
Every external claim carries its locator at first mention. An UNVERIFIED claim does not carry an argument.

---

## 2. The question and the short answer

**Question.** What can a ctxvm trace contribute to building a self-improving model?

**Short answer.** Use ctxvm as the measurement and data-generation layer around an existing loop:

1. Generate **causal labels** by page ablation. Start open-weight: leave-one-out on output
   probabilities is compute-only (Part II §12.1). Use a hosted model for behaviour, with a noise floor.
2. Use **fault events as a selection feature**, not as a standalone policy objective. Faults tell the
   ablation step which pages to test; they do not evaluate a new policy offline.
3. Version the evaluator. A view is a trace joined with its sources and the omission record. Two
   model versions can be scored against one view version.

ctxvm does not do the update. A team still trains a ranker, a policy, or a data selector. Part I §16
and Part II §10 bound what a trace can support.

---

## 3. Evidence base and method

### 3.1 Corpus and selection

The scientist list came from Anthropic's own pages and a third-party index. OpenAlex supplied
2,007 (scientist, paper) rows for 88 scientists. The source JSON declares a configured window of
2021-01-01 to 2026-12-31; observed paper dates run 2021-01-01 to 2026-11-12, the range reported
here. Deduplication by OpenAlex work id gave 1,495 works. PDF download succeeded for 1,064; 431
went to `lookup.txt` (433 lines including two header comments).
Text extraction with `pdftotext -layout` and a one-page reference per work produced a SQLite table
of 1,061 rows (`name | date | title | url | reference`). Three PDFs failed extraction.

A SQL lab-name search with a word-boundary filter returned 159 papers
(`ai-lab-paper-summaries.txt`). **Selection protocol for this paper:** from those 159, the author
picked 12 sources by relevance to learning loops — self-critique, ablation, process supervision,
search, monitoring and failure modes. This is a **purposive sample, not a systematic review**; the
pool was already skewed toward Anthropic-affiliated authors, and a reader cannot infer that the
choice was unbiased. Every cited source was then re-checked on arXiv for authors and date; the
four Abstract-level checks whose local extracts lacked a detected abstract are recorded in
`PART3-CITATION-CHECK-20261118.md`.

### 3.2 Lab counts

| Lab | Papers |
|---|---|
| Anthropic | 59 |
| OpenAI | 48 |
| DeepMind | 32 |
| — of which "Google DeepMind" | 22 (subset, not additional) |
| Google Brain | 6 |
| Apple | 9 |
| Hugging Face | 7 |
| Mistral | 5 |
| EleutherAI | 3 |
| Redwood Research | 4 |
| Amazon | 4 |
| Allen Institute | 3 |
| Cohere, Stability AI, IBM Research | 2 each |
| Meta AI, Microsoft Research, NVIDIA | 1 each |

Counts overlap; one paper may mention several labs. `59` is both the single-term SQL `LIKE` and
the word-boundary count over `title + reference` (§12 prints both; both measured 59 on 2026-11-18).
`research/datamining/datamining.json` holds concept-term OR-aggregates (for example `counterfactual`
= 80), not lab aggregates; the lab figures are single-term mention counts and lower bounds.

### 3.3 Limits

Author matching is noisy: 38 of 88 profiles lacked an Anthropic affiliation and spot checks found
wrong-person matches. That error produced two wrong author attributions in version 1.0 of this
paper, now corrected against arXiv. Several extractive references had no detected abstract; those
claims are now marked Snippet and carry no argument. The lab search finds mentions, not authorship.

---

## 4. What ctxvm provides

Part I §2–3 defines the wire; §3.8 the engine; §10 intervention replay; §12 monitor views.

| Capability | Mechanism | Value for a loop |
|---|---|---|
| Page identities and hashes | `page.declare` carries `(logical_ref, content_hash)`, kind, token count | Stable keys across runs and model versions |
| Deterministic derivation | The renderer derives the page table from events; same bytes give same projection on one machine and build | Reproducible baseline (scoped) |
| Fault events | `page.fault` with a source; meaning depends on surface | A selection feature, not a process ground truth (§4.1) |
| Token accounting | `turn.render` carries resident, evicted and headroom | Context pressure |
| Intervention replay | Remove, stub or replace a page; call the model again | Counterfactual label at page granularity |
| Noise-floor protocol | Baseline vs baseline; several samples per arm | Separates effect from sampling noise |
| Six-part provenance | Digest, intervention, sampling, model snapshot and date, harness versions, tokenizer | Reproducible, citable runs |
| Versioned views | Trace joined with sources and omission record | Comparable evaluator across versions |
| Export and diff | ODPS artifacts; `ctxvm diff` | Versioned data |

### 4.1 What the format does not record

- A trace holds identities and hashes, not page content.
- Rendering does not cause an answer. Only an intervention supports a causal claim.
- A hosted model is not deterministic at fixed settings. One draw is not an effect.
- Sealed v0 has no verb for a page removed without a stub (Part II §2.4).
- `turn.render.evictedTokens` is recorded but unchecked in v0 for removal policies (Part I §7).
- The paid paging cell cost 2.11× the control. No cost-saving claim (law 7).

---

## 5. What a loop needs

A loop has four parts. The update is the author's formulation, not a quoted source:

$$
M_{t+1} = U\bigl(M_t,\; E_t(G(M_t, D_t)),\; D_t\bigr)
$$

This equation gives a **taxonomy of three failure points**: the generator may produce no useful
variation; the evaluator may rank noise as signal; the update may change the wrong object.

### 5.1 Route-to-object map

| Route | Changed object | Type of contribution |
|---|---|---|
| A — fault-driven ablation selection | Training-data selector | Selects which pages to ablate |
| B — counterfactual page ablation | Page ranker / training-data filter | Ground-truth causal labels |
| C — trace-grounded critique | Context-use behaviour (in-session) | Critique on structure, not content |
| D — active selection | Training-data selector | Selects hard traces for labelling |
| E — versioned views | Evaluator | Comparable score across versions |
| F — harness summarisation | Context policy (harness-side) | Compresses the request |

### 5.2 Cited sources

| Source | Date, locator | Contribution | Level |
|---|---|---|---|
| Bai et al., *Constitutional AI* | 2022-12-15, https://arxiv.org/pdf/2212.08073 | Self-critique, revision, SFT, RLAIF | Abstract |
| Wu et al., *Recursively Summarizing Books* | 2021-09-22, https://arxiv.org/pdf/2109.10862 | Recursive decomposition with human feedback | Abstract |
| Lightman et al., *Let's Verify Step by Step* | 2023-05-31, https://arxiv.org/pdf/2305.20050 | Process supervision beats outcome supervision on MATH (78%); active learning helps | Abstract |
| Koh et al., *Tree Search for Language Model Agents* | 2024-07-01, https://arxiv.org/pdf/2407.01476 | Inference-time best-first search; +39.7% relative on VisualWebArena | Abstract |
| Zhong, Raghunathan, Carlini, *ImpossibleBench* | 2025-10-23, https://arxiv.org/pdf/2510.20270 | Spec/test conflict; a pass implies a shortcut | Abstract |
| Souly et al., *A StrongREJECT for Empty Jailbreaks* | 2024-02-15, https://arxiv.org/pdf/2402.10260 | A fixed judge; existing evaluations overstate success | Abstract |
| Najt, Toft, Tracy, Roger, Benton, *SLEIGHT-Bench* | 2026-05-15, https://arxiv.org/pdf/2605.16626 | 40 monitor attacks; 20 never caught at 1% FPR | Abstract |
| Deng et al., *OpenVLThinker* | 2025-03-21, https://arxiv.org/pdf/2503.17352 | Alternating SFT and RL beats either alone | Abstract |
| Scheurer et al., *Training LMs with Language Feedback* | 2022-04-29, https://arxiv.org/pdf/2204.14146 | Natural-language feedback; 100 human samples reach roughly human level | Abstract |
| Mindermann et al., *Prioritized training* | 2021-07-06, https://arxiv.org/pdf/2107.02565 | Goldilocks Selection; "just right" points beat hard/easy/uncertain | Abstract |
| Pan, He, Bowman, Feng, *Spontaneous Reward Hacking* | 2024-07-05, https://arxiv.org/pdf/2407.04549 | Self-refinement can hack a shared evaluator | Abstract |
| Pan, Jones, Jagadeesan, Steinhardt, *Feedback Loops* | 2024-02-09, https://arxiv.org/pdf/2402.06627 | Feedback loops cause in-context reward hacking | Abstract |

Self-improvement through context and memory, absent from version 1.0, is added at Snippet level
and carries no argument: *Reflexion* (Shinn et al., arXiv:2303.11366), *Self-Refine* (Madaan et al.,
arXiv:2303.17651), *STaR* (Zelikman et al., arXiv:2203.14465), *Self-Rewarding Language Models*
(Yuan et al., arXiv:2401.10020), *Voyager* (Wang et al., arXiv:2305.16291). All five improve without
weight updates in at least one variant. This is the region where a page substrate may fit; it is a
reading list, not evidence for a route. Level `Abstract` for Scheurer, Mindermann and both Pan
papers was re-checked against the arXiv abstract pages on 2026-11-18; see
`PART3-CITATION-CHECK-20261118.md`.

---

## 6. Routes

Each route states a mechanism, a changed object, inputs, output, cost and falsifier.

### Route A — Fault events as an ablation-selection feature

**Statement.** Use fault events and touch counts to choose which pages to ablate in Route B.

**Mechanism.** Faults are observed only under the logged policy. A new policy's faults need
counterfactual runs. So fault labels cannot evaluate a policy offline. Use them instead to stratify
the ablation sample: pages named by a `tool_recall` fault, or by an `identifier_scan` mention on a
non-resident page, are candidates. The objective must include the budget term
$\max_{\pi}\; I(\text{answer}; \text{pages}\mid\pi) - \lambda\,\text{tokens}(\pi)$; without
$\lambda$, "keep everything resident" trivially minimises faults. A control is required because
identifier-scan faults on rendered pages are close to definitional (Part I §17).

**Changed object.** Training-data selector for Route B. **Inputs.** Traces, touch counts, faults.
**Output.** A stratified ablation list. **Cost.** Compute; Route B's calls are separate.
**Falsifier.** Fault-stratified ablation does not beat matched random ablation at predicting answer
change on held-out pages.
**Evidence.** Part II §12.1 (touch ratio); Part I §4 and §17 (faults, definition). *Inference*.

### Route B — Counterfactual page ablation

**Statement.** Turn each page into a causal-importance label. This is the first step the repo can
run, because the open-weight arm costs compute only.

**Mechanism.** Open-weight primary: leave-one-out on output probabilities, as Part II §12.1 defines.
Hosted secondary: remove page $p$, call the model again, use several samples and a baseline-vs-baseline
noise floor. With three samples, a binary answer-change label takes four values and the noise floor
is equally coarse; use a binomial interval on the change rate, not a hard threshold. **One learned
object**: a page ranker / training-data filter. Ablation importance is not step correctness, so it
does not yield a process reward model.

$$
\Delta(p) = \frac{1}{n}\sum_{i=1}^{n} \mathbb{1}[a_i(\tau) \neq a_i(\tau\setminus p)],
\qquad \hat c(p) = \mathrm{BinInt}(\Delta(p), n, \alpha)
$$

**Changed object.** Page ranker / data filter. **Inputs.** Frozen traces; an open-weight model; a
hosted model for the secondary arm. **Output.** Causal labels at page granularity.
**Cost.** Open-weight: compute only. Hosted: about **1,300 calls**, ≈ **$11.37** at the repo's
blended $0.00861/request (`reports/W8-SPEND.md:82`):
$(20 \times 10 \times 3 \times 2) + (20 \times 3 \times 2) = 1{,}320$ calls.
**UNVERIFIED estimate**; check the receipt before quoting.
**Falsifier.** A ranker trained on ablation labels does not beat random ablation on held-out task
success. **Evidence.** Part II §12.1 defines this design; cross-reference it rather than duplicating
it. ContextCite (Cohen-Wang et al., arXiv:2409.00729, Abstract) is related work at sentence level.

### Route C — Trace-grounded critique for context use

**Statement.** Use the projection as critique input to change **context-use behaviour**, not answer
correctness.

**Mechanism.** Give the model its page table, faults, token totals and the request's estimated size.
Ask for a revision of the tool plan. The trace holds no content, so the critique can plausibly change
re-reads, faults and steps to finish; it cannot supply missing content. Measure those behaviours.
A wrong-answer corpus with traces, a constitution and an SFT cost are **not in the repo**; the weight
update is therefore Blocked (Part II status), and the route stays in-session.

**Changed object.** Context-use behaviour. **Inputs.** Traces, in-session critique. **Output.** A
critique dataset and behaviour measurements. **Cost.** Game calls for generation; SFT unpriced.
**Falsifier.** Projection-grounded critique does not beat plain critique on faults per turn or steps
to finish. **Status.** Blocked for the weight step; prototype-able for the in-session step.

### Route D — Active selection from context metrics

**Statement.** Select hard traces for labelling with ctxvm metrics and Route B labels.

**Mechanism.** Compute thrash index, refetch rate, net token reduction and touch ratio. Select high
pressure or high fault density. Route B labels supply ground truth where a claim needs it. Send the
selected steps to a judge; retrain the selector. This does not rest on an UNVERIFIED source:
Goldilocks Selection (Mindermann et al., 2021-07-06, Abstract) reports that "just right" points beat
hard, easy and uncertain ones.

**Changed object.** Training-data selector. **Inputs.** Traces, metrics, judge. **Output.** Selected
set. **Cost.** Judge time. **Falsifier.** A selector trained on ctxvm metrics does not beat random
selection at equal label budget. **Evidence.** Mindermann et al. (Abstract); Part I §6 metrics.
*Inference*.

### Route E — Versioned monitor views as evaluator

**Statement.** Make the evaluator a versioned object.

**Mechanism.** Define $V_k$ as a trace joined with its sources and the omission record (Part II §1.1).
Score model versions on one corpus with one view version. Keep the view and scoring rule out of the
agent context. Three versions cannot support a significance claim; use at least ten versions, or
report the three-version result as a descriptive paired comparison, not an inference.

**Changed object.** Evaluator. **Inputs.** Corpus, sources, view function. **Output.** Comparable
scores. **Cost.** Compute. **Falsifier.** View scores do not predict the held-out task metric across
the version set. **Evidence.** Part I §12; ImpossibleBench and SLEIGHT-Bench (Abstract) for scorer
exploitation.

### Route F — Harness-side recursive summarisation

**Statement.** Compress a long request at page boundaries — in the harness, not from the trace.

**Mechanism.** Summarising a prefix needs page content, which the trace does not hold. This is a
harness policy. The stock compressor in the W8 control arm may already summarise; that is
**UNKNOWN** and must be checked before any arm is defined. E5 uses the existing W8 profiles rather
than a new feature.

**Changed object.** Context policy (harness-side). **Inputs.** Long traces; W8 profiles.
**Output.** A comparison of compression policies. **Cost.** Compute plus existing model calls.
**Falsifier.** The summary policy does not beat plain truncation at equal context budget.
**Evidence.** Wu et al. (2021-09-22, Abstract) gives the analogy, not the method.

### 6.1 Route summary

| Route | Changed object | New model spend | Falsifiable |
|---|---|---|---|
| A — fault selection | Training-data selector | none (feeds B) | yes |
| B — page ablation | Ranker / data filter | open-weight: none; hosted: ~1,300 calls | yes |
| C — trace critique | Context-use behaviour | game calls; SFT unpriced | yes, in-session only |
| D — active selection | Training-data selector | judge time | yes |
| E — versioned views | Evaluator | none | yes, with ≥10 versions |
| F — harness summary | Context policy | existing W8 profiles | yes |

---

## 7. Guardrails

1. **Noise floor before effect** (Part I §10).
2. **Several samples per arm**; use intervals, not hard thresholds (Part I §10).
3. **Six-part provenance** (Part I §10).
4. **Keep deterministic replay and model-driven runs separate** — no shared directory, checksum or claim.
5. **Content-blindness**: do not train a model to recover page content from a trace.
6. **No causal claim from rendering**; only an intervention supports one.
7. **Hold out the scorer** (ImpossibleBench; SLEIGHT-Bench).
8. **Include the budget term**; "keep everything" is not a result.
9. **Mark unverified sources** with Part II's vocabulary; they carry no argument.
10. **Record the negative** with its falsifier.
11. **No cost-saving claim** (law 7); the paid cell was 2.11× the control.

---

## 8. Failure modes and risks

| Failure | Signal | Response |
|---|---|---|
| Reward hacking in self-refinement | Judge score rises, held-out task flat | Hold out the judge; impossible control (Pan et al., 2024-07-05, Abstract) |
| In-context reward hacking | Feedback loop changes behaviour in one session | Separate feedback from evaluation turns (Pan et al., 2024-02-09, Abstract) |
| Definitional fault labels | Fault rate tracks mention rate, not need | Use `tool_recall`; add matched ablation (Route B) |
| Omission gap | Table shows full pages the request omitted | Part II §2.4; provider receipts; do not infer content |
| Evaluator evasion | Monitor misses covert behaviour | SLEIGHT-Bench-style tests (Abstract) |
| Optimising the view | View score rises, held-out metric flat | Falsifier fires; stop the route |
| Author mismatch | Wrong-person papers in a training set | Filter on `author_match = confirmed` |

**Capability uplift (Part II).** Context management is a capability. A loop that improves page
selection can also improve sabotage: an agent that learns which pages to keep learns what a monitor
sees. Before any route is run, add the Part II capability-uplift check — does the change improve a
harmful task as well as the benign one? — and keep a **human gate** on every weight or policy update.
A negative uplift check stops the route.

---

## 9. Experiment designs

Each design names its unit, sample size, margin and command. All are preregistered before the first
call; post-result changes are deviations and are recorded.

### 9.0 E0 — Open-weight page ablation (Route B primary)

- **Question.** Does page-level causal importance beat matched random ablation?
- **Data.** 20 prompts; one frozen model snapshot; 10 pages per trace.
- **Arms.** Baseline; baseline repeat; leave-one-out per page; matched random page.
- **Primary metric.** Rank correlation between touch count and log-probability change, with a
  confidence interval over prompts. **Unit:** correlation coefficient.
- **Sample size / margin.** 20 prompts gives a wide interval; report it rather than claiming
  significance. 40 prompts if a narrower interval is needed.
- **Command.** The Part II §12.1 protocol; cross-reference it, do not fork it.
- **Stop rule.** Interval includes zero → negative result.

### 9.1 E1 — Fault availability and label quality (Route A, zero spend)

- **Question.** How many faults of each source exist, and do they name pages?
- **Data.** Frozen corpus only (15 fault-bearing paths; 41 `identifier_scan`, 21 `tool_recall`);
  full path as unit, never basename flattening.
- **Metric.** Counts by source; fraction of faulted pages that were resident. **Unit:** events.
- **Command.** JSON parse over `corpus/m*/**/*.jsonl`; manifest with `sha256sum`.
- **Stop rule.** If `tool_recall` n < 10, label quality is insufficient; Route A is Blocked.

### 9.2 E2 — Hosted ablation with intervals (Route B secondary)

- **Question.** Does the open-weight effect transfer to answer change?
- **Data / arms.** 20 prompts, 10 pages, 3 samples per arm across 2 arms (leave-one-out and matched random; 6 calls per page), baseline twice.
- **Primary metric.** Binomial interval on answer-change rate. **Unit:** proportion.
- **Cost.** ~1,320 calls; ≈ $11.37 at the blended $0.00861/request (`reports/W8-SPEND.md:82`); UNVERIFIED estimate; check receipts.
- **Command.** Part II §12.1 hosted protocol with the parameters above; preregister model snapshot and seed.
- **Stop rule.** Intervals overlap random ablation → negative result.

### 9.3 E3 — In-session critique (Route C)

- **Question.** Does projection-grounded critique reduce faults per turn?
- **Design.** 30 tasks, three arms, 3 trials each. **Unit:** faults per turn.
- **Command.** Parse held-out traces before and after critique; count `page.fault` per `turn.render` with the §9.1 JSON parser; preregister task ids and seed.
- **Margin.** Report a paired difference with an interval; 30 tasks is a pilot, not a power claim.
- **Blocker.** The weight step needs a wrong-answer corpus and an SFT price; both UNKNOWN/Blocked.

### 9.4 E4 — Versioned views (Route E)

- **Question.** Does a view score predict task success across versions?
- **Design.** ≥10 model versions; one corpus; one view version; paired comparisons plus a
  descriptive trend. **Unit:** score difference. With n=3, no significance claim is possible.
- **Command.** Score all versions on one corpus with view `V_k`; paired comparison over version ids; preregister the view hash.
- **Guard.** View and scoring rule stay out of agent context.

### 9.5 E5 — Harness summarisation (Route F)

- **Question.** Do page-boundary checkpoints beat truncation at equal budget?
- **Design.** Use existing W8 profiles; first verify what the control compressor already does
  (UNKNOWN). Longest traces in the corpus. **Unit:** held-out task success at equal token budget.
- **Command.** `benchmarks/metrics` policy simulator over the longest corpus traces; compare summary against truncation at equal token budget.

---

## 10. What ctxvm cannot do

1. Train weights or choose a training objective.
2. See activations, probes or hidden reasoning.
3. Reconstruct request bytes from a trace.
4. Judge correctness; a human or model judge must do that.
5. Prove causation from a render; only an intervention can.
6. Record a page removed without a stub in sealed v0.
7. Supply page content for a summary or a content-grounded critique.
8. Make a loop safe from reward hacking or capability uplift.
9. Claim cost savings on the measured cell.

---

## 11. Research agenda

| # | Question | Route | Status | Next step |
|---|---|---|---|---|
| 1 | Do causal labels beat random ablation? | B | Designed; compute-only arm available | Run E0 |
| 2 | Are fault labels usable selection features? | A | Designed; label quality unknown | Run E1 |
| 3 | Does the open-weight effect transfer? | B | Designed; needs spend | Preregister E2 |
| 4 | Does critique change context use? | C | Prototype-able in-session; weight step Blocked | Run E3 |
| 5 | Do metrics select useful training data? | D | Designed | Use E0 labels |
| 6 | Does a view predict task success? | E | Designed; needs ≥10 versions | Run E4 |
| 7 | Do checkpoints beat truncation? | F | Designed; control compressor UNKNOWN | Check W8 profile |
| 8 | Does a policy lift harmful capability? | All | Risk check | Add to each prereg |

---

## 12. Reproducing the evidence

```bash
# from the ctxvm repo root
python3 research/datamining/datamining.py
# single-term count (word boundary, title+reference) — see script for the regex
python3 - <<'PY'
import os, sqlite3, re
c = sqlite3.connect(os.path.expanduser("~/research/anthropic-papers-reference.sqlite"))
c.row_factory = sqlite3.Row
rows = [dict(r) for r in c.execute("SELECT title, reference FROM papers")]
n = sum(1 for r in rows if re.search(r"\bAnthropic\b", (r["title"] or "") + " " + (r["reference"] or ""), re.I))
print("word-boundary Anthropic:", n)   # print both this and the SQL LIKE 59
PY
sqlite3 "$HOME/research/anthropic-papers-reference.sqlite" \
  "SELECT COUNT(*) FROM papers WHERE reference LIKE '%Anthropic%';"   # 59; word-boundary count is also 59
```

The SQLite table has five columns; the reference column holds a one-page extractive reference.
Equations in those references are heuristic PDF conversions. `$HOME` is expanded here because the
database lives outside the repo; `lookup.txt` has 433 lines (two header comments + 431 data rows).
Both Anthropic counts above measured 59 on 2026-11-18. The keyword lists and JSON dump are in-repo
at `research/datamining/`.

---

## 13. Conclusion

A self-improvement loop needs four parts. ctxvm does not close it. It makes the input side
observable, versioned and open to controlled intervention. That is enough to improve an evaluator
and a training-data selector; it is not enough to improve weights.

The first step is open-weight page ablation (E0): it gives causal labels at compute cost and can be
run now. Those labels test the fault-selection and active-selection routes, then the view route.
Every route has a falsifier, a unit, a sample size and a human gate. If a falsifier fires, the route
is a negative result and must be recorded.

---

## References

Links are the arXiv PDF URLs verified on 18 November 2026. Level follows Part II §1.2.

1. Bai et al. *Constitutional AI: Harmlessness from AI Feedback.* 2022-12-15. https://arxiv.org/pdf/2212.08073 — Abstract
2. Wu et al. *Recursively Summarizing Books with Human Feedback.* 2021-09-22. https://arxiv.org/pdf/2109.10862 — Abstract
3. Lightman et al. *Let's Verify Step by Step.* 2023-05-31. https://arxiv.org/pdf/2305.20050 — Abstract
4. Koh et al. *Tree Search for Language Model Agents.* 2024-07-01. https://arxiv.org/pdf/2407.01476 — Abstract
5. Zhong, Raghunathan, Carlini. *ImpossibleBench.* 2025-10-23. https://arxiv.org/pdf/2510.20270 — Abstract
6. Souly et al. *A StrongREJECT for Empty Jailbreaks.* 2024-02-15. https://arxiv.org/pdf/2402.10260 — Abstract
7. Najt, Toft, Tracy, Roger, Benton. *SLEIGHT-Bench.* 2026-05-15. https://arxiv.org/pdf/2605.16626 — Abstract
8. Deng et al. *OpenVLThinker.* 2025-03-21. https://arxiv.org/pdf/2503.17352 — Abstract
9. Scheurer et al. *Training Language Models with Language Feedback.* 2022-04-29. https://arxiv.org/pdf/2204.14146 — Abstract
10. Mindermann et al. *Prioritized training.* 2021-07-06. https://arxiv.org/pdf/2107.02565 — Abstract
11. Pan, He, Bowman, Feng. *Spontaneous Reward Hacking in Iterative Self-Refinement.* 2024-07-05. https://arxiv.org/pdf/2407.04549 — Abstract
12. Pan, Jones, Jagadeesan, Steinhardt. *Feedback Loops With Language Models.* 2024-02-09. https://arxiv.org/pdf/2402.06627 — Abstract
13. Cohen-Wang, Shah, Georgiev, Madry. *ContextCite.* 2024-09-01. https://arxiv.org/pdf/2409.00729 — Abstract
14. Shinn et al. *Reflexion.* arXiv:2303.11366 — Snippet, UNVERIFIED
15. Madaan et al. *Self-Refine.* arXiv:2303.17651 — Snippet, UNVERIFIED
16. Zelikman et al. *STaR.* arXiv:2203.14465 — Snippet, UNVERIFIED
17. Yuan et al. *Self-Rewarding Language Models.* arXiv:2401.10020 — Snippet, UNVERIFIED
18. Wang et al. *Voyager.* arXiv:2305.16291 — Snippet, UNVERIFIED
19. Part I and Part II of this paper; repository reports cited there.

---

## Document control

| Item | Value |
|---|---|
| Title | What a context trace offers a self-improvement loop (Part III) |
| Version | 1.1, 18 November 2026; 1.0 had two wrong author attributions and one wrong date |
| Method | Purposive sample of 12 sources from a 159-paper lab filter; all authors/dates re-checked on arXiv |
| Experiments run | None; all designs are preregistration candidates |
| Style | ASD-STE100-inspired: short sentences, active voice, defined terms |
| Open items | §11, items 1–8; capability uplift and human gate on every prereg |
| Integrity rule | Locator at first mention; UNVERIFIED carries no argument; no cost-saving claim |
