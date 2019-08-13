import os
from textwrap import dedent

import nbformat

from pytest_notebook.execution import COVERAGE_KEY, execute_notebook
from pytest_notebook.notebook import create_notebook, create_cell

PATH = os.path.dirname(os.path.realpath(__file__))


def test_execute_notebook_fail():
    """Test executing a notebook that should fail."""
    notebook = nbformat.read(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    exec_error, new_notebook, resources = execute_notebook(notebook)
    assert exec_error


def test_execute_notebook_success():
    """Test executing a notebook that should succeed."""
    notebook = nbformat.read(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    exec_error, new_notebook, resources = execute_notebook(
        notebook, cwd=os.path.join(PATH, "raw_files")
    )
    if exec_error:
        raise exec_error
    assert isinstance(new_notebook, nbformat.NotebookNode)


def test_execute_notebook_with_coverage():
    """Test executing a notebook with coverage."""
    notebook = create_notebook()
    notebook.cells = [
        create_cell(
            dedent(
                """\
            from pytest_notebook.notebook import create_notebook
            create_notebook()
            import nbformat
            """
            )
        )
    ]
    exec_error, new_notebook, resources = execute_notebook(
        notebook, cwd=os.path.join(PATH, "raw_files"), with_coverage=True
    )
    if exec_error:
        raise exec_error
    assert isinstance(new_notebook, nbformat.NotebookNode)
    assert "!coverage.py" in resources[COVERAGE_KEY]
