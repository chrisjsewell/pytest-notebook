# -*- coding: utf-8 -*-
"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin

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


def pytest_addoption(parser):
    group = parser.getgroup("nb_regression")
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

    parser.addini("nb_exec_cwd", help=HELP_EXEC_CWD)
    parser.addini("nb_exec_allow_errors", help=HELP_EXEC_ALLOW_ERRORS)
    parser.addini("nb_exec_timeout", help=HELP_EXEC_TIMEOUT)
    parser.addini("nb_diff_ignore", type="linelist", help=HELP_DIFF_IGNORE)


def get_config_value(config, name, default):
    """Return the configured value, prioritising commandline over ini file."""
    if config.getoption(name, None) is not None:
        return config.getoption(name)
    if config.getini(name, None) is not None:
        return config.getini(name)
    return default


@pytest.fixture(scope="function")
def nb_regression(pytestconfig):
    """Fixture to execute a Jupyter Notebook, and test its output is as expected."""
    kwargs = {}
    for name, value_type in [
        ("nb_exec_cwd", str),
        ("nb_exec_allow_errors", bool),
        ("nb_exec_timeout", int),
        ("nb_diff_ignore", tuple),
        ("nb_force_regen", bool),
    ]:
        # commandline is prioritised over ini file
        if pytestconfig.getoption(name, None) is not None:
            kwargs[name[3:]] = value_type(pytestconfig.getoption(name))
        try:
            ini_value = pytestconfig.getini(name)
        except ValueError:
            ini_value = None
        if ini_value:
            kwargs[name[3:]] = value_type(pytestconfig.getini(name))

    return NBRegressionFixture(**kwargs)
