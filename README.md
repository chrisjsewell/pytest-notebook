# pytest-notebook

[![Build Status](https://travis-ci.org/chrisjsewell/pytest-notebook.svg?branch=master)](https://travis-ci.org/chrisjsewell/pytest-notebook)
[![Coverage Status](https://coveralls.io/repos/github/chrisjsewell/pytest-notebook/badge.svg?branch=master)](https://coveralls.io/github/chrisjsewell/pytest-notebook?branch=master)
[![Docs status](https://readthedocs.org/projects/pytest-notebook/badge)](http://pytest-notebook.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/pytest-notebook.svg)](https://pypi.org/project/pytest-notebook)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/pytest-notebook/badges/version.svg)](https://anaconda.org/conda-forge/pytest-notebook)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A [pytest](https://github.com/pytest-dev/pytest) plugin for testing Jupyter Notebooks.

------------------------------------------------------------------------

## Features

- Clear API

Diff [nbval](https://github.com/computationalmodelling/nbval)

## Installation

You can install `pytest-notebook` *via*
[pip](https://pypi.org/project/pip/) from
[PyPI](https://pypi.org/project):

```shell
>> pip install pytest-notebook
```

## Usage

TODO

## Contributing

Contributions are very welcome.

The following will discover and run all unit test:

```shell
>> pip install -e .[testing]
>> pytest -v
```

### Coding Style Requirements

The code style is tested using [flake8](http://flake8.pycqa.org),
with the configuration set in `.flake8`, and code should be formatted with [black](https://github.com/ambv/black) (configuration set in `.style.yapf`).

Installing with `pytest-notebook[code_style]` makes the [pre-commit](https://pre-commit.com/)
package available, which will ensure these tests are passed by reformatting the code
and testing for lint errors before submitting a commit.
It can be setup by:

```shell
>> cd pytest-notebook
>> pre-commit install
```

Optionally you can run `black` and `flake8` separately:

```shell
>> black.
>> flake8
```

Editors like VS Code also have automatic code reformat utilities, which can adhere to this standard.

## License

Distributed under the terms of the
[BSD-3](http://opensource.org/licenses/BSD-3-Clause) license,
\"pytest-notebook\" is free and open source software

## Issues

If you encounter any problems, please [file an
issue](https://github.com/chrisjsewell/pytest-notebook/issues) along
with a detailed description.
