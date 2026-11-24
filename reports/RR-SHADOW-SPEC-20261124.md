# RR-SHADOW-SPEC-20261124 — one-page shadow-mode specification (proposal, not authorized)

**Status: DESIGN ONLY.** Zero spend, zero model calls, no code or profile change. Implements the
research recommendation in `RR-SHADOW-RESEARCH-20261124`; does not authorize implementation,
default-on behavior, a live arm, or a paper result. Hermes owns `packages/hermes/**`; research
owns this specification. Repo untouched; staged for owner copy.

## 1. Purpose

Compute and log what the current ctxvm keep law **would** do on real sessions without changing
the request, model-visible context, tool availability, or response. Build a growing corpus of:

- pressure and floor distributions (when the budget actually bites);
- would-drop page identities and selection churn;
- later observable re-use of would-drop pages (re-call, identifier scan, dependency proximity);
- right-censored “never observed before session end” cases, which are **not** proof of safety.

This supplies data volume without perturbing behavior. It does not estimate causal importance;
later reference is a proxy. FOCUS defines causal utility by counterfactual future-trajectory
divergence (arXiv:2609.37590 §3–4), and CoMem shows relevance is query-dependent
(arXiv:2611.16384 §2.1–2.2).

## 2. Verified insertion point

`CtxvmFaultPinEngine.select_context()` computes `units`, `keep_hard`, `dropped`,
`repositioned`, `plan_facts`, and `assembled` on ctxvm sessions, then calls
`OBSERVER["plan"]` on every selection before returning
(`packages/hermes/live/context_engine.py:548–621`). The plan payload already contains
`budgetTokens`, `residentTokens`, `floorTokens`, `droppedCount`, `droppedTokens`,
`repositionedCount`, `selectionHash`, `selectionMode`, `trigger`, `callIndex`, and
`prefixHash`. `CALL_LOG` already records per-call `removed[{tokens, ids}]` (`:641–660`).

**Important:** control/naive profiles return at `:495–512`, before planning. To shadow those
sessions without changing their request, implementation must add a **pure shadow planner**:
either a side-effect-free `compute_plan(messages, budget, config)` function or a short-lived
clone whose page/pin state is initialized from the current request but never writes back to
the live engine. It must not call `_update_page_state`, `_credit_demand`, pin mutation, or
`_assemble` on the live instance. On ctxvm sessions, the existing plan may be observed directly;
on control sessions, the pure shadow planner supplies the counterfactual plan. In both cases
the live return value remains exactly what the current mode would return (`None` or
`assembled`).

## 3. Configuration (default off)

Add a profile/constructor setting, e.g. `shadowSelection: true`, default **false**. Explicit
constructor value wins; a real session profile may opt in exactly like `selectionMode` and
`stubDropped` (`context_engine.py:522–536`). No environment-only backdoor and no effect on
`stubDropped`.

## 4. Sidecar record (content-free)

One JSONL record per selection, private under the existing state/trace directory:

```json
{
  "schema": "ctxvm-shadow-selection/v1",
  "session_id": "<opaque>",
  "turn": 0,
  "call_index": 0,
  "ts": "<UTC>",
  "policy": {"name": "keep-law", "version": "<hash>", "mode": "fresh|stable"},
  "budget_tokens": 24000,
  "resident_tokens": 0,
  "floor_tokens": 0,
  "dropped_tokens": 0,
  "dropped_pages": [{"page_id": "<logicalRef+contentHash>", "tokens": 0, "kind": "tool_result"}],
  "repositioned_pages": [],
  "selection_hash": "sha256:...",
  "prefix_hash": "sha256:...",
  "trigger": "new-page|overflow|every-B|held|null",
  "request_unchanged": true
}
```

**Forbidden:** page bodies, stub text, tool arguments, user/assistant text, answer text,
absolute paths, credentials. `page_id` may contain a logicalRef with a path; if so, hash it
for the shadow sidecar or apply the existing redaction consumer before export. The private
sidecar is not a public corpus drop.

## 5. Later-event labels (offline join, no model)

Join shadow records to the same session's later events by `page_id` / producing `call_id`:

- `later_tool_recall`: same tool+args re-invoked after the shadow drop;
- `later_identifier_scan`: identifier from the page appears later;
- `later_dependency_use`: a dependent call/page is used (graph distance ≥1);
- `never_observed`: no later event before session end — right-censored;
- `position_band`: head / middle / tail under the keep law;
- `selection_churn`: Jaccard(dropped_t, dropped_t-1);
- `recovery_observed`: a would-drop page later returns full (only observable in a real
  intervention/stub arm, not in shadow mode).

Report counts and rates with denominators. Never label `never_observed` “unimportant.”

## 6. Acceptance gates (before any live shadow rollout)

1. **No-perturbation gate:** with shadow off/on, the assembled request is byte-identical and
   the model-visible transcript is unchanged; only the sidecar differs.
2. **Per-session gate:** two interleaved sessions produce disjoint records; no global last-writer
   contamination (the repo has been burned by this before).
3. **Schema gate:** every record validates; all token counts non-negative; `dropped_tokens ≤
   resident_tokens`; `request_unchanged=true`; hashes match recomputation.
4. **Privacy gate:** no body/prompt/answer/argument fields; no absolute host paths in export;
   private dir 0700 / files 0600.
5. **Failure gate:** sidecar write failure is fail-open for the request but increments a visible
   `shadowWriteFailures` counter; no silent partial data.
6. **Red-before:** mutation that returns `assembled` when the original mode returns `None`
   must fail the no-perturbation test.

## 7. What shadow mode can and cannot establish

**Can:** how often the keep law engages; which pages it would drop; whether those pages are
later re-used; selection churn; pressure/floor distributions; candidate pins and dependency
edges.

**Cannot:** that dropping a page caused an answer change; that a never-reused page is safe to
drop; that a stub causes recovery; cost saving; model quality. Those require the planted-truth
damage curve and a trace-attested live stub arm (`PREREG-NEEDLE-20261122`).

## 8. Routing / owner decisions

Hermes implementation; review verifies no-perturbation + privacy gates. Owner must rule:
enable on which profile(s), retention period, whether hashed logicalRefs are sufficient, and
whether a later live stub arm may use the resulting candidate pins. No default-on, no model
call, no spend, no D17 action, no push.
