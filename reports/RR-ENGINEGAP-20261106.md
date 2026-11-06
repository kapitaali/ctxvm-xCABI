# RR-ENGINEGAP-20261106 — the engine is attached and does nothing

Card: analysis of the first captures after `context.engine: ctxvm` was set. No code changed. The
finding is a design-bound no-op plus a risk, and it is worth stating before the W8 run.

## Evidence chain

1. **The engine is attached.** No fallback appears in the log (`Context engine 'ctxvm' not found —
   falling back`, or `could not be safely copied`) at 13:18 or 13:21, and the plugin's registration
   line is present. `context.engine: ctxvm` matches `CtxvmFaultPinEngine.name` exactly.

2. **The request shipped far above the declared budget.** The 13:21 capture's single render row:

```
turn 0  resident=1764  prefix={source: measured, toolSchemas: 21, messageCount: 708,
                               requestChars: 1,434,464, approxInputTokens: 358,616,
                               systemPromptBytes: 55,350}
call.meta  cacheEstimate={estHit: 0, estMiss: 0, providerReported: false}
           providerUsage={inputTokens: 268, outputTokens: 848, cachedInputTokens: 380,160}
```

358,616 tokens against `budgetTokens: 200,000`. With `should_compress()` returning `False` by design,
an attached engine cannot compact — so either the engine is attached and the context is unbounded, or
the built-in compressor is attached and would have compacted. The absence of any fallback warning and
of any compaction makes the first reading the consistent one.

3. **The floor law explains the no-op, and a probe confirms it.** `_plan` returns early when the
   protected floor — system prompt, `protect_first_n=3` head messages, `protect_last_n=6` tail
   messages, and pinned pages — already exceeds `vBudget` (L5: "keep law owns this request"). At
   vBudget 24,000 that is easy to hit: six tail messages of 60,000 characters each are ~90,000 tokens.

```
probe A: 600,200 chars in, six 60k-char tail results   -> select_context returns None (no selection)
probe B: 1,372,470 chars in, small tail (2k results)   -> 92,477 chars out, 81 -> 50 messages,
                                                          32 tool results dropped
```

So the engine works, and the live session is in the regime where it cannot act.

## What the traces show anyway

- **The fault taxonomy is saturated by `identifier_scan`.** The full 0.8.0 capture (one process slice):
  209 declares, 191 faults — 187 `identifier_scan`, 4 `tool_recall`. A page that is mentioned once is
  "faulted". That is why the W18 tier-1 numbers came out as they did: the feature is close to "pages
  ever mentioned", not "pages re-read".
- **A capture is a process slice, not a session.** The 13:21 file holds 13 events and one render for a
  708-message conversation, because every restart builds a new tracer and every stop truncates. The
  209-page capture is a slice too. `ctxvm stream`'s per-session rows are per-process segments.
- **Where the context actually goes:** `tool:skill_view` 91,435 tokens, `tool:terminal` 50,351,
  `tool:web_extract` 19,437, `tool:read_file` 6,169. A paging policy sized for read_file pages meets
  skill_view pages first.
- **Hook brackets are cheap:** 801 tool calls bracketed in the witness log, median 0.72 s, p90 8.28 s
  end-to-end (that is the tool, not the plugin; the bracket is where the trace gets `latencyMs`).

## The risk, stated plainly

With `context.engine: ctxvm` and vBudget 24,000, a long session is in the worst of both states:
selection cannot act because the floor is above the budget, and compaction is disabled because the
engine owns the policy. The context grows until the provider truncates or the call fails. Nothing in
the trace says "no selection was applied" — the engine emits no record — so the artifact cannot answer
the question the key was set to change.

## Recommendation, owner's call

1. **For daily use:** raise the budget at gateway start (`CTXVM_VBUDGET`, confirm-or-raise only) to a
   value above the protected floor of real traffic — the 13:21 request was 358k tokens, so 24k was
   never a workable daily setting. Or set `context.engine: compressor` until the W8 run.
2. **For W8:** keep 24,000 as the preregistered arm value, and note that the arm is only meaningful on
   sessions whose floor is below it; otherwise both arms behave the same and the comparison measures
   nothing.
3. **For the format (a card, not this one):** the engine should record what it selected — pages
   dropped, pages served, floor tokens — as a sidecar or an additive field. A context policy that
   leaves no trace in the record contradicts the paper's own thesis.
