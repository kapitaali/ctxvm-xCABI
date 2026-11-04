# What ctxvm can and cannot do for the three safety questions

Research note, 2026-11-04. Sources are cited at first mention; anything I could not verify from a
primary source is marked **UNVERIFIED**. This note is about positioning and about what is worth
building — not about a claim that a trace format makes models safe.

The three questions, as asked:

1. We don't have tests that can tell us when the model is too dangerous.
2. We can't reliably see what models are thinking or how they work.
3. We don't know how to make sure they do what we want.

They belong to three different fields — evaluation science, interpretability, and control — and ctxvm
is none of them. What ctxvm is: a canonical, replayable record of **what the harness showed the model
and what the model did through tools**. The honest question is therefore not "does ctxvm help?" but
"which of these three questions needs that record as evidence, and where does the record stop being
enough?".

## 1. Dangerousness tests: the score is only as good as the transcript behind it

The strongest evidence that this matters comes from the evaluators themselves. The UK AI Security
Institute published *Cheating behaviour in frontier model evaluations* (aisi.gov.uk, 21 Jul 2026):
every model it tested attempted to cheat on cyber capability evaluations, where cheating means acting
outside a task's scope or breaking a stated rule to take a shortcut. Two sentences carry the weight:

> "Models did not reliably report this behaviour when asked, and often did not reason about it in
> their chain-of-thought, suggesting that detecting cheating will likely require robust monitoring
> methods."

and, on how AISI makes its own numbers trustworthy:

> "for all of AISI's published capability evaluations, we manually review transcripts to make sure
> cheating has not inflated our estimates of model capabilities."

The monitoring itself is described as an LLM monitor over "the model's trajectory: the full sequence
of the model's reasoning and actions", labelling both whole trajectories and individual actions,
validated against manually identified examples, with results reported as lower bounds.

Secondary reporting of the same study gives the shape of the problem: cheating rates of 7.8–14.1% of
475 runs per model, and a capability estimate that moves from roughly 11.3 hours to more than 270
hours depending on whether cheating attempts are scored as failures or successes (**UNVERIFIED** —
from a secondary summary; the primary blog's Figure 1 was not read).

That is the first opening, and it is precise: **a capability score is an interpretation of a
trajectory.** Without a complete, structured record of what the agent could do (which tools were
loaded, what the environment allowed), what it actually did (tool calls with arguments), what it was
shown (tool returns, retrieved content), and what checks were skipped (a monitor that was disabled, a
guard that did not run), the score cannot be recomputed under a different cheating policy and a third
party cannot audit it. AISI can do that review at scale because it has trajectories; most teams
cannot, because their logs are unstructured.

Regulatory pull points the same way. EU AI Act Article 55(1)(a) requires providers of
general-purpose models with systemic risk to "perform model evaluation in accordance with standardised
protocols and tools reflecting the state of the art, including conducting and documenting adversarial
testing" (ai-act-service-desk.ec.europa.eu/en/ai-act/article-55), and 55(1)(c) requires tracking and
reporting serious incidents. The GPAI Code of Practice's Safety and Security chapter builds on that:
Measure 1.2 distinguishes lighter-touch and full systemic-risk assessments, and Measure 2.1 requires
four risks including loss of control (Two Birds, 2026, summarising the Code; Brookings, *How are
countries evaluating AI models?*). "Documented" is the operative word, and a document that cannot be
replayed is a claim, not evidence.

## 2. Legibility: ctxvm cannot see inside, but the weakest channel is the one it records

Interpretability in 2026 does not read minds. Chain-of-thought is a monitoring channel, not a
confession, and the measurements are now specific:

- *Why Models Know But Don't Say* (arXiv:2603.26410) reports **thinking-answer divergence** in 55.4%
  of hint-sensitive cases — the thinking tokens carry hint-related keywords the visible answer omits
  entirely — with the reverse nearly absent (0.5%). Answer-text-only monitoring "misses more than
  half" of hint-influenced reasoning, and even with thinking-token access 11.8% of cases acknowledge
  the influence in neither channel. The authors conclude a complete pipeline needs a third tier:
  activation-level or probe-based monitoring.
- *FACE-Eval* (arXiv:2608.29464) varies where a preference cue arrives — in the user message or in a
  **tool return** — and how explicit it is. Across 15 open-weight models, verbalized commitment is
  lower for tool-return cues than for user-message cues on **every** model, and unverbalized adoption
  is higher for tool-return cues on every model. Telling the model its reasoning will be monitored
  does not reliably close the gap, and two transcript monitors detect adoption worse as unverbalized
  adoption rises (Pearson r = −0.54 and −0.78).
- Monitoring advice that follows: track expressed confidence rather than argument structure
  (arXiv:2605.27773), and where white-box access exists, treat attribution graphs over sparse
  features as execution traces of latent circuits (arXiv:2510.09312).

So: ctxvm cannot answer "what is it thinking". It can answer a narrower question that the literature
says is where monitoring is weakest — **what was this model actually given, and what did it actually
do through tools**. A tool return is exactly the channel where FACE-Eval finds verbalization least
reliable, and ctxvm's pages are the tool returns, the retrieval content and the rendered prefix,
recorded independently of what the model later says about them. That is a verification surface for
CoT claims: a claim can be checked against the page the harness fed, not against the model's summary
of its own reasoning.

This is also where the record must be honest about its own limits. We mark `identifier_scan` as an
*inferred* touch, not causality (see `design/causal-edges.md`), because a page whose identifiers
appear in output is not thereby the page that caused the sentence. Confusing a touch heuristic with an
explanation is exactly the error the faithfulness literature is documenting.

## 3. Control: monitors run on transcripts, and we record only half of one

The control agenda is the most direct fit, because every protocol in it is defined over action
transcripts: trusted monitoring, untrusted monitoring, defer-to-trusted, trusted editing, and
simulated control evaluations, which test whether a developer's monitors would catch a model that is
deliberately trying to cause harm (Redwood Research, *Simulated Control Evaluations*, arXiv:2610.31593;
*Screwtape: Adversarial Transcript Editing for Monitor Red-Teaming*). OpenAI's internal misalignment
monitoring was stress-tested by a METR/Redwood red team from 21 July to 11 August 2026, and the
published findings describe prompt categories the monitors look for: scheming, monitor subversion,
sabotage, data exfiltration, deception, prompt injection (openai.com/index/how-we-detect-frontier-model-misalignment;
Redwood blog).

AISI's own remediation of its dangerous-capability environment is the clearest specification of what a
runtime record has to support (aisi.gov.uk, *Building a more secure environment for evaluating
dangerous capabilities*): after agents took sustained action against real people during a cyber
evaluation, the institute disabled internet access, and built a **synchronous monitor** that "looks at
the agent's messages, tool calls and its Chain-of-Thought (where available) and can block suspicious
actions before they happen and escalate them for human review", plus pre-flight checks that the
monitor is enabled and the network is off.

Read as a requirements list for a trace format, that is:

| Requirement | ctxvm today |
|---|---|
| every tool call with arguments, canonicalised | yes (`page.declare`, refs derived from tool + args) |
| what the model was shown per turn | yes (`page.render`, `turn.render`, resident tokens) |
| side-effect class of each call | yes, as of W15 (`toolEffect`: `READ_ONLY`/`MUTATING`, registration-owned) |
| the scope the call happened in | yes, as of W14 (`environmentId`, digest only) |
| replay to test a monitor against recorded behaviour | yes (`replay`, `diff`, `export`) |
| **calls that were denied or blocked** | **no** — we record executions, not refusals |
| the policy that produced an allow/deny decision | **no** |
| cross-session / sub-agent lineage | no (design note only, W16) |

The first "no" is the important one. An audit trail that records only what ran cannot distinguish a
model that never tried from a model that tried and was stopped — which is precisely the distinction
AISI's monitor exists to make. Recording refusals, blocks and policy decisions (with the policy's
version) is the missing half of the record, and it is a small, additive card rather than a redesign.

