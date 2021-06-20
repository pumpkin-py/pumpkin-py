# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "pumpkin.py core"
copyright = "2021, Czechbol, sinus-x"
author = "Czechbol, sinus-x"

with open("../pumpkin.py", "r") as handle:
    version = "UNKNOWN"
    for line in handle.readlines():
        if line.startswith("__version__"):
            version = line.split(" = ")[1].strip(' \n"')
            break

release = version

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "autoapi.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for extensions --------------------------------------------------

# Change the colors of code snippets
pygments_style = "sphinx"

# TODO Description
todo_include_todos = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "discord": ("https://discordpy.readthedocs.io/en/latest/", None),
}

autodoc_default_options = {
    "members": True,
    "members-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
}

autoapi_dirs = [
    "../core",
    "../database",
    "../modules",
    "../pumpkin.py",
]
autoapi_type = "python"
autoapi_generate_api_docs = True
autoapi_member_order = "bysource"
autoapi_python_class_content = "class"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
