import textwrap

import nbformat

from pytest_notebook.post_processors import blacken_code
from pytest_notebook.utils import prepare_cell_v4


def test_blacken_no_code():
    """Test blacken if no code cells present."""
    notebook = nbformat.v4.new_notebook()
    new_notebook, _ = blacken_code(notebook, {})
    assert notebook == new_notebook


def test_blacken_code():
    """Test coalesce_streams if streams require merging."""
    notebook = nbformat.v4.new_notebook()
    notebook.cells.append(
        prepare_cell_v4(
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
    expected = nbformat.v4.new_notebook()
    expected.cells.append(
        prepare_cell_v4(
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": textwrap.dedent(
                    """\
                    for i in range(5):
                        x = i
                        a = "123"  # comment
                    """
                ),
            }
        )
    )
    new_notebook, _ = blacken_code(notebook, {})
    assert new_notebook == expected
