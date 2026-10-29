# RR — ADOPTION-INTAKE — 08.1-UPDATE-PROMPT.md intake: conflict check, citation spot-check, W1–W5 schedule

**Card:** the owner's adoption-push master prompt (`08.1-UPDATE-PROMPT.md`)
entered the repo untracked; this card commits it and executes its §10 first
actions: (1) conflict check vs `08-HANDOFF.md`, (2) independent spot-check of
the prior-art citations and quoted figures, (3) the one-page W1–W5 schedule,
then start W1 and W2.

**Attribution:** commits sign `kapitaali <teppo@kapitaali.com>`. No push;
operator pushes personally.

## 1. Spot-check results (§10.2) — ALL CONFIRMED, no repo corrections needed

| Claim (repo site) | Paper statement (locator) | Verdict |
|---|---|---|
| System name "Pichay" (01-PLAN §1) | "We present Pichay, a demand paging system for LLM context windows" — arXiv 2603.09023 abs + §1 | ✓ |
| Quote "…It is L1 cache…" (01-PLAN §1) | "The context window of a large language model is not memory. It is L1 cache" — abs + §1 | ✓ |
| 857-session measurement (01-PLAN §1) | "across 857 production sessions and 4.45 billion effective input tokens" — abs + §1 + §4.1 | ✓ |
| 21.8% structural waste (01-PLAN §1) | "21.8% is structural waste" — abs + §1 + Table 6 (970.4M/4.45B) | ✓ |
| 84.4× median re-mention amplification (01-PLAN §2.2, 07-benchmarks §2) | §1: "stale tool results (8.7%) reprocessed at a median amplification of 84.4×"; §5.1: "For main sessions: median A = 84.4×, P75 = 217.9×, P90 = 570.8×" | ✓ (full-text; NOT in the abstract) |
| §3.5 fault-driven pinning incl. unpin-on-content-change (01-PLAN §1) | §3.5 "Fault-Driven Pinning", algorithm step (4): "On new read of a pinned path with different content (file was edited): unpin" | ✓ |
| Neural Paging = CPP + Semantic Belady, learned controllers (01-PLAN §2.3) | "We formulate the Context Paging Problem (CPP)"; "approximate 'Semantic Belady's Optimality'"; "a lightweight, differentiable Page Controller" — arXiv 2603.02228 abs | ✓ |
| MemGPT coined "virtual context management" (01-PLAN §1) | "we propose virtual context management" — arXiv 2310.08560 abs (v2) | ✓ |

