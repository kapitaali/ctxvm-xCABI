#!/usr/bin/env bash
# Build research/white-paper.pdf from white-paper.md.
#
# Why this script exists: the README used to say `weasyprint white-paper.md ../white-paper.pdf`.
# WeasyPrint has no Markdown reader — it renders whatever it is given as HTML — so that command
# produced a garbled, 11-page plain-text rendering (mojibake em dashes, no headings, no tables)
# where the committed deliverable has 19 proper pages. The missing step was Markdown → HTML with
# an explicit UTF-8 charset, which is what this script does.
#
# Usage: bash build-pdf.sh   (writes ../white-paper.pdf)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ROOT="$(cd ../.. && pwd)"
PY="$ROOT/venvs/odps/bin/python"
WEASY="$ROOT/venvs/odps/bin/weasyprint"
[ -x "$PY" ] || { echo "build-pdf: missing $PY (run tools/setup-env.sh)" >&2; exit 2; }
[ -x "$WEASY" ] || { echo "build-pdf: missing $WEASY (pip install weasyprint in the odps venv)" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

"$PY" - "$TMP/paper.html" <<'PYEOF'
import sys, markdown

SRC = "white-paper.md"
CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm;
        @bottom-center { content: counter(page) " / " counter(pages);
                         font-size: 8.5pt; color: #666; } }
body { font-family: "DejaVu Serif", Georgia, serif; font-size: 10.4pt; line-height: 1.42;
       color: #111; hyphens: auto; }
h1 { font-size: 19pt; line-height: 1.2; margin: 0 0 14pt; padding-bottom: 6pt;
     border-bottom: 1.5pt solid #333; page-break-after: avoid; }
h2 { font-size: 13.5pt; margin: 15pt 0 7pt; page-break-after: avoid; }
h3 { font-size: 11.4pt; margin: 12pt 0 5pt; page-break-after: avoid; }
h4 { font-size: 10.6pt; margin: 10pt 0 4pt; page-break-after: avoid; }
p, li { margin: 0 0 5pt; }
ul, ol { margin: 0 0 6pt 0; padding-left: 16pt; }
code, pre { font-family: "DejaVu Sans Mono", monospace; }
code { font-size: 8.9pt; background: #f4f4f4; padding: 0; border-radius: 2pt; }
pre { font-size: 8.6pt; background: #f7f7f7; border-left: 2pt solid #ccc;
      padding: 6pt 8pt; margin: 7pt 0; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 7pt 0 9pt; }
th, td { border: 0.5pt solid #b8b8b8; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #eeeeee; }
blockquote { margin: 7pt 0 7pt 10pt; padding-left: 8pt; border-left: 2pt solid #ddd; color: #333; }
hr { border: none; border-top: 0.5pt solid #ccc; margin: 12pt 0; }
a { color: #0b4f9c; text-decoration: none; }
img { max-width: 100%; }
"""

body = markdown.markdown(
    open(SRC, encoding="utf-8").read(),
    extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    output_format="html5",
)
html = ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>Virtual memory for LLM agent context</title>\n<style>{CSS}</style>\n"
        f"</head>\n<body>\n{body}\n</body>\n</html>\n")
open(sys.argv[1], "w", encoding="utf-8").write(html)
print(f"build-pdf: html {len(html)} bytes, {body.count('<h2')} h2 / {body.count('<h3')} h3, "
      f"{body.count('<table')} tables")
PYEOF

"$WEASY" -e utf-8 "$TMP/paper.html" ../white-paper.pdf
echo "build-pdf: wrote ../white-paper.pdf ($(stat -c%s ../white-paper.pdf) bytes)"
