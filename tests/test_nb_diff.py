import os

import nbformat

from pytest_notebook.diffing import diff_notebooks, diff_to_string
from pytest_notebook.notebook import mapping_to_dict

path = os.path.dirname(os.path.realpath(__file__))


def test_notebooks_equal(data_regression):
    initial = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    diff = diff_notebooks(initial, initial)
    assert diff == []


def test_notebooks_unequal(data_regression):
    initial = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    final = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs_altered.ipynb"), as_version=4
    )
    diff = diff_notebooks(initial, final)
    data_regression.check(mapping_to_dict(diff))


def test_diff_to_string(file_regression):
    initial = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    final = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs_altered.ipynb"), as_version=4
    )
    diff = diff_notebooks(initial, final)
    file_regression.check(diff_to_string(initial, diff))
