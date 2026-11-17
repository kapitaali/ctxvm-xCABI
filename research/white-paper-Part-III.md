# Part III — Using ctxvm in the creation of self-improving AI models

**Author:** Kapitaali · **Date:** 2026-11-17 · **Status:** draft for review
**Part I:** *Virtual memory for LLM agent context: the xCABI standard and the ctxvm engine.*
**Part II:** *What a context trace can and cannot show about AI safety.*

---

## Abstract

This paper answers one question. How can a team use ctxvm to create a self-improving AI model, or to
help create one? The answer is narrow. ctxvm does not train weights. It has no reward model and no
access to model internals. It supplies the input side of a learning loop: a portable record of the
harness request, deterministic replay of the page-table projection, and page-level counterfactual
interventions with the provenance that a causal claim needs. A self-improvement loop still needs a
generator, an evaluator, a selector, and an update step. ctxvm strengthens two of those four parts.
It supplies process labels from faults and supply causal labels from ablation. We describe six routes
that use this capability. Three need no new model calls. Three need paid calls and a preregistration.
We state the guardrails, the failure modes, and the limits. No route in this paper has been run.
The paper marks claims that rest on extractive references as UNVERIFIED.

---

## 1. Scope and vocabulary

### 1.1 Defined terms

| Term | Meaning in this paper |
|---|---|
| Self-improvement | A loop that changes a system so that a later version scores better on a held-out task. The change may be in weights, in a policy outside the model, or in the data used for training. |
| Loop | Generate, evaluate, select, update, repeat. |
| Process label | A label on an intermediate step, not on the final answer. |
| Page | The unit of context that ctxvm records: a `(logical_ref, content_hash)` identity with a kind and a token count. |
| Intervention replay | A run that changes one thing in a recorded trace and calls the model again. The engine is deterministic. The model is not. |
| Monitor view | A versioned function from a trace to the data a monitor sees. |
| Noise floor | The answer-change rate between two unchanged runs. |
| Trace-only claim | A claim that uses the recorded projection without a new model call. |

### 1.2 Evidence levels

| Level | Meaning |
|---|---|
| **Repo** | Stated in Part I or Part II of this paper, or in a cited repository report. |
| **Paper body** | The abstract of the cited paper was read in this work. |
| **Extract** | The statement comes from an automated reference built from the PDF text layer. Mark UNVERIFIED where used. |
| **Inference** | This paper's own reasoning. Not a measured result. |

Every external claim carries its locator at first mention. UNVERIFIED claims do not carry an argument.

---

## 2. The question and the short answer

**Question.** How can a team use ctxvm to create a self-improving AI model, or use ctxvm in the
creation of one?

**Short answer.** Use ctxvm as the measurement and data-generation layer around an existing training
loop. Use it for three jobs:

1. Label process errors from the trace itself. A `page.fault` says the model asked again for a page.
2. Generate causal labels with page-level ablation. Remove one page. Call the model again. Measure
   the change above the noise floor.
3. Version the evaluator. A monitor view is a pure function of a trace. Two model versions can be
   scored against the same view.

ctxvm does not do the update step. The team must still train a model, train a policy, or change data.
Part I §16 limits what a trace can support. Part II §10 repeats those limits for safety claims.

---

## 3. Evidence base and method

### 3.1 Corpus used for this paper

