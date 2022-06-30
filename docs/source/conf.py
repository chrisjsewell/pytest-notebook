# -*- coding: utf-8 -*-
#
# pytest-notebook documentation build configuration file
#
# This file is execfile()d with the current directory set to its
# containing dir.

import os
import subprocess
import sys

import pytest_notebook

# -- General configuration ------------------------------------------------

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
]

templates_path = []
exclude_patterns = ["_build", "**/.ipynb_checkpoints", "**/example_nbs"]

master_doc = "index"

# General information about the project.
project = "pytest-notebook"
copyright = "2019, Chris Sewell"  # noqa: A001
author = "Chris Sewell"
# The full version, including alpha/beta/rc tags, will replace |release|
release = pytest_notebook.__version__
# The short X.Y version, will replace |version|
version = ".".join(release.split(".")[:2])

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.6", None),
    "_pytest": ("https://doc.pytest.org/en/latest/", None),
    # "PIL": ("http://pillow.readthedocs.org/en/latest/", None),
    "nbclient": ("https://nbclient.readthedocs.io/en/latest/", None),
    "nbformat": ("https://nbformat.readthedocs.io/en/latest/", None),
    "attr": ("https://www.attrs.org/en/stable/", None),
    "coverage": ("https://coverage.readthedocs.io/en/6.2/", None),
}

intersphinx_aliases = {
    ("py:class", "List"): ("py:class", "list"),
    ("py:class", "Sequence"): ("py:class", "list"),
    ("py:class", "Mapping"): ("py:class", "dict"),
    ("py:class", "Tuple"): ("py:class", "tuple"),
    ("py:class", "Callable"): ("py:class", "collections.abc.Callable"),
    ("py:class", "callable"): ("py:class", "collections.abc.Callable"),
    ("py:class", "_pytest.nodes.File"): ("py:class", "_pytest.nodes.Node"),
    ("py:class", "NotebookNode"): ("py:class", "nbformat.NotebookNode"),
    ("py:class", "nbformat.notebooknode.NotebookNode"): (
        "py:class",
        "nbformat.NotebookNode",
    ),
    ("py:class", "nbconvert.preprocessors.execute.ExecutePreprocessor"): (
        "py:class",
        "nbconvert.preprocessors.ExecutePreprocessor",
    ),
    ("py:class", "coverage.control.Coverage"): ("py:class", "coverage.Coverage"),
}

nitpick_ignore = [
    ("py:class", "NoneType"),
    ("py:class", "Config"),
    ("py:class", "TextIO"),
    ("py:class", "attr.ib"),
    ("py:class", "attr.s"),
    ("py:class", "ruamel.yaml.dumper.RoundTripDumper"),
    ("py:exc", "nbconvert.preprocessors.CellExecutionError"),
    ("py:class", "nbdime.diff_format.DiffEntry"),
    ("py:class", "_pytest.nodes.Item"),
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/chrisjsewell/pytest-notebook",
    "repository_branch": "master",
    "path_to_docs": "docs/source",
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
}
jupyter_execute_notebooks = "cache"
execution_show_tb = "READTHEDOCS" in os.environ
execution_timeout = 60  # Note: 30 was timing out on RTD
myst_enable_extensions = ["colon_fence"]

# -- Sphinx setup for other outputs ---------------------------------------


def run_apidoc(_):
    """Run sphinx-apidoc when building the documentation.

    Needs to be done in conf.py in order to include the APIdoc in the
    build on readthedocs.
    See also https://github.com/rtfd/readthedocs.org/issues/1139
    """
    source_dir = os.path.abspath(os.path.dirname(__file__))
    apidoc_dir = os.path.join(source_dir, "apidoc")
    package_dir = os.path.join(source_dir, os.pardir, os.pardir, "pytest_notebook")

    # In #1139, they suggest the route below, but this ended up
    # calling sphinx-build, not sphinx-apidoc
    # from sphinx.apidoc import main
    # main([None, '-e', '-o', apidoc_dir, package_dir, '--force'])

    cmd_path = "sphinx-apidoc"
    if hasattr(sys, "real_prefix"):  # Check to see if we are in a virtualenv
        # If we are, assemble the path manually
        cmd_path = os.path.abspath(os.path.join(sys.prefix, "bin", "sphinx-apidoc"))

    options = [
        "-o",
        apidoc_dir,
        package_dir,
        "--private",
        "--force",
        "--no-toc",
        "--separate",
    ]

    # See https://stackoverflow.com/a/30144019
    env = os.environ.copy()
    env["SPHINX_APIDOC_OPTIONS"] = "members,undoc-members,show-inheritance"
    subprocess.check_call([cmd_path] + options, env=env)


def add_intersphinx_aliases_to_inv(app):
    """Add type aliases for intersphinx.

    see https://github.com/sphinx-doc/sphinx/issues/5603
    """
    from sphinx.ext.intersphinx import InventoryAdapter

    inventories = InventoryAdapter(app.builder.env)

    for alias, target in app.config.intersphinx_aliases.items():
        alias_domain, alias_name = alias
        target_domain, target_name = target
        try:
            found = inventories.main_inventory[target_domain][target_name]
            try:
                inventories.main_inventory[alias_domain][alias_name] = found
            except KeyError:
                continue
        except KeyError:
            continue


def setup(app):
    """Add functions to the Sphinx setup."""
    app.connect("builder-inited", run_apidoc)
    app.add_config_value("intersphinx_aliases", {}, "env")
    app.connect("builder-inited", add_intersphinx_aliases_to_inv)
