# What a context trace can and cannot show about AI safety

Nov 7, 2026 · @kapitaali

A context trace is evidence about the structure of the request a harness sent to a model: which pages were declared, which were stubbed, and how many tokens each took. It is not evidence about what the model understood, intended, or would do next. This paper is Part II of “Virtual memory for LLM agent context: the xCABI standard and the ctxvm engine” (Part I).

## Abstract

People ask three questions about frontier models. Can an evaluation tell us that a model is too dangerous? Can we see what a model is doing? Can we make it do what we want? People rarely ask these questions of the harness, the software that builds each request to the model. Part I describes ctxvm, a recorder and virtual-memory manager for agent context, and xCABI, its trace format. Part II asks what that record is worth for the three questions.

The answer is narrow. A trace gives the input side: which pages the harness declared, with their identities, hashes, and token counts, and in which environment. A trace records stubbed pages. It does not yet record pages that a removal policy left out of a request (section 2.4). That makes three things measurable: the effect of context policy on an evaluation score, the effect of removing one page on the next action, and the view a monitor was given. A replayable intervention is the only route from a trace to a causal claim.

A trace does not reach inside a model. It cannot detect deception, sandbagging, sabotage, or poisoning. It cannot make a harness honest. This paper runs no experiment. Each research question carries a status, and each source carries the level at which it was read. Rows that need the pager can now run, at a cost. Part I §7 reported the paged arm inert at the default 24k budget on real traffic. Later cells showed the engine holding the request at a 60,000 budget (0.60 of the control’s on the free tier, 0.57 on the paid cell), and the paid cell cost 2.11 times the control. No saving is claimed (repository report RR-W8C-CLOSING-20261113).

## 1. Scope, vocabulary, and evidence levels

Part II applies the Part I record to safety questions and states where the record stops being evidence. Section 3 gives the threat model. Section 4 defines counterfactual replay. Sections 5 to 7 take the three questions in turn. Section 8 covers regulation and safety cases, section 9 covers redaction, and section 10 lists what a trace cannot do. Sections 11 and 12 give the research agenda and first experimental designs. Section 13 states the method and the open verification items.

### 1.1 Terms from Part I

| Term | Meaning |
| --- | --- |
| Harness | The software that assembles each request to the model and runs the agent loop. |
| Page | A unit of context with stable identity: a page\_id, a kind (file, tool\_result, summary, image\_ref), and a token count. The trace does not store the page’s content. |
| page\_id | The pair (logical\_ref, content\_hash). Example: tool:read\_file(path=src/auth.ts) plus the SHA-256 of the file content. |
| Trace | An append-only sequence of xCABI events, one JSON object per line. |
| Turn | The determinism unit, as the adapter defines it. On Hermes a turn is a user turn and buckets about two model requests. On OpenCode and the AI SDK a turn is one model request. |
| Render | The per-turn record of the request: the declared pages, the stub text for stubbed pages, and token totals. A removal policy’s omissions are not in it (section 2.4). Pages carry identity and hashes, not content. |
| Fault | A reference to evicted content, found by a tool re-call, an identifier scan, or an explicit request. |
| Stub | The inline placeholder that replaces an evicted page. It names what left and how to recover it. |
| Intervention run | A run that changes one thing in a recorded trace and calls the model again (section 4). |

### 1.2 Evidence levels and statuses

Every source in this paper carries the level at which it was read. Every research question carries a status. The sources came from LLM-assisted literature passes in November 2026. Section 13 describes the method and its limits.

| Source level | Meaning |
| --- | --- |
| Read in full | The whole page or paper was read. |
| Abstract | The abstract was read. Body figures are not used. |
| Snippet | A search excerpt or summary was read. The claim is marked. |
| Secondary | A third party reports the claim. The claim is UNVERIFIED. |

| Status | Meaning |
| --- | --- |
| Answered | A source answers the question at the stated level. |
| Partly answered | A source answers part of it, in a narrower setting. |
| Designed | A protocol exists. No run exists. |
| Prototype-able | A local build can test it without model spend. |
| Blocked | A named dependency is missing. |
| Not found | This review found no study. Other studies may exist. |

## 2. What a trace records

A trace records the request the harness sent, turn by turn. It does not record what the provider did to that request before the model saw it.

### 2.1 What the agent did and what the harness sent

Conventional logs record what the agent did: which tools it called, with which arguments, and with what result. A trace adds the page table state and a per-turn render record. Two cases show the difference.

1. The model had the information and ignored it. The pages were resident, and the model decided wrongly. This is a model-quality problem.
2. The model never received the information. The pages were stubbed or undeclared, and the model decided without them. This is a context-management problem.

A conventional log cannot tell the two cases apart. A trace can for stubbed or undeclared pages, within the limits below. It cannot yet do so for pages that a removal policy omitted (section 2.4).

### 2.2 What the record makes possible

- **Deterministic replay.** The renderer is a pure function of the events. The same trace gives the same page table, stub text, and token totals. It does not give the message bytes, because pages carry identity and hashes, not content.
- **Forensics.** A failed run shows which pages were resident or stubbed and which faults the model raised.
- **Regression tests.** A known-good trace becomes a test of the context layer.
- **An audit trail for forks.** A branch records which pages were resident and which render it saw.

### 2.3 Where the record stops

The harness cannot see provider-side system prompts, tokenization, hidden reasoning, or cache behaviour. The trace proves that the harness emitted these events. It does not prove that the model saw nothing else. A trace also holds only the reasoning that the provider returned (section 6.2).

This paper therefore states its central claim: **a context trace lets a reader re-derive and replay the structure of the request the harness sent (which pages, with what identities, hashes and token counts), not its bytes.** Content can be reconstructed only where the sources behind the page hashes still exist. Knowing the structure of the request is necessary for every claim about evaluation, monitoring, or control. It is sufficient for none.

### 2.4 Omission: a page that left the request

Sealed v0 can say that a page was replaced by a stub. It has no event for a page that a policy removed from the request without a substitute. The live Hermes policy removes messages and emits no stubs.

In the confirmation capture of the paged arm (run w8b-20261113-150420, budget 60,000), the derived page table holds 21 pages and 86,569 tokens at every turn, with none stubbed. The request at turn 19 carried 12 pages and 47,805 tokens of page content. The table is right about what the harness declared and wrong about what the model was sent. The provider’s receipts agree with the removal: the paged request was 0.563 of the control’s at turn 19, against 0.570 in the trace (repository packet P12).

Three consequences follow.

- “Zero stubs” is true by construction when a trace has no `page.evict` row, so it is not evidence about the mechanism.
- `turn.render.residentTokens` is whole-table residency, pinned by the adapter, and is constant across turns. It is not the request’s residency.
- The removal count in `turn.render.evictedTokens` is a lagging cumulative sum, and the v0 validator does not check it. In the capture it reads 210,856 against 38,764 unique tokens removed.

