# Installation

[![PyPI][pypi-badge]][pypi-link]
[![Conda][conda-badge]][conda-link]

To install from PyPi:

```shell
>> pip install pytest-notebook
```

To install from Conda:

```shell
>> conda install -c conda-forge pytest-notebook
```

To install the development version:

```shell
>> git clone https://github.com/chrisjsewell/pytest-notebook .
>> cd pytest-notebook
>> pip install -e ".[code_style,testing,docs]"
```

# Development

## Testing

[![CI][ci-badge]][ci-link]
[![Coverage][cov-badge]][cov-link]

It is recommended to use [tox](https://tox.readthedocs.io) to run tests.

```shell
>> tox
```

## Coding Style Requirements

[![Code style: black][black-badge]][black-link]

The code style is tested using [flake8](http://flake8.pycqa.org),
with the configuration set in `.flake8`, and
[black](https://github.com/ambv/black).

Installing with `pytest-notebook[code_style]` makes the
[pre-commit](https://pre-commit.com/) package available, which will
ensure these tests are passed by reformatting the code and testing for
lint errors before submitting a commit. It can be set up by:

```shell
>> pre-commit run --all
>> pre-commit install
```

Editors like VS Code also have automatic code reformat utilities, which
can check and adhere to this standard.

## Documentation

[![RTD][rtd-badge]][rtd-link]

The documentation can be created locally by:

```shell
>> tox -e py37-docs-clean
>> tox -e py37-docs-update
```

[ci-badge]: https://github.com/chrisjsewell/pytest-notebook/workflows/continuous-integration/badge.svg?branch=master
[ci-link]: https://github.com/chrisjsewell/pytest-notebook
[cov-badge]:https://codecov.io/gh/chrisjsewell/pytest-notebook/branch/master/graph/badge.svg
[cov-link]: https://codecov.io/gh/chrisjsewell/pytest-notebook
[rtd-badge]: https://readthedocs.org/projects/pytest-notebook/badge
[rtd-link]: http://pytest-notebook.readthedocs.io/
[pypi-badge]: https://img.shields.io/pypi/v/pytest-notebook.svg
[pypi-link]: https://pypi.org/project/pytest-notebook
[conda-badge]: https://anaconda.org/conda-forge/pytest-notebook/badges/version.svg
[conda-link]: https://anaconda.org/conda-forge/pytest-notebook
[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/ambv/black
