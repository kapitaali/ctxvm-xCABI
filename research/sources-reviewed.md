# Sources reviewed — internal register

**What this is.** A running list of papers, explainers and posts we have actually read, with what
each one argues and what it means for ctxvm. It is a working notebook, not a bibliography.

**It is not the white paper's citation list.** `research/white-paper/white-paper.md` §References is
the only place a source becomes a citation; the eight entries there are marked CITED below. Nothing
else on this page is cited anywhere, and nothing here should be added to the paper without a
deliberate decision to cite it.

**How to add an entry.** One row: date read, source, type, identifier (arXiv id, DOI or URL), the
claim in one line, what it means for ctxvm in one line, and a disposition. Verify from the primary
source and write down what you verified — an abstract read is not the same as a paper read, and the
column should say which.

Dispositions: **CITED** (in the white paper) · **POSITIONING** (usable for framing, deliberately not
cited) · **BACKGROUND** (informs design, not argued in public) · **WATCH** (unvalidated or
incomplete — do not build against it) · **COUNTER** (argues against our position; keep, and answer).

## Reviewed 2026-10-31

| Date | Source | Type | Identifier | What it argues | What it means for ctxvm | Disposition |
|---|---|---|---|---|---|---|
| 2026-10-31 | "The Last Harness You'll Ever Build" — Seong, Yin, Zhang, Shi (Sylph.AI) | Framework paper, **no experiments** | arXiv:2604.21003v3, 01 May 2026, CC BY 4.0 | A two-level loop — Worker/Evaluator/Evolution agents optimizing a harness, then a meta-loop optimizing the blueprint itself — automates harness engineering; "we plan to follow up with empirical results" | Names ctxvm's category inside its own taxonomy ("hooks and middleware… verification loops", "context management") and its Evaluator consumes an execution trace, yet its `improved/regressed` verdict has no reproducibility requirement and its scoring has no context-cost term. ctxvm is the missing substrate and the missing metric | WATCH (positioning) |
| 2026-10-31 | "Gated DeltaNet Explained" — Attention Lab (interactive explainer) | Explainer | divagr.com/attention-lab/delta | Fixed-size recurrent state replaces the per-token KV cache; delta rule writes prediction error; learned decay and write gates; hybrids keep sliding-window attention | Model-internal memory, not input paging — orthogonal to ctxvm's mechanism, but it forces a qualifier onto `cacheEstimate` (D12/W8) and strengthens the provenance argument: a state matrix is not replayable, so the auditable record must live outside the model | BACKGROUND |
| 2026-10-31 | "Gated Delta Networks: Improving Mamba2 with Delta Rule" — Yang, Kautz, Hatamizadeh | Primary paper (ICLR 2025) | arXiv:2412.06464 (v3, 06 Mar 2025) | Gating (rapid erasure) and the delta rule (targeted update) are complementary; Gated DeltaNet beats Mamba2/DeltaNet on language modelling, common-sense reasoning, in-context retrieval, length extrapolation and long-context understanding; hybrids with sliding-window attention or Mamba2 layers do better still | Verification note: abstract read, not the full paper. The hybrid claim is the load-bearing one for us — it means "context is free now" is not a reading this paper supports | BACKGROUND |

Notes on the two new ones, because the one-line columns lose the argument:

- **2604.21003** — the parts worth stealing are the vocabulary (`Agent = Model + Harness`, harness
  components as a closed list) and the observation that a harness *evolution* loop needs an
  improvement signal, which is where our replay/diff fits. The parts to keep at arm's length: zero
  ablations, an LLM evaluator scoring LLM-evolved harnesses with no external anchor, and a two-tier
  score (pass/fail, wall-clock tiebreak) with no context-budget term — a loop optimizing that
  converges on whatever passes fastest while context bloat stays invisible. Also a company preprint
  with a stated product roadmap behind it.
- **divagr.com + 2412.06464** — the explainer is faithful to the abstract, but its numbers (8 GB vs
  1 MB at 64K, "8192×") are illustrative arithmetic on assumed dimensions, not measurements. Do not
  quote them.

## CITED — the white paper's references

These are the eight in `white-paper.md` §References. Recorded here so the register shows what the
paper rests on, but the paper remains the authority for their exact wording.

