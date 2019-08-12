import textwrap

from pytest_notebook.post_processors import blacken_code
from pytest_notebook.notebook import create_notebook, prepare_cell


def test_blacken_no_code():
    """Test blacken if no code cells present."""
    notebook = create_notebook()
    new_notebook, _ = blacken_code(notebook, {})
    assert notebook == new_notebook


def test_blacken_code():
    """Test coalesce_streams if streams require merging."""
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
    expected = create_notebook()
    expected.cells.append(
        prepare_cell(
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
