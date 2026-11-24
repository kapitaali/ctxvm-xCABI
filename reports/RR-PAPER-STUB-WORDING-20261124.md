# RR-PAPER-STUB-WORDING-20261124 — paper wording now matches stub-mode wire; source-path erratum

Lane: research. Zero spend, zero model calls. Sandbox-only changes; repo untouched until the
owner runs `copy-staging.sh`. Implements the wording routed by `RR-PAGE-EVICT-PAPER-ROUTE`
and the design §5 requirement that paper and wire agree.

## 1. Source-path erratum

The route names `research/uncommitted/white-paper_reviewed.md` as Part I. That file is the
research note, not Part I. Verified actual sources:

- Part I: `research/white-paper/white-paper.md` (tracked), mirrored by `research/white-paper/index.md`;
- Part II: `research/uncommitted/white-paper-Part-II_reviewed.md` (intentionally gitignored working source).

The owner's policy that uncommitted sources are intentional is unchanged. This card corrects
only the wrong filename in the route.

## 2. Wording applied (sandbox copies)

Part I (`white-paper.md` + `index.md`):
- §3.11 now says Hermes stub mode 0.13.33 emits `page.render(mode=stub)` + `page.evict` per
  dropped result at the same visibility turn; drop mode emits neither; other adapters still
  emit `full` at first reveal.
- §16 now says stub mode records stubbed identities + exact stub text; drop-mode omissions
  remain unrecorded.

Part II:
- abstract, terms table, §2.1, §2.4 and §10 now distinguish stub-mode omissions (recorded)
  from drop-mode omissions (still unrecorded).
- §2.4 records the 0.13.33 behavior and keeps the historical W8 capture explicitly as a
  drop-mode example.
- §2.4 adds prior art: DTOC (arXiv:2609.26121), Scroll (arXiv:2608.21690), ACM
  (arXiv:2607.23809). The narrowed contribution is portable attestation of omission/recovery
  under a specified keep law, not the invention of recoverable placeholders.

## 3. Verification

```
grep -n 'Hermes stub mode' research/white-paper/white-paper.md research/white-paper/index.md
grep -n 'page.render(mode=stub)' research/uncommitted/white-paper-Part-II_reviewed.md
grep -n 'DTOC\|Scroll\|ACM' research/uncommitted/white-paper-Part-II_reviewed.md
```

All external claims carry primary arXiv locators and are marked method-level readings; no
benchmark result is reproduced or claimed. The implementation facts are verified by
`RR-STUB-RENDER-REVIEW-20261124` (0.13.33 live, full stub wire, default-off sidecars). No
cost-saving, paging-quality, model-quality or unscoped-determinism claim. No
E0/E1/E2/M1/M2/M3 pooling.

## 4. Note to the review lane

Please verify the staged source copies and record LOG/day/PROJECT-STATE as appropriate. The
research note `RR-SHADOW-RESEARCH-20261124.md` carries the broader literature synthesis and
the proposed shadow-mode measurement. The earlier `RR-PAGE-EVICT-RESEARCH-20261124.md` has
its three stale locators corrected and an implementation-update section.

Nothing here authorizes a live stub arm, a model call, a restart, default-on stub mode, D17,
or a push. The accepted live-attestation/re-read gap remains open.
