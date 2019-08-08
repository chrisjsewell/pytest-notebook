import os

import nbformat

from pytest_notebook.execution import execute_notebook

PATH = os.path.dirname(os.path.realpath(__file__))


def test_execute_notebook_fail():
    notebook = nbformat.read(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    exec_error, new_notebook = execute_notebook(notebook)
    assert exec_error


def test_execute_notebook_success():
    notebook = nbformat.read(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    exec_error, new_notebook = execute_notebook(
        notebook, cwd=os.path.join(PATH, "raw_files")
    )
    if exec_error:
        raise exec_error
    assert isinstance(new_notebook, nbformat.NotebookNode)
