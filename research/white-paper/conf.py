# Sphinx configuration for ctxvm white paper website
project = "ctxvm / xCABI — White Paper"
author = "ctxvm Project"
extensions = ["myst_parser"]
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "amsmath",
    "html_image",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3
html_theme = "sphinx_book_theme"
html_title = "ctxvm / xCABI — A white paper"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "RESEARCH-PLAN.md", "white-paper.md"]