We built a scientist list from public sources (Anthropic's own pages and a third-party index). We
queried OpenAlex for papers by those names from 2021-01-01 to 2026-11-12. The result held 2,007
(scientist, paper) rows for 88 scientists. We removed duplicate papers by OpenAlex work id.
That gave 1,495 unique works. We tried to download a PDF for each work. We saved 1,064 PDFs and
wrote 431 unavailable papers to `lookup.txt`. We extracted text from each PDF with `pdftotext
-layout` and built a short reference for each. The SQLite table holds 1,061 rows with the columns
`name | date | title | url | reference`. Three PDFs failed extraction.

We then ran a SQL search for common AI lab names over `reference` and `title`. A word-boundary
filter removed false matches such as "Mila" inside "similar". The search returned 159 papers.
The file `ai-lab-paper-summaries.txt` holds those summaries. This paper uses that file as its
literature base.

### 3.2 Counts from the SQL search

| Lab | Papers |
|---|---|
| Anthropic | 59 |
| OpenAI | 48 |
| DeepMind (incl. Google DeepMind) | 32 (22) |
| Google Brain | 6 |
| Apple | 9 |
| Hugging Face | 7 |
| Mistral | 5 |
| EleutherAI | 3 |
| Redwood Research | 4 |
| Amazon | 4 |
| Allen Institute | 3 |
| Cohere | 2 |
| Stability AI | 2 |
| IBM Research | 2 |
| Meta AI, Microsoft Research, NVIDIA | 1 each |

Counts overlap. One paper may mention several labs.

### 3.3 Limits of this evidence base

OpenAlex author matching is not exact. Of 88 author profiles, 38 had no Anthropic affiliation in
OpenAlex. Spot checks found wrong-person matches. We marked those rows `unverified` in the data.
Several paper references have no detected abstract. We mark such claims UNVERIFIED. The lab search
finds papers that mention a lab, not papers written only by that lab. None of these limits changes
the mechanisms in this paper. They change how much weight a reader should give the examples.

---

## 4. What ctxvm provides

Part I §2–3 defines the wire format. Part I §3.8 defines the engine. Part I §10 defines intervention
replay. Part I §12 defines monitor views. The capabilities are these.

| Capability | Mechanism | Value for a learning loop |
|---|---|---|
| Page identities and hashes | `page.declare` carries `(logical_ref, content_hash)`, kind, token count | Stable keys for pages across runs and model versions |
| Deterministic derivation | The renderer derives the page table from the event stream. Same trace bytes give the same projection bytes on one machine and build | A reproducible baseline |
| Fault events | `page.fault` records a re-request, with a source | A process label that needs no human annotator |
| Token accounting per turn | `turn.render` carries resident tokens, evicted tokens, and headroom | A measure of context pressure |
| Intervention replay | Remove, stub, or replace one page; call the model again | A counterfactual label at page granularity |
| Noise-floor protocol | Baseline vs baseline; several samples per arm | Separates an effect from sampling noise |
| Six-part provenance | Parent digest, intervention, sampling, model snapshot and date, harness versions, tokenizer version | Makes a run reproducible and citable |
| Versioned views | A view is a pure function of a trace | A stable evaluator across model versions |
| Export and diff | ODPS artifacts; `ctxvm diff` compares traces | Versioned data for repeated experiments |

### 4.1 What the format does not record

Part I §16 and Part II §10 state the limits. We repeat the ones that matter here.

- A trace holds identities and hashes. It does not hold page content.
- Rendering a page does not cause an answer. Only an intervention supports a causal claim.
- A hosted model is not deterministic at fixed settings. One draw is not an effect.
- Sealed v0 has no verb for a page removed without a stub. Part II §2.4 describes the gap.
- `turn.render.evictedTokens` is recorded but unchecked in v0 for removal policies. Part I §7.
- No cost saving was measured on the paid cell. The paged arm cost 2.11 times the control.
  We make no cost-saving claim in this paper.

---

## 5. What a self-improvement loop needs

A loop has four parts. We write the update as an author's formulation, not as a quote from a source.

Let $M_t$ be the system at iteration $t$. Let $D_t$ be the data, $E_t$ the evaluator, and $U$ the
update operator. Then

$$
M_{t+1} = U\bigl(M_t,\; E_t(G(M_t, D_t)),\; D_t\bigr)
$$

where $G$ generates traces or answers. The loop improves only when the evaluator's ranking predicts
the held-out metric. Three failure modes follow from this equation.

1. The generator produces no useful variation.
2. The evaluator ranks noise as signal.
3. The update changes the wrong object.

The cited literature addresses these failures.

| Source | Date and locator | What it contributes | Evidence |
|---|---|---|---|
| Constitutional AI: Harmlessness from AI Feedback | 2022-12-15, https://arxiv.org/pdf/2212.08073 | Self-critique and revision, SFT, then AI preference model and RLAIF. Self-improvement without human labels of harmful outputs. | Paper body |
| Recursively Summarizing Books with Human Feedback | 2021-09-22, https://arxiv.org/pdf/2109.10862 | Recursive task decomposition. Small-part models help supervise the larger task. | Paper body |
| Let's Verify Step by Step | 2023-05-31, https://arxiv.org/pdf/2305.20050 | Process supervision beats outcome supervision on MATH (78% on a representative subset). Active learning improves it. | Paper body |
| Tree Search for Language Model Agents | 2024-07-01, https://arxiv.org/pdf/2407.01476 | Inference-time best-first search in a real environment. +39.7% relative success on VisualWebArena. | Paper body |
| ImpossibleBench | 2025-10-23, https://arxiv.org/pdf/2510.20270 | A test with a deliberate conflict between spec and tests. A pass implies a shortcut. | Paper body |
| A StrongREJECT for Empty Jailbreaks | 2024-01-01, https://arxiv.org/pdf/2402.10260 | A standard judge for jailbreak success. Shows the need for a fixed evaluator. | Paper body |
| SLEIGHT-Bench | 2026-05-15, https://arxiv.org/pdf/2605.16626 | 40 attacks against agent monitors; 20 never detected. Shows the limits of the evaluator. | Paper body |
| OpenVLThinker: Iterative SFT-RL Cycles | 2025, https://arxiv.org/pdf/2503.17352 | Alternating SFT and RL beats either alone. | Extract — UNVERIFIED |
| Training Language Models with Language Feedback | 2022-04-29, https://arxiv.org/pdf/2204.14146 | Language feedback as a training signal. | Extract — UNVERIFIED |
| Prioritized training on learnable, worth learning, and not yet learned points | 2021-07-06, http://export.arxiv.org/pdf/2107.02565 | Data selection is part of the loop. | Extract — UNVERIFIED |
| Spontaneous Reward Hacking in Iterative Self-Refinement | 2024-07-05, https://arxiv.org/pdf/2407.04549 | Self-refinement can produce reward hacking without an external reward model. | Extract — UNVERIFIED |
| Feedback Loops With Language Models Drive In-Context Reward Hacking | 2024-02-09, https://arxiv.org/pdf/2402.06627 | Feedback loops can create in-context reward hacking. | Extract — UNVERIFIED |

### 5.1 A note on equations in the sources

Some reference records contain equations converted from the PDF text layer. They are noisy. One
cleaner example is the weak-to-strong loss from *Weak-to-Strong Generalization*
(2023-12-14, https://arxiv.org/pdf/2312.09390):

$$
L_{\mathrm{conf}}(f) = \mathrm{CE}\bigl(f(x),\, (1-\alpha)\cdot f_w(x) + \alpha \cdot \hat{f}_t(x)\bigr)
$$

The conversion is heuristic. Verify the symbols against the PDF before use. The other equations in
this paper are the author's formulations. We do not attribute them to a source.

---

## 6. Six routes

Each route has the same shape. We state the mechanism, the inputs, the output, the cost, and the
falsifier. A falsifier is an observation that would show the route does not work.

### Route A — Fault-driven process supervision

**Statement.** Use `page.fault` events as process labels for a context policy.

**Mechanism.** Collect traces from many tasks. For each step, record whether a fault occurred on a
page already rendered. Train a small policy to choose pages so that this label becomes rare. The
model weights do not change. The policy that builds the request changes.

**Inputs.** A corpus of traces. No new model calls.

**Output.** A policy and a labeled dataset of steps.

**Cost.** Compute only.

**Falsifier.** A policy trained on fault labels does not reduce faults on a held-out corpus more than
a policy that removes random pages.

**Evidence.** Part I §4 defines `page.fault`. Part I §17 warns that faults on rendered pages are
close to definitional for the identifier-scan surface. A control is required. *Inference*.

### Route B — Counterfactual page ablation

**Statement.** Turn each page into a causal-importance label.

**Mechanism.** For a page $p$ in a trace $\tau$, run intervention replay with $p$ removed. Use
three samples per arm and a baseline-vs-baseline control. Define the causal label

$$
c(p) = \mathbb{1}\bigl[\, \Delta(p) > \epsilon_{\mathrm{noise}} \,\bigr],
\qquad
\Delta(p) = \frac{1}{n}\sum_{i=1}^{n} \mathbb{1}[a_i(\tau) \neq a_i(\tau \setminus p)]
$$

where $a_i$ is the answer on draw $i$ and $\epsilon_{\mathrm{noise}}$ is the baseline-vs-baseline
change rate. Train a page ranker or a process reward model on these labels.

**Inputs.** A frozen trace corpus. Paid model calls for the intervention arms.

**Output.** Causal labels at page granularity. A trained ranker or reward model.

**Cost.** One model call per page per sample. High.

**Falsifier.** A ranker trained on $c(p)$ does not beat a ranker trained on random ablation on a
held-out success metric.

**Evidence.** Part I §10 defines intervention replay and the controls. Part I §8.8 compares
page-level ablation with ContextCite (arXiv:2409.00729, abstract read in Part I). *Inference*.

### Route C — Trace-grounded self-critique and revision

**Statement.** Use the projection as the critique input in a Constitutional-AI-style loop.

**Mechanism.** Give the model its own page table, faults, token totals, and the request's estimated
size. Ask it to revise the answer or the tool plan. Fine-tune on the revisions. Then collect AI
preferences between revised and original answers and train a preference model.

**Inputs.** Traces plus a model that can read a structured projection.

**Output.** A revised-answer dataset and a preference model.

**Cost.** Compute for generation; paid calls only if a hosted model is used.

**Falsifier.** Revision guided by the projection does not beat revision guided by the same words
without the projection.

**Evidence.** Constitutional AI (2022-12-15) supplies the pattern. Part I §16 says the trace is
content-blind. The critique must concern structure and shape. *Inference*.

### Route D — Active selection from context metrics

**Statement.** Train where the agent struggles, using ctxvm metrics as the selector.

**Mechanism.** Compute the thrash index, refetch rate, net token reduction, and touch ratio for each
trace. Select the steps with high pressure or high fault density. Send those steps to a human or
model judge. Add the labels. Retrain.

**Inputs.** A corpus of traces. Judging capacity.

**Output.** A selected training set.

**Cost.** Judge time, not model calls, if the judge is human.

**Falsifier.** A model trained on selected traces does not beat a model trained on the same number
of random traces on a held-out task.

**Evidence.** The 2021 prioritized-training paper supplies the selection idea (Extract —
UNVERIFIED). Part I §6 defines the metrics. *Inference*.

### Route E — Versioned monitor views as evaluator

**Statement.** Make the evaluator a versioned object.

**Mechanism.** Define a view $V_k$ as a pure function of a trace. Examples: rendered pages only;
resident pages plus stubs. Score each model version on the same corpus with the same view. Feed the
score into the selection step. Keep the view and the scoring rule out of the agent's context.

**Inputs.** A trace corpus. A scoring function.

**Output.** Comparable scores across model versions.

**Cost.** Compute.

**Falsifier.** Scores from $V_k$ do not correlate with a held-out task metric across model versions.

**Evidence.** Part I §12 defines monitor views. ImpossibleBench and SLEIGHT-Bench show that a scorer
visible to the agent will be exploited. *Inference*.

### Route F — Recursive page-boundary decomposition

**Statement.** Use page boundaries as checkpoints for long tasks.

**Mechanism.** Split a trace with `export --turn N`. Summarize each prefix. Feed the summary forward
as a new page. Repeat. This is the context-layer analogue of recursive book summarization.

**Inputs.** Long traces. A summarizer.

**Output.** A recursive dataset and a shorter context policy.

**Cost.** Compute plus summarizer calls.

**Falsifier.** Recursive summary traces do not beat plain truncation on a long-task metric.

**Evidence.** Recursively Summarizing Books (2021-09-22) supplies the analogy, not the method.
Part I §3 defines `export`. **UNVERIFIED as a training recipe**.

### 6.1 Route summary

| Route | New model spend | Main artifact | Cheap to test |
|---|---|---|---|
| A — fault labels | none | labeled steps | yes |
| B — page ablation | high | causal labels | no |
| C — self-critique | low to medium | revision dataset | yes |
| D — active selection | judge time | selected set | yes |
| E — versioned views | none | comparable scores | yes |
| F — recursive decomposition | medium | recursive set | no |

---

## 7. Guardrails

1. **Noise floor before effect.** Run baseline against baseline. Measure the answer-change rate.
   An effect below that rate is not an effect (Part I §10).
2. **Several samples per arm.** One draw is noise (Part I §10).
3. **Six-part provenance.** Parent trace and digest; intervention; sampling parameters; model
   snapshot and date; harness and adapter versions; tokenizer version (Part I §10).
4. **Keep run kinds separate.** Deterministic replay and model-driven intervention must not share a
   directory, a checksum file, or a claim (Part I §10).
5. **Content-blindness.** Do not train a model to recover page content from a trace. The trace does
   not hold it (Part I §16, seventh bullet).
6. **No causal claim from rendering.** Only an intervention supports a causal claim (Part I §16).
7. **Hold out the scorer.** A visible scorer will be exploited (ImpossibleBench; SLEIGHT-Bench).
8. **No cost-saving claim.** The measured paid cell cost 2.11 times the control. Spend must be
   justified by capability, not savings.
9. **Mark unverified sources.** Extract-level claims do not carry an argument.
10. **Record the negative.** A route that fails must be written down with its falsifier.

The first four guardrails apply to every route. The rest apply where stated.

---

## 8. Failure modes

| Failure | Signal | Response |
|---|---|---|
| Reward hacking in self-refinement | Revisions improve the judge, not the held-out task | Hold out the judge; add an impossible control |
| In-context reward hacking | Feedback loop changes the model's behavior inside one session | Separate feedback from evaluation turns |
| Fault labels are definitional | Fault rate tracks mention rate, not need | Add page-ablation control (Route B) |
| Author mismatch in the corpus | Wrong-person papers in training data | Filter on `author_match = confirmed` |
| Evaluator evasion | Monitor misses covert behavior | Use SLEIGHT-Bench-style adversarial tests |
| Trace projection is not turn-scoped on a flush-tail capture | The table shows pages the request did not carry | Read Part II §2.4; use the provider receipts |
| Loop optimizes the view, not the task | View score rises; held-out metric flat | Falsifier triggers; stop the route |

---

## 9. Experiment designs

### 9.1 E1 — Fault labels without paid calls (Route A)

- **Question.** Do fault labels predict steps that a context policy should change?
- **Data.** One frozen corpus. All traces with at least one `page.fault`.
- **Arms.** Fault-label policy vs random-page policy. No model calls.
- **Metric.** Fault count per turn on a held-out corpus.
- **Stop rule.** No difference above 10% → negative result.

### 9.2 E2 — Page ablation with controls (Route B)

- **Question.** Does page-level causal importance beat random ablation for data selection?
- **Data.** 20 prompts. One model snapshot. Ten pages per trace.
- **Arms.** Baseline twice; remove target page; remove random page. Three samples per arm.
- **Labels.** Answer-change rate above the noise floor.
- **Train half. Validate half.** Held-out metric is task success, not the ranker's own score.
- **Provenance.** Six parts for every arm.
- **Stop rule.** No gain over random ablation → negative result.

### 9.3 E3 — Trace-grounded revision (Route C)

- **Question.** Does a projection-grounded critique beat a plain critique?
- **Arms.** Same words; same words plus projection; projection only.
- **Data.** 100 wrong answers from a fixed corpus.
- **Metric.** Held-out correctness after SFT on revisions.
- **Stop rule.** Projection-only does not beat plain critique → no evidence for trace grounding.

### 9.4 E4 — Versioned view across model versions (Route E)

- **Question.** Does a view score predict a held-out task metric across versions?
- **Data.** Three model versions. One corpus. One view, versioned.
- **Metric.** Rank correlation between view score and task metric.
- **Guard.** The view and the scoring rule stay out of the agent context.

### 9.5 E5 — Recursive decomposition (Route F)

- **Question.** Do page-boundary checkpoints beat truncation on long tasks?
- **Data.** The longest traces in the corpus.
- **Arms.** Truncate at a token budget; summarize at page boundaries; no compression.
- **Metric.** Held-out task success at equal context budget.

Each design must be preregistered before the first call. A change after the result is a deviation and
must be recorded as such.

---

## 10. What ctxvm cannot do

1. It cannot train weights.
2. It cannot choose a training objective.
3. It cannot see activations, probes, or hidden reasoning.
4. It cannot reconstruct request bytes from a trace.
5. It cannot judge correctness. A human or a model judge must do that.
6. It cannot prove causation from a render. Only an intervention can.
7. It cannot record a page removed without a stub in sealed v0.
8. It cannot make a loop safe from reward hacking.
9. It cannot claim cost savings on the measured cell.

This list is not a defect list. It is the boundary of the instrument.

---

## 11. Research agenda

| # | Question | Route | Status | Next step |
|---|---|---|---|---|
| 1 | Do fault labels reduce context-policy errors? | A | Designed; no run | Run E1 |
| 2 | Does page-level causal importance beat random ablation? | B | Designed; needs spend | Preregister E2 |
| 3 | Does a projection-grounded critique beat a plain critique? | C | Designed | Run E3 |
| 4 | Do context metrics select useful training data? | D | Designed; judge needed | Select a corpus |
| 5 | Does a versioned view predict task success? | E | Designed | Run E4 |
| 6 | Do page-boundary checkpoints beat truncation? | F | Designed; UNVERIFIED analogy | Run E5 |
| 7 | Can a self-refinement loop avoid reward hacking with ctxvm feedback? | A+C | Not designed | Add impossible control |
| 8 | Does a stable-prefix selection policy keep the provider cache? | Engine | Separate question | See the cache-stable design note |

Agenda items are designs, not results. UNVERIFIED marks an analogy without a source in the record.

---

## 12. Reproducing the evidence in this paper

```bash
# Corpus and references
~/research/anthropic-scientist-papers-2021-2026.json
~/research/anthropic-scientist-papers-2021-2026.csv
~/research/lookup.txt
~/research/anthropic-papers-reference.sqlite
~/research/ai-lab-paper-summaries.txt

# Lab counts
sqlite3 ~/research/anthropic-papers-reference.sqlite \
  "SELECT COUNT(*) FROM papers WHERE reference LIKE '%Anthropic%';"

# A filtered export
sqlite3 -header ~/research/anthropic-papers-reference.sqlite \
  "SELECT name,date,title,url FROM papers WHERE reference LIKE '%Constitutional AI%';"
```

The database table has five columns. The reference column holds the short reference for each paper.
Equations in those references are heuristic conversions from the PDF text layer.

---

## 13. Conclusion

A self-improving model needs a loop. ctxvm does not close the loop. It makes the input side of the
loop observable, versioned, and open to controlled intervention. That is enough to improve the
evaluator and the training data. It is not enough to improve the weights by itself.

Three routes need no new model calls. A team can start with fault labels, active selection, and
versioned views. Page ablation and recursive decomposition need paid calls and a preregistration.
Every route has a falsifier. If the falsifier fires, the route is a negative result and must be
recorded. That rule protects the claim more than any positive result would.

---

## References

All arXiv PDF links below are the URLs recorded in the SQLite database. "Extract" marks a source
read only through the automated reference.

1. Bai et al. *Constitutional AI: Harmlessness from AI Feedback.* 2022-12-15. https://arxiv.org/pdf/2212.08073
2. Wu et al. *Recursively Summarizing Books with Human Feedback.* 2021-09-22. https://arxiv.org/pdf/2109.10862
3. Lightman et al. *Let's Verify Step by Step.* 2023-05-31. https://arxiv.org/pdf/2305.20050
4. Koh et al. *Tree Search for Language Model Agents.* 2024-07-01. https://arxiv.org/pdf/2407.01476
5. Harding et al. *ImpossibleBench.* 2025-10-23. https://arxiv.org/pdf/2510.20270
6. Chao et al. *A StrongREJECT for Empty Jailbreaks.* 2024-01-01. https://arxiv.org/pdf/2402.10260
7. *SLEIGHT-Bench: A Benchmark of Evasion Attacks Against Agent Monitors.* 2026-05-15. https://arxiv.org/pdf/2605.16626
8. *OpenVLThinker: Iterative SFT-RL Cycles.* 2025. https://arxiv.org/pdf/2503.17352 — Extract
9. *Training Language Models with Language Feedback.* 2022-04-29. https://arxiv.org/pdf/2204.14146 — Extract
10. *Prioritized training on learnable, worth learning, and not yet learned points.* 2021-07-06. http://export.arxiv.org/pdf/2107.02565 — Extract
11. *Spontaneous Reward Hacking in Iterative Self-Refinement.* 2024-07-05. https://arxiv.org/pdf/2407.04549 — Extract
12. *Feedback Loops With Language Models Drive In-Context Reward Hacking.* 2024-02-09. https://arxiv.org/pdf/2402.06627 — Extract
13. *Weak-to-Strong Generalization.* 2023-12-14. https://arxiv.org/pdf/2312.09390
14. Cohen-Wang et al. *ContextCite: Attributing Model Generation to Context.* arXiv:2409.00729 — abstract read in Part I
15. Part I and Part II of this paper; repository reports cited there.

---

## Document control

| Item | Value |
|---|---|
| Title | Using ctxvm in the creation of self-improving AI models (Part III) |
| Version | 1.0 draft, 17 November 2026 |
| Method | Synthesis of the ctxvm white papers, a 1,061-paper reference database, and a 159-paper lab filter |
| Experiments run | None; all designs are preregistration candidates |
| Style | ASD-STE100-inspired: short sentences, active voice, defined terms, no marketing language |
| Open items | §11, items 1–8 |
| Integrity rule | Every external claim carries its locator at first mention. UNVERIFIED claims do not carry an argument. No cost-saving claim. |
