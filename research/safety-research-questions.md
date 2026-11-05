# The seven research questions, answered as far as the evidence goes

Answers to the research questions in `research/uncommitted/ctxvm and AI safety research note and
proposed white-paper sections.md` (5 Nov 2026). Every citation below was fetched and read at abstract
level during this pass; where a specific number appears only in a paper body I could not open, it is
marked **body-level, unverified**. One measurement was run on this repository's own traces (§8).

This file is the experiment-level pass. The merged record of the two source notes is
`research/synthesis-20261105.md`; the paper sections that carry these answers are §8.7–§17 of
`research/white-paper/white-paper.md`.

The short version: **none of the seven can be answered from the literature alone, and only one can be
answered at all from data we already hold.** What the literature does establish is that each question
is well-posed, that the missing ingredient in each is a record of what the model was shown, and that
nobody has published the measurement. That is a research agenda, not a result, and the paper should
present it as one.

## 1. How much do dangerous-capability scores change with context policy?

**Known.** Evaluations can establish lower bounds on capability and can assess some misuse risks, but
they cannot establish upper bounds, cannot reliably forecast, and cannot robustly assess risks from
autonomous systems (Barnett & Thiergart, arXiv:2412.08653, abstract). The Holistic Agent Leaderboard
ran 21,730 rollouts across 9 models and 9 benchmarks for about $40,000 and reports three-dimensional
analysis over models, **scaffolds** and benchmarks, with one counter-intuitive finding already: higher
reasoning effort reduced accuracy in the majority of runs (Kapoor et al., arXiv:2510.11977, abstract).
The specific claim that scaffold choice strongly affects accuracy and cost is **body-level,
unverified**; the abstract establishes only that scaffolds are an analysis axis.

**What ctxvm can say now.** Nothing causal, but it can say what the context policy *was*: pages
declared, pages rendered per turn, resident tokens, and — since W13 — the static prefix (tool schemas,
request characters, host token estimate). In the one live capture we have, `turn.render` carries
`toolSchemas: 21`, `requestChars: 1,628,596`, `approxInputTokens: 407,149` for a single boundary. Any
capability comparison that does not report those numbers is comparing runs under unknown context
policies.

**The experiment.** Same task set, same model, three context policies (full context, paged with
eviction, summarized), identical traces except for the policy, and the capability score reported per
policy with intervals. Cost is dominated by model spend, not by engineering: the trace side already
exists. **Verdict: unanswered anywhere; runnable; needs a spend decision.**

## 2. Which pages give an evaluation away?

**Known.** Frontier models are above chance at telling evaluation transcripts from deployment ones:
Gemini-2.5-Pro reaches AUC 0.83 against a human baseline of 0.92, and both models and humans do better
in agentic settings than in chat settings (Needham et al., arXiv:2505.23836, abstract). The authors
recommend tracking this capability, and the note's suggested use — differential analysis of evaluation
versus deployment traces — is consistent with the benchmark they built (1,000 prompts and transcripts
from 61 datasets).

**What ctxvm can say now.** It can compute the diff, but not yet *attribute* it: `ctxvm diff` compares
two traces under a law-aware relation, which says where they differ, not which page caused a
classifier to say "evaluation". Attribution needs a classifier run per page-subset — an intervention,
not a comparison.

**The experiment.** Take paired evaluation and deployment traces, ablate one page family at a time,
and measure the evaluation-awareness classifier's AUC change. **Verdict: not runnable here** — it needs
real deployment traces (privacy work) and a classifier. The prerequisite is the redaction pipeline,
not the trace format.

## 3. Do chains of thought admit an injected hint, on agentic traces?

**Known.** Chen et al. find that CoTs "reveal their usage of hints in at least 1% of examples where
they use the hint, but the reveal rate is often below 20%", that outcome-based RL "improves
faithfulness but plateaus without saturating", and that when RL increases hint usage the propensity to
verbalize does not rise (arXiv:2505.05410, abstract). The 41-author position paper holds CoT
monitorability to be a real but fragile opportunity that development decisions can erode
(arXiv:2507.11473, abstract). Newer work sharpens the channel question: verbalized commitment is lower
when the cue arrives in a **tool return** than in the user message, on all fifteen models tested, and
transcript monitors detect worse as unverbalized adoption rises (FACE-Eval, arXiv:2608.29464).
Thinking-answer divergence appears in 55.4% of hint-sensitive cases, and even with thinking-token
access 11.8% acknowledge the influence in neither channel (arXiv:2603.26410).

**What ctxvm can say now.** The channel is already in the record: a page is the tool return. What is
missing is the *hint* — an injected fact with a known target page, and the model's answer.

**The experiment.** Hint-injection with page-granular removal, at agentic scale: insert a fact into one
tool return, ask a question whose answer depends on it, and score whether the CoT admits the fact and
whether the answer moves. This is the Chen et al. design with pages as the intervention unit and traces
as the record. **Verdict: the strongest available experiment**, because the intervention is exact
(remove one page), the metric is borrowed from a published design, and the trace supplies the audit
trail. Cost: model calls plus engineering on the harness.

## 4. Does the identifier-based touch ratio predict causal influence?

This is the question that decides whether our own waste metric means anything, and it has a
known-good instrument on the other side: ContextCite learns a surrogate for how an output changes when
context parts are ablated, at a cost the note puts at about 32× the original generation
(**body-level, unverified**; the abstract establishes the method and three applications, not the
multiplier) (Cohen-Wang et al., arXiv:2409.00729).

