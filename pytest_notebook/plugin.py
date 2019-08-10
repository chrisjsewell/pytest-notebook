# -*- coding: utf-8 -*-
"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin
- http://doc.pytest.org/en/latest/example/nonpython.html

"""
from distutils.util import strtobool as _str2bool
import os

import pytest

from pytest_notebook.nb_regression import (
    HELP_DIFF_COLOR_WORDS,
    HELP_DIFF_IGNORE,
    HELP_DIFF_USE_COLOR,
    HELP_EXEC_ALLOW_ERRORS,
    HELP_EXEC_CWD,
    HELP_EXEC_TIMEOUT,
    HELP_FORCE_REGEN,
    HELP_POST_PROCS,
    load_notebook,
    NBRegressionFixture,
)

HELP_TEST_FILES = "Treat each .ipynb file as a test to be run."
HELP_FILE_FNMATCH = "The fnmatch pattern for collecting notebooks, default: '*.ipynb'."


def pytest_addoption(parser):
    group = parser.getgroup("nb_regression")
    group.addoption(
        "--nb-test-files",
        action="store_true",
        default=None,
        dest="nb_test_files",
        help=HELP_TEST_FILES,
    )
    group.addoption(
        "--nb-file-fnmatch", dest="nb_file_fnmatch", type=str, help=HELP_FILE_FNMATCH
    )
    group.addoption("--nb-exec-cwd", dest="nb_exec_cwd", type=str, help=HELP_EXEC_CWD)
    group.addoption(
        "--nb-exec-errors",
        action="store_true",
        default=None,
        dest="nb_exec_allow_errors",
        help=HELP_EXEC_ALLOW_ERRORS,
    )
    group.addoption(
        "--nb-exec-timeout", dest="nb_exec_timeout", type=int, help=HELP_EXEC_TIMEOUT
    )
    group.addoption(
        "--nb-force-regen",
        action="store_true",
        default=None,
        dest="nb_force_regen",
        help=HELP_FORCE_REGEN,
    )

    parser.addini("nb_test_files", help=HELP_TEST_FILES)
    parser.addini("nb_file_fnmatch", help=HELP_FILE_FNMATCH)
    parser.addini("nb_exec_cwd", help=HELP_EXEC_CWD)
    parser.addini("nb_exec_allow_errors", help=HELP_EXEC_ALLOW_ERRORS)
    parser.addini("nb_exec_timeout", help=HELP_EXEC_TIMEOUT)
    parser.addini("nb_post_processors", type="linelist", help=HELP_POST_PROCS)
    parser.addini("nb_diff_ignore", type="linelist", help=HELP_DIFF_IGNORE)
    parser.addini("nb_diff_use_color", help=HELP_DIFF_USE_COLOR)
    parser.addini("nb_diff_color_words", help=HELP_DIFF_COLOR_WORDS)
    parser.addini("nb_force_regen", help=HELP_FORCE_REGEN)


def str2bool(string):
    """Convert a string representation of truth to True or False.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if isinstance(string, bool):
        return string
    return True if _str2bool(string) else False


def gather_config_options(pytestconfig):
    """Gather all options, from command-line and ini file.

    Note; command-line set options are prioritised over ini file ones.
    """
    nbreg_kwargs = {}
    for name, value_type in [
        ("nb_exec_cwd", str),
        ("nb_exec_allow_errors", str2bool),
        ("nb_exec_timeout", int),
        ("nb_post_processors", tuple),
        ("nb_diff_ignore", tuple),
        ("nb_diff_use_color", str2bool),
        ("nb_diff_color_words", str2bool),
        ("nb_force_regen", str2bool),
    ]:

        try:
            ini_value = pytestconfig.getini(name)
        except ValueError:
            ini_value = None
        if pytestconfig.getoption(name, None) is not None:
            nbreg_kwargs[name[3:]] = value_type(pytestconfig.getoption(name))
        elif ini_value:
            nbreg_kwargs[name[3:]] = value_type(pytestconfig.getini(name))

    other_args = {}
    for name, value_type in [("nb_test_files", bool), ("nb_file_fnmatch", str)]:

        try:
            ini_value = pytestconfig.getini(name)
        except ValueError:
            ini_value = None
        if pytestconfig.getoption(name, None) is not None:
            other_args[name] = value_type(pytestconfig.getoption(name))
        elif ini_value:
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
    if other_args.get("nb_test_files", False) and path.fnmatch(
        other_args.get("nb_file_fnmatch", "*.ipynb")
    ):
        return JupyterNbCollector(path, parent)


class JupyterNbCollector(pytest.File):
    """This class represents a pytest collector object for Jupyter Notebook files.

    A collector is associated with a .ipynb file and collects it for testing.
    """

    def collect(self):
        """Collect tests for the notebook."""
        name = os.path.splitext(os.path.basename(self.fspath))[0]
        yield JupyterNbTest(f"nbregression({name})", self)


class JupyterNbTest(pytest.Item):
    """This class represents a pytest test invocation for a Jupyter Notebook file."""

    def __init__(self, name, parent):
        """Initialise the class, parsing the notebook metadata, and adding markers."""
        super().__init__(name, parent)
        self._fixtureinfo = self.session._fixturemanager.getfixtureinfo(
            self.parent, NBRegressionFixture.check, NBRegressionFixture
        )  # this is required for --setup-plan
        notebook, nb_config = load_notebook(self.fspath)
        if nb_config.skip:
            self.add_marker(pytest.mark.skip(reason=nb_config.skip_reason))

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

    def reportinfo(self):
        """Report location of item."""
        return self.fspath, 0, f"notebook: {self.name}"
