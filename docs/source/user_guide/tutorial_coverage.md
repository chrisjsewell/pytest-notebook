---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.6.0rc0
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(tutorial_coverage)=

# Execution and Coverage Reporting

:::{seealso}
This notebook was rendered with [myst-nb](https://myst-nb.readthedocs.io): {nb-download}`tutorial_coverage.ipynb`
:::

+++

The core component of the notebook execution API is the {py:class}`~pytest_notebook.execution.CoverageNotebookClient` class,
which is a subclass of {py:class}`nbclient.client.NotebookClient`,
that can additionally create code [coverage](https://coverage.readthedocs.io) analytics.

This class is called by {py:func}`~pytest_notebook.execution.execute_notebook`,
which returns an {py:class}`~pytest_notebook.execution.ExecuteResult` object.

```{code-cell} ipython3
from pytest_notebook.execution import execute_notebook
from pytest_notebook.notebook import create_notebook, create_cell, dump_notebook
```

```{code-cell} ipython3
notebook = create_notebook(
    metadata={
        "kernelspec": {
            "name": "python3",
            "display_name": "Python 3",
        }
    },
    cells=[
        create_cell("""
from pytest_notebook import __version__
from pytest_notebook.notebook import create_notebook
print(__version__)
"""
    )]
)
```

```{code-cell} ipython3
result = execute_notebook(notebook, with_coverage=True)
result.notebook
```

```{code-cell} ipython3
result.coverage_data()
```

```{code-cell} ipython3
:tags: [hide-output]

result.coverage_dict
```

The coverage can be limited to particular files or modules, by setting `cov_source`.

```{code-cell} ipython3
result = execute_notebook(
    notebook, with_coverage=True, cov_source=['pytest_notebook.notebook'])
result.coverage_dict
```

## Integration with pytest-cov

+++

If the [pytest-cov](https://pytest-cov.readthedocs.io) plugin is installed,
the {py:class}`~pytest_notebook.nb_regression.NBRegressionFixture` will be initialised
with the settings and {py:class}`coverage.Coverage` object, that
`pytest-cov` has created.

If the `--nb-coverage` flag is set, then `nb_regression` will run coverage introspection,
and merge the data back into the main {py:class}`~coverage.Coverage` object.

```{code-cell} ipython3
%load_ext pytest_notebook.ipy_magic
```

```{code-cell} ipython3
%%pytest --disable-warnings --color=yes --cov=pytest_notebook --nb-coverage --log-cli-level=info

import logging
try:
    # Python <= 3.8
    from importlib_resources import files
except ImportError:
    from importlib.resources import files
from pytest_notebook import example_nbs

def test_notebook(nb_regression):
    logging.getLogger(__name__).info(nb_regression)
    with files(example_nbs).joinpath("coverage.ipynb") as path:
        nb_regression.check(str(path))
```

This is also the case, when using the pytest file collection approach.

```{code-cell} ipython3
%%pytest --disable-warnings --color=yes --cov=pytest_notebook --log-cli-level=info

---
[pytest]
nb_coverage = True
nb_test_files = True
---

***
(dump_notebook(notebook), "test_notebook1.ipynb")
***
```