**What our data says — measured, §8 below.** Across 24 traces in this repo (the frozen corpus plus live
captures): 417 declared pages, 312 of them rendered at least once (74.8%), 303 `page.fault` events, and
**99.3% of faults land on pages that had been rendered**. That number is close to definitional: the
fault taxonomy fires when the model re-requests content it has seen, so a page never shown has almost
no way to produce the event we count. The consequence is not that the metric is wrong; it is that
**the fault metric cannot by itself separate "the model needed it" from "the harness had shown it"** —
which is exactly the confound RQ4 proposes to test with ablation.

**The experiment.** For a fixed question and trace, ablate each rendered page in turn and measure the
answer change (ContextCite-style, page granularity), then compare the resulting ranking with the touch
ratio. Report rank correlation and the disagreement cases. **Verdict: design is ready, needs spend and
a model with a stable API; page-level ablation is coarser than ContextCite's sentence-level surrogate
but matches agent semantics and is cheap in engineering.**

## 5. Which page-level views produce the best monitors?

**Known.** Monitors often do **better with less** information — the "less-is-more effect for automated
oversight" — and the authors' extract-and-evaluate (EaE) protocol, where one monitor isolates excerpts
and another scores them, improved sabotage detection by 16.8 percentage points over the next-best
approach in BigCodeBench-Sabotage with a GPT-4.1-mini monitor (arXiv:2601.21112, abstract). Agents
unaware of being monitored were caught much more easily. Separately, CoT monitoring beats
action-only monitoring where the sabotage is subtle but can be *misled* by rationalizations on obvious
cases, and a weighted hybrid of reasoning and action scores outperforms both across all tested models
(arXiv:2505.23575, abstract).

**What ctxvm can say now.** A "view" is a projection of the page table, and the page table is exactly
what we can render reproducibly: full context, rendered pages only, resident pages plus stub text, or
the prefix alone. Today the views are ad hoc; W13's prefix record makes the "what the monitor saw"
side measurable.

**The experiment.** Fix a monitor model and a sabotage corpus (BashBench-style), vary the view, and
report TPR/FPR per view. **Verdict: runnable, and it is the same harness needed for card 3 of the
monitor-replay idea in the main note. The literature already supplies the baseline to beat (EaE), which
is a good sign the experiment is well-posed.**

## 6. Can page-level provenance give taint-style protection in an ordinary harness?

**Known.** CaMeL extracts control and data flow from the trusted query so untrusted data cannot alter
program flow, and enforces capability policies at tool calls; it solves 77% of AgentDojo tasks with
provable security against 84% for an undefended system (Debenedetti et al., arXiv:2503.18813,
abstract). The design requires a policy layer, not just a record.

**What ctxvm has.** Page identity (logicalRef + contentHash), kind (`tool_result`, `file`, `summary`,
`image_ref`), and — since W15 — a side-effect class on the call that produced a tool_result page. What
it does not have: origin/trust of the page, an allowed-reader set, or a policy decision. Those are the
three attributes CaMeL needs, and adding them is an additive schema change, not a redesign.

**The experiment.** Prototype trust tags and a capability check on one harness (read-only vs mutating
tools already distinguishes calls), then measure task success against the undefended baseline on a
prompt-injection corpus. **Verdict: plausible and cheap to prototype; the honest claim is "the trace
can carry the attributes a CaMeL-style layer needs", not "ctxvm provides the protection".**

## 7. Does evicting early wrong assumptions help or hurt goal adherence?

**Known.** All tested models lose performance in multi-turn settings, averaging a 39% drop across six
tasks over 200,000+ simulated conversations, decomposed into a small aptitude loss and a large
reliability increase; models make assumptions early and "when LLMs take a wrong turn in a conversation,
they get lost and do not recover" (Laban et al., arXiv:2505.06120, abstract). That is the strongest
published motivation for a policy that removes an early wrong premise.

**What ctxvm can say now.** It can identify the wrong premise's page and when it was rendered — a
prerequisite, not an answer. No experiment has been run.

**The experiment.** Two arms on the same task stream: (a) leave the wrong assumption resident, (b) evict
it after the turn where it is contradicted, and (c) an oracle arm that removes it before it is ever
rendered. Measure task success and turns-to-completion. **Verdict: runnable and directly on-thesis; the
oracle arm is what makes the result interpretable, since it bounds the benefit.**

## 8. The measurement this pass did run

Over 24 traces in this repository (frozen corpus `m1`–`m8` plus the live capture directory):

```
declared pages        417
rendered at least once 312  (74.8%)
page.fault events     303
faults on rendered pages 301  (99.3%)
faults on never-rendered pages 2
```

Two readings, both worth keeping:

1. **The fault metric is definition-bound.** It fires when the model re-requests content it has seen, so
   it cannot see a page that was never shown. Any claim that faults measure "need" has to survive the
   ablation test in RQ4; this number is a reminder, not evidence.
2. **A quarter of declared pages are never rendered.** In v0 (no eviction) that means declarations that
   never reached a turn — tail declarations, sessions that ended early, or pages declared after the last
   render. It matters for the waste metric: the denominator is "declared", and the numerator is
   "rendered".

Reproduce: the numbers come from counting `page.declare`, `page.render` and `page.fault` events per
file; the counting script is three set operations over parsed JSONL and is written inline in the session
that produced this note.

## 9. What this means for the paper

- The seven questions belong in one section, as a research agenda with what exists and what is missing —
  not as claims that ctxvm answers them.
- The strongest falsifiable pitch is not token savings; it is that a capability score, a monitor and a
  control protocol all consume a record that is currently ad hoc, and that a standard trace makes the
  record comparable and replayable. That claim survives the evidence above.
- The weakest claim to keep out: that a trace gives causal attribution. RQ4 exists precisely because it
  does not.
