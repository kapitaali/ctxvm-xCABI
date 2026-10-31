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
