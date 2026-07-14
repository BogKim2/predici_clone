from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "PREDICI Clone Manual"
author = "PREDICI Clone contributors"
release = "0.1.0"
language = "ko"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autosummary_generate = True
autodoc_typehints = "none"
autodoc_member_order = "bysource"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "PREDICI Clone Manual"

html_theme_options = {
    "description": "Polymerization simulation, GUI, API, and validation guide",
    "fixed_sidebar": True,
    "page_width": "1120px",
    "sidebar_width": "260px",
}
