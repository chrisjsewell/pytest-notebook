# -*- coding: utf-8 -*-
"""Test the  ``nb_regression`` plugin fixture."""
import os
import sys

import attr
import pytest

from pytest_notebook.nb_regression import NBRegressionFixture

PATH = os.path.dirname(os.path.realpath(__file__))


def test_help_message(testdir):
    """Test that the nb_regression commands have been added to the pytest help msg."""
    result = testdir.runpytest("--help")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "nb_regression:",
            "*--nb-exec-cwd*",
            "*--nb-exec-errors*",
            "*--nb-exec-timeout*",
            "*--nb-force-regen*",
        ]
    )


@pytest.mark.parametrize(
    "command", ("", "--nb-exec-errors", "--nb-exec-timeout=100", "--nb-force-regen")
)
def test_nb_regression_fixture_init(testdir, command):
    """Test that pytest accepts the nb_regression fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            pass
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest(command, "-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_nb_regression_cmndline_setting_init(testdir):
    """Test the nb_regression fixture is initialised with the commandline settings."""

    testdir.makepyfile(
        """
        import attr

        def test_nb(nb_regression):
            assert attr.asdict(nb_regression) == {config}
    """.format(
            config=attr.asdict(
                NBRegressionFixture(
                    **{
                        "exec_allow_errors": True,
                        "exec_timeout": 90,
                        "force_regen": True,
                        # the following are the defaults for pytest-cov
                        "cov_source": (),
                        "cov_config": ".coveragerc",
                    }
                )
            )
        )
    )

    result = testdir.runpytest(
        "-vv", "--nb-exec-timeout", "90", "--nb-exec-errors", "--nb-force-regen"
    )

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_nb_regression_ini_setting_init(testdir):
    """Test the nb_regression fixture is initialised with the config file settings."""
    testdir.makeini(
        r"""
        [pytest]
        nb_exec_cwd = {path}
        nb_exec_allow_errors = True
        nb_exec_timeout = 100
        nb_diff_use_color = True
        nb_diff_color_words = True
        nb_diff_ignore =
            /metadata/language_info/version
            /cells/*/execution_count
            /cells/*/outputs/*/traceback
            /cells/*/outputs/*/execution_count
            /cells/12/outputs/0/data/text/latex
            /cells/9/outputs/0/metadata/application/json
        nb_post_processors =
        nb_diff_replace =
            /cells/*/outputs/*/traceback \<ipython\-input\-[\-0-9a-zA-Z]*\> "< >"
        """.format(
            path=os.path.join(PATH, "raw_files")
        )
    )

    testdir.makepyfile(
        """
        import attr

        def test_nb(nb_regression):
            assert attr.asdict(nb_regression) == {config}
    """.format(
            config=attr.asdict(
                NBRegressionFixture(
                    **{
                        "exec_cwd": os.path.join(PATH, "raw_files"),
                        "exec_allow_errors": True,
                        "exec_timeout": 100,
                        "post_processors": (),
                        "diff_ignore": (
                            "/metadata/language_info/version",
                            "/cells/*/execution_count",
                            "/cells/*/outputs/*/traceback",
                            "/cells/*/outputs/*/execution_count",
                            "/cells/12/outputs/0/data/text/latex",
                            "/cells/9/outputs/0/metadata/application/json",
                        ),
                        "diff_replace": (
                            (
                                "/cells/*/outputs/*/traceback",
                                "\\<ipython\\-input\\-[\\-0-9a-zA-Z]*\\>",
                                "< >",
                            ),
                        ),
                        "diff_use_color": True,
                        "diff_color_words": True,
                        # the following are the defaults for pytest-cov
                        "cov_source": (),
                        "cov_config": ".coveragerc",
                    }
                )
            )
        )
    )

    result = testdir.runpytest("-vv")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_nb_regression_fixture_check_fail(testdir):
    """Test running an nb_regression.check that fails."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            nb_regression.check("{path}")
    """.format(
            path=os.path.join(PATH, "raw_files", "simple-diff-output.ipynb")
        )
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb FAILED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret != 0


@pytest.mark.skipif(
    sys.version_info.minor <= 7, reason="svg attributes different order"
)
def test_nb_regression_fixture_check_pass(testdir):
    """Test running an nb_regression.check that passes."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            nb_regression.diff_ignore = (
                "/metadata/language_info/version",
                "/cells/*/execution_count",
                "/cells/*/outputs/*/traceback",
                "/cells/*/outputs/*/execution_count",
                "/cells/12/outputs/0/data/text/latex",
                "/cells/9/outputs/0/metadata/application/json"
            )
            nb_regression.check("{path}")
    """.format(
            path=os.path.join(PATH, "raw_files", "different_outputs.ipynb")
        )
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_nb_regression_fixture_regen(testdir):
    """Test running an nb_regression.check with nb_force_regen.

    The first test should fail (regenerating the file), then the 2nd test should pass.
    """

    with open(
        os.path.join(PATH, "raw_files", "simple-diff-output.ipynb"), "rb"
    ) as handle:
        data = handle.read()
    with open("test_nb.ipynb", "wb") as handle:
        handle.write(data)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            nb_regression.check("test_nb.ipynb")
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--nb-force-regen", "-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb FAILED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret != 0

    # re-run pytest with the following cmd args
    result = testdir.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret == 0