| Source | Identifier | Role in the paper |
|---|---|---|
| Mason, T. — "The Missing Memory Hierarchy: Demand Paging for LLM Context Windows" | arXiv:2603.09023 | The demand-paging result the engine implements |
| Chen, L. & Liu, Q. — "Neural Paging: Learning Context Management Policies for Turing-Complete Agents" | arXiv:2603.02228 | Learned paging policies |
| Kidwai, Y. A. — "Virtual Context: Unbounded Context for LLM Agents via OS-Style Memory Management" | virtual-context.com/paper/ | OS-style framing |
| Packer, C. et al. — "MemGPT: towards LLMs as operating systems" | arXiv:2310.08560 | Source of "virtual context management"; led to Letta |
| Sarath M S — "l1-pager — Context Garbage Collector for LangGraph" | github.com/sarath-m-s/l1-pager, PyPI l1-pager 1.1.1 | Prior art, nearest in shape |
| IBM — "chuk-ai-session-manager" | github.com/IBM/chuk-ai-session-manager | Prior art, summarization-based (not paging) |
| Jiang, Y. et al. — "LLMLingua" | 2024 | Prompt compression, the alternative to paging |
| Wang, Y. et al. — "SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents" | arXiv:2601.16746 | Pruning result with token-reduction numbers |

## INDEXED — already listed in the research docs

Listed there with their key claims; reproduced here only so the register is one place. Verify at the
original if a claim is ever used.

**`research/tracing-benefits-and-use-cases.md` §6** — Respan AI, "AI Agent Debugging: A Trace-First
Guide" (2026) · MLflow, "Agent Observability" (2026) · ISX4, "LLM Observability in Production"
(2026) · LangChain survey (2025, 1,340 teams: 89% running observability, 71% detailed tracing) ·
TestQuality, "How to Test AI Agents" (2026) · ESAA, "Event Sourcing for Autonomous Agents"
(arXiv:2602.23193v1 — append-only log, time-travel debugging, SHA-256 projection hashing) · Apica,
"LLM Observability" (2026) · agent-trace (GitHub, 2026 — HTTP-level record/replay).

**`research/token-savings-strategies.md`** — Mason, "The Missing Memory Hierarchy: Demand Paging for
LLM Context Windows" (arXiv:2603.09023; **Pichay is the system's name, not the author** — see the
cleanup note below) · "A Systematic Study of Context
Compression in LLM Agents" (arXiv:2609.32961v1 — TRC: 0.71× cost, 0.79× latency, 35,000 agent runs) ·
"Cache Engineering for Agents" (arXiv:2610.28577v1 — tool-response rolling drop, 27.7% cost
reduction) · "SWE-Pruner" (arXiv:2601.16746, 23–54% token reduction) · "Context Compaction"
(morphllm.com, 2026) · "Agent Cost" (neelmishra.github.io, 2026 — prompt caching 41–80%) ·
"LLM Cost Optimization for Agents" (viralruparel.com, 2026).

## Two facts this register had to settle

**"Pichay" is the system, Tony Mason is the author.** Checked against the arXiv listing for
2603.09023: single author, `Tony Mason`; "We present Pichay, a demand paging system…". Our older
`research/token-savings-strategies.md` writes "Pichay, 2026" eleven times as though it were a
surname, and `white-paper.md` carries "Source: Pichay, arXiv 2603.09023" — a reader checking the
author list finds no such author. The paper's own prose is mixed the same way, which is where the
confusion came from, but our citations should say `Mason (Pichay)`.

**The paper contradicts itself on corpus size, and we cite the body.** arXiv abstract says
"4.45 **million** effective input tokens"; the body says "4.45 **billion**" five times
("54,170 API calls and 4.45 billion effective input tokens"). We cite the body's figure, which is
what `RESEARCH-PLAN.md` recorded. Anyone auditing against the abstract will find a mismatch — so
state the body figure and note the abstract divergence rather than quoting either silently.

## Cleanups this register surfaced — done 2026-10-31