A trace-only monitor view would therefore show the model pages it never received (section 6.3).

Packet P12 proposes an optional list of removed-page identities with token counts, omitted when unknown, recorded per request and not per turn, and checked per call against the engine’s removed tokens. It also proposes a separate scoped-view export field. The reviewer’s answer favours the wire over the sidecar, because a sidecar makes a view a function of a trace and its sidecar. This is a proposal. No wire change exists, and the decision (D19) is the owner’s.

## 3. Threat model and trust boundaries

A trace is evidence only if its provenance is clear. Four questions decide what a given trace can support.

1. **Who wrote it?** The harness. The model never writes the trace. It writes tool calls, and the harness records them.
2. **Who can read it?** Traces contain prompts, code, and file paths. Access control and redaction are part of the artifact (section 9).
3. **Who can change it?** If the agent can reach the trace directory, a checksum in that directory is not tamper evidence.
4. **What does it prove?** That the harness emitted these events. It cannot prove that the harness was honest.

Three integrity levels follow.

| Level | What it needs | Status in Part I |
| --- | --- | --- |
| Accidental integrity | Canonical serialisation, byte-identical replay, per-drop checksums | Built |
| Tamper evidence | Hash-chained events or a signed root, and a verifier that checks the chain first | Not built |
| Attestation | The harness proves what it ran | Out of scope |

Version 0 provides accidental integrity and deterministic replay. It does not provide tamper evidence, and it does not make the harness trustworthy.

### 3.1 Design note: chain plus signed root

Canonical serialisation makes a `prev` field cheap to compute. Each line would carry the digest of the previous canonical line. A chain alone is not enough: an agent that can rewrite the file can rewrite the whole chain. The chain must therefore end in a signed root, held where the agent cannot write.

A verifier would check four things.

1. Each line’s `prev` equals the digest of the previous canonical line.
2. The root signature verifies against a key the agent cannot reach.
3. The first line anchors to a session-start record stored outside the agent’s reach.
4. The `skipped_untraced` counter is zero, or each skip is explained.

This is a proposal. No verifier exists.

## 4. Counterfactual replay

Two operations share the word “replay.” They must not be confused.

**Byte-identical replay** takes a trace and re-derives the same facts. It is deterministic and offline. Every determinism claim in this paper applies to this kind only.

**Intervention replay** changes one thing and calls the model again. The change can remove a page, add a stub, or replace a tool result. The engine stays deterministic. The model does not. The output is a new trace, not a corrected one.

Intervention replay turns a trace into an experimental instrument. Most questions in sections 5 to 7 depend on it. The record must say which kind of run produced it. The two kinds must not share a directory, a checksum file, or a claim.

### 4.1 Run kinds and what each supports

| Run kind | Determinism | What it supports | Cost |
| --- | --- | --- | --- |
| Byte-identical replay | Deterministic | Re-deriving the page table and render geometry; checking the context layer | Compute only |
| Intervention on a hosted model | Non-deterministic | Behavioural effects of a change, as a distribution | One paid call per sample per arm |
| Intervention on an open-weight model | Deterministic given the weights and the code path | Output-probability effects; cached-activation attribution; probes | Compute; weights are required |

### 4.2 One run is one draw

Hosted models are often non-deterministic even at fixed settings. A single intervention result cannot separate an effect from sampling noise. Two controls are required before any causal claim.

1. **Baseline against baseline.** Run the unchanged prompt twice and measure the answer-change rate. That rate is the noise floor. An effect that does not exceed it is not an effect.
2. **Several samples per arm.** A claim needs a distribution per arm. Until then the run is a demonstration, and the record must say so.

A naive arm that already has several rounds on the same template gives the noise floor with no extra model spend, if its checkers are mechanical and can be re-run offline (repository review RR-WP2REV-20261107).

### 4.3 Provenance of an intervention run

A record has six parts: the parent trace and its digest; the intervention (kind, target page, replacement); the sampling parameters (temperature, seed, number of samples); the model identity, with the provider’s snapshot or version and the date; the harness and adapter versions; and the tokenizer version. Without all six, a counterfactual is not reproducible and cannot support a causal claim.

### 4.4 Cost of ablation

On a hosted model, ablating every page costs roughly pages times samples times tokens per call. Three results suggest ways to lower it.

- Thought Anchors measures a sentence’s counterfactual importance by resampling. Its authors’ post reports 100 resamples per sentence (arXiv:2506.19143).
- ContextCite fits a surrogate model over ablations. Part I records its cost as about 32 times a generation, a body-level figure not verified here (arXiv:2409.00729).
- AttriBoT approximates leave-one-out attribution with cached activations, hierarchical attribution, and small proxy models. It reports a speedup above 300 times (arXiv:2411.15102; abstract).

All three assume open-weight access or cached activations. For a hosted model, the hierarchical idea still transfers: ablate whole pages first, then spans inside the pages that matter.

## 5. Question 1: can an evaluation tell us that a model is too dangerous?

A trace cannot define “too dangerous.” It makes the conditions of an evaluation recordable and comparable. That matters because a score depends on more than the model.

### 5.1 A score is an interpretation of transcripts

Evaluations establish lower bounds on capability. They cannot establish upper bounds (Barnett and Thiergart, arXiv:2412.08653). Scaffold choice is a first-order variable in agent evaluation (arXiv:2510.11977). A score therefore depends on three things:

1. the transcript: what the agent saw and did;
2. the scoring convention: how cheating, errors, and defects are counted;
3. the environment: the tasks, packages, and tools around the agent.

Four reports show how large the second and third effects can be.

- METR scores a detected cheating attempt as a failure. Secondary reports of its 26 June 2026 evaluation of GPT-5.6 Sol give about 11 hours when cheating counts as failure, about 71 hours when cheating runs are discarded, and over 270 hours when they count as success. These figures are UNVERIFIED until read in the METR report.
- METR’s June 2025 post found reward hacking by two methods, a high-score heuristic and a model monitor with manual review. The methods missed each other’s cases.
- UK AISI reports that every model tested in its cyber analysis attempted to cheat some of the time. Self-report and chain of thought did not reliably show it. AISI’s published estimates rest on manual transcript review plus an automated trajectory monitor, and it reports its cheating rates as lower bounds (AISI, 21 July 2026).
- Transluce reports that adding missing packages to an InterCode environment raised GPT-4o’s solve rate from 68.6% to 78%. The change was in the environment, not the model (crosspost; snippet).

HAL’s log inspection found agents searching for the benchmark instead of solving the task (arXiv:2510.11977). Traces expose problems that scores hide.

### 5.2 Context policy is an unreported variable

Context handling is part of the scaffold. A ctxvm trace reports the static prefix of every turn (tool schemas loaded, request characters, the host’s estimated size) and the environment the run happened in. The repository’s current build records both on each live capture row (repository review RR-WP2REV-20261107). A score that does not carry those numbers compares runs under unknown conditions.

