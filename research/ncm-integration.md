# NCM → ctxvm Integration Analysis

**Source:** arXiv 2610.14162 "Next-Concept Modeling: Fast, Parallel Coarse-to-Fine Text Generation"
(Kumbong, Khare, Mlauzi, Woen, Ding, Buchanan, Arora, Mirhoseini, Ré; Stanford / Together AI; Oct 2026)
**Location:** ctxvm/research/ncm-integration.md
**Status:** Analysis notes — not yet implemented

---

## What NCM Is

**Next-Concept Modeling (NCM)** is a two-stage, coarse-to-fine text generation framework:

1. **Stage 1 — Encoder:** A multiscale residual VQ-VAE encodes text into **K levels of discrete codes**, from short coarse representations (level 1) to longer fine ones (level K), where K << L (token count).
2. **Stage 2 — Generator:** A transformer generates levels **sequentially**, but predicts all codes within each level **in parallel**, conditioned on the reconstruction of earlier levels (`ẑ^(k-1)`). After the final level, the cumulative reconstruction is decoded into tokens.

Key verified claims:
- K << L steps — generates in far fewer steps than tokens
- Coarse levels capture global structure; finer levels add detail (probed in Appendix H, Figs 17–19)
- Generation trajectory: coarse predictions get corrected at finer levels (Fig 3 German→English, Fig 20 Sudoku)
- 21–31× faster than diffusion baselines at comparable quality; 4–5× fewer training tokens
- Test-time scaling: saved time + MBR decoding → ~7% higher ROUGE-L within same budget

---

## Mapping NCM Concepts onto ctxvm

ctxvm is a virtual-memory manager for LLM agent context — it decides what stays resident in the context window (pages) vs what gets evicted (stubs), tracks faults, and replays traces deterministically. NCM operates at the generation layer, not context management, but the two share a core insight: **not all tokens are equal, and you can pay coarse-to-fine.**

| NCM concept | ctxvm mapping |
|-------------|---------------|
| Level-k code `r_k^i` (coarse → fine) | Page at fidelity level k |
| `ẑ^(k-1)` (reconstruction of earlier levels) | Resident pages already rendered |
| Level k codes conditioned on earlier levels | Page render depends on resident context |
| Decode cumulative reconstruction to tokens | Final render = stubs + resident content |
| Coarse→fine refinement | Stub → fuller content on demand |

ctxvm's page table is already keyed by `(logical_ref, content_hash)` with stubs for evicted pages. The stub format `[Paged out: read src/auth/session.ts (8.2k tok, 187 lines). Re-call...]` is essentially a level-1 code — a coarse placeholder. NCM's refinement process shows how to progressively replace stubs with finer detail without re-rendering everything.

### 1. Multi-resolution page table

Add a `fidelity_level` field to pages. The renderer renders all resident pages at level 1 (coarse), then refines evicted pages to level 2/3 on demand:

```
page = {
  page_id = (logical_ref, content_hash),
  kind = file | tool_result | summary | image_ref,
  fidelity_level = 1 | 2 | 3,   # NEW
  tokens = <token count at this fidelity>
}
```

A page can be evicted *down* a level instead of fully evicted: a level-3 page (full text) becomes a level-2 page (compressed summary) becomes a level-1 page (stub). This is NCM's coarse-to-fine applied to context management.

### 2. Fault taxonomy extension

NCM's trajectory shows coarse predictions corrected at finer levels (e.g., "Ag" → "Ag however" → "However, Ag there Ag is Ag concern..." → correct English). Each correction is a coarse-level fault resolved at finer fidelity.

ctxvm's fault taxonomy (`tool_recall`, `identifier_scan`, `explicit_api`, `semantic_*`) could add:
- **`coarse_fault`** — a page was rendered at too-coarse fidelity and needs refinement
- **`refine_fault`** — a page's stub needs to be replaced with fuller content

This gives ctxvm a **refinement loop** analogous to NCM's coarse-to-fine generation: render cheap stubs first, then page-in detail only where needed.

### 3. Deterministic replay of refinement trajectories

NCM's generation is deterministic given model + seed. Each step produces codes at a level. ctxvm's replay engine already guarantees byte-identical re-renders of traces. NCM traces could be recorded as xCABI events:

- `page.declare` for each level-k code batch
- `page.render` showing which fidelity level is visible
- `page.fault` (source: `refine`) when a coarse code is refined

The xCABI schema already supports arbitrary event payloads, so adding `page.refine` would not break the schema.

### 4. Metric simulator extensions

ctxvm's four formulas:
- `net_token_reduction`, `fault_recall`, `touch_ratio`, `thrash_index`

NCM introduces additional measurable quantities:
- **NFE (function evaluations) per level** — "fault evaluations per level": how many pages needed refinement
- **Coarse-to-fine speedup** — tokens saved by rendering coarse levels first vs always rendering full
- **Per-level touch ratio** — which fidelity levels actually get touched by the model vs wasted

These could be added as optional metrics without changing the existing four.

### 5. Test-time scaling for paging

NCM shows saved inference time can be used for MBR decoding — generate more candidates, pick the best. ctxvm could analogously use saved context budget (from evicting stubs) to page in more candidate pages, run multiple eviction policies in parallel and pick the best by touch ratio, or pre-fetch pages likely needed based on coarse-level predictions.

---

## Concrete Implementation Sketch

### Phase 1: Multi-resolution pages (no engine change)

Add `fidelity_level` to the page descriptor and stub format:

```json
{
  "type": "page.declare",
  "page": {
    "id": {"logicalRef": "file:src/auth.ts", "contentHash": "sha256:abc"},
    "kind": "file",
    "tokens": 8192,
    "fidelity_level": 1
  },
  "stubText": "[Paged out: src/auth.ts (8.2k tok)]"
}
```

Renderer renders level-1 pages as stubs, level-2 as compressed, level-3 as full. Eviction works at any level — evict a level-3 page down to level 2 instead of fully evicting.

### Phase 2: Refinement faults

Add `page.refine` event type: a page at level k is being refined to level k+1. Fault taxonomy gets `refine` as a source. Renderer applies refinements in order (coarse → fine), producing a progressive render trace.

### Phase 3: NCM-native traces

Record NCM generation sessions as xCABI traces where each level is a page. Corpus gets a new artifact class: "paged generation traces" where you can replay not just what the model saw, but at what fidelity, and measure how much detail was actually needed.

---

## Bottom Line

NCM and ctxvm solve different problems (generation vs. context management) but share the same insight: **not all tokens are equal, and you can pay coarse-to-fine.** ctxvm's page/stub mechanism is essentially a manual, application-level version of what NCM does automatically with a VQ-VAE + transformer hierarchy. Integrating them means ctxvm could manage context at multiple fidelity levels, with NCM-style refinement as the fault/repair mechanism, and the whole thing still replayable byte-identically via xCABI.