# RR-PAGE-EVICT-RESEARCH-20261124 — research-side suggestion for the owner-gated page.evict card

Lane: research. Zero spend, zero calls, no commit. Answer to the reviewer's `page.evict` card:
what does our own research say that should shape it? Grounded in the research copies (files
win over chat). Findings are suggestions, not rulings — the card stays owner-gated.

## 1. The suggestion in one line

**Do not emit `page.evict` from a hook that only knows an eviction was planned; emit it from
the same seam that writes the stub into the request, and equalize the turn tag against
`page.render(mode=stub)` — the ground-truth event the research already names.** That directly
answers the card's timing caveat and its honesty requirement.

## 2. Why — three research locators

1. **The wire's own semantics make `page.evict` the record of what the model saw, not what the
   pager intended.** Part I's event table (`research/white-paper/white-paper.md:152-153`) defines
   `page.render` as "turn #, mode (full or stub) — **ground truth** for waste measurement" and
   `page.evict` as "turn #, stub text used — the paging decision and **what the model was told**."
   Part II §1.1 (`research/uncommitted/white-paper-Part-II_reviewed.md`, Render/Stub rows) is
   identical in substance: Render records full content for resident pages and stub text for
   stubbed pages; Fault requires the reference be *evicted*. So the honest source of the stub
   text and its visibility time is the render seam.

2. **The timing hazard the reviewer flags is already known and bounded by the sealed model.**
   `rust/crates/ctxvm-core/src/page_table.rs:4-13` states the event-effect timing: `page.evict @ t
   → stub visible AT turn t` (batched at the boundary before the turn they are tagged with), and
   `page.fault @ t → re-materialized FROM t+1`. The reviewer's "two-calls-per-turn bucketing"
   concern is exactly a risk of tagging the evict at the call boundary instead of the turn
   boundary. The card's design question should be settled as: **tag the evict with the turn at
   which the stub first becomes visible, and assert it equals the first `page.render(mode=stub)`
   for that page in replay.** The checker then has a mechanical cross-check, not an assumption.

3. **The re-classification payoff the card claims is precisely a research measurement claim.**
   Part I `:245-247`: conventional logging cannot distinguish "the model was told" from "the model
   never saw it"; context tracing records both plus "the exact rendered message array". Part I
   `:265` says `page.render` captures the render mode per page per turn and `page.fault` captures
   re-requests of evicted content. If a re-read of a stubbed page is currently counted as
   "faultOfResidentPage" (E0's replay violations class), emitting `page.evict` with matching
   render mode removes that false class — the derived table would show a stub, not a resident
   page that faulted. This is the metric-integrity reason to do it.

## 3. The reviewer's own earlier wording (research copy)

The Part III review's A3/A4 asks (`reports/RR-PAPER-REVIEW-20261115.md:266-288`) recommended
**format-scoped + adapter-scoped** wording: "The `page.render` event can carry full or stub per
page per turn. The shipped adapters today emit full only, once per page, at its first reveal";
and an honest §16 limit: "the shipped adapters do not yet emit the stub renders that would
record a turn's omissions." A `page.evict` emission in stub mode is the adapter change that
retires that caveat — so the paper wording should change in the **same card**, or the trace and
the paper will disagree. This is the suggestion closest to "what we should tell the reviewer."

## 4. Scope guard the research record demands

- **Stub mode only.** The drop mode's earlier honesty decision (`RR-W8CEVICT`, 2026-11-11) still
  holds; no stub text = no `page.evict`. The card already says this — keep it.
- **No claim.** This is instrument hygiene, not evidence of paging benefit, recoverability, cost
  saving (law 7), or fault-rate improvement. `RR-RECOVER-BLOCKED-20261123` recorded that no live
  `stubDropped: recoverable` sidecar exists and the re-read readout remains UNVERIFIED — emitting
  `page.evict` makes future captures self-describing; it does **not** fill that gap retroactively.
- **Redaction/consent:** `stubText` is a known raw-text channel (Part II §13 audit,
  `:360`; `RR-FIELDAUD`); the bounded stub-arg escape in 0.13.31 helps, but G4's consumer reports
  `channels modelled: logicalRef` — do not claim stubText redaction.

## 5. Concrete suggestion for the card's design question

1. Emit from the render/stub seam, with `stubText` byte-identical to the text placed in the request.
2. Set `turn` = the turn at which that stub is first visible; cross-check in replay against the
   first `page.render(mode=stub)` for the same `(logicalRef, contentHash)`; fail the gate if unequal.
3. Add a negative fixture: drop-mode capture must emit **zero** `page.evict` rows (honesty guard).
4. Update Part I/II wording (A3/A4 merged) in the same landing so paper and wire agree.
5. Route implementation to hermes lane; review verifies trace/validator side; do not default-on
   without a new ruling; no push from this lane.

LOG/day owed to the review lane if landed. Nothing authorized or started here.

## 6. Implementation update and source-path erratum (2026-11-24)

The suggestion was subsequently ruled, authored, and implemented: `design/page-evict-stub-mode.md`,
`RR-PAGE-EVICT-RULING`, `RR-PAGE-EVICT-IMPL`, and `RR-STUB-RENDER` (Hermes 0.13.33). The
implementation emits both events at the same current turn; Rust replay checks turn + PageId,
not `stubText` on `page.render` (which the sealed schema does not allow). The accepted
attestation gap remains: no live `stubDropped: recoverable` sidecar or observed re-read exists
(`RR-PARTC-ARM-RESULT`, `RR-RECOVER-BLOCKED`).

**Source-path erratum:** `RR-PAGE-EVICT-PAPER-ROUTE` names
`research/uncommitted/white-paper_reviewed.md` as the Part I source. That file is actually the
research note ("ctxvm and AI safety: research note…"), not Part I. The real Part I source is
`research/white-paper/white-paper.md` (with `index.md` as its mirror); Part II is
`research/uncommitted/white-paper-Part-II_reviewed.md`. The staged wording update uses those
actual files. This is a locator correction, not a change to the owner's policy that uncommitted
sources are intentional.