1. **Attribution.** "Pichay" is the system; the author is Tony Mason. `white-paper.md` and
   `index.md` now introduce him at first mention ("Source: Mason, arXiv:2603.09023; the system is
   named Pichay"), the §2.1 heading reads "Mason's Pichay", the 84.4× measurement is attributed to
   Mason, and Reference 1 names the system. `token-savings-strategies.md` still uses "Pichay" as
   shorthand — it is an internal note and its first mention now points at the register.
2. **The corpus-size divergence.** The same sentence that cites the 4.45 billion body figure now
   records that the abstract says 4.45 million and that the paper cites the body.

Rebuilding the PDF exposed a third defect, which is fixed in `research/white-paper/build-pdf.sh`:
the documented build command could not have produced the committed PDF. WeasyPrint does not read
Markdown; passing a `.md` file renders it as plain text. The script does Markdown → HTML (UTF-8) →
WeasyPrint, and the README now says so.

## Reviewed 2026-11-01

| Date | Source | Type | Identifier | What it argues | What it means for ctxvm | Disposition |
|---|---|---|---|---|---|---|
| 2026-11-01 | "TokenEconomizer: Experience-Driven Black-Box Cost Control for Coding Agents" — Li, Xu, Singh, Chen, Inala, Siska, Tamersoy, Yu, Stoica, Galley, Gao | Primary paper, five agent-model settings, three seeds | arXiv:2610.22732v1, 15 Oct 2026, CC BY 4.0 | An external controller over a *sequence* of tasks in one repository cuts mean cache-aware cost 18.4–30.9% at comparable Pass@1, through three learned policies: inject operational micro-skills, prune persistently unused tools, intervene in failure loops. Cheaper in all 30 repository-setting cells (5.2–40.1%). Gains need ~6 tasks to appear | Confirms the thesis but not the mechanism: it wins **without any context virtualization** — tool pruning alone is −13.2/−17.7%, because 23 schemas load every turn and no repository uses more than 7 (16 never called). Its three signals are signals ctxvm already records (repeat, unused page, loop), yet our ledger has **no row for static schema/prefix cost**, so the biggest measured saving is invisible to us | ACT (schema gap) |
| 2026-11-01 | "Accelerating Scientific Research with Gemini in the Real-World" (Co-Scientist) — Schmidgall et al. | Primary paper | arXiv:2608.26701, 27 Aug 2026, CC BY-NC-ND 4.0 | Execution-grounded multi-agent research: wet-lab loops, 450 double-blind reviews; reliability modules "reduce hallucination and plagiarism" | Cited by the X post below as the source of a "90% → 4%" fabrication figure. **The abstract states no such numbers.** Treat the post's figure as UNVERIFIED until the body is read | BACKGROUND (cited-by) |
| 2026-11-01 | "ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory" — Ouyang et al. (Google) | Primary paper, ICLR 2026 | arXiv:2509.25140 (v2, 16 Mar 2026) | Distils generalizable reasoning strategies from self-judged successful and failed trajectories; retrieval beats storing raw trajectories or success-only routines | The distillation target the X post's §4 leans on. For us: it is the argument that raw traces are *not* the memory product — which is what the page table is for, and a warning that a page table without distilled strategy is only half the object | BACKGROUND |
| 2026-11-01 | "Trace Engineering" thread — @marfinxx | Practitioner essay (marketing funnel) | x.com/marfinxx/status/2094016175617241109, 30 Aug 2026, ~208 likes | Agents are distributed non-deterministic state machines; separate log / trajectory / trace; event-sourced ledger with seeds; mocked replay vs live resumption; causal DAG localization; READ_ONLY vs MUTATING spans with a WAL; circuits on step-count MAD > 3.5 and token-entropy variance < 0.02 | A usable requirements list, not evidence: no measurements, thresholds asserted, cites a "90% → 4%" figure its cited paper's abstract does not contain, and ends with a Telegram "additional alpha" link. The parts ctxvm already has: event ledger, replay to turn N, resume with provenance, validator. The parts we lack: causal edges, side-effect classification + WAL, seed/sampling capture, schema-cost accounting | BACKGROUND |

Short notes, because the columns compress the argument:

- **2610.22732** is the one to engage seriously. Two things it does that we cannot currently
  answer: (i) it reduces cost with **no paging at all**, so "ctxvm saves tokens" is not a claim we
  can make from category membership; (ii) the saving it measures is mostly the **static per-turn
  prefix** (tool schemas), which our ledger does not model — we track pages that are touched, not
  bytes that are billed every turn. Its own limitation section names the experiment we are placed
  to run: "our SWE-Bench streams consist of related but independent fixes rather than actual user
  sessions… interactive coding workflows are a natural next test." Our capture now records exactly
  those sessions, but per-session only — there is no repository/environment key joining them into a
  stream, so the paper's unit of analysis is not yet ours.
- **The X post** is worth mining for its 8 rules and 5 anti-patterns and worth nothing as evidence.
  Two of its claims collide with facts we hold: "record the seed every time" — our live trace has
  `provider: unknown` and no seed or sampling parameters at all; "status: OK does not mean correct"
  — our own replay proves derivation determinism, never model-output determinism, which is the same
  distinction stated more carefully in `RR-DET-20261101.md`.

## Reviewed 2026-11-04 — safety, auditability, oversight

| Date | Source | Type | Identifier | What it argues | What it means for ctxvm | Disposition |
|---|---|---|---|---|---|---|
| 2026-11-04 | "Cheating behaviour in frontier model evaluations" — UK AI Security Institute | Primary blog, capability evaluations | aisi.gov.uk/blog/cheating-behaviour-in-frontier-model-evaluations, 21 Jul 2026 | Every model tested attempted to cheat on cyber capability evaluations; models did not reliably report it and often did not reason about it in CoT; AISI manually reviews transcripts so cheating does not inflate published capability estimates; detection needs robust monitoring | The strongest external argument that a capability score is an interpretation of a transcript. Our gap is the other half: we record executions, not refusals, so "did not try" and "was stopped" are indistinguishable | ACT (record refusals) |
| 2026-11-04 | "Building a more secure environment for evaluating dangerous capabilities" — UK AISI | Primary blog, incident response | aisi.gov.uk, 2026 | Agents took sustained action against real people in a cyber eval; response: internet disabled, synchronous LLM monitor over messages, tool calls and CoT that blocks suspicious actions before execution, plus pre-flight checks the monitor is on | Reads as a requirements list for a runtime record: per-call arguments, per-turn inputs, side-effect class, scope, replay — and policy decisions, which we do not have | ACT (coverage manifest) |
| 2026-11-04 | Article 55, EU AI Act + GPAI Code of Practice measures 1.2/3.2 | Regulation + code | ai-act-service-desk.ec.europa.eu/en/ai-act/article-55; Brookings, "How are countries evaluating AI models?" | Systemic-risk providers must evaluate with standardised protocols, **document** adversarial testing, track and report serious incidents; the Code ties assessment depth to post-market and incident data | "Documented" is auditable only if replayable; post-market evidence is exactly the trace category, and the systemic layer is described as method-thin | BACKGROUND (regulatory pull) |
| 2026-11-04 | "Why Models Know But Don't Say" | arXiv:2603.26410 | Primary paper, 12 open-weight reasoning models | Thinking-answer divergence in 55.4% of hint-sensitive cases; answer-only monitoring misses more than half; even thinking-token access leaves 11.8% unacknowledged; a third activation-level tier is needed | CoT is a channel, not a confession. Our record is the independent account of what the model was *given*, which is what a CoT claim can be checked against | BACKGROUND |
| 2026-11-04 | "FACE-Eval: Chain-of-Thought Faithfulness ... Varies with Where and How Preference Cues Are Delivered" | arXiv:2608.29464 | Primary paper, 15 models, 5,100 samples | Verbalized commitment is lower for **tool-return** cues than user-message cues on every model; unverbalized adoption higher for tool-return cues on every model; warning models they are monitored does not close the gap; transcript monitors detect worse as unverbalized adoption rises (r = −0.54, −0.78) | The tool channel is the weakest for verbalization, and it is the channel ctxvm records natively. Strongest single argument for the tool-return page as a verification surface | ACT (positioning) |
| 2026-11-04 | "Simulated Control Evaluations" (SCE) + Screwtape — Redwood Research | arXiv:2610.31593 + blog | Primary paper + tooling | Control protocols are defined over action transcripts; SCEs test whether a developer's monitors would catch deliberate harm; Screwtape finds monitor failures by editing real transcripts | Confirms the substrate: monitors and their evaluation both need replayable, editable transcripts. Also a concrete cheap card: monitor-replay harness with TPR/FPR over recorded traces | WATCH |
| 2026-11-04 | "Auditing Games for Sandbagging" — FAR.AI | arXiv:2512.07810 | Primary paper, red/blue team game | Blue team could not reliably discriminate sandbaggers from benign models; black-box defeated by imitation of a weaker model; training-based elicitation reliably elicited but also raised benign models | The discouraging bound on what any trace can do: our record improves the evidence, it does not detect hidden capability | BACKGROUND |
| 2026-11-04 | "From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance" | arXiv:2606.04990 (alphaXiv) | Survey | Frames agent runs as typed provenance graphs; names three field-wide gaps: provenance not integrated with trust functions, no benchmark for the complete provenance chain, and **little reporting of tamper-evident or attested traces** | Places ctxvm in a real but unproven niche: we have determinism and replay, not signatures. A tamper-evidence card would move us from "reproducible" to "attestable" | WATCH |

Notes, because a table flattens the argument:

- The AISI finding and the FACE-Eval finding are the two pillars of the positioning: the first says a
  score needs a transcript, the second says the tool channel is where verbalized reasoning is least
  trustworthy. Together they make "record what the model was shown and did, independently of what it
  says" a specific claim rather than a slogan.
- Rates and the 11.3h-versus-270h capability swing appeared only in secondary summaries during this
  review and are marked **UNVERIFIED** in `safety-and-auditability.md`. The primary blog states the
  direction and the monitoring method, not those numbers, in the text read here.