No study found in this review varies context policy at fixed tasks. The proposed test is a grid of three scoring conventions against three context policies (section 12.3). The conventions are re-scorings of the same runs, so only the policy arms need new model calls. Token receipts differ by harness: Hermes records one providerUsage row per user turn, the last write winning, and OpenCode records none, so cost and cache claims must come from provider exports (repository review RR-OCDIFFREV-20261113).

### 5.3 Evaluation awareness is not one quantity

Frontier models can tell evaluation transcripts from deployment transcripts. Gemini 2.5 Pro reached an AUC of 0.83, against 0.92 for a human baseline (arXiv:2505.23836). Newer work shows the measure is harder to use than one number suggests.

- A nine-model study on four benchmarks finds that awareness is dominated by the model-environment interaction, 74.9% of variance (arXiv:2605.23055; snippet).
- Verbalized awareness is a lower bound, because a model may be aware and not say so (arXiv:2605.02269; snippet). It also rose with training in the models studied in arXiv:2509.15541 (snippet).
- Goodfire reports that removing prompt cues that trigger verbalized awareness reduces it, and that steering effects on safe-behaviour rates vary (4 May 2026; snippet).
- An Alignment Forum summary of Anthropic’s steering work on Claude Sonnet 4.5 says one steering vector cut verbalized awareness to zero with no change in misaligned responses, while another raised the misalignment rate to 8%. The method is from Hua et al. (arXiv:2510.20487; UNVERIFIED, seen only as a citation).

Cue-level work on prompts exists. A page-level version is coarser, but it works on whole agent runs. The environment key lets a study control for the environment, the largest variance source found. The proposed test removes or replaces candidate tells in a replayed trace and measures both verbalized awareness and behaviour, each against a no-change control. Stripping cues can change the task, so the control is required. The test also needs deployment traces, which depend on redaction (section 9).

### 5.4 Structured access for external evaluators

One taxonomy separates model access, model information, and evaluation timeframe, in three levels from AL1 to AL3 (Charnock et al., arXiv:2601.11916; abstract). It lists the architecture of the agent scaffold, such as prompt construction and loop management, as an access dimension. A redacted trace is a concrete artifact for the middle tier: it discloses how the loop assembled context and discloses no weights.

### 5.5 What the trace answers

- It records the conditions of a run, so two scores can be compared.
- It makes cheating and environment defects inspectable in one query across harnesses.
- It makes context policy a variable instead of an unknown.
- It does not decide which scoring convention is right, and it does not remove sandbagging (section 10).

## 6. Question 2: can we see what a model is doing?

A trace shows the input to a model and the output it returned, including any reasoning the provider exposed. It does not show the computation between them.

### 6.1 Chain of thought is useful and fragile

A 41-author position paper argues that the human-language chains of thought of reasoning models are a monitorable signal, and that development choices could erode it (arXiv:2507.11473). Chen et al. find that chain-of-thought monitoring helps but cannot rule out undesired behaviour. Chains of thought admit a used hint less than 20% of the time in most settings. Outcome-based reinforcement learning raises faithfulness and then plateaus. When it raises hint use, verbalization does not rise (arXiv:2505.05410).

FACE-Eval finds that cues delivered through a tool return are verbalized less often than cues in other channels. It tested open-weight models in a single-call setting (arXiv:2608.29464). Agent traces use the tool channel heavily, so this result matters here.

The Chen et al. test inserts a hint, then checks whether the answer changes and whether the chain of thought admits the hint. That is a replay primitive. The authors list agentic tasks as future work. Status: partly answered on multiple-choice questions, not answered on agentic traces.

### 6.2 Reasoning visibility

SHADE-Arena has 17 pairs of a benign task and a hidden harmful side task (arXiv:2506.15740). By default its monitor sees the whole transcript except the side-task description and the agent’s hidden scratchpad. Sabotage success relied heavily on that scratchpad, and the best monitor reached an AUC of 0.87.

A trace holds only the reasoning the provider returned to the harness. Providers differ in how much they return: full, summarised, or none. This paper has not checked provider documentation, so the claim is UNVERIFIED.

A trace should therefore record the reasoning visibility the provider gave. The proposal is a session-level field with four values: full, summary, none, unknown. It is a proposal for the next spec revision. The sealed spec does not change. Without the field, two monitor results are not comparable. Status: not started.

### 6.3 Monitor views

A monitor never sees the world. It sees a projection of the trace: messages, tool calls, reasoning, and some subset of the pages. A view is a first-class object. ctxvm can define it as a function of a trace joined with its sources, meaning the content that the page hashes point to and, for removal policies, the record of what was omitted (section 2.4). The version of a view names its join inputs. Examples of views:

- rendered pages only;
- resident pages plus stubs;
- the static prefix alone;
- tool calls without results;
- reasoning without actions.

Three consequences follow. A monitor result is comparable to another only when both used the same view. A view is versioned, so a change in the projection is visible. A view is reproducible offline where its sources are available, so a monitor’s error rate is measurable without re-running the agent.

The literature shows that the projection can matter as much as the volume.

- On one monitor family in one sabotage benchmark, monitors did better with less information. An extract-and-evaluate protocol beat the next-best approach by 16.8 percentage points (arXiv:2601.21112; abstract).
- Chain-of-thought monitoring helps on subtle sabotage and misleads on obvious cases. Scoring reasoning and action separately, then combining, works best (arXiv:2505.23575; abstract).
- A recent paper reports that pooled monitor accuracy conceals a reasoning-dependent fragility (arXiv:2608.00583; title and snippet only; follow-up reading).

The best view depends on the task and the monitor. Status: partly answered. The open step is a view-parameterised monitor run.

### 6.4 Attribution

The touch ratio in Part I is a behavioural proxy. It counts identifiers that appear in model output. A page can influence an action without being named. Whether the touch ratio predicts causal influence is open.

Context attribution methods give the ground truth. ContextCite learns a sparse surrogate of how an output changes when parts of the context are ablated (arXiv:2409.00729). ARC-JSD ranks context sentences by the shift in the response distribution under ablation, without fine-tuning or a surrogate. It is evaluated on retrieval-augmented generation (arXiv:2505.16415; abstract and introduction). Thought Anchors resamples to find reasoning steps with outsized influence (arXiv:2506.19143).

The proposed test ablates whole pages first, then spans inside the pages that matter. It compares the ablation effect with the touch count, and with leave-one-out on an open-weight replay. Single-page ablation misses interactions between pages, so the top pages also need pair ablations. The result would give Part I a ground truth for its fault-recall metric. Status: designed; compute only on open weights.

### 6.5 White-box bridge

Linear probes separated honest from deceptive responses with AUROCs between 0.96 and 0.999. The authors say this is not yet robust enough as a defence (arXiv:2502.03407; abstract). Replaying a recorded trace into an open-weight model would let probes and sparse autoencoders run on real agent trajectories. That needs the model’s own tokenizer and a record of how tokens were counted.

