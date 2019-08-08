# -*- coding: utf-8 -*-
import os
import pytest

PATH = os.path.dirname(os.path.realpath(__file__))


def test_help_message(testdir):
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
    """Make sure that pytest accepts our fixture."""

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


def test_nb_regression_fixture_exec_fail_diff(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            nb_regression.check("{path}")
    """.format(
            path=os.path.join(PATH, "raw_files", "different_outputs.ipynb")
        )
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--nb-exec-cwd", os.path.join(PATH, "raw_files"), "-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb FAILED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret != 0


def test_nb_regression_fixture_exec_pass(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            nb_regression.diff_ignore = (
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
    result = testdir.runpytest("--nb-exec-cwd", os.path.join(PATH, "raw_files"), "-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_nb_regression_ini_setting(testdir):
    testdir.makeini(
        """
        [pytest]
        nb_exec_cwd = {path}
        nb_exec_allow_errors = True
        nb_exec_timeout = 100
        nb_diff_ignore =
            /cells/*/execution_count
            /cells/*/outputs/*/traceback
            /cells/*/outputs/*/execution_count
            /cells/12/outputs/0/data/text/latex
            /cells/9/outputs/0/metadata/application/json
    """.format(
            path=os.path.join(PATH, "raw_files")
        )
    )

    testdir.makepyfile(
        """
        def test_nb(nb_regression):
            nb_regression.check("{path}")
    """.format(
            path=os.path.join(PATH, "raw_files", "different_outputs.ipynb")
        )
    )

    result = testdir.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_nb_regression_fixture_regen(testdir):
    """Make sure that pytest accepts our fixture."""

    with open(
        os.path.join(PATH, "raw_files", "different_outputs.ipynb"), "rb"
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
    result = testdir.runpytest(
        "--nb-exec-cwd", os.path.join(PATH, "raw_files"), "--nb-force-regen", "-v"
    )

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb FAILED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret != 0

    # re-run pytest with the following cmd args
    result = testdir.runpytest("--nb-exec-cwd", os.path.join(PATH, "raw_files"), "-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_nb PASSED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret == 0
