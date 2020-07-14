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
sys.path.insert(0, os.path.abspath('../../src/'))


# -- Project information -----------------------------------------------------

project = 'Alfred'
copyright = '2020, Kyle Darling'
author = 'Kyle Darling'

# The full version, including alpha/beta/rc tags
release = '0.1.0'


# -- General configuration ---------------------------------------------------

extensions = ['sphinx.ext.napoleon']
templates_path = ['_templates']
source_suffix = ['.rst']
master_doc = 'index'
exclude_patterns = ['_build']
pygments_style = 'sphinx'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'

html_theme_options = {
    'description': 'Python AI for training',
    'fixed_sidebar': True,
    'github_button': True,
    'github_repo': "https://github.com/IAmAbszol/Alfred",
    'github_user': "IAmAbszol",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_sidebars = {
    "**": [
        "about.html",
        "localtoc.html",
        "relations.html",
        "searchbox.html",
    ]
}


# -- Extension configuration -------------------------------------------------

from sphinx.ext.autodoc import ClassLevelDocumenter, InstanceAttributeDocumenter

autodoc_member_order = 'bysource'

def skip(app, what, name, obj, skip, options):
    if name == '__init__' and obj.__doc__:
        return False
    return skip

def setup(app):
    app.connect("autodoc-skip-member", skip)
    app.add_stylesheet('custom.css')
    app.add_javascript('custom.js')

# remove the useless " = None" after every ivar
def iad_add_directive_header(self, sig):
    ClassLevelDocumenter.add_directive_header(self, sig)

InstanceAttributeDocumenter.add_directive_header = iad_add_directive_header