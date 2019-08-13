pytest-notebook
===============

.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   user_guide/get_started

.. toctree::
   :maxdepth: 1
   :caption: Tutorials
   :hidden:

   user_guide/tutorial_intro
   user_guide/tutorial_config
   user_guide/tutorial_coverage

.. toctree::
   :maxdepth: 1
   :caption: Validation Schemas
   :hidden:

   literal_includes/nb_metadata_schema

.. toctree::
   :maxdepth: 1
   :caption: Miscellaneous
   :hidden:

   changelog
   api_index


A `pytest`_ plugin for regression testing and regenerating `Jupyter`_ Notebooks.

.. image:: _static/pytest-notebook-screenshot.png
   :alt: Example Test
   :align: center
   :height: 400px

Purpose
-------

The purpose of the plugin is to ensure that changes to the python
environment (e.g. updating packages), have not affected the outputs
of the notebook. If the notebook has changed, this plugin can also
regenerate the notebooks, saving the new outputs.

Features
--------

-  Recognise, collect, execute then diff input
   vs. output `Jupyter`_ Notebooks.

-  Provides clear and colorized diffs of the notebooks (using `nbdime`_)

-  Regenerate failing notebooks (see :ref:`regen_notebooks`).

-  Integration with `coverage`_ and `pytest_cov`_ (see :ref:`tutorial_coverage`).

-  A well defined API allows notebook regression tests to be run in multiple ways
   (see :ref:`pytest_notebook_by_example`):

   1. Using the pytest test collection architecture.
   2. As a pytest fixtures.
   3. Using the ``pytest_notebook`` python package.

-  All stages are highly configurable (see :ref:`configuring_pytest_notebook`) *via*:

   1. The pytest command-line interface.
   2. The pytest configuration file.
   3. The notebook and cell level metadata.

-  Post-processor plugin entry-points, allow for customisable
   modifications of the notebook, including source code formatting with
   `black`_ (see :ref:`post_processors`).

.. image:: _static/collaged_in_out.png
   :alt: Configuration Examples
   :align: center

License
-------

Distributed under the terms of the
`BSD-3 <http://opensource.org/licenses/BSD-3-Clause>`__ license,
``pytest-notebook`` is free and open source software.

Issues
------

If you encounter any problems, please `file an
issue <https://github.com/chrisjsewell/pytest-notebook/issues>`__ along
with a detailed description.

Acknowledgements
----------------

- `nbdime <https://nbdime.readthedocs.io>`__
- `nbval <https://github.com/computationalmodelling/nbval>`__
- `pytest-regressions <https://pytest-regressions.readthedocs.io>`__

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _pytest: https://github.com/pytest-dev/pytest
.. _coverage: https://coverage.readthedocs.io
.. _pytest_cov: https://pytest-cov.readthedocs.io
.. _Jupyter: https://jupyter.org/
.. _nbdime: https://nbdime.readthedocs.io
.. _black: https://github.com/ambv/black