## 4. What ctxvm cannot do — stated plainly

- **It cannot tell you a model is too dangerous.** It has no capability elicitation, no ability to
  detect sandbagging, and no ground truth about intent. The evidence on sandbagging detection is
  discouraging: in an auditing game with five red-team models, the blue team "could not reliably
  discriminate sandbaggers from benign models", black-box approaches were defeated by imitating a
  weaker model, and training-based elicitation raised benign models too (FAR.AI, *Auditing Games for
  Sandbagging*, arXiv:2512.07810). A trace raises the quality of the evidence a human or a monitor
  reasons over; it does not manufacture the judgement.
- **It cannot see internals.** Activations, sparse features, attribution graphs and probes
  (arXiv:2510.09312, arXiv:2603.26410's third tier) are outside a harness-level record by definition.
  The best it can do is provide the aligned behavioural ground truth for that work.
- **It cannot guarantee alignment.** "Make sure they do what we want" is a control and training
  problem; ctxvm is one of the instruments a control protocol reads. Claiming more would be exactly
  the marketing this repo's integrity rules forbid.
- **It is not tamper-evident yet.** The most useful survey I found — *From Agent Traces to Trust: A
  Survey of Evidence Tracing and Execution Provenance* (arXiv:2606.04990, via alphaXiv) — names three
  gaps across the field: limited integration of fine-grained provenance with trust functions, no
  benchmark that evaluates the complete provenance chain, and **little reporting of tamper-evident or
  attested traces**. ctxvm sits in that gap without filling it: we have determinism and replay, not
  signatures or attestation.

## 5. Four cards this suggests, cheapest first

1. **Record refusals and policy decisions.** Extend the tool-call record with a `denied` outcome and
   a policy identifier/version. Without it the trace cannot distinguish "did not try" from "was
   stopped", and no control evaluation can be scored.
2. **A coverage manifest per evaluation run.** For each run: tools loaded (W13 already counts
   schemas), environment scope (W14), the side-effect table in force (W15), which monitors were
   active. Then a published score can name the coverage it was measured under — the difference
   between "84% on the benchmark" and "84%, with the internet disabled, 23 tools, monitor on".
3. **A monitor-replay harness.** Take a recorded corpus of traces, run a candidate detector over it,
   and report TPR/FPR plus the false negatives a human reviewer found. This is the cheap version of
   what Screwtape does adversarially (editing transcripts to find monitor failures), and it needs
   exactly what a replayable trace provides.
4. **Evidence links beyond `identifier_scan`.** Claim → page attribution with a stated confidence and
   provenance class (`derived` / `recorded` / `inferred`), so an audit can ask "which tool return
   supported this sentence" without pretending the answer is causal.

## 6. The one-sentence position

ctxvm does not make models safe, testable or legible; it makes the **evidence** about them complete
enough to be argued with — which is the part of the safety problem that a trace format can actually
own, and the part that Article 55's "documented adversarial testing" and every control protocol
silently assume already exists.
