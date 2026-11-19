# RR-H12RESULT-REVIEW — verified: H12 is NEGATIVE, and the cause is structural

Review lane, verify-then-record. Subject: `f0c5e81` / `reports/RR-H12RESULT-20261119.md`. No code change, no model
call, no spend, no cell by this lane. The $1 cap stands untouched.

## 1. Verdict

**Negative result accepted**, and it is a result about the hypothesis, not the plumbing: the paged sidecar reads
`policyMode: stable`, `policyModeSource: settings`, `selectionMode: stable`, `trigger: overflow`, with
`droppedTokens 69,111` — the mode engaged. Two of the design's four acceptance conditions pass (request held at
budget, artefact parsed-equal); the two the design exists for fail (no hold between triggers, cache-read falls).

## 2. Evidence re-derived

| claim | how | result |
|---|---|---|
| pair ran free | arm summaries | `h12c2-naive`: 41 calls / $0.0000 / CONTROL / 378.4 s; `h12p2-paged`: 39 calls / $0.0000 / CELL / 400.1 s |
| card's pair table | card §1 | peak 100,455 → 24,776 (0.25×), cache-read 2,022,528 → 447,104 (0.22×), uncached 181,010 → 343,459 (1.90×), share 91.8% → 56.6%, artefact PASS both |
| mode genuinely on | newest paged coverage sidecar | `policyMode stable`, `policyModeSource settings`, `selectionMode stable`, `trigger overflow`, `reason evicted`, `droppedCount 16`, `droppedTokens 69,111` — matches the card's final plan |
| zero hold | trace `local-fc828608…jsonl`, 20 `turn.render` events | `prefix.approxInputTokens` series 10,806 → 15,677 → 20,215 → 24,638 → 24,491 → 24,776 …; **0 consecutive same-size pairs**. Every prompt adds a page, so a trigger fires each time and `stable` degenerates to `fresh`. Confirms condition 3 fails for lack of calls *between* triggers, not from a mode fault |
| structural finding | card §3 | a provider cache keys on a **prefix**; 69,111 tokens are dropped from the **middle**, so reuse truncates at the hole. Holding the selection holds a hole. Append-only growth governs where new content goes, not where eviction cuts. No "hold the choice" variant recovers the cache with a mid-prefix cut |
| design closed | `design/w8-cache-stable-selection.md:3` | status line says H12 measured 19 Nov, NEGATIVE, pointing at the card — the closed hypothesis will not be re-run |
| clean suite | `CTXVM_*` cleared, pytest | 216 passed, 15 subtests — matches |

## 3. What the result is and is not

- **Is:** a measured negative on one free pair, one model, one T-A v2 read-once shape, with a mechanism explanation
  that survives the cell: mid-prefix holes defeat a prefix cache regardless of hold. Published negative results are
  valid outcomes in this repo.
- **Is not:** a cost or saving claim (free tier, harness-reported columns, no receipts), a paging-quality claim, a
  model-quality claim, a determinism claim, or a GO for any further cell. Route-length variance across runs of the
  same arm (41 vs 58 calls) is the card's own reason to claim mechanism, not a token ratio.
- The three options in the card — tail-only eviction, prefix-contiguous compaction, stop paging — are **options,
  not claims**. Choosing one is the owner's decision; none is authorized by this review.

## 4. Carry-forward

The owner's open decision: which option to take. My recommendation, as previously stated, is **tail-only eviction**
— the only variant that keeps a contiguous prefix while still holding the request at a budget — as a policy change
plus one free pair, no spend. But that is a recommendation, not a ruling; no implementation or cell is authorized.

Kit/gate: the card reports ALL GATES GREEN; my clean pytest confirms 216 passed; hygiene was green at the last check.
