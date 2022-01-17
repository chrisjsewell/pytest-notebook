"""Tests for blacken_code post-processor."""
import textwrap

from pytest_notebook.notebook import create_notebook, mapping_to_dict, prepare_cell
from pytest_notebook.post_processors import blacken_code


def test_blacken_no_code():
    """Test blacken if no code cells present."""
    notebook = create_notebook()
    new_notebook, _ = blacken_code(notebook, {})
    assert notebook == new_notebook


def test_blacken_code(data_regression):
    """Test blacken unformatted code."""
    notebook = create_notebook()
    notebook.cells.append(
        prepare_cell(
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": textwrap.dedent(
                    """\
                    for i in range(5):
                      x=i
                      a ='123'# comment
                    """
                ),
            }
        )
    )

    new_notebook, _ = blacken_code(notebook, {})
    new_notebook.nbformat_minor = None
    data_regression.check(mapping_to_dict(new_notebook))
