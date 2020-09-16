# -*- coding: utf-8 -*-
"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin
- http://doc.pytest.org/en/latest/example/nonpython.html
- https://docs.pytest.org/en/latest/_modules/_pytest/hookspec.html

"""
from distutils.util import strtobool as _str2bool
import os
import shlex

import pytest

from pytest_notebook.nb_regression import (
    HELP_COVERAGE,
    HELP_DIFF_COLOR_WORDS,
    HELP_DIFF_IGNORE,
    HELP_DIFF_REPLACE,
    HELP_DIFF_USE_COLOR,
    HELP_EXEC_ALLOW_ERRORS,
    HELP_EXEC_CWD,
    HELP_EXEC_NOTEBOOK,
    HELP_EXEC_TIMEOUT,
    HELP_FORCE_REGEN,
    HELP_POST_PROCS,
    NBRegressionFixture,
)
from pytest_notebook.notebook import load_notebook_with_config, validate_regex_replace

HELP_TEST_FILES = "Treat each .ipynb file as a test to be run."
HELP_FILE_FNMATCH = (
    "The fnmatch pattern(s) for collecting notebooks, default: '*.ipynb'."
)


class NotSet:
    """Class to indicate a configuration value was not set."""


def pytest_addoption(parser):
    """Add pytest commandline and configuration file options."""
    group = parser.getgroup("nb_regression")
    group.addoption(
        "--nb-test-files",
        action="store_true",
        default=None,
        dest="nb_test_files",
        help=HELP_TEST_FILES,
    )
    # group.addoption(
    #     "--nb-file-fnmatch", dest="nb_file_fnmatch", type=str, help=HELP_FILE_FNMATCH
    # )
    # TODO option for --nb-no-exec-notebook
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
        "--nb-coverage",
        action="store_true",
        default=None,
        dest="nb_coverage",
        help=HELP_COVERAGE,
    )
    group.addoption(
        "--nb-diff-color-words",
        action="store_true",
        default=None,
        dest="nb_diff_color_words",
        help=HELP_DIFF_COLOR_WORDS,
    )
    group.addoption(
        "--nb-force-regen",
        action="store_true",
        default=None,
        dest="nb_force_regen",
        help=HELP_FORCE_REGEN,
    )

    parser.addini("nb_test_files", type="bool", help=HELP_TEST_FILES, default=NotSet())
    parser.addini(
        "nb_file_fnmatch", type="args", help=HELP_FILE_FNMATCH, default=NotSet()
    )
    parser.addini(
        "nb_exec_notebook", type="bool", help=HELP_EXEC_NOTEBOOK, default=NotSet()
    )
    parser.addini("nb_exec_cwd", help=HELP_EXEC_CWD, default=NotSet())
    parser.addini(
        "nb_exec_allow_errors",
        type="bool",
        help=HELP_EXEC_ALLOW_ERRORS,
        default=NotSet(),
    )
    parser.addini("nb_exec_timeout", help=HELP_EXEC_TIMEOUT, default=NotSet())
    parser.addini("nb_coverage", type="bool", help=HELP_COVERAGE, default=NotSet())
    parser.addini(
        "nb_post_processors", type="linelist", help=HELP_POST_PROCS, default=NotSet()
    )
    parser.addini(
        "nb_diff_ignore", type="linelist", help=HELP_DIFF_IGNORE, default=NotSet()
    )
    parser.addini(
        "nb_diff_replace", type="linelist", help=HELP_DIFF_REPLACE, default=NotSet()
    )
    parser.addini(
        "nb_diff_use_color", type="bool", help=HELP_DIFF_USE_COLOR, default=NotSet()
    )
    parser.addini(
        "nb_diff_color_words", type="bool", help=HELP_DIFF_COLOR_WORDS, default=NotSet()
    )
    parser.addini(
        "nb_force_regen", type="bool", help=HELP_FORCE_REGEN, default=NotSet()
    )


def str2bool(string):
    """Convert a string representation of truth to True or False.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if isinstance(string, bool):
        return string
    return True if _str2bool(string) else False


def strip_quotes(string):
    """Strip quotes from string."""
    if string.startswith("'"):
        string = string.strip("'")
    elif string.startswith('"'):
        string = string.strip('"')
    return string


def validate_diff_replace(pytestconfig):
    r"""Extract the ``nb_diff_replace`` option from the ini file.

    This should be of the format::

        nb_diff_replace =
            /cells/*/outputs \d{1,2}/\d{1,2}/\d{2,4} REPLACE_DATE
            /cells/*/outputs "\d{2}:\d{2}:\d{2}" "REPLACE_TIME"

    """
    nb_diff_replace = pytestconfig.getini("nb_diff_replace")
    if isinstance(nb_diff_replace, NotSet):
        return None

    if not isinstance(nb_diff_replace, (list, tuple)):
        raise ValueError("nb_diff_replace option should be a list or tuple")
    output = []
    for i, line in enumerate(nb_diff_replace):
        args = tuple(strip_quotes(arg) for arg in shlex.split(line, posix=False))
        validate_regex_replace(args, i)
        output.append(args)

    return tuple(output)