**Paper-internal note (no repo impact):** the arXiv landing abstract of
2603.09023 says "4.45 **million** effective input tokens" while the full text
(abs v1 HTML + §4.1) says "4.45 **billion**" — the full text is self-consistent
(54,170 calls × 82,061 avg tokens ≈ 4.446B). The repo never quotes the 4.45
figure, so nothing to correct; recorded here because the prompt demanded
figure-level scrutiny. **Bonus for W3:** the paper's own §3.2 GC-vs-paging
denominator law ("Only paging (Read evictions) can produce faults… Conflating
them inflates the eviction denominator and deflates the apparent fault rate")
is direct published support for the prompt's `fault_recall` critique — the
ground-truth method should adopt the same hard-fault discipline.

## 2. Conflict list (§10.1) — prompt vs repo state (HANDOFF governs process)

1. **W4 is ~fully landed.** `packages/hermes` exists (plugin, 5 observed
   hooks, typed pause/resume, boot checks, 80 tests); corpus m6 (opencode
   pair) and m7 (hermes pair, user-driven REAL sessions) are dropped,
   schema-validated, and replay-checked. The prompt's W4 acceptance
   ("a real Hermes session produces a trace that passes schema conformance
   and replays with zero divergences") is met by corpus/m7. **Remaining W4
   delta:** the official-docs hook-surface verification note (the prompt's
   own rule: third-party hook names need verifying against
   `hermes-agent.nousresearch.com`), a hooks-are-cheap audit, and the
   `turn.render` observability-gap documented in the trace provenance.
2. **W5's premise is stale:** the prompt says W5 "replaces the 'Vercel AI
   SDK' second adapter as the M2 portability evidence" — but the Vercel AI
   SDK adapter LANDED (T15, live corpus/m8). The repo has THREE emitters
   (opencode, hermes, ai-sdk). W5's core (one identical scripted task in
   OpenCode AND Hermes → `ctxvm diff`, classify divergences) is still open
   and now feeds THREE-way portability.
3. **W2 is genuinely open** — `rust/crates/ctxvm-tokenizer` is a T1a
   scaffold ("token counting backends … deferred; stub only"). No repo
   token count is model-true today.
4. **W1 is genuinely open** — the live wiring exists (T12 opencode adapter,
   T15 ai-sdk), but no waste-report artifact exists. NOTE: the corpora
   (m1/m2/m6/m7/m8) are real captures — the analyzer can be built and
   dry-run against them TODAY, labeled single-corpus/directional, with the
   owner's live-session run to follow.
5. **W6 open** — no `design/otel-mapping.md`. **W7 open** (RFC-0 sealed;
   proposal-only card; application gated on D4). **W8 gated** on W2–W4 +
   D5 budget. **W10 prepare-only** (publish gated). **W11 open** (README
   honesty pass). **W12 Steps 0–1 open** (analysis only; `00-SPEC.md` does
   not exist under that name — the spec is `02-xcabi-events-v0.md` + sealed
   `spec/rfc-0/RFC-0-xCABI.md`; W12 drafts will cite those and live in
   `design/runtime-abi/`).
6. **Process: no conflict.** Reporting protocol (RR + append-only LOG),
   one-commit-per-card, kapitaali signature, operator-gated publishing —
   the prompt and the HANDOFF agree. The §5 board gains one row per workstream
   as each lands (short rows; the RR carries the detail) — the owner's prompt
   is the approval to track them.
7. **Privacy rule adopted repo-wide (§4 of the prompt):** redaction DQ +
   secrets scan + provenance record BEFORE any trace enters `corpus/` or
   leaves the machine — m1–m8 were all redaction-scanned at drop time
   (0-hit records in the LOG); the rule now also covers the W1 live
   dogfood runs (raw stays local; only the redacted summary is a
   deliverable).

## 3. One-page schedule (§10.3) — W1–W5

| # | Card | First command | Deliverable | Deps |
|---|---|---|---|---|
| 1 | **W2 tokenizer** (START NOW) | `cargo test -p ctxvm-tokenizer` after wiring a real backend behind a feature (`tiktoken-rs` o200k/cl100k); provider-reported usage recorded alongside, each count marked | trace events + page-table/manifest carry `tokenizer` identity + `tokens_source: provider\|estimated`; suite green | — |
| 2 | **W1 dogfood analyzer** (START NOW, in parallel) | `node tools/waste-report.mjs corpus/m7/handoff/turn-3` (dry run on the real m7 capture, labeled directional) then the same on the owner's live run | `reports/RR-DOGFOOD-<date>.md` + redacted summary; honest naming: "identifier-touched share", waste as upper bound, limitations section; duplicate-call rate computed from recall events (tool, canonical args) | reads traces; benefits from W2 marks |
| 3 | **W3 metrics** | `python -m pytest benchmarks/metrics -q` after the formula work: hard-fault ground truth (explicit re-calls only — the Pichay §3.2 denominator law, cited), versioned price model as explicit YAML input, bootstrap CIs | updated `07-benchmarks-go-no-go.md` (the 95% gate marked unfalsifiable until then) + metrics tests | W2 marks |
| 4 | **W4 delta** | docs audit against `hermes-agent.nousresearch.com` + the hermes source | hook-surface verification note + cheap-hooks audit + turn.render gap in provenance | — |
| 5 | **W5 cross-harness** | one scripted task run in OpenCode + Hermes (owner runs; nothing published) → `ctxvm diff` | divergence classification (harness vs adapter vs spec) + spec ambiguities → W7 | owner runs the task |
| 6 | W6/W7 (parallel) | — | `design/otel-mapping.md` with locators / RFC-0.1 proposal-only | W5 findings for W7 |

**Sequencing note:** W2 before W1's final numbers (token marks make the
report honest), but W1's analyzer can be built and dry-run immediately —
its v1 numbers re-emit once W2 lands.

## 4. What was done in this card

- Spot-checks above (arXiv abs ×3 + 2603.09023 full text v1).
- Repo scoping: tokenizer stub state confirmed; `reports/` has no
  dogfood/otel artifacts; the 2026-10-22 prior-art audit (RR-AUDIT +
  RR-LOCPASS) found and this check independently re-confirmed.
- Committed `08.1-UPDATE-PROMPT.md` (the owner's prompt, previously
  untracked) so the standard it sets is in-repo.
- `01-PLAN.md` §1 verification note extended with the 2026-10-29
  independent re-check line.

## 5. Open questions for the owner

1. **W2 backend choice:** `tiktoken-rs` (o200k_base + cl100k_base embedded
   vocabs, feature-flagged) as the v0 real tokenizer — or a different
   backend you prefer for your models (NVIDIA NIM nemotron + free-tier
   models are not OpenAI vocabularies; provider-reported usage stays the
   authoritative mark where the harness records it)?
2. **W1 live run:** the dogfood recipe needs YOUR real OpenCode sessions
   with the plugin armed (nothing leaves the machine). Say the word and
   I'll ship the recipe + analyzer; the dry run on m7 starts meanwhile.
3. **D5 later:** W8's budget cap — not needed until W2–W4 land.