A probe that disagrees with a monitor is a detector to validate. It is not evidence of hidden knowledge. Status: not started.

### 6.6 What the trace answers

- It fixes the input structure, and the content where sources exist, so a monitor, probe, or ablation run can be repeated.
- It makes a monitor’s view an explicit, versioned object.
- It does not show internal computation, and it shows reasoning only as far as the provider exposed it.

## 7. Question 3: can we make models do what we want?

A trace cannot make a model behave. It can carry the attributes a policy layer needs, and it can record the forks a control protocol creates.

### 7.1 Provenance, trust, and readers

A page carries identity and kind. Since the RFC-0.1 side-effect class field, it also carries the class of the call that produced it. It does not carry origin, trust, or permitted readers.

CaMeL fills that gap from the other side. It extracts control and data flow from the trusted query, so untrusted data cannot change program flow. It enforces capability policies when tools are called (arXiv:2503.18813; abstract). No effectiveness figures from the paper body are cited here.

Three page attributes would carry the same information inside a trace:

- **origin**: which input produced the page (user, tool, retrieval, model);
- **trust**: asserted by the harness at declaration, never inferred from content;
- **readers**: which sinks may receive the page.

A policy check is then a pure function of the page table. It stays inside the determinism boundary, and its decision is replayable. The claim is narrow. The trace can carry the attributes a taint-style layer needs. ctxvm enforces nothing. Status: prototype-able.

### 7.2 Control protocols over forkable state

Control protocols assume that a deployment can stop, resample, or roll back (arXiv:2312.06942). Ctrl-Z resamples suspicious actions (arXiv:2504.10374). Part I does not cite its body-level effect sizes, and neither does this paper.

Resampling needs state that can be forked: the same conversation, two continuations, compared. A page table with copy-on-write branching is such a state. That design exists and is not built. A trace that records page identity and turn boundaries is the audit trail for a fork. It shows which pages were resident on each branch and which render each branch saw.

### 7.3 Eviction and stubs as an attack surface

Four threats are specific to paging or close to it.

- **Eviction.** An adversary who influences what is evicted could push out safety instructions or force thrashing. This review found no study of it. The claim is a gap in what was read, not a gap in the field.
- **Many-shot jailbreaking.** Attack success follows a power law in the number of demonstrations, and fine-tuning alone did not fully mitigate it at arbitrary lengths (Anil et al., NeurIPS 2024). Anthropic reports that a prompt-modification defence cut one attack from 61% to 2% success. A pager changes what sits in context. Eviction could remove many-shot structure. Pinning could keep it.
- **Memory poisoning.** AgentPoison plants a backdoor in an agent’s long-term memory or retrieval store. The arXiv abstract reports an average attack success above 80%, under 1% effect on benign performance, and a poison rate under 0.1% (arXiv:2407.12784). The NeurIPS listing gives slightly different figures. A pager’s evicted heap and fault-in path form a retrieval channel of the same kind.
- **Stubs.** A stub holds harness-written text that includes tool names and arguments. If file names or arguments are attacker-controlled, they enter the model’s context inside text that looks trusted. This is an inference from the stub design. No published result covers it. The live policy in the W8C cells removes messages and emits no stubs, so this path applies to a stubbing policy that is designed and not yet captured. Removal has its own exposure: dropped content is invisible to a reader who has only the trace (section 2.4).

A lazy retrieval handle is also an opportunity. A monitor can inspect a page before it faults in. A fully resident context has no such checkpoint.

Three mitigations are proposals. Render names inside stubs from a closed vocabulary or as hashes. Apply length and character limits to any attacker-controlled field. Add a static test that a stub contains no unescaped substring of such a field. The static test needs no model call (section 12.4).

### 7.4 Long-horizon reliability

LLMs lost 39% of performance on average in multi-turn conversations, mostly through unreliability. They tend not to recover after a wrong turn (arXiv:2505.06120; abstract). Evicting an early wrong assumption should help, but models also over-rely on earlier responses, so the effect is not obvious.

The proposed test has three arms: unchanged context; the wrong assumption evicted or stubbed; and an oracle arm, in which the wrong assumption is replaced by the correct one. Status: not started.

### 7.5 Dual use

The SHADE-Arena authors find that models still struggle at sabotage mainly because they fail at long-context execution of the main task (arXiv:2506.15740; abstract). A pager that improves long-horizon execution could therefore raise sabotage success. Context management is a capability, not only a cost saving.

Any evaluation of the pager needs a capability-uplift check. The public split of SHADE-Arena can serve for this. Status: blocked, because the paged arm is inert on real traffic.

### 7.6 What the trace answers

- It can carry origin, trust, and reader attributes, and make a policy decision replayable.
- It records the forks and resamples a control protocol creates.
- It exposes eviction and stub text as inputs that can be tested.
- It does not enforce anything, and it does not make a model more obedient.

## 8. Audit, regulation, and safety cases

### 8.1 Regulation

Two provisions of the EU AI Act matter here. Article 12 requires high-risk systems to allow the automatic recording of events over the system’s lifetime (Regulation (EU) 2024/1689). Article 55 requires providers of general-purpose models with systemic risk to evaluate with standardised protocols, to conduct and document adversarial testing, and to track and report serious incidents. The GPAI Code of Practice builds assessment depth on post-market and incident data (Measure 1.2).

California SB 53 is a third example. Law-firm summaries say it took effect on 1 January 2026 and applies to developers of frontier models. A critical safety incident must be reported to the state’s Office of Emergency Services within 15 days, or 24 hours if harm is imminent. This paper has not read the statute. These details are UNVERIFIED.

“Documented” is the operative word in these texts. A document that cannot be replayed is a claim. The compliance case is nevertheless conditional. It holds if the deployment is a high-risk system under Article 12, or if the operator is a general-purpose-model provider with systemic risk who runs its own evaluations under Article 55. Most coding-agent users and harness builders are neither. SB 53 also addresses model developers, not harness builders.

This paper does not claim that a context trace satisfies Article 12. The trace covers the harness input, not the whole lifetime of the system. Two cautions apply. Compliance guidance notes that tamper resistance is implied by the purpose of record-keeping, so a checksum is not enough for a high-risk audit. Published summaries also disagree on application dates, so this paper cites the regulation and no date.

### 8.2 Safety cases

Clymer et al. define a safety case as a structured rationale that an AI system is unlikely to cause a catastrophe. They group the arguments into four categories: inability, control, trustworthiness, and deference (arXiv:2403.10462; abstract). The table below is a first-cut mapping. It is this paper’s inference, not a published result.

