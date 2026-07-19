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


def test_matches_pattern():
    """Test fnmatch patterns against the old ``py.path.local.fnmatch`` semantics."""
    from pathlib import Path

    from pytest_notebook.plugin import _matches_pattern

    file_path = Path("/repo/docs/test_nb.ipynb")
    assert _matches_pattern(file_path, "*.ipynb")
    assert _matches_pattern(file_path, "test_nb.ipynb")
    assert not _matches_pattern(file_path, "other_*.ipynb")
    # relative patterns with a separator match any trailing path segments
    assert _matches_pattern(file_path, "docs/*.ipynb")
    assert _matches_pattern(file_path, "docs/test_nb.ipynb")
    assert not _matches_pattern(file_path, "other/*.ipynb")
    # absolute patterns match the full path
    assert _matches_pattern(file_path, "/repo/docs/*.ipynb")
    assert not _matches_pattern(file_path, "/other/docs/*.ipynb")


def test_run_with_coverage_merge(testdir):
    """Test that collected notebook coverage is merged into pytest-cov's data."""
    copy_nb_to_tempdir(os.path.join("coverage_test", "call_package.ipynb"))
    with open(os.path.join(PATH, "raw_files", "coverage_test", "package.py")) as fh:
        data = fh.read()
    with open("package.py", "w") as fh:
        fh.write(data)
    testdir.makeini(
        """
        [pytest]
        nb_diff_ignore =
            /metadata/language_info
        """
    )
    result = testdir.runpytest(
        "--nb-test-files", "--nb-coverage", "--cov=package", "-v"
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) PASSED*", "*package.py*"])
    assert result.ret == 0


def test_run_no_exec_with_cov(testdir):
    """Test a non-executed run with pytest-cov enabled."""
    copy_nb_to_tempdir()
    testdir.makeini(
        """
        [pytest]
        nb_test_files = True
        nb_exec_notebook = False
        """
    )
    result = testdir.runpytest("--cov", "-v")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) PASSED*"])
    assert result.ret == 0


def _write_nb_with_wrong_output(filename="test_nb.ipynb"):
    """Write a notebook whose stored output will differ from its execution."""
    cell = nbformat.v4.new_code_cell("print('hallo')", execution_count=1)
    cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text="wrong\n")]
    notebook = nbformat.v4.new_notebook(cells=[cell], metadata=KERNELSPEC)
    nbformat.write(notebook, filename)


def test_run_with_nbdime_config(testdir):
    """Test that nbdime_config.json ignores are merged with ``nb_diff_ignore``."""
    import json

    _write_nb_with_wrong_output()
    with open("nbdime_config.json", "w") as handle:
        json.dump(
            {
                "Diff": {
                    "Ignore": {
                        "/cells/*/outputs": True,
                        "/cells/*/execution_count": True,
                    }
                }
            },
            handle,
        )
    testdir.makeini(
        """
        [pytest]
        nb_test_files = True
        nb_diff_use_nbdime_config = True
        nb_diff_ignore =
            /metadata/language_info
        """
    )
    result = testdir.runpytest("-v")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) PASSED*"])
    assert result.ret == 0


def test_run_with_nbdime_config_missing(testdir):
    """Test an actionable error, when no nbdime_config.json exists."""
    _write_nb_with_wrong_output()
    testdir.makeini(
        """
        [pytest]
        nb_test_files = True
        nb_diff_use_nbdime_config = True
        """
    )
    result = testdir.runpytest()
    result.stderr.fnmatch_lines(["*no nbdime_config.json found*"])
    assert result.ret != 0


def test_nbdime_config_preserves_default_ignore(testdir):
    """Test enabling the nbdime config does not drop the default diff_ignore."""
    import json

    with open("nbdime_config.json", "w") as handle:
        json.dump({"Diff": {"Ignore": {"/metadata": ["language_info"]}}}, handle)
    testdir.makeini(
        """
        [pytest]
        nb_diff_use_nbdime_config = True
        """
    )
    testdir.makepyfile(
        """
        def test_opts(nb_regression):
            assert "/cells/*/outputs/*/traceback" in nb_regression.diff_ignore
            assert "/metadata/language_info" in nb_regression.diff_ignore
        """
    )
    result = testdir.runpytest("-v")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_opts PASSED*"])
    assert result.ret == 0


def test_run_without_nbdime_config(testdir):
    """Test that nbdime_config.json is not loaded, when not enabled."""
    import json

    _write_nb_with_wrong_output()
    with open("nbdime_config.json", "w") as handle:
        json.dump({"Diff": {"Ignore": {"/cells/*/outputs": True}}}, handle)
    result = testdir.runpytest("--nb-test-files", "-v")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) FAILED*"])
    assert result.ret != 0


def test_run_with_diff_normalize_ini(testdir):
    """Test the ``nb_diff_normalize`` ini option."""
    cell = nbformat.v4.new_code_cell(
        "print('\\x1b[32mok\\x1b[0m 2022-01-01 00:00:00')", execution_count=1
    )
    # stored output has different ANSI codes and timestamp to the executed output
    cell.outputs = [
        nbformat.v4.new_output(
            "stream", name="stdout", text="\x1b[31mok\x1b[39m 1999-12-31 23:59:59\n"
        )
    ]
    notebook = nbformat.v4.new_notebook(cells=[cell], metadata=KERNELSPEC)
    nbformat.write(notebook, "test_nb.ipynb")
    testdir.makeini(
        """
        [pytest]
        nb_test_files = True
        nb_diff_normalize =
            strip_ansi
            mask_timestamps
        nb_diff_ignore =
            /metadata/language_info
            /cells/*/execution_count
        """
    )
    result = testdir.runpytest("-v")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::nbregression(test_nb) PASSED*"])
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
