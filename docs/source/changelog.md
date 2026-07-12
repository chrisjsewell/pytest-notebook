# Changelog

## v0.11.0 (2026-07-12)

‼️ **BREAKING**: Python 3.10+ and pytest 7.4+ are now required.

* ‼️ Drop Python 3.8/3.9 support; add official Python 3.13 support
* 🐛 Fix compatibility with pytest 8/9: port the notebook collector from the removed `py.path`/`fspath` API to the `pathlib` based API ([#73](https://github.com/chrisjsewell/pytest-notebook/issues/73), [#81](https://github.com/chrisjsewell/pytest-notebook/issues/81))
* ⬆️ Un-pin `attrs` (now `>=21`), `nbclient` (now `>=0.5.10`, tested against 0.11) and `coverage` (now v6.5+, tested against v7) ([#84](https://github.com/chrisjsewell/pytest-notebook/issues/84))
* ✨ Notebooks can now skip themselves at runtime, by raising `pytest.skip(...)` within a cell ([#43](https://github.com/chrisjsewell/pytest-notebook/issues/43))
* ✨ Add `exec_env` fixture option / `nb_exec_env` ini option (lines of `KEY=VALUE`), to set environment variables for the kernel, e.g. `PYTHONPATH` ([#15](https://github.com/chrisjsewell/pytest-notebook/issues/15), [#85](https://github.com/chrisjsewell/pytest-notebook/issues/85))
* 🔧 Move development dependencies from `testing`/`code_style` extras to PEP 735 dependency groups (`test`, `pre_commit`); the `docs` extra is retained
* 🔧 Add `AGENTS.md`, update pre-commit hooks (ruff v0.15) and CI (Python 3.10-3.13 matrix, PyPI trusted publishing, weekly dependabot)

## v0.10.0 (2023-11-28)

* ⬆️ Support nbdime v4 (drop v3 support) by @amotl and @krassowski in <https://github.com/chrisjsewell/pytest-notebook/pull/62>

## v0.9.0 (2023-11-12)

* ⬆️ Add support for Python 3.12 by @sphuber in <https://github.com/chrisjsewell/pytest-notebook/pull/41>
* ⬆️ Drop Python 3.7 by @chrisjsewell in <https://github.com/chrisjsewell/pytest-notebook/pull/55>

## v0.8.1 (2022-11-21)

* ⬆️ Add support for Python 3.10 and 3.11 by @sphuber in <https://github.com/chrisjsewell/pytest-notebook/pull/37>

## v0.8.0 (2022-07-30)

* 🐛 Coverage.py fix by @renefritze in <https://github.com/chrisjsewell/pytest-notebook/pull/25>

## v0.7.0 (2022-01-17)

🔀 Merge: Update package (#20)

- ⬆️ UPGRADE: nbconvert -> nbclient (for notebook execution)
- ⬆️ UPGRADE: coverage v4 -> v5 API (for execution with code coverage)
- 📚 DOCS: Use https for inter-sphinx URLs
- 📚 DOCS: Update documentation packages
- 🔧 Move to flit for PEP 621 packaging
- 🔧 Add isort pre-commit hook

## v0.6.1 (2020-10-16)

- 🐛 Fixed compatibility with pytest version 6
- 👌 Improved repository and documentation

## v0.6.0 (2019-08-13)

- Add Coverage Functionality (#3)

  An ``ExecuteCoveragePreprocessor`` class has been implemented,
  and integrated into the ``NBRegressionFixture`` and ``pytest_notebook.plugin``.
  Also, tests and a tutorial have been added.

## v0.5.2 (2019-08-12)

- Add documentation for beautifulsoup post-processor.
- Add beautifulsoup post-processor.
- Add header info for pytest execution.
- Add minor docstring update.

## v0.5.1 (2019-08-12)

- Include package data.

## v0.5.0 (2019-08-12)

- Fix dependency.

## v0.4.0 (2019-08-12)

- Added regex-replacement functionality (#1)

  Also added:

  - Cell execution logging.
  - Tutorial on configuring `pytest-notebook`.

- Added Conda install documentation.

## v0.3.1 (2019-08-10)

- Add screenshot to manifest.

## v0.3.0 (2019-08-10)

- Add travis deployment key.

- Add documentation and make relevant improvements to the code.

- Add nb_post_processors to configuration options.

- Add diff configuration via notebook metadata.

- Added ordering of stdout/stderr outputs.

  Since they are asynchronous, so order isn't guaranteed.
- Add collection/execution of notebooks.

- Add blacken_code post-processor.

- Add initial working implementation.

- Commit before changing to nbdime.

- Initial commit.
