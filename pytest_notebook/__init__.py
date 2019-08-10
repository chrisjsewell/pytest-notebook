"""pytest-notebook.

A pytest plugin for testing Jupyter Notebooks.
"""
from .diffing import diff_notebooks, diff_to_string, filter_diff  # noqa: F401
from .execution import execute_notebook  # noqa: F401
from .nb_regression import NBRegressionFixture  # noqa: F401
from .post_processors import (  # noqa: F401
    document_processors,
    list_processor_names,
    load_processor,
)

__version__ = "0.3.0"
