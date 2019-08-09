# -*- coding: utf-8 -*-
"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin
- http://doc.pytest.org/en/latest/example/nonpython.html

"""
import pytest

from pytest_notebook.nb_regression import (
    HELP_DIFF_IGNORE,
    HELP_EXEC_ALLOW_ERRORS,
    HELP_EXEC_CWD,
    HELP_EXEC_TIMEOUT,
    HELP_FORCE_REGEN,
    NBRegressionFixture,
)

HELP_TEST_FILES = "Treat each .ipynb file as a test to be run."


def pytest_addoption(parser):
    group = parser.getgroup("nb_regression")
    group.addoption(
        "--nb-test-files",
        action="store_true",
        dest="nb_test_files",
        help=HELP_TEST_FILES,
    )
    group.addoption(
        "--nb-exec-cwd",
        action="store",
        dest="nb_exec_cwd",
        type=str,
        help=HELP_EXEC_CWD,
    )
    group.addoption(
        "--nb-exec-errors",
        action="store_true",
        default=None,
        dest="nb_exec_allow_errors",
        help=HELP_EXEC_ALLOW_ERRORS,
    )
    group.addoption(
        "--nb-exec-timeout",
        action="store",
        dest="nb_exec_timeout",
        type=int,
        help=HELP_EXEC_TIMEOUT,
    )
    group.addoption(
        "--nb-force-regen",
        action="store_true",
        dest="nb_force_regen",
        help=HELP_FORCE_REGEN,
    )

    parser.addini("nb_test_files", help=HELP_TEST_FILES)
    parser.addini("nb_exec_cwd", help=HELP_EXEC_CWD)
    parser.addini("nb_exec_allow_errors", help=HELP_EXEC_ALLOW_ERRORS)
    parser.addini("nb_exec_timeout", help=HELP_EXEC_TIMEOUT)
    parser.addini("nb_diff_ignore", type="linelist", help=HELP_DIFF_IGNORE)


def gather_config_options(pytestconfig):
    """Gather all options, from command-line and ini file.

    Note; command-line set options are prioritised over ini file ones.
    """
    nbreg_kwargs = {}
    for name, value_type in [
        ("nb_exec_cwd", str),
        ("nb_exec_allow_errors", bool),
        ("nb_exec_timeout", int),
        ("nb_diff_ignore", tuple),
        ("nb_force_regen", bool),
    ]:

        if pytestconfig.getoption(name, None) is not None:
            nbreg_kwargs[name[3:]] = value_type(pytestconfig.getoption(name))
        try:
            ini_value = pytestconfig.getini(name)
        except ValueError:
            ini_value = None
        if ini_value:
            nbreg_kwargs[name[3:]] = value_type(pytestconfig.getini(name))

    other_args = {}
    for name, value_type in [("nb_test_files", bool)]:

        if pytestconfig.getoption(name, None) is not None:
            other_args[name] = value_type(pytestconfig.getoption(name))
        try:
            ini_value = pytestconfig.getini(name)
        except ValueError:
            ini_value = None
        if ini_value:
            other_args[name] = value_type(pytestconfig.getini(name))

    return nbreg_kwargs, other_args


@pytest.fixture(scope="function")
def nb_regression(pytestconfig):
    """Fixture to execute a Jupyter Notebook, and test its output is as expected."""

    kwargs, other_args = gather_config_options(pytestconfig)
    return NBRegressionFixture(**kwargs)


def pytest_collect_file(path, parent):
    """Collect Jupyter notebooks using the specified pytest hook."""
    kwargs, other_args = gather_config_options(parent.config)
    if other_args.get("nb_test_files", False) and path.fnmatch("*.ipynb"):
        return JupterNbCollector(path, parent)


class JupterNbCollector(pytest.File):
    """This class represents a pytest collector object for Jupyter Notebook files.

    A collector is associated with a .ipynb file and collects it for testing.
    """

    def collect(self):
        """Collect tests for the notebook."""
        # name = os.path.splitext(os.path.basename(self.fspath))[0]
        yield JupyterNbTest("test_nbregression", self)


class JupyterNbTest(pytest.Item):
    """This class represents a pytest test invocation for a Jupyter Notebook file."""

    # TODO use the notebook metadata and self.add_marker
    # to add skip markers for certain notebooks
    # see: http://doc.pytest.org/en/latest/_modules/_pytest/nodes.html

    def runtest(self):
        """Run the test."""
        kwargs, other_args = gather_config_options(self.config)
        fixture = NBRegressionFixture(**kwargs)
        fixture.check(self.fspath)

    def repr_failure(self, exc_info):
        """Handle exception raised by ``self.runtest()``.

        :param exc_info: see
            https://docs.pytest.org/en/latest/reference.html#_pytest._code.ExceptionInfo
        """
        # return exc_info.getrepr()
        return exc_info.exconly()
