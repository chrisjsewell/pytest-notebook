# AGENTS.md

This file provides guidance for AI coding agents working on the **pytest-notebook** repository.

## Project Overview

pytest-notebook is a [pytest](https://docs.pytest.org) plugin for regression-testing and executing [Jupyter Notebooks](https://jupyter.org/). It provides:

- Collection of `.ipynb` files as pytest tests (each notebook becomes a test item)
- Execution of notebooks via [nbclient](https://nbclient.readthedocs.io), with optional [coverage.py](https://coverage.readthedocs.io) integration
- Regression testing of notebook outputs by diffing against the stored notebook, using [nbdime](https://nbdime.readthedocs.io)
- Configurable diff ignoring, regex replacement, and output post-processing
- An `nb_regression` fixture and a `%%pytest` IPython magic for interactive use

pytest-notebook is designed to make notebooks a first-class, testable artifact, verifying that they execute cleanly and that their outputs remain stable.

Documentation is hosted at [pytest-notebook.readthedocs.io](https://pytest-notebook.readthedocs.io).

## Repository Structure

```
pyproject.toml          # Project configuration and dependencies (flit)
tox.ini                 # Tox environments + [pytest] self-testing config

pytest_notebook/        # Main source code
├── __init__.py         # Package init / version
├── plugin.py           # pytest hooks, `nb_regression` fixture, notebook collector
├── nb_regression.py    # NBRegressionFixture - core execute + diff logic
├── execution.py        # nbclient-based execution, coverage.py integration
├── diffing.py          # nbdime diffing, filtering, and formatting of diffs
├── notebook.py         # Notebook loading + `nbreg` metadata config (JSON-schema validated)
├── post_processors.py  # Entry-point post-processors (coalesce_streams, blacken_code, beautifulsoup)
├── normalizers.py      # Entry-point diff normalizers (strip_ansi, mask_timestamps, ...)
├── ipy_magic.py        # `%pytest` / `%%pytest` IPython magic
├── utils.py            # Utility helpers (e.g. autodoc)
├── resources/          # JSON schema and other package resources
└── example_nbs/        # Example notebooks

tests/                  # Test suite
├── conftest.py         # Shared fixtures
├── test_nb_regression.py   # NBRegressionFixture tests
├── test_execution.py       # Execution tests
├── test_nb_diff.py         # Notebook diffing tests
├── test_cell_diff.py       # Cell-level diffing tests
├── test_filter_diff.py     # Diff filtering tests
├── test_notebook.py        # Notebook loading / config tests
├── test_coalesce_streams.py, test_postprocessors/  # Post-processor tests
├── test_plugin_collector.py, test_plugin_fixture.py # Plugin/collector/fixture tests
├── test_ipy_magic.py       # IPython magic tests
├── test_utils.py
└── raw_files/          # Stored fixtures for pytest-regressions comparisons

docs/                   # Documentation source (Sphinx + myst-nb)
└── source/
    ├── conf.py         # Sphinx configuration
    ├── index.rst       # Documentation index
    ├── changelog.md    # Changelog (update on every user-facing change)
    ├── user_guide/     # User guide notebooks/pages
    ├── apidoc/         # API documentation
    └── literal_includes/
```

## Development Commands

Tests can be run either via [`tox`](https://tox.wiki) (recommended, for isolated environments) or directly with pytest in a local install.

### Testing

```bash
# Run the default environment
tox

# Run tests with a specific Python version
tox -e py311 -- {pytest args}

# Run a specific test file
tox -e py311 -- tests/test_nb_regression.py

# Run a specific test function
tox -e py311 -- tests/test_nb_regression.py::test_basic_execution
```

Or, for a local (non-tox) workflow, install the test dependency group and run pytest directly:

```bash
# Install the package with the PEP 735 `test` dependency group
pip install --group test -e .

# Run the tests
pytest
```

> Test dependencies live in the PEP 735 `[dependency-groups]` `test` group in `pyproject.toml`
> (this replaces the old `testing` extra). Documentation dependencies are the `docs` extra.

### Documentation

```bash
# Build docs (clean rebuild)
tox -e docs-clean

# Build docs (incremental update)
tox -e docs-update
```

The docs environment runs `make` in the `docs/` directory using the `docs` extra.

### Code Quality

```bash
# Run pre-commit hooks on all files (ruff + ruff-format)
pre-commit run --all-files

# Linting and formatting individually
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

There is no mypy / type-checking step configured in this repository.

## Code Style Guidelines

- **Formatter/Linter**: Ruff (configured in `pyproject.toml`, `[tool.ruff.lint]`)
- **Pre-commit**: Use pre-commit hooks for consistent code style (`.pre-commit-config.yaml`)
- **Python**: Requires Python `>=3.10`

### Best Practices

- **Docstrings**: Use Sphinx-style (`:param:` / `:return:`) docstrings, as used throughout the codebase.
- **attrs**: Configuration classes (e.g. `NBRegressionFixture`) use [attrs](https://www.attrs.org) with validators; follow the existing pattern when adding options.
- **Import sorting**: isort is enabled with `force-sort-within-sections` (via Ruff).
- **Testing**: Write tests for all new functionality. Use `pytest-regressions` for output comparison tests.

## Architecture Overview

The core flow is: **collect a notebook → execute it → diff its new outputs against the stored outputs → report differences**.

### Key Components

#### Plugin (`plugin.py`)

The pytest integration layer:

- `pytest_addoption` / `pytest_report_header` – register and report configuration options
- `nb_regression` fixture (function scope) – exposes an `NBRegressionFixture` built from pytest config
- `pytest_collect_file` + `JupyterNbCollector` (a `pytest.File`) and `JupyterNbTest` (a `pytest.Item`) – collect `.ipynb` files as test items when notebook testing is enabled

#### NBRegressionFixture (`nb_regression.py`)

The core class tying everything together: it loads a notebook, executes it, applies post-processors and diff filtering, diffs against the original, and raises/reports on differences (with a `--nb-force-regen`-style regeneration path).

#### Execution (`execution.py`)

Executes notebooks with `nbclient.NotebookClient`, handling timeouts, allowed errors, working directory, and optional coverage.py data collection (injected via setup/teardown code cells).

#### Diffing (`diffing.py`)

Wraps nbdime to compute notebook diffs, filter out ignored paths, and pretty-print/format the resulting diff. (Note: nbdime is currently hard-coded to notebook format v4.)

#### Notebook config (`notebook.py`)

Loads notebooks and reads per-notebook configuration from the `nbreg` notebook metadata key (`META_KEY = "nbreg"`), validated against a JSON schema in `resources/`. Also provides regex-replacement helpers.

#### Post-processors (`post_processors.py`)

Registered via the `nbreg.post_proc` entry-point group. Built-in processors:

- `coalesce_streams` – merge consecutive stream outputs
- `blacken_code` – format code cells with black
- `beautifulsoup` – normalize HTML outputs

#### IPython magic (`ipy_magic.py`)

Provides the `%pytest` line and `%%pytest` cell magics (loaded via `%load_ext pytest_notebook.ipy_magic`) to run pytest against inline test content from within a notebook.

## Testing Guidelines

- Tests use `pytest` with fixtures from `tests/conftest.py`.
- Regression testing uses `pytest-regressions` (`file_regression` / `data_regression`); stored fixtures live under `tests/raw_files/` (and per-test folders such as `tests/test_nb_diff/`).
- pytest-notebook self-tests some of its own documentation notebooks: the `[pytest]` section in `tox.ini` configures `nb_file_fnmatch` (which notebooks to collect) and `nb_diff_replace` (regex substitutions to normalize volatile output such as paths, timings, and platform/plugin banners).

> **Caution:** Because outputs are compared exactly, changing the installed **black** or **IPython** version (or other output-affecting dependencies) can shift regression fixtures. Regenerate fixtures deliberately and review the diffs when this happens.

### Test Best Practices

- **Test coverage**: Write tests for all new functionality and bug fixes.
- **Isolation**: Each test should be independent.
- **Descriptive names**: Test function names should describe what is being tested.
- **Regression testing**: Use the `file_regression.check()` fixture for complex output comparisons.

## Commit Message Format

Use this format:

```
<EMOJI> <KEYWORD>: Summarize in 72 chars or less (#<PR>)

Optional detailed explanation.
```

Keywords:

- `✨ NEW:` – New feature
- `🐛 FIX:` – Bug fix
- `👌 IMPROVE:` – Improvement (no breaking changes)
- `‼️ BREAKING:` – Breaking change
- `📚 DOCS:` – Documentation
- `🔧 MAINTAIN:` – Maintenance changes only (typos, etc.)
- `🧪 TEST:` – Tests or CI changes only
- `♻️ REFACTOR:` – Refactoring

## PR Title and Description Format

Use the same format as commit messages, but for the title you can omit the `KEYWORD` and only use `EMOJI`.

## Pull Request Requirements

When submitting changes:

1. **Description**: Include a meaningful description or link explaining the change.
2. **Tests**: Include test cases for new functionality or bug fixes.
3. **Documentation**: Update the docs if behavior changes or new features are added.
4. **Changelog**: Update `docs/source/changelog.md` under the appropriate section.
5. **Code Quality**: Ensure `pre-commit run --all-files` passes.

## Key Files

- `pyproject.toml` – Project configuration, dependencies, dependency groups, entry points, and Ruff settings
- `tox.ini` – Tox environments and the `[pytest]` self-testing configuration
- `pytest_notebook/plugin.py` – pytest hooks, `nb_regression` fixture, notebook collector
- `pytest_notebook/nb_regression.py` – `NBRegressionFixture` core execute + diff logic
- `pytest_notebook/execution.py` – nbclient execution and coverage.py integration
- `pytest_notebook/diffing.py` – nbdime diffing, filtering, and formatting
- `pytest_notebook/notebook.py` – notebook loading and `nbreg` metadata config
- `pytest_notebook/post_processors.py` – entry-point post-processors
- `pytest_notebook/ipy_magic.py` – `%pytest` / `%%pytest` IPython magic
- `docs/source/changelog.md` – Changelog

## Reference Documentation

- [pytest-notebook Documentation](https://pytest-notebook.readthedocs.io)
- [pytest-notebook Repository](https://github.com/chrisjsewell/pytest-notebook)
- [pytest Documentation](https://docs.pytest.org)
- [nbclient Documentation](https://nbclient.readthedocs.io)
- [nbdime Documentation](https://nbdime.readthedocs.io)
- [nbformat Documentation](https://nbformat.readthedocs.io)
