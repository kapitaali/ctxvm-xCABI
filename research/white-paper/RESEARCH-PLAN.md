# Research plan — ctxvm white paper

*(Paths below are repo-relative, as of authoring; the white paper now lives under `research/white-paper/`.)*

## Goal
Write a white paper that explains what the ctxvm / xCABI framework is and how to use it.
Audience: coders, scientists, and generally computer-literate people.
Format: Markdown as single source (MyST for website, Markdown -> LaTeX/WeasyPrint for PDF).
Style: ASD-STE100-inspired (active voice, defined terms, no idioms, no marketing language). Sentence length is not constrained.
Rule: every external claim is web-verified or flagged UNVERIFIED. No hallucinated citations.

## Phases (checkpoint after each)
| Phase | Content | Checkpoint |
|-------|---------|------------|
| P1 | Title, abstract, §1 problem statement, §2 background + prior work (verified citations) | Review outline + background before writing §3 |
| P2 | §3 what ctxvm/xCABI is (definitions, standard, engine, measurement stack) | Review definitions before writing §4 |
| P3 | §4 how to use it (tracer API, CLI, tracer-first adoption, xCABI trace format) | Review tutorial steps for correctness |
| P4 | §5 architecture, §6 metrics, §7 limitations, §8 related work, §9 conclusion, references | Review full draft before Phase 5 |
| P5 | Final review, references, prepare for PDF/website build | Deliver |

## Status
- P1: complete
- P2: complete
- P3: complete
- P4: complete
- P5: complete (PDF built at research/white-paper.pdf; website built at research/_build/html/index.html)

## Deliverables
- `research/white-paper.md` — Markdown single source (495 lines)
- `research/white-paper.pdf` — PDF via WeasyPrint (77KB)
- `research/_build/html/index.html` — website via MyST/Sphinx (94KB)
- `research/RESEARCH-PLAN.md` — phased plan + verified fact baseline

## Source material (all read from repo)
- 00-README.md, 01-PLAN.md, 02-xcabi-events-v0.md, 03-tracer-api-ts.md, 04-odps-dataproduct-corpus.yaml, 05-llms.txt, 06-odps-integration.md, 07-benchmarks-go-no-go.md, 08-HANDOFF.md
- spec/rfc-0/RFC-0-xCABI.md, spec/rfc-0/x-cabi.schema-v0.json
- rust/ (ctxvm-core, ctxvm-codec, ctxvm-tokenizer, ctxvm-conformance)
- benchmarks/metrics/, contracts/, hub/, design/, projects/, reports/
- Web-verified: arxiv 2603.09023 (Pichay, fully read primary HTML), arxiv 2603.02228 (Neural Paging), virtual-context.com (Virtual Context), pypi.org/project/l1-pager + github.com/sarath-m-s/l1-pager (l1-pager), github.com/IBM/chuk-ai-session-manager (IBM session manager)
- UNVERIFIED (do not cite as fact): Pichay conference venue (arXiv only, no venue confirmed)
- VERIFIED (newly confirmed): l1-pager v1.1.1 Context Garbage Collector for LangGraph, Sarath M S, Feb–Mar 2026; LRU/IMPORTANCE/HYBRID eviction, fetch_evicted_page tool; small indie traction (~5★, ~200 weekly downloads). IBM chuk-ai-session_manager: IBM-org OSS session manager with token monitoring, tool-call logging, "infinite context" via automatic summarization — NOT demand paging (summarization-based).
- Pichay 84.4× stale-result amplification: VERIFIED from primary source (Section 1). Pichay token count: 4.45 billion (not million).
- "virtual context management" term origin: MemGPT arXiv 2310.08560 (Packer et al., 2023) → Letta; Virtual Context system (virtual-context.com, Kidwai) is a separate later implementation.
- "65% of context never read": internal estimate from 01-PLAN.md §3, NOT externally verified.

## Verified facts to use (with sources)
- Pichay: arXiv 2603.09023 v1, March 2026, Tony Mason (UBC / Georgia Tech). 857 production sessions, 4.45 billion effective input tokens, 21.8% structural waste (unused tool schemas 11.0%, duplicated content 2.2%, stale tool results 8.7%). Stale results reprocessed at median amplification 84.4×. Fault rate 0.0254% across 1.4M simulated evictions. Up to 93% context reduction (5,038 KB → 339 KB) over 681 production turns. Thrashing under extreme sustained pressure. Source: primary arXiv HTML, fully read.
- Neural Paging: arXiv 2603.02228 v1, 11 Feb 2026, Chen & Liu. Context Paging Problem, Semantic Belady, H-NTM, O(N²)→O(N·K²), Theorem 4 robustness bound, synthetic validation. Paper's own scope: end-to-end eval on real agents is out of scope.
- Virtual Context: virtual-context.com/paper/, Y. Ahmed Kidwai. 20M virtual / 200K real / 60K signal window. Three-layer hierarchy, bidirectional paging, 5 retrieval tools (find_quote, query_facts, expand_topic, remember_when, recall_all). LRU eviction. LongMemEval: 95% vs 33% baseline, 55% fewer tokens (52,347 vs 117,582).
- ODPS 4.1 manifest validated: valid, compliance_level full, production_ready true (SDK 0.4.0). ODCS v3.0.2 contract audit green (datacontract-cli 1.2.7).
- Rust M0: 28+ tests green, 0 warnings; replay determinism byte-identical; conformance validator 108/108 PASS.
- Metric simulator: 18/18 pytest green; fixtures schema-conformance 108/108.