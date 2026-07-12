import json
import os

import nbformat
import pytest

from pytest_notebook.diffing import (
    diff_notebooks,
    diff_to_string,
    load_nbdime_ignore_config,
)
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


def test_load_nbdime_ignore_config(tmp_path):
    """Test extracting diff-ignore paths from an nbdime configuration file."""
    config_file = tmp_path / "nbdime_config.json"
    config_file.write_text(
        json.dumps(
            {
                "Global": {
                    "Ignore": {
                        "/cells/*/outputs": True,
                        "/cells/*/execution_count": True,
                    }
                },
                "Diff": {
                    "Ignore": {
                        "/cells/*/execution_count": False,
                        "/cells/*/metadata": ["collapsed", "autoscroll"],
                        "/metadata": ["language_info"],
                    }
                },
                "NbDiffWeb": {"Ignore": {"/cells/*/source": True}},
            }
        )
    )
    assert load_nbdime_ignore_config(config_file) == (
        "/cells/*/metadata/autoscroll",
        "/cells/*/metadata/collapsed",
        "/cells/*/outputs",
        "/metadata/language_info",
    )


@pytest.mark.parametrize(
    "config",
    [
        [],
        {"Diff": []},
        {"Diff": {"Ignore": []}},
        {"Diff": {"Ignore": {"cells": True}}},
        {"Diff": {"Ignore": {"/cells": "true"}}},
        {"Diff": {"Ignore": {"/cells": [1]}}},
    ],
    ids=[
        "not-a-mapping",
        "section-not-a-mapping",
        "ignore-not-a-mapping",
        "path-without-slash",
        "value-not-bool-or-list",
        "value-list-not-strings",
    ],
)
def test_load_nbdime_ignore_config_invalid(tmp_path, config):
    """Test that invalid nbdime configuration files raise errors."""
    config_file = tmp_path / "nbdime_config.json"
    config_file.write_text(json.dumps(config))
    with pytest.raises((TypeError, ValueError)):
        load_nbdime_ignore_config(config_file)


def test_diff_to_string(file_regression):
    initial = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs.ipynb"), as_version=4
    )
    final = nbformat.read(
        os.path.join(path, "raw_files", "different_outputs_altered.ipynb"), as_version=4
    )
    diff = diff_notebooks(initial, final)
    file_regression.check(diff_to_string(initial, diff, use_color=False))
