# RR-HEADROOM-20261107 — an over-budget capture is unreadable, and the naive arm is over budget by design

Card: defect found while reading back the orchestrator's own capture. Python and TypeScript emitters
changed; no wire change, no schema change. Found by the strict codec doing its job.

## What happened

`ctxvm stream` refused a live capture:

```
ctxvm stream: …/local-a08f0c28….jsonl:1500: jsonl: invalid event:
  invalid value: integer `-225267`, expected u64
```

The event:

```
{"type": "turn.render", "turn": 0, "residentTokens": 425267, "evictedTokens": 0,
 "headroom": -225267, "prefix": {...}}
```

`headroom` is `Option<u64>` in `rust/crates/ctxvm-codec/src/model.rs:238`. Both emitters computed
`budgetTokens - residentTokens` unconditionally, so any session whose resident set exceeded its
declared budget wrote a negative integer — which the sealed v0 wire cannot represent and the strict
codec rejects. The whole file becomes unreadable: `stream`, `replay`, `profile` and `diff` all refuse
it, not just the offending line.

One live file carried it (`local-a08f0c28…`, resident 425,267 against a 200,000 budget). It stays
invalid: captures are append-only, and rewriting it would be forgery.

## Why this matters more than one bad file

**The naive arm is over budget by design.** The experiment's pressure comes from the stock arm
letting the context grow past the declared budget; that is precisely the state that produced a
negative headroom. Every naive capture in the W8 grid would have been unreadable, and the failure
would have surfaced at analysis time — after the money was spent.

## The fix

Omit `headroom` when the resident set exceeds the budget. Not a clamp to 0: zero means "no headroom
left", which is false when the set is 225k tokens over. Not a signed widening: the v0 field is sealed,
and a reader that needs the overrun computes `budgetTokens - residentTokens` from rows it already has.

```python
headroom = self._init.budget_tokens - resident
if self._init.budget_tokens > 0 and headroom >= 0:
    tr["headroom"] = headroom
```

```ts
if (init.budgetTokens > 0 && resident <= init.budgetTokens) {
  tr.headroom = init.budgetTokens - resident;
}
```

The TypeScript tracer is the source for the opencode and ai-sdk lanes, so all three adapters inherit
the fix.

## Tests

- Python: a 5,000-token page against a 1,000-token budget renders without `headroom`; the same page
  against 9,000 renders with `headroom: 4000`.
- TypeScript: the same two cases.
- Counts: python 171 → 172, node 21 → 22.

## What this does not change

- The wire. `headroom` stays optional and unsigned; absent means "no representable headroom".
- Existing traces. The one bad capture stays unreadable by design.
- The engine. Its `vBudget` is unrelated to this field; `turn.render.headroom` is page-table
  bookkeeping, not the engine's budget.