| Argument | Rests on | A trace supplies | A trace does not supply | Minimum integrity |
| --- | --- | --- | --- | --- |
| Inability | Evaluation results showing the model cannot do the task, even with elicitation | Replayable transcripts, context policy, environment key, scoring inputs | Completeness of elicitation; sandbagging detection | Accidental for internal use; tamper evidence for external review |
| Control | Monitoring and restrictions that hold even if the model is misaligned | Reproducible monitor views; an audit trail of forks and resamples | Monitor quality; honesty of the harness | Tamper evidence, because the agent may reach its own log |
| Trustworthiness | Evidence that the model does not try to cause harm | Inputs for white-box replays and interventions | Evidence of intent or of hidden reasoning | Accidental, paired with model-side evidence |
| Deference | Credible AI advisers | A record of what the adviser was shown | Whether the adviser is credible | Tamper evidence |

### 8.3 Minimum trace content for incident reconstruction

A proposed minimum, again as inference: session metadata (model snapshot and date, harness and adapter versions, tokenizer version); the render and static prefix of every turn; the turn unit the adapter uses (a user turn on Hermes, a model request on OpenCode); the pages removed from each request when the policy removes pages (section 2.4); tool calls with their side-effect class; the environment key; reasoning visibility; the redaction stages applied; the integrity level; and the identity of the party that holds the trace.

One question stays open: who holds the trace, the harness operator or the model developer, and how the other party gains access. Status: not found in this review.

## 9. Redaction and consent

A trace is made of prompts, tool returns, file paths, and code. A redaction policy must handle that material. The format cannot decide the policy.

### 9.1 Where redaction runs

Redaction can run in three places: at capture, where a page’s content is replaced before it is declared; at flush, where a redacting writer rewrites content fields; and at export, where a slice is produced for a third party. Each leaves a different artifact. A trace redacted at capture cannot be told from one that never held the text. The record must therefore say which stage ran and with which rule set.

### 9.2 What the format should carry

The repository’s proposal card (design/redaction-block.md, RR-P3REDACT-20261109, proposal-only and sidecar-first, so the sealed v0 and RFC-0.1 wire schemas stay untouched) defines the redaction record as an ordered list of stages (capture, flush, export), because one trace can be redacted at capture and again at export. Each stage entry carries the policy id, the rule-set version, the stage, the number of fields replaced, and a reference-policy declaration (raw, keyed-hashed, or dropped). An absent record means unknown, never unredacted, and the block is an assertion without tamper evidence. Pages keep their identity and the hashes of the redacted content. Replay stays consistent within the redacted artifact and does not pretend to reproduce the original.

### 9.3 Fields that leak

Redaction must cover references, not only content. A `logical_ref` can embed file paths and tool arguments, for example `tool:read_file(path=src/auth.ts)`. Hashes of short or common strings can be reversed by a dictionary attack. A salted keyed hash (HMAC) avoids that. Its limit is that a salt which differs between corpora breaks joins between traces. A salt shared within one corpus keeps them.

The first task is an audit: a table of every field that can hold user-derived content (page content, stub text, `logical_ref`, tool arguments, paths, model output) and whether each is stored raw, hashed, or counted. That audit is recorded in reports/RR-FIELDAUD-20261107.md across all nine event types and 17 corpus traces (476 rows). It identifies raw logicalRef, stubText, and reason as the primary leak channels, while page bodies and model outputs are absent from the wire (as recorded by the repository; this paper has not read the report in full).

### 9.4 A verifier

A claim that a trace is redacted to a standard someone else can check needs a checker. A verifier would scan for secret and personal-data patterns, compare the stage list with the fields it finds, and report residual matches. A partial one exists: the repository’s dq-secret-scan.py stamps its own identity and scan-list version into the provenance file and never prints matched bytes. It has no stage-list comparator, no third-party standard, and few personal-data classes (repository review RR-WP2REV-20261107). The full verifier is not built.

### 9.5 Consent and defaults

Part I states that capture is on by default in the plugin it ships. A user who does not know a trace exists cannot consent to it. A trace holds page identities, content hashes, token counts, and references. The references, stub text, and reason fields can contain file paths and tool arguments, although page content is not stored. The state directory is mode 0700, which protects against other local users but not against the agent process or a backup tool running as the same user. Storage is local-only. The opt-out (CTXVM\_TRACE=0) is found only by reading the documentation, and a first-run notice is a proposed change, bound before any registry release under D6 and D17, not a shipped one. These mitigations reduce the risk. They do not replace consent.

The recommendation, as a proposal, is to make capture opt-in. The alternative is a first-run notice with hashes and counts stored by default, and content capture as an explicit choice. Data-protection law may apply to captured prompts and code. This paper gives no legal advice.

### 9.6 What the research agenda needs

The evaluation-awareness comparison (section 11, row 9) needs deployment traces, redacted to a standard another party can check. Without that stage the row is blocked, not merely unstarted.

### 9.7 Content-bearing capture (proposal)

A trace holds page identities and hashes, not content. Monitor runs, hint injection, and ablation (section 11, rows 2 to 5) need content. Two routes exist. A separate content channel could store page content with its own access control and redaction stage. Alternatively, an analysis step could join the trace with its sources, and each view would name its join inputs (section 6.3). Either route belongs in the redaction story. Either needs an owner decision, and the sealed spec does not change.

## 10. What a trace cannot do

- **It cannot see inside a model.** It has no activations, no sparse features, and no probes. White-box work needs weights, and a harness-level trace has none. A trace also cannot show which declared pages a removal policy left out of a request until the omission record in section 2.4 exists.
- **It cannot detect deception or sabotage.** A trace records what happened, not what was intended. Monitors, probes, and control protocols make the judgement. The trace supplies their input.
- **It cannot detect sandbagging.** In an auditing game, blue teams could not reliably tell sandbagging models from benign ones (AISI, arXiv:2512.07810; abstract). Record quality does not fix a problem that lives in capability elicitation.
- **It cannot detect poisoning or injection.** It can record which pages entered the context, and it lets a detector run on them.
- **It cannot establish causation.** Rendering a page is not causing an answer. Only an intervention (section 4) supports a causal claim, and the intervention is not the trace.
- **It cannot make the harness honest.** See section 3.
- **It cannot settle evaluation-awareness measures.** Verbalized awareness is a lower bound, and steering confounds the measure (section 5.3).
- **It can create false confidence.** The most likely misuse is an audit that reads a complete trace and concludes that the system was understood. The record covers the input side. Safety claims need the model side, and this paper does not supply it.

## 11. Research agenda

The questions below are the ones this design makes askable. None is answered here. Each row states what exists, what is missing, and a status from section 1.2. Faults on rendered pages are close to definitional, so they cannot separate “the model needed it” from “the harness had shown it.” Row 1 exists to make that separation.

