# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from typing import List


project = "GeoNinja"
copyright = "Copyright 2026, Urban Energy Systems Lab, Empa"
author = "Urban Energy Systems Lab, Empa"
release = "1.0.0"

# -- General configuration ---------------------------------------------------


# extensions = ['sphinx.ext.autosectionlabel', 'sphinx.ext.autodoc']
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax"
]

myst_enable_extensions = [
    "dollarmath",
    "amsmath",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns: List[str] = []
root_doc = "index"


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "includehidden": True,
}
html_static_path = []

# -- Options for PDF output --------------------------------------------------
latex_engine = "xelatex"
latex_documents = [
    (
        "index",
        "GeoNinja Documentation",
        "Urban Energy Systems Lab, Empa",
        "manual",
    ),
]
latex_elements = {
    "preamble": r"""
\usepackage{pdflscape}
\usepackage{adjustbox}
""",
}
