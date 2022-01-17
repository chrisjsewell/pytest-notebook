# Changelog

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
