"""Tests for ``NBRegressionFixture``."""
import os
import sys

import pytest

from pytest_notebook.execution import COVERAGE_KEY
from pytest_notebook.nb_regression import NBRegressionError, NBRegressionFixture

PATH = os.path.dirname(os.path.realpath(__file__))


def test_init_fixture():
    """Test initialisation of NBRegressionFixture."""
    fixture = NBRegressionFixture(exec_timeout=10)
    assert fixture.exec_timeout == 10


def test_regression_fail():
    """Test a regression that will fail."""
    fixture = NBRegressionFixture()
    with pytest.raises(NBRegressionError):
        fixture.check(os.path.join(PATH, "raw_files", "simple-diff-output.ipynb"))


@pytest.mark.skipif(
    sys.version_info.minor <= 7, reason="svg attributes different order"
)
def test_regression_diff_ignore_pass():
    """Test a regression that will succeed by ignoring certain notebook paths."""
    fixture = NBRegressionFixture()
    fixture.diff_ignore = (
        "/metadata/language_info/version",
        "/cells/*/execution_count",
        "/cells/*/outputs/*/traceback",
        "/cells/*/outputs/*/execution_count",
        "/cells/12/outputs/0/data/text/latex",
        "/cells/9/outputs/0/metadata/application/json",
    )
    fixture.check(os.path.join(PATH, "raw_files", "different_outputs.ipynb"))


@pytest.mark.skipif(
    sys.version_info.minor <= 7, reason="svg attributes different order"
)
@pytest.mark.skipif(sys.version_info.minor > 7, reason="ipython error message changes")
def test_regression_regex_replace_pass():
    """Test a regression that will succeed by regex replacing certain paths."""
    fixture = NBRegressionFixture()
    fixture.diff_ignore = (
        "/metadata/language_info/version",
        "/cells/*/execution_count",
        "/cells/*/outputs/*/execution_count",
        "/cells/12/outputs/0/data/text/latex",
        "/cells/9/outputs/0/metadata/application/json",
    )
    fixture.diff_replace = (
        ("/cells/*/outputs/*/traceback", r"\<module\>.*\n", "<module>\n"),
        ("/cells/*/outputs/*/traceback", r"[\-]+", "-"),
        (
            "/cells/*/outputs/*/traceback",
            r"\s*Traceback \(most recent call last\)",
            " Traceback (most recent call last)",
        ),
        (
            "/cells/*/outputs/*/traceback",
            r"\<ipython\-input\-[\-0-9a-zA-Z]*\>",
            "<ipython-input-XXX>",
        ),
    )
    fixture.check(os.path.join(PATH, "raw_files", "different_outputs.ipynb"))


def test_regression_coverage():
    """Test a regression that will fail."""
    fixture = NBRegressionFixture()
    fixture.diff_ignore = ("/metadata/language_info/version",)
    fixture.coverage = True
    result = fixture.check(
        os.path.join(PATH, "raw_files", "coverage_test", "call_package.ipynb")
    )

    assert COVERAGE_KEY in result.process_resources
    assert "package.py" in result.process_resources[COVERAGE_KEY]
    # assert "[1,2,3]" in result.process_resources[COVERAGE_KEY]
