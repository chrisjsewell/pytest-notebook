# -*- coding: utf-8 -*-
"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin

"""
import pytest


def pytest_addoption(parser):
    group = parser.getgroup("notebook")
    group.addoption(
        "--foo",
        action="store",
        dest="dest_foo",
        default="2019",
        help='Set the value for the fixture "bar".',
    )

    parser.addini("HELLO", "Dummy pytest.ini setting")


@pytest.fixture
def bar(request):
    return request.config.option.dest_foo
