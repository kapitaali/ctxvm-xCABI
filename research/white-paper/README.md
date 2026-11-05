# White paper sources

Two renderings of the same paper, each from its own Markdown source. The
duplication is real and is declared here rather than left for a reader to
discover.

| File | Role | Built with |
|---|---|---|
| `../white-paper.pdf` (committed) | the PDF deliverable, 15 pages | `bash build-pdf.sh` — Markdown → HTML (UTF-8) → WeasyPrint |
| `white-paper.md` | single source for the PDF | — |
| `index.md` | source for the website build (MyST entry point) | `sphinx-build` |
| `conf.py` | Sphinx config; excludes `white-paper.md` and `RESEARCH-PLAN.md` from the site | — |
| `RESEARCH-PLAN.md` | phased plan + verified-fact baseline, as of authoring | — |
| `_build/` | build output, gitignored | — |

## Build

```sh
# PDF (from research/white-paper/)
bash build-pdf.sh              # writes ../white-paper.pdf

# website
sphinx-build -b html . _build/html
```

`build-pdf.sh` exists because the old instruction was wrong: WeasyPrint has no Markdown
reader, so `weasyprint white-paper.md ../white-paper.pdf` rendered the Markdown as plain
text — mojibake em dashes, no headings, no tables, 11 pages instead of the real document.
The script converts Markdown to HTML with an explicit UTF-8 charset and a print stylesheet,
then renders that. The page count is a consequence of the stylesheet, not a fixed target.

## Sync rule

`white-paper.md` is the single source of the body; `index.md` is generated from it
and keeps only its own front block (title, status). The generator exists as of
2026-11-05:

```sh
python3 sync-index.py            # rewrite index.md from white-paper.md
python3 sync-index.py --check    # exit 1 if index.md is stale
```

Edit `white-paper.md`, run the generator, and commit both. A commit that changes
the body of one without the other is now a defect the `--check` mode can catch.

## Claims

External claims carry a locator at first mention or are marked `UNVERIFIED`.
Repo facts are reproducible by the commands in `reports/`. File paths are
repo-relative; do not commit absolute home paths here.
