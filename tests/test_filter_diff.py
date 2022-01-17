import json
import os

from pytest_notebook.diffing import filter_diff

PATH = os.path.dirname(os.path.realpath(__file__))


def get_test_diff(filename="different_outputs_alt_diff.json"):
    with open(os.path.join(PATH, "raw_files", filename)) as fp:
        diff = json.load(fp)
    return diff


def test_filter_diff_no_paths():

    diff = filter_diff(get_test_diff(), [])
    assert diff == get_test_diff()


def test_filter_diff_cells():

    diff = filter_diff(get_test_diff(), ["/cells"])
    assert diff == []


def test_filter_diff_outputs():

    diff = filter_diff(get_test_diff(), ["/cells/*/outputs"])
    assert diff == [
        {
            "diff": [
                {
                    "diff": [{"key": "execution_count", "op": "replace", "value": 6}],
                    "key": 2,
                    "op": "patch",
                }
            ],
            "key": "cells",
            "op": "patch",
        }
    ]


def test_filter_diff_outtypes(data_regression):

    diff = filter_diff(
        get_test_diff(),
        [
            "/cells/*/outputs/*/text",  # streams
            "/cells/*/outputs/*/data/text",
            "/cells/*/outputs/*/data/application",
        ],
    )
    data_regression.check(diff)


def test_filter_diff_complex():
    diff = filter_diff(
        get_test_diff("different_outputs_diff.json"),
        [
            "/cells/*/execution_count",
            "/cells/*/outputs/*/traceback",
            "/cells/*/outputs/*/execution_count",
            "/cells/12/outputs/0/data/text/latex",
            "/cells/9/outputs/0/metadata/application/json",
        ],
    )
    assert diff == []