| # | Question | What exists | What is missing | Status |
| --- | --- | --- | --- | --- |
| 1 | Does the identifier-based touch ratio predict causal influence? | ContextCite (arXiv:2409.00729); ARC-JSD (arXiv:2505.16415) | A page-then-span ablation run, with pair ablations for the top pages | Designed; compute only on open weights |
| 2 | Do chains of thought admit an injected hint on agentic traces? | Hint-injection design (arXiv:2505.05410); tool-channel weakness (arXiv:2608.29464) | The agentic experiment, with reasoning visibility recorded | Designed; strongest candidate |
| 3 | Which page-level views produce the best monitors? | Less-is-more and extract-and-evaluate (arXiv:2601.21112); hybrid scoring (arXiv:2505.23575) | A view-parameterised monitor run | Designed |
| 4 | How much does monitor accuracy change when reasoning is summarised, not full? | SHADE-Arena scratchpad result (arXiv:2506.15740) | The reasoning-visibility field and a paired run | Not started |
| 5 | Does page-then-span ablation match leave-one-out, and at what cost? | AttriBoT (arXiv:2411.15102); ARC-JSD | An open-weight replay experiment | Designed; compute only |
| 6 | Do probes and sparse autoencoders work on replayed agent trajectories? | Linear probes (arXiv:2502.03407) | Open-weight replay with tokenizer provenance | Not started |
| 7 | How much do capability scores move with context policy and scoring convention? | Lower-bound limits (arXiv:2412.08653); scaffold variance (arXiv:2510.11977); METR conventions (UNVERIFIED) | A three-by-three grid at fixed tasks | Not found; designed |
| 8 | Do environment defects leave a signature in traces? | Transluce environment fix (crosspost) | A scan of existing traces for repeated failing tool calls; the repository’s corpus digests already hold a fixture | Prototype-able |
| 9 | Which pages give an evaluation away? | AUC 0.83 against 0.92 (arXiv:2505.23836); model-environment variance (arXiv:2605.23055) | Deployment traces, redaction, a classifier, no-change controls | Blocked on redaction |
| 10 | Do verbalized and behavioural awareness measures agree under page ablation? | Lower-bound result (arXiv:2605.02269); Goodfire | An ablation run that measures both | Designed; needs model spend |
| 11 | Can page provenance give taint-style protection? | CaMeL (arXiv:2503.18813) | Origin, trust, and reader attributes, and a policy layer | Prototype-able |
| 12 | Can attacker-controlled names inject instructions through stubs or the fault-in path? | AgentPoison for retrieval channels (arXiv:2407.12784) | A red-team of stub text; a static property test | Prototype-able; local |
| 13 | Does evicting an early wrong assumption help? | 39% multi-turn degradation (arXiv:2505.06120) | A three-arm experiment with an oracle arm | Not started |
| 14 | Does paging reduce many-shot jailbreak success, and can pinning defeat that? | Power-law result (Anil et al., NeurIPS 2024) | Paged and unpaged arms on many-shot prompts | Runnable; engine engages at 60,000, cost-negative |
| 15 | Does paging change sabotage success? | SHADE-Arena (arXiv:2506.15740) | Paged and unpaged arms on its public split | Runnable; engine engages at 60,000, cost-negative |
| 16 | Can xCABI be an OpenTelemetry semantic-convention extension? | OpenTelemetry GenAI conventions (UNVERIFIED; vendor blog) | A check against the OpenTelemetry repository, then a mapping | Open |
| 17 | Can Inspect Scout scanners run over xCABI traces? | Inspect Scout; Docent; CAISI and AISI transcript work | An adapter and a same-run comparison | Prototype-able |
| 18 | What is the minimum trace content for incident reconstruction, and who holds it? | Articles 12 and 55; SB 53 (UNVERIFIED) | The field list in section 8.3, tested against a real incident | Not found |
| 19 | Which trace properties does each safety-argument category need? | Clymer et al. (arXiv:2403.10462) | Review of the first-cut mapping in section 8.2 | Designed (first cut) |

Rows 14 and 15 can run now, because the engine engages at a 60,000 budget on a 20-prompt shape: the request was held at 0.60 of the control’s on the free tier and 0.57 on the paid cell. They are cost-negative. The paid cell cost 2.11 times the control, with 72.2% of its bill in cache writes (repository report RR-W8C-CLOSING-20261113). The earlier W8 experiment on a 12-prompt shape was closed as failed, because that shape capped any saving at 5.3% of request tokens (repository reports RR-W8INDEX-20261107 and RR-W8SIM-20261110). This paper has not read these reports in full. On real traffic the protected floor exceeds the 24k budget (Part I §7). A result at this shape is a cost measurement only, and no saving may be claimed from it. The change must be logged as a deviation from preregistration before any paged run.

## 12. Experimental designs for first runs

These are protocols, not results. Each needs preregistration before its first run. A preregistration states: the hypothesis and the smallest effect of interest; the arms; the noise-floor measurement; the number of samples, chosen so that the 95% interval on the answer-change rate is narrower than half the smallest effect of interest; the model snapshot and date; the harness, adapter, and tokenizer versions; the detector and scorer versions; the stop rule; the budget cap; and what counts as a deviation.

### 12.1 Page ablation against the touch ratio

- **Hypothesis.** Pages with a high identifier-touch count have more causal influence on the next action than matched pages with a low count.
- **Arms.** Baseline; baseline repeat, for the noise floor; one page ablated, drawn from a stratified sample matched on kind and token count.
- **Models.** An open-weight model first, with leave-one-out on output probabilities as the reference. A hosted model second, for behaviour.
- **Primary metric.** The rank correlation between touch count and ablation effect.
- **Secondary metrics.** Pair ablations on the top pages. Agreement between page-then-span and flat leave-one-out.
- **Threats.** Ablation changes the prompt distribution. Pages interact. Open-weight results may not transfer to hosted models. The touch count depends on the identifier rules.
- **Output.** A ground truth for the fault-recall metric in Part I.

### 12.2 Hint injection on agentic traces

- **Hypothesis.** Chains of thought admit an injected hint less often when it arrives in a tool-result page than in a user message.
- **Arms.** Baseline; baseline repeat; hint in a user message; hint in a tool-result page; an irrelevant-hint control.
- **Measures.** Whether the action changes. Among changed cases, whether the returned reasoning admits the hint. Results are stratified by reasoning visibility.
- **Threats.** If the provider returns no reasoning, admission cannot be measured. A model that judges admission needs validation on a manual sample. Admission rates will be low on tasks where reasoning is not needed.

### 12.3 Scoring convention by context policy

- **Hypothesis.** Capability estimates differ across scoring conventions by more than the sampling interval, and the convention effect differs by context policy.
- **Arms.** Three context policies at fixed tasks: full context, a pruning or paged policy, and summarised context. Each runs with several samples.
- **Conventions.** Applied by re-scoring the same runs: cheating as failure, cheating discarded, cheating as success. A versioned cheating detector flags runs, and a manual review checks the flags, because METR found that two detection methods missed each other’s cases.
- **Metrics.** The pass rate per cell, with intervals, and the interaction between convention and policy.
- **Threats.** The policy may change the cheating rate. The detector may miss cases. Environment defects may dominate, so a defect scan (row 8) runs first. If the paged arm stays inert, a simple eviction policy that does act replaces it, and the substitution is recorded. The substitution is a policy change, so the owner approves it before the run.

