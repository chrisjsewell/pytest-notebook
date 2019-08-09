from pytest_notebook.utils import autodoc
from pytest_notebook.nb_regression import NBRegressionFixture


def test_autodoc(file_regression):
    new_class = autodoc(NBRegressionFixture)
    file_regression.check(new_class.__doc__)
