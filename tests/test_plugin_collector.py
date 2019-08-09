# -*- coding: utf-8 -*-
"""Test the  plugin collection and direct invocation of notebooks."""
import os

PATH = os.path.dirname(os.path.realpath(__file__))


def copy_nb_to_tempdir(in_name="different_outputs.ipynb", out_name="test_nb.ipynb"):
    with open(os.path.join(PATH, "raw_files", in_name), "rb") as handle:
        data = handle.read()
    with open(out_name, "wb") as handle:
        handle.write(data)


def test_collection(testdir):
    copy_nb_to_tempdir()
    result = testdir.runpytest("--nb-test-files", "--collect-only")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        ["*<JupyterNbCollector*test_nb.ipynb>*", "*<JupyterNbTest test_nbregression>*"]
    )


def test_run_fail(testdir):
    copy_nb_to_tempdir("different_outputs_altered.ipynb")
    result = testdir.runpytest(
        "--nb-exec-cwd", os.path.join(PATH, "raw_files"), "--nb-test-files", "-v"
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*::test_nbregression FAILED*",
            "*pytest_notebook.nb_regression.NBRegressionError:*",
            "*## modified /cells/11/outputs/0/data/image/svg+xml*",
        ]
    )

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret != 0
