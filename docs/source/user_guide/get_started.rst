Installation
++++++++++++

|PyPI| |Conda|

.. To install from Conda (recommended)::

..     >> conda install -c conda-forge pytest-notebook aiida-core.services

To install from pypi::

    >> pip install --pre pytest-notebook

To install the development version::

    >> git clone https://github.com/chrisjsewell/pytest-notebook .
    >> cd pytest-notebook

.. and either use the pre-written Conda development environment (recommended)::

..     >> conda env create -n aiida_testenv -f conda_dev_env.yml python=3.6
..     >> conda activate aiida_testenv
..     >> pip install --no-deps -e .

or install all *via* pip::

    >> pip install -e .
    #>> pip install -e .[code_style,testing,docs] # install extras for more features


Development
+++++++++++

Testing
~~~~~~~

|Build Status| |Coverage Status|

The following will discover and run all unit test:

.. code:: shell

   >> cd pytest-notebook
   >> pytest -v

Coding Style Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

The code style is tested using `flake8 <http://flake8.pycqa.org>`__,
with the configuration set in ``.flake8``, and
`black <https://github.com/ambv/black>`__.

Installing with ``pytest-notebook[code_style]`` makes the
`pre-commit <https://pre-commit.com/>`__ package available, which will
ensure these tests are passed by reformatting the code and testing for
lint errors before submitting a commit. It can be setup by:

.. code:: shell

   >> cd pytest-notebook
   >> pre-commit install

Optionally you can run ``black`` and ``flake8`` separately:

.. code:: shell

   >> black .
   >> flake8 .

Editors like VS Code also have automatic code reformat utilities, which
can check and adhere to this standard.

Documentation
~~~~~~~~~~~~~

The documentation can be created locally by:

.. code:: shell

   >> cd pytest-notebook/docs
   >> make clean
   >> make  # or make debug

.. |PyPI| image:: https://img.shields.io/pypi/v/pytest-notebook.svg
   :target: https://pypi.python.org/pypi/pytest-notebook/
.. |Conda| image:: https://anaconda.org/conda-forge/pytest-notebook/badges/version.svg
   :target: https://anaconda.org/conda-forge/pytest-notebook
.. |Build Status| image:: https://travis-ci.org/chrisjsewell/pytest-notebook.svg?branch=master
   :target: https://travis-ci.org/chrisjsewell/pytest-notebook
.. |Coverage Status| image:: https://coveralls.io/repos/github/chrisjsewell/pytest-notebook/badge.svg?branch=master
   :target: https://coveralls.io/github/chrisjsewell/pytest-notebook?branch=master