def gather_config_options(pytestconfig):
    """Gather all options, from command-line and ini file.

    Note: command-line set options are prioritised over ini file ones.
    """
    nbreg_kwargs = {}
    for name, value_type in [
        ("nb_exec_notebook", str2bool),
        ("nb_exec_cwd", str),
        ("nb_exec_allow_errors", str2bool),
        ("nb_exec_timeout", int),
        ("nb_coverage", str2bool),
        ("nb_post_processors", tuple),
        ("nb_diff_ignore", tuple),
        ("nb_diff_use_color", str2bool),
        ("nb_diff_color_words", str2bool),
        ("nb_force_regen", str2bool),
    ]:

        if pytestconfig.getoption(name, None) is not None:
            nbreg_kwargs[name[3:]] = value_type(pytestconfig.getoption(name))
        elif not isinstance(pytestconfig.getini(name), NotSet):
            nbreg_kwargs[name[3:]] = value_type(pytestconfig.getini(name))

    other_args = {}
    for name, value_type in [("nb_test_files", bool), ("nb_file_fnmatch", tuple)]:

        if pytestconfig.getoption(name, None) is not None:
            other_args[name] = value_type(pytestconfig.getoption(name))
        elif not isinstance(pytestconfig.getini(name), NotSet):
            other_args[name] = value_type(pytestconfig.getini(name))

    nb_diff_replace = validate_diff_replace(pytestconfig)
    if nb_diff_replace is not None:
        nbreg_kwargs["diff_replace"] = nb_diff_replace

    # options from pytest_cov
    # see: https://github.com/pytest-dev/pytest-cov/blob/master/src/pytest_cov/plugin.py
    if pytestconfig.getoption("cov_source", None) is not None:
        if pytestconfig.getoption("cov_source") == [""]:
            # this is returned if --cov= is used
            nbreg_kwargs["cov_source"] = None
        else:
            nbreg_kwargs["cov_source"] = tuple(pytestconfig.getoption("cov_source"))
    if pytestconfig.getoption("cov_config", None) is not None:
        nbreg_kwargs["cov_config"] = pytestconfig.getoption("cov_config")
    if pytestconfig.pluginmanager.hasplugin("_cov"):
        plugin = pytestconfig.pluginmanager.getplugin("_cov")
        if plugin.cov_controller:
            nbreg_kwargs["cov_merge"] = plugin.cov_controller.cov

    return nbreg_kwargs, other_args


def pytest_report_header(config):
    """Add header information for pytest execution."""

    kwargs, other_args = gather_config_options(config)
    header = []
    if kwargs.get("exec_notebook", True) and kwargs.get("exec_cwd", None):
        header.append(f"NB exec dir: {kwargs['exec_cwd']}")
    if kwargs.get("post_processors", None):
        header.append(f"NB post processors: {' '.join(kwargs['post_processors'])}")
    if kwargs.get("force_regen", None):
        header.append(f"NB force regen: {kwargs['force_regen']}")
    return header


@pytest.fixture(scope="function")
def nb_regression(pytestconfig):
    """Fixture to execute a Jupyter Notebook, and test its output is as expected."""

    kwargs, other_args = gather_config_options(pytestconfig)
    return NBRegressionFixture(**kwargs)


def pytest_collect_file(path, parent):
    """Collect Jupyter notebooks using the specified pytest hook."""
    kwargs, other_args = gather_config_options(parent.config)
    if other_args.get("nb_test_files", False) and any(
        path.fnmatch(pat) for pat in other_args.get("nb_file_fnmatch", ["*.ipynb"])
    ):
        try:
            return JupyterNbCollector.from_parent(parent, fspath=path)
        except AttributeError:
            return JupyterNbCollector(path, parent)


class JupyterNbCollector(pytest.File):
    """This class represents a pytest collector object for Jupyter Notebook files.

    A collector is associated with a .ipynb file and collects it for testing.
    """

    def collect(self):
        """Collect tests for the notebook."""
        name = os.path.splitext(os.path.basename(self.fspath))[0]
        try:
            yield JupyterNbTest.from_parent(self, name=f"nbregression({name})")
        except AttributeError:
            yield JupyterNbTest(f"nbregression({name})", self)


class JupyterNbTest(pytest.Item):
    """This class represents a pytest test invocation for a Jupyter Notebook file."""

    def __init__(self, name, parent):
        """Initialise the class, parsing the notebook metadata, and adding markers."""
        super().__init__(name, parent)
        self._fixtureinfo = self.session._fixturemanager.getfixtureinfo(
            self.parent, NBRegressionFixture.check, NBRegressionFixture
        )  # this is required for --setup-plan
        notebook, nb_config = load_notebook_with_config(self.fspath)
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
