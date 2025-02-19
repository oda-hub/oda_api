# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import json
sys.path.insert(0, os.path.abspath('../../'))
#import oda_api
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'


# -- Project information -----------------------------------------------------

project = 'oda_api'
author = 'Andrea Tramacere, Volodymyr Savchenko, Gabriele Barni'
copyright = '2021, ' + author


with open('../../oda_api/pkg_info.json') as fp:
    _info = json.load(fp)

__version__ = _info['version']

version = __version__

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [ 'sphinx.ext.autodoc',
               'sphinx.ext.doctest',
               'sphinx.ext.intersphinx',
               'sphinx.ext.todo',
               'sphinx.ext.coverage',
               'sphinx.ext.ifconfig',
               'sphinx.ext.viewcode',
               'sphinx.ext.autosummary',
               'sphinx.ext.graphviz',
               'sphinx_automodapi.automodapi',
               'sphinx.ext.inheritance_diagram',
               'sphinx.ext.autosummary',
               'sphinx.util.console',
               'nbsphinx',
               'sphinx.ext.mathjax']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']


# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

exclude_patterns = ['_build', '**.ipynb_checkpoints']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#theme = 'bootstrap'

theme='sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


if theme=='sphinx_rtd_theme':
#    html_theme='sphinx_rtd_theme'
    html_theme = 'furo'

    html_theme_options = {
        #'canonical_url': '',
        #'analytics_id': 'UA-XXXXXXX-1',  # Provided by Google in your dashboard
        'logo_only': False,
        'display_version': True,
        'prev_next_buttons_location': 'bottom',
        #'style_external_links': False,
        #'vcs_pageview_mode': '',
        # Toc options
        'collapse_navigation': True,
        'sticky_navigation': True,
        'navigation_depth': 4,
        #'includehidden': True,
        #'titles_only': False
    }

if theme=='bootstrap':
    html_theme = 'bootstrap'

    #html_sidebars = {'**': ['localtoc.html', 'sourcelink.html', 'searchbox.html']}

    #html_sidebars = {
    #    '**': ['localtoc.html'],
    #}
    html_sidebars = {'**': ['my_side_bar.html', 'sourcelink.html']}


    html_static_path = ['_static']

    html_theme_options = {
        # Navigation bar title. (Default: ``project`` value)
        'navbar_title': "oda api",

        # Tab name for entire site. (Default: "Site")
        'navbar_site_name': "oda api",

        # A list of tuples containing pages or urls to link to.
        # Valid tuples should be in the following forms:
        #    (name, page)                 # a link to a page
        #    (name, "/aa/bb", 1)          # a link to an arbitrary relative url
        #    (name, "http://example.com", True) # arbitrary absolute url
        # Note the "1" or "True" value above as the third argument to indicate
        # an arbitrary url.
        #'navbar_links': [
        #    ("Examples", "examples"),
        #    ("Link", "http://example.com", True),
        #],

        # Render the next and previous page links in navbar. (Default: true)
        'navbar_sidebarrel': 'True',

        # Render the current pages TOC in the navbar. (Default: true)
        'navbar_pagenav': 'true',

        # Tab name for the current pages TOC. (Default: "Page")
        'navbar_pagenav_name': "Page",

        # Global TOC depth for "site" navbar tab. (Default: 1)
        # Switching to -1 shows all levels.
        'globaltoc_depth': 2,

        # Include hidden TOCs in Site navbar?
        #
        # Note: If this is "false", you cannot have mixed ``:hidden:`` and
        # non-hidden ``toctree`` directives in the same page, or else the build
        # will break.
        #
        # Values: "true" (default) or "false"
        'globaltoc_includehidden': "true",

        # HTML navbar class (Default: "navbar") to attach to <div> element.
        # For black navbar, do "navbar navbar-inverse"
        'navbar_class': "navbar navbar-inverse",

        # Fix navigation bar to top of page?
        # Values: "true" (default) or "false"
        'navbar_fixed_top': "true",

        # Location of link to source.
        # Options are "nav" (default), "footer" or anything else to exclude.
        'source_link_position': "nav",

        # Bootswatch (http://bootswatch.com/) theme.
        #
        # Options are nothing (default) or the name of a valid theme
        # such as "cosmo" or "sandstone".
        #
        # The set of valid themes depend on the version of Bootstrap
        # that's used (the next config option).
        #
        # Currently, the supported themes are:
        # - Bootstrap 2: https://bootswatch.com/2
        # - Bootstrap 3: https://bootswatch.com/3
        'bootswatch_theme': "spacelab",

        # Choose Bootstrap version.
        # Values: "3" (default) or "2" (in quotes)
        'bootstrap_version': "3",
    }


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'oda_apidoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'oda_api.tex', 'oda\\_api Documentation',
     'andrea tramacere', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'oda_api', 'oda_api Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'oda_api', 'oda_api Documentation',
     author, 'oda_api', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']

nbsphinx_execute = 'never'
