# RR-SHADOW-RESEARCH-20261124 — recoverable omission is prior art; ctxvm's gap is attested recovery under a real keep law

Lane: research. Zero spend, zero model calls. Literature scan (primary arXiv abstracts + method
sections) plus current repo artifacts. This is a research note and proposed next measurement,
not a result or authorization. No code, profile, gateway, commit or push.

## 1. What changed in the literature picture

The earlier working assumption — "recoverable stubs may be a novel mechanism" — is **wrong**.
Direct prior art exists:

- **DTOC** (Chaturvedi et al., arXiv:2609.26121, 2026-08-06) stores full tool outputs in external
  memory, replaces disabled outputs with metadata-only placeholders, and exposes an explicit
  `manage_context(enable, disable)` tool. Its ablation reports that disabling recovery degrades
  performance while full reversible operation restores baseline accuracy at lower context cost
  ([HTML §3.1–3.3, §5.2](https://arxiv.org/html/2609.26121v1)). **Evidence level: method + abstract
  results read; not independently reproduced.**
- **Scroll** (Lin et al., arXiv:2608.21690, 2026-08-21) keeps an append-only Event Log and evicts
  spans from the working view while retaining stable addresses; an eviction index of headlines
  lets the model navigate back and materialize exact records ([HTML §2.2–2.4](https://arxiv.org/html/2608.21690v1)).
  **Evidence level: method read; benchmark numbers not independently reproduced.**
- **ACM** (Li et al., arXiv:2607.23809, 2026-07-26) gives the agent `manage_context` and
  `query_memory` tools: raw messages go to external storage, summaries carry ids, and the agent
  queries raw messages on demand ([HTML §3](https://arxiv.org/html/2607.23809v1)). It also reports
  a training pipeline for *when* to manage context. **Evidence level: method read.**
- At the KV-cache layer, **QEvict** (Garg et al., arXiv:2608.05326, 2026-08-05) uses a recoverable
  quantized tier and reports that token/window importance drifts, so irreversible eviction is
  brittle; it measures Future Missed Mass and reactivation ([HTML §1, §3](https://arxiv.org/html/2608.05326v1)).
  **Different layer (KV, not prompt pages), but same recoverability principle.**

**Therefore the defensible claim is not "we invented recoverable stubs."** It is:
**ctxvm can record the omission and the recovery path in a portable, replayable trace, and test
whether recovery works under the actual keep law.** That is an instrumentation/measurement
contribution, not a novelty claim about the mechanism.

## 2. What the repo now supports (verified)

- Stub mode emits `page.evict` + `page.render(mode=stub)` at the same current turn, with
  `stubText` byte-identical to the request stub; drop mode emits neither
  (`RR-STUB-RENDER-20261124`, 0.13.33; suite 247, gate green). The review lane subsequently
  verified 0.13.33 live under the gateway and real default-off sidecars
  (`RR-STUB-RENDER-REVIEW-20261124`, `RR-STUB-RENDER-LIVE-20261124`).
- Rust replay checks first stub-render turn == evict turn for the same PageId
  (`RR-PAGE-EVICT-IMPL-REVIEW`); the design erratum correctly notes `page.render` has no
  `stubText`, so text identity is checker-side (`RR-PAGE-EVICT-DESIGN-ERRATUM`).
- The engine's keep law is real and offline-callable: `CtxvmFaultPinEngine(v_budget,
  protect_first_n=3, protect_last_n=6, selection_mode=...)` + `select_context()`
  (`packages/hermes/live/context_engine.py:322,422,900`).
- **Still missing:** a live `stubDropped: recoverable` sidecar and an observed re-read. The
  Part C accuracy recovery (middle 1/8 → 7/8) stands, but mechanism attestation remains
  UNVERIFIED (`RR-PARTC-ARM-RESULT`, `RR-RECOVER-BLOCKED`). The new wire events make a future
  capture self-describing; they do not fill that gap retroactively.

## 3. The measurement trap to avoid

"Pages referenced later" is **not causal importance**. It is a behavioral proxy shaped by
what the policy kept, what the stub mentioned, and what the model chose to do.

- **FOCUS** defines counterfactual future utility as the divergence between future-trajectory
  distributions with and without a span, then estimates it with draft-model plan rollouts and
  defensive verification ([HTML §3–4](https://arxiv.org/html/2609.37590v1)). A later mention is
  only one noisy signal toward that counterfactual, not the definition.
- **CoMem** shows relevance is query-dependent: the same context needs different retained
  evidence for different queries, and they use same-context/different-query hard negatives
  ([HTML §2.1–2.2](https://arxiv.org/html/2611.16384v1)). A single global "important page" label
  is therefore suspect.
- **Tool Graph Retriever** models prerequisite dependencies, not isolated similarity
  ([HTML §3.1–3.3](https://arxiv.org/html/2508.05152v1)). For ctxvm, a page's producing call and
  its dependents may need to travel together; a stub that preserves only the result identity can
  still break the dependency chain.
- **Lost in the Middle, and In-Between** reports degradation both by distance from edges and
  between multiple necessary pieces in multi-hop QA ([abstract](https://arxiv.org/abs/2412.10079)).
  Position-stratified evaluation is necessary; a single pooled accuracy number hides the effect.
- **LLMs Get Lost in Multi-Turn Conversation** reports an average 39% drop and increased
  unreliability, with early wrong assumptions persisting ([abstract](https://arxiv.org/abs/2505.06120)).
  Recovery must be measured as a trajectory, not only a final answer.

## 4. Proposed next measurement: shadow mode first, live recovery second

### Phase S0 — shadow selection on synthetic tasks ($0, no model)

Run the **real engine's selection** on the needle bank but do not change any real request.
For each selection, log a shadow record:

```
session_id, turn, budget_tokens, resident_tokens, floor_tokens,
kept_page_ids[], would_drop_page_ids[], protected_reasons[],
policy_name, policy_version, selection_hash
```

No page bodies, prompts or answers. Then label each would-drop page with **future observable
events**, not "truth":

- `later_tool_recall` — same tool/args re-invoked later;
- `later_identifier_scan` — identifier named later;
- `never_observed` — no later event before session end (right-censored, not proof of safety);
- `dependency_distance` — graph distance from a later used page/call;
- `position_band` — head / middle / tail.

This yields pressure, floor, drop-set churn, and recall/recovery-rate distributions without
perturbing a single model call. It also fixes the "n=4 hard faults" data-volume problem: the
unit becomes **selection events**, not only faults.

### Phase S1 — offline damage curve on planted truth ($0, no generation)

On the 36-task needle bank, compare keep law / recency / random-middle / touch-aware / oracle /
anti-oracle at 80/60/40% budgets. Readout is forced-gold logP and top-1, as in
`PREREG-NEEDLE-20261122`. This tests whether the *selection* loses causally required content.
It does **not** test whether a stub causes re-fetch.

### Phase S2 — live recovery (free tier, conditional, owner-gated)

Only if S1 shows middle-band damage: naive / drop / stub on identical tasks, ≥3 repeats,
paired by task. Primary outcome: gold-answer accuracy. Mechanism outcomes:

1. `page.evict` + matching `page.render(mode=stub)` present at the same turn;
2. later `page.fault` / tool re-call names the stubbed PageId;
3. restored full page appears after the fault;
4. answer changes after restoration (not just a tool call);
5. uncached input tokens and hard-fault count (token counts, not cost saving).

A stub re-call without answer recovery is a **failed recovery**, not a success. A final-answer
improvement without a trace-attested re-read is an association, not mechanism validation.

## 5. Frozen gates for any future S2 (proposed, not ratified)

- **Attestation gate:** every stub session has a sidecar with `stubDropped=recoverable`,
  `stubCount>0`, and matching evict/render rows; otherwise the session is UNVERIFIED and excluded
  from mechanism claims (accuracy may still be reported separately).
- **Recovery gate:** ≥1 trace-attested stub→re-read→full-restoration chain per arm before any
  mechanism claim. Zero chains = no recovery evidence, not zero faults.
- **Noise gate:** baseline-repeat answer-change rate must be below a frozen fraction of the
  expected stub effect; otherwise the hosted route is too stochastic (the E2 lesson).
- **Dependency gate:** the producing tool call remains in the carrier for every stubbed result
  (current code does this); a missing carrier invalidates the session.
- **Stop:** no post-hoc stub-text changes, no re-scoring under a new definition of "recovery."

## 6. What this means for the paper and plugin

- **Paper:** add DTOC / Scroll / ACM as related work. Narrow the contribution to *observable,
  replayable omission + recovery under a specified policy*, not "recoverable stubs are new."
- **Plugin:** shadow mode is the highest-value zero-spend addition; stub mode is already
  implemented but still needs a real attested arm. A future touch-pin must be query-conditioned
  and dependency-aware, not a global "pages mentioned later" score.
- **Research gap:** no located study evaluates ctxvm's exact combination of a fixed head/tail
  keep law, inline re-run stub, sealed-v0 eviction/render events, and replay-checked recovery.
  This is a **gap in the reviewed literature**, not proof that no such study exists.

## 7. Scope / evidence levels

All external claims above carry primary arXiv locators. Method sections were read where stated;
benchmark numbers are not independently reproduced and do not carry a ctxvm claim. No
cost-saving (law 7), model-quality, paging-quality or unscoped-determinism (law 8) claim.
Nothing pooled with E0/E1/E2/M1/M2/M3. LOG/day owed to the review lane if landed.
