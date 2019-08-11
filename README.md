# pytest-notebook

[![Build Status](https://travis-ci.org/chrisjsewell/pytest-notebook.svg?branch=master)](https://travis-ci.org/chrisjsewell/pytest-notebook)
[![Coverage Status](https://coveralls.io/repos/github/chrisjsewell/pytest-notebook/badge.svg?branch=master)](https://coveralls.io/github/chrisjsewell/pytest-notebook?branch=master)
[![Docs status](https://readthedocs.org/projects/pytest-notebook/badge)](http://pytest-notebook.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/pytest-notebook.svg)](https://pypi.org/project/pytest-notebook)
[![Conda](https://anaconda.org/conda-forge/pytest-notebook/badges/version.svg)](https://anaconda.org/conda-forge/pytest-notebook)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A [pytest](https://github.com/pytest-dev/pytest) plugin for regression testing and regenerating [Jupyter Notebooks](https://jupyter.org/).

![Example Test](pytest-notebook-screenshot.png)

------------------------------------------------------------------------

## Purpose

The purpose of the plugin is to ensure that changes to the python
environment (e.g. updating packages), have not affected the outputs
of the notebook. If the notebook has changed, this plugin can also
regenerate the notebooks, saving the new outputs.

## Features

- Recognise, collect, execute (optionally output) then diff input vs. output [Jupyter Notebooks](https://jupyter.org/).
- Provides clear and colorized diffs of the notebooks (using [nbdime](https://nbdime.readthedocs.io))
- A well defined API allows notebook regression tests to be run:

    1. Using the pytest test collection architecture.
    2. As a pytest fixtures (`nb_regression.check(filename)`).
    3. Using the `pytest_notebook` python package.

- All stages are highly configurable *via*:

    1. The pytest command-line interface.
    2. The pytest configuration file.
    3. The notebook and cell level metadata.

- Post-processor plugin entry-points, allow for customisable modifications of the notebook,
  including source code formatting with [black](https://github.com/ambv/black)

![Configuration Examples](docs/source/_static/collaged_in_out.png)

## Installation

To install from [Conda](https://docs.conda.io) (recommended):

```shell
>> conda install -c conda-forge pytest-notebook
```

To install *via* [pip](https://pypi.org/project/pip/) from [PyPI](https://pypi.org/project):

```shell
>> pip install pytest-notebook
```

To install the development version:

```shell
>> git clone https://github.com/chrisjsewell/pytest-notebook .
>> cd pytest-notebook
>> pip install -e .
>> # pip install -e .[code_style,testing,docs] # install extras for more features
```

## Usage

See the documentation at: http://pytest-notebook.readthedocs.io/

## Contributing

Contributions are very welcome.

The following will discover and run all unit test:

```shell
>> pip install -e .[testing]
>> pytest -v
```

### Coding Style Requirements

The code style is tested using [flake8](http://flake8.pycqa.org),
with the configuration set in `.flake8`,
and code should be formatted with [black](https://github.com/ambv/black).

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
>> black .
>> flake8 .
```

Editors like VS Code also have automatic code reformat utilities, which can adhere to this standard.

## License

Distributed under the terms of the [BSD-3](http://opensource.org/licenses/BSD-3-Clause) license,
`pytest-notebook` is free and open source software.

## Issues

If you encounter any problems, please [file an issue](https://github.com/chrisjsewell/pytest-notebook/issues) along with a detailed description.

## Acknowledgements

- [nbdime](https://nbdime.readthedocs.io)
- [nbval](https://github.com/computationalmodelling/nbval)
