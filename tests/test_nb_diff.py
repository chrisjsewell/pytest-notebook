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


def test_notebooks_unequal_removed_outputs():
    """Test that removed trailing outputs diff at the correct indices."""
    cell = nbformat.v4.new_code_cell("print('a')\nprint('b')", execution_count=1)
    cell.outputs = [
        nbformat.v4.new_output("stream", name="stdout", text="a\n"),
        nbformat.v4.new_output("stream", name="stdout", text="b\n"),
    ]
    initial = nbformat.v4.new_notebook(cells=[cell])
    final = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(cell.source)])
    diff = diff_notebooks(initial, final)
    (outputs_diff,) = [
        entry for entry in diff[0]["diff"][0]["diff"] if entry["key"] == "outputs"
    ]
    (removerange,) = outputs_diff["diff"]
    assert removerange["op"] == "removerange"
    # the removal starts at the end of the final outputs (0), not the initial
    assert removerange["key"] == 0
    assert removerange["length"] == 2


def test_load_nbdime_ignore_config(tmp_path):
    """Test extracting diff-ignore paths from an nbdime configuration file."""
    config_file = tmp_path / "nbdime_config.json"
    config_file.write_text(
        json.dumps(
            {
                "Diff": {
                    "Ignore": {
                        "/cells/*/outputs": True,
                        "/cells/*/execution_count": True,
                        "/cells/*/attachments": True,
                        "/metadata": ["language_info"],
                    }
                },
                "GitDiff": {
                    "Ignore": {
                        # False de-selects a previously ignored path
                        "/cells/*/execution_count": False,
                        "/cells/*/metadata": ["collapsed", "autoscroll"],
                    }
                },
                "NbDiff": {
                    "Ignore": {
                        # null removes a previously set path
                        "/cells/*/attachments": None,
                        "/cells/*/metadata": ["scrolled"],
                    }
                },
                # sections not read by nbdiff are excluded
                "NbDiffWeb": {"Ignore": {"/cells/*/source": True}},
                "Global": {"Ignore": {"/nbformat": True}},
            }
        )
    )
    assert load_nbdime_ignore_config(config_file) == (
        "/cells/*/metadata/scrolled",
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
        {"Diff": {"Ignore": {"/cells": 1}}},
        {"Diff": {"Ignore": {"/cells": [1]}}},
    ],
    ids=[
        "not-a-mapping",
        "section-not-a-mapping",
        "ignore-not-a-mapping",
        "path-without-slash",
        "value-str",
        "value-int",
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
