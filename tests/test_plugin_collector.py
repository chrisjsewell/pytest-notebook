"""Test the  plugin collection and direct invocation of notebooks."""

import os

import nbformat

PATH = os.path.dirname(os.path.realpath(__file__))

KERNELSPEC = {
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}
}


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
        [
            "*<JupyterNbCollector*test_nb.ipynb>*",
            "*<JupyterNbTest nbregression(test_nb)>*",
        ]
    )


def test_setup_with_skip_meta(testdir):
    copy_nb_to_tempdir("nb_with_skip_meta.ipynb")
    result = testdir.runpytest("--nb-test-files", "--setup-plan", "-rs")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        ["*test_nb.ipynb*s*", "*I have my reasons*", "*1 skipped*"]
    )


def test_run_fail(testdir):
    copy_nb_to_tempdir("different_outputs_altered.ipynb")
    result = testdir.runpytest(
        "--nb-exec-cwd", os.path.join(PATH, "raw_files"), "--nb-test-files", "-v"
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        ["*::nbregression(test_nb) FAILED*", "*CellExecutionError:*"]
    )
    # result.stderr.fnmatch_lines(
    #     [
    #         "*## modified /cells/11/outputs/0/data/image/svg+xml*",
    #     ]
    # )

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret != 0


def test_run_pass_with_meta(testdir):
    copy_nb_to_tempdir("different_outputs_with_metadata.ipynb")
    result = testdir.runpytest(
        "--nb-exec-cwd", os.path.join(PATH, "raw_files"), "--nb-test-files", "-v"
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) PASSED*"])

    # make sure that that we get a non '0' exit code for the testsuite
    assert result.ret == 0


def test_run_skip_inside_notebook(testdir):
    """Test that a notebook can skip itself, by raising ``pytest.skip`` in a cell."""
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "import pytest\npytest.skip('skipping from within the notebook')"
            )
        ],
        metadata=KERNELSPEC,
    )
    nbformat.write(notebook, "test_nb.ipynb")
    result = testdir.runpytest("--nb-test-files", "-v", "-rs")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*skipping from within the notebook*", "*1 skipped*"])
    assert result.ret == 0


def test_run_with_exec_env_ini(testdir):
    """Test ``nb_exec_env`` and ``nb_diff_ignore`` set in the ini file."""
    cell = nbformat.v4.new_code_cell(
        "import os\nprint(os.environ['PYTEST_NB_EXEC_ENV_VAR'])", execution_count=1
    )
    cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text="hallo\n")]
    notebook = nbformat.v4.new_notebook(cells=[cell], metadata=KERNELSPEC)
    nbformat.write(notebook, "test_nb.ipynb")
    testdir.makeini(
        """
        [pytest]
        nb_test_files = True
        nb_exec_env =
            PYTEST_NB_EXEC_ENV_VAR=hallo
        nb_diff_ignore =
            /metadata/language_info
            /cells/*/execution_count
        """
    )
    result = testdir.runpytest("-v")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) PASSED*"])
    assert result.ret == 0
