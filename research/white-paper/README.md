# White paper sources

Two renderings of the same paper, each from its own Markdown source. The
duplication is real and is declared here rather than left for a reader to
discover.

| File | Role | Built with |
|---|---|---|
| `../white-paper.pdf` (committed) | the PDF deliverable, 19 pages | `weasyprint` from `white-paper.md` |
| `white-paper.md` | single source for the PDF | — |
| `index.md` | source for the website build (MyST entry point) | `sphinx-build` |
| `conf.py` | Sphinx config; excludes `white-paper.md` and `RESEARCH-PLAN.md` from the site | — |
| `RESEARCH-PLAN.md` | phased plan + verified-fact baseline, as of authoring | — |
| `_build/` | build output, gitignored | — |

## Build

```sh
# PDF (from research/white-paper/)
weasyprint white-paper.md ../white-paper.pdf

# website
sphinx-build -b html . _build/html
```

## Sync rule

`white-paper.md` and `index.md` carry the same twelve sections and are both
maintained by hand. Until one is generated from the other, **every content edit
must land in both**, and a commit touching one without the other is a defect.
The intended fix is a generator card that renders `index.md` from
`white-paper.md` (or the reverse), after which this section shrinks to the
generator command.

## Claims

External claims carry a locator at first mention or are marked `UNVERIFIED`.
Repo facts are reproducible by the commands in `reports/`. File paths are
repo-relative; do not commit absolute home paths here.