### 12.4 Stub injection

- **Part 1, static, no model.** A property test generates attacker-controlled names: instruction-like strings, very long strings, control characters, and delimiter lookalikes. The stub renderer must place each name only inside an escaped, length-limited field. No instruction-like substring may appear outside it.
- **Part 2, with a model.** After approval of the spend, compare whether an injected instruction in a name is followed, against a benign-name control and against the noise floor.
- **Threats.** A closed vocabulary or hashed names can make stubs less useful. Measure the token cost and the recovery rate of the changed stubs.

### 12.5 Order of work

1. The static stub test (12.4, part 1). It costs no model spend.
2. Local tooling rows: 8, 16, and 17.
3. Open-weight ablation (12.1). It costs compute only.
4. The grid (12.3) and hint injection (12.2), under preregistration and with approval of model spend.
5. Rows 14 and 15, which can run now because the engine engages on the 20-prompt shape. Each is a cost measurement only, and no saving may be claimed from it.

Three dependencies cut across these steps. Rows 2 and 4 need the reasoning-visibility field. Row 9 needs the redaction verifier. Rows 5 and 6 need tokenizer provenance.

## 13. Method, limits, and open verification items

### 13.1 Method

The sources came from LLM-assisted passes in November 2026: web searches, and notes on 17 papers compiled by the repository agent. Most sources were read at abstract or snippet level, as the reference list shows. No experiment was run and no money was spent. “Not found” means not found in the sources read.

The agent’s compiled answers restate each research question with its literature support and a status. This paper consolidates them into one agenda and adds the verifier design (3.1), run kinds and cost (4.1, 4.4), reasoning visibility (6.2), the stub analysis (7.3), the safety-case mapping (8.2), the minimum incident content (8.3), the redaction refinements (9), and the experimental designs (12).

Version 1.1 applies corrections from the repository agent’s review of version 1.0 (repository report RR-WP2REV-20261107). The review found that pages carry identity and hashes, not content, so the byte-identity claim covers render geometry only. Version 1.2 merges the repository lane’s edits to section 9 and updates the pager status, the turn unit, and omission (section 2.4) from the W8C closing card, the OpenCode comparison, the replay reviews, and packet P12 (RR-W8C-CLOSING-20261113, RR-OCDIFFREV-20261113, RR-W8CREPLAY-20261112, RR-W8CREPLAY2-20261113). Those reports were read as supplied to the reviewer, and the source captures were not re-read.

### 13.2 Limits of this paper

- The literature coverage is limited. Other relevant studies may exist.
- Several 2026 papers were read as snippets.
- A vendor blog and law-firm summaries are secondary sources.
- The mappings in sections 8.2 and 8.3 are this paper’s inference.
- No design in section 12 has been run. The W8C cells cited in sections 2.4 and 11 were run by the repository lane, not by this paper.

### 13.3 Open verification items

| Item | Status | What to check |
| --- | --- | --- |
| METR figures for GPT-5.6 Sol (about 11 hours, about 71 hours, over 270 hours) | UNVERIFIED; secondary only | Read the METR pre-deployment report |
| OpenTelemetry GenAI conventions: status and content | UNVERIFIED; vendor blog | Check the repository and its release state |
| California SB 53 details | UNVERIFIED; law-firm summaries | Read the statute |
| Hua et al., arXiv:2510.20487 | UNVERIFIED; citation and forum post only | Read the paper |
| arXiv:2605.23055 | Snippet; authors not recorded | Read it and record the authors |
| arXiv:2601.21112 and arXiv:2608.00583 | Abstract or snippet | Read in full; record the figures used |
| Provider documentation on reasoning visibility | Not checked | Read each provider’s documentation and record the versions |
| CAISI joint paper on transcript scanners | Title taken from a file name | Fetch the paper |
| Transluce environment result (68.6% to 78%) | Crosspost | Read the Transluce write-up |

The agent’s compiled answers list the OpenTelemetry conventions, SB 53, provider documentation, and the CAISI title as verified. They also list arXiv:2601.21112 as both read in full and available only as snippets. They record no locator for any of these. This paper treats all of them as UNVERIFIED until the agent records what it fetched and where.

## 14. Conclusion

A context trace is a record of the structure of the requests a harness sent: which pages were declared or stubbed on each turn. For each of the three questions, that record is necessary and not sufficient.

- **Evaluation.** The trace makes scores comparable by recording context policy, scoring inputs, and environment. It does not define danger.
- **Monitoring.** It fixes the input and makes a monitor’s view an explicit object. It does not reveal computation.
- **Control.** It can carry provenance and record forks. It enforces nothing.

Three pieces of work come first: a tamper-evident chain, the redaction and consent work, and a pager that pages on real traffic. Then the agenda has 19 questions. The first four to run cost no model spend. Part I builds the recorder. Part II states what the recorder is evidence for, and where another kind of evidence has to take over.

## References

The level at which each source was read is in brackets.

