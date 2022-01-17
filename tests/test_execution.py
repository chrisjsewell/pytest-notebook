import os
from textwrap import dedent

from coverage import CoverageData
import nbformat

from pytest_notebook.execution import execute_notebook
from pytest_notebook.notebook import create_cell, create_notebook

PATH = os.path.dirname(os.path.realpath(__file__))


def test_execute_notebook_fail():
    """Test executing a notebook that should fail."""
    notebook = nbformat.read(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    exec_results = execute_notebook(notebook)
    assert exec_results.exec_error is not None


def test_execute_notebook_success():
    """Test executing a notebook that should succeed."""
    notebook = nbformat.read(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    exec_results = execute_notebook(notebook, cwd=os.path.join(PATH, "raw_files"))
    if exec_results.exec_error:
        raise exec_results.exec_error
    assert isinstance(exec_results.notebook, nbformat.NotebookNode)


def test_execute_notebook_with_coverage():
    """Test executing a notebook with coverage."""
    notebook = create_notebook(
        metadata={
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3",
            }
        },
        cells=[
            create_cell(
                dedent(
                    """\
            from pytest_notebook.notebook import create_notebook
            create_notebook()
            import nbformat
            """
                )
            )
        ],
    )
    exec_results = execute_notebook(
        notebook, cwd=os.path.join(PATH, "raw_files"), with_coverage=True
    )
    if exec_results.exec_error:
        raise exec_results.exec_error
    assert isinstance(exec_results.notebook, nbformat.NotebookNode)
    assert isinstance(exec_results.coverage_dict, dict)
    assert isinstance(exec_results.coverage_data(), CoverageData)
