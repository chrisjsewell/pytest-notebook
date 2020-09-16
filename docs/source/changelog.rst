Changelog
=========

v0.6.1 (2020-10-16)
-------------------

🐛 Fixed compatibility with pytest version 6
👌 Improved repository and documentation

v0.6.0 (2019-08-13)
-------------------
- Add Coverage Functionality (#3) [Chris Sewell]

  An ``ExecuteCoveragePreprocessor`` class has been implemented,
  and integrated into the ``NBRegressionFixture`` and ``pytest_notebook.plugin``.
  Also, tests and a tutorial have been added.

v0.5.2 (2019-08-12)
-------------------
- Add documentation for beautifulsoup post-processor. [Chris Sewell]

- Add beautifulsoup post-processor. [Chris Sewell]

- Add header info for pytest execution. [Chris Sewell]

- Add minor docstring update. [Chris Sewell]


v0.5.1 (2019-08-12)
-------------------
- Include package data. [Chris Sewell]


v0.5.0 (2019-08-12)
-------------------
- Fix dependency. [Chris Sewell]


v0.4.0 (2019-08-12)
-------------------
- Added regex-replacement functionality (#1) [Chris Sewell]

  Also added:

  - Cell execution logging.
  - Tutorial on configuring `pytest-notebook`.
- Added Conda install documentation. [Chris Sewell]


v0.3.1 (2019-08-10)
-------------------
- Add screenshot to manifest. [Chris Sewell]


v0.3.0 (2019-08-10)
-------------------
- Add travis deployment key. [Chris Sewell]

- Add documentation and make relevant improvements to the code. [Chris Sewell]

- Add nb_post_processors to configuration options. [Chris Sewell]

- Add diff configuration via notebook metadata. [Chris Sewell]

- Added ordering of stdout/stderr outputs. [Chris Sewell]

  Since they are asynchronous, so order isn't guaranteed.
- Add collection/execution of notebooks. [Chris Sewell]

- Add blacken_code post-processor. [Chris Sewell]

- Add initial working implementation. [Chris Sewell]

- Commit before changing to nbdime. [Chris Sewell]

- Initial commit. [Chris Sewell]