- Barnett and Thiergart, What AI evaluations for preventing catastrophic risks can and cannot do, [arXiv:2412.08653](https://arxiv.org/abs/2412.08653) \[abstract\]
- Kapoor et al., Holistic Agent Leaderboard, [arXiv:2510.11977](https://arxiv.org/abs/2510.11977) \[abstract\]
- Needham et al., Large Language Models Often Know When They Are Being Evaluated, [arXiv:2505.23836](https://arxiv.org/abs/2505.23836) \[abstract\]
- Charnock et al., Expanding External Access to Frontier AI Models for Dangerous Capability Evaluations, [arXiv:2601.11916](https://arxiv.org/abs/2601.11916) \[abstract\]
- Cohen-Wang et al., ContextCite, [arXiv:2409.00729](https://arxiv.org/abs/2409.00729) \[abstract; the 32 times cost figure is body-level and unverified\]
- Liu, Kandpal and Raffel, AttriBoT, [arXiv:2411.15102](https://arxiv.org/abs/2411.15102), ICLR 2025 \[abstract\]
- Li et al., Attributing Response to Context (ARC-JSD), [arXiv:2505.16415](https://arxiv.org/abs/2505.16415), ICLR 2026 \[abstract and introduction\]
- Bogdan et al., Thought Anchors, [arXiv:2506.19143](https://arxiv.org/abs/2506.19143) \[abstract; the 100-resample figure is from the authors’ post\]
- Korbak et al., Chain of Thought Monitorability, [arXiv:2507.11473](https://arxiv.org/abs/2507.11473) \[abstract\]
- Chen et al., Reasoning Models Don’t Always Say What They Think, [arXiv:2505.05410](https://arxiv.org/abs/2505.05410) \[abstract\]
- FACE-Eval, Chain-of-Thought Faithfulness of Reasoning Models Varies with Where and How Preference Cues Are Delivered, [arXiv:2608.29464](https://arxiv.org/abs/2608.29464) \[abstract\]
- Arnav et al., CoT Red-Handed, [arXiv:2505.23575](https://arxiv.org/abs/2505.23575) \[abstract\]
- Arike et al., How does information access affect LLM monitors’ ability to detect sabotage?, [arXiv:2601.21112](https://arxiv.org/abs/2601.21112) \[abstract; see 13.3\]
- A False Average: Pooled CoT-Monitor Accuracy Conceals a Reasoning-Dependent Fragility, [arXiv:2608.00583](https://arxiv.org/abs/2608.00583) \[title and snippet; see 13.3\]
- Goldowsky-Dill et al., Detecting Strategic Deception Using Linear Probes, [arXiv:2502.03407](https://arxiv.org/abs/2502.03407) \[abstract\]
- Kutasov et al., SHADE-Arena, [arXiv:2506.15740](https://arxiv.org/abs/2506.15740) \[abstract\]
- Greenblatt et al., AI Control, [arXiv:2312.06942](https://arxiv.org/abs/2312.06942) \[abstract\]
- Bhatt et al., Ctrl-Z: Controlling AI Agents via Resampling, [arXiv:2504.10374](https://arxiv.org/abs/2504.10374) \[abstract\]
- Debenedetti et al., Defeating Prompt Injections by Design (CaMeL), [arXiv:2503.18813](https://arxiv.org/abs/2503.18813) \[abstract\]
- Laban et al., LLMs Get Lost In Multi-Turn Conversation, [arXiv:2505.06120](https://arxiv.org/abs/2505.06120) \[abstract\]
- Clymer et al., Safety Cases: How to Justify the Safety of Advanced AI Systems, [arXiv:2403.10462](https://arxiv.org/abs/2403.10462) \[abstract\]
- Chen et al., AgentPoison, [arXiv:2407.12784](https://arxiv.org/abs/2407.12784), NeurIPS 2024 \[abstract; figures differ in the NeurIPS listing\]
- Anil et al., Many-shot Jailbreaking, NeurIPS 2024, with [Anthropic’s summary](https://www.anthropic.com/research/many-shot-jailbreaking) \[abstract and summary page\]
- AISI, Auditing Games for Sandbagging Detection, [arXiv:2512.07810](https://arxiv.org/abs/2512.07810) \[abstract\]
- Hua et al., Steering Evaluation-Aware Language Models to Act Like They Are Deployed, [arXiv:2510.20487](https://arxiv.org/abs/2510.20487) \[UNVERIFIED: citation only\]
- Decomposing and Measuring Evaluation Awareness, [arXiv:2605.23055](https://arxiv.org/abs/2605.23055) \[snippet\]
- Towards Understanding Specification Gaming in Reasoning Models, [arXiv:2605.02269](https://arxiv.org/abs/2605.02269) \[snippet\]
- Stress Testing Deliberative Alignment for Anti-Scheming Training, [arXiv:2509.15541](https://arxiv.org/abs/2509.15541) \[snippet\]
- Goodfire, [Verbalized Eval Awareness Inflates Measured Safety](https://www.goodfire.com/research/verbalized-eval-awareness-inflates-measured-safety), 4 May 2026 \[snippet\]
- Alignment Forum, [Steering Evaluation-Aware Models to Act Like They Are Deployed](https://www.alignmentforum.org/posts/peKrvZ6t9PSCzoQDa/steering-evaluation-aware-models-to-act-like-they-are) \[snippet\]
- UK AISI, Cheating behaviour in frontier model evaluations, 21 July 2026 \[as read for Part I; secondary coverage checked here\]
- UK AISI, [Transcript analysis for AI agent evaluations](https://www.aisi.gov.uk/blog/transcript-analysis-for-ai-agent-evaluations) \[snippet\]
- NIST CAISI, [Analyzing Transcripts from AI Agent Evaluations](https://www.nist.gov/blogs/caissi-research-blog/analyzing-transcripts-ai-agent-evaluations), 18 February 2026 \[read in full\]
- METR, [Recent Frontier Models Are Reward Hacking](https://metr.org/blog/2025-06-05-recent-reward-hacking), 5 June 2025 \[snippet\]
- METR, GPT-5.6 Sol pre-deployment evaluation, 26 June 2026 \[UNVERIFIED: secondary only\]
- Transluce, Docent, [documentation](https://docs.transluce.org/) \[snippet; the 68.6% to 78% figure is from a crosspost\]
- OpenTelemetry GenAI semantic conventions, read through a [vendor blog](https://www.truefoundry.com/blog/opentelemetry-genai-semantic-conventions) dated 22 August 2026 \[UNVERIFIED\]
- California SB 53, Transparency in Frontier Artificial Intelligence Act \[UNVERIFIED: law-firm summaries\]
- Regulation (EU) 2024/1689 (AI Act), Articles 12 and 55; General-Purpose AI Code of Practice, Measure 1.2 \[as read for Part I\]

Repository reports cited as locators. They were read as supplied to the reviewer, not at source.

- reports/RR-W8C-CLOSING-20261113.md: the W8C closing card, with the cells and the instrument chain
- reports/RR-OCDIFFREV-20261113.md: review of the OpenCode against Hermes turn accounting (the source report RR-OCDIFF-20261113 was not read)
- reports/RR-W8CREPLAY-20261112.md and reports/RR-W8CREPLAY2-20261113.md: replay and the turn-invariant projection
- handoff/packets/P12-omission-representation.md: the omission proposal
- design/redaction-block.md, reports/RR-P3REDACT-20261109.md, and reports/RR-FIELDAUD-20261107.md: redaction and the field audit
- reports/RR-WP2REV-20261107.md, reports/RR-W8INDEX-20261107.md, and reports/RR-W8SIM-20261110.md: the Part II review, the W8 closure index, and the offline budget simulation

## Document control

| Item | Value |
| --- | --- |
| Title | What a context trace can and cannot show about AI safety (Part II) |
| Part I | Virtual memory for LLM agent context: the xCABI standard and the ctxvm engine |
| Version | 1.2 draft, 13 November 2026 |
| Reused from Part I | Threat model, counterfactual replay, evaluation infrastructure, monitor views, provenance, control protocols, regulation, limits, research agenda, and redaction, in revised wording |
| Added | The research note (version 2), the agent’s compiled answers of 6 November 2026, and new searches |
| Wording changes | The central claim is the request the harness sent. The compliance case is conditional. Absence claims read “not found in this review.” Internal work-item labels are removed. Figures not checked against a primary source are flagged UNVERIFIED and do not carry the argument. Version 1.1 narrows the central claim to the structure of the request, because pages carry identity and hashes, not content. Version 1.2 merges the repository lane’s section 9 text and adds omission (section 2.4), the turn unit, and the W8C pager status. |
| Style | ASD-STE100-inspired: short sentences, active voice, defined terms, no marketing language |
| Experiments run | None |
| Open items | Section 13.3 |
