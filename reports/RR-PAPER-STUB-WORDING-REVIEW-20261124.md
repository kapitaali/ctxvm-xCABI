# RR-PAPER-STUB-WORDING-REVIEW-20261124 — verified: A3/A4 wording matches 0.13.33 wire; prior-art locators checked

Review lane, verify-then-record. Subject: research lane `reports/RR-PAPER-STUB-WORDING-20261124.md` (untracked),
Part I tracked working changes in `research/white-paper/white-paper.md` + `index.md`, Part II intentionally
gitignored working source `research/uncommitted/white-paper-Part-II_reviewed.md`, and the research literature note
`reports/RR-SHADOW-RESEARCH-20261124.md` (untracked). Date 2026-11-24. $0, no model call, no push.

## 1. A3/A4 implementation facts verified

The new Part I wording says: as of 2026-11-24, opt-in Hermes stub mode 0.13.33 emits `page.render(mode=stub)` and
`page.evict` per dropped result at the same visibility turn; drop mode emits neither; other shipped adapters still
emit `full` at first reveal. This matches the verified implementation (`RR-STUB-RENDER-REVIEW-20261124`):
`Tracer.emit_stub_render`, `Tracer.emit_evict`, bridge emits both at `tracer._turn`, drop-mode zero, 0.13.33 live.
The §16 limitation now says stub mode records stubbed identities + exact stub text while drop mode still does not
record omissions — accurate, and it does **not** claim raw-request-byte reconstruction.

Verified locations:
- `research/white-paper/white-paper.md:265,583`
- mirrored in `research/white-paper/index.md:271,589`

Part II's abstract/terms/§2.1/§2.4/§10 carry the same stub-vs-drop distinction. The terms table's "Render" entry is
the paper's render projection, not a claim that `page.render` itself has `stubText`; the next sentence names
`page.evict` explicitly. No schema over-claim.

## 2. Source-path erratum verified

`RR-PAGE-EVICT-PAPER-ROUTE` named `research/uncommitted/white-paper_reviewed.md` as Part I. That file is the
research note, not Part I. The corrected paths are right:
- Part I: `research/white-paper/white-paper.md` (tracked), mirrored by `research/white-paper/index.md`;
- Part II: `research/uncommitted/white-paper-Part-II_reviewed.md` (intentionally gitignored working source).

The owner's gitignore policy is unchanged. The earlier review route's path error is now explicitly corrected, not
silently rewritten.

## 3. External prior-art claims checked against primary sources

| claim in research note | primary locator checked | result |
|---|---|---|
| DTOC stores full tool outputs externally, replaces disabled outputs with metadata-only placeholders, exposes `manage_context(enable, disable)` | [arXiv:2609.26121v1 HTML §3.1–3.3](https://arxiv.org/html/2609.26121v1) | **verified** — exact method description; the note's "method + abstract results, not independently reproduced" evidence level is honest |
| Scroll keeps append-only Event Log + stable addresses; eviction index of headlines supports on-demand materialization | [arXiv:2608.21690v1 HTML §2.2–2.4](https://arxiv.org/html/2608.21690v1) | **verified** — append-only log §2.2, eviction index and address-anchored headlines §2.4 |
| ACM gives `manage_context` + `query_memory`, offloads raw messages and queries them later | [arXiv:2607.23809v1 HTML §3](https://arxiv.org/html/2607.23809v1) | **verified** — exact tool/memory mechanism |
| QEvict uses recoverable quantized KV tier; importance drifts; FMM/reactivation diagnostics | [arXiv:2608.05326v1 HTML §1, §3](https://arxiv.org/html/2608.05326v1) | **verified** — recoverable three-tier KV scheme and FMM/Global LIR diagnostics; different layer, correctly labeled KV not prompt pages |

No benchmark result is reproduced or attributed to ctxvm. The narrowed contribution — portable attestation of
omission/recovery under a specified keep law, not inventing recoverable placeholders — is supported by these
sources and keeps the repo's no-cost-saving/no-paging-quality claim ceiling.

## 4. Repo state / ownership

- Part I changes are present but **unstaged** (` M research/white-paper/index.md`, ` M research/white-paper/white-paper.md`).
- Part II is the intentionally gitignored working source; its edits are on disk, not committable by design.
- `reports/RR-PAPER-STUB-WORDING-20261124.md`, `reports/RR-SHADOW-RESEARCH-20261124.md`, and
  `reports/RR-PAGE-EVICT-RESEARCH-20261124.md` are **untracked research-lane artifacts**.
- I edited none of those files. Research/owner must commit its own tracked artifacts via its private index; review
  commits only this review card + LOG/day. The research card's "sandbox-only / copy-staging" note describes its
  pre-copy state; the tracked Part I edits are now present in the shared tree, so that sentence is historical, not
  the current status.

## 5. Verification / limits

`bash tools/run-ci.sh` unpiped → **rc=0 ALL GATES GREEN**; `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK.
No arm, model call, spend, default-on, D17, Part B re-score, or push. No live stub-mode capture exists; the accepted
Part C attestation/re-read gap remains unchanged. No cost-saving, paging-quality, model-quality, determinism, or
`stubText`-redaction claim.

## 6. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
