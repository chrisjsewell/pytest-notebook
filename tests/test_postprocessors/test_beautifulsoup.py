"""Tests for beautifulsoup post-processor."""
from pytest_notebook.notebook import create_notebook, mapping_to_dict, prepare_cell
from pytest_notebook.post_processors import beautifulsoup


def test_beautifulsoup_no_output():
    """Test prettify if no outputs present."""
    notebook = create_notebook()
    new_notebook, _ = beautifulsoup(notebook, {})
    assert notebook == new_notebook


def test_beautifulsoup(data_regression):
    """Test applying beautifulsoup to html outputs."""
    notebook = create_notebook()
    notebook.cells.extend(
        [
            prepare_cell(
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [
                        {
                            "data": {
                                "text/html": [
                                    "\n",
                                    '<div class="section" id="submodules">\n',
                                    '    <h2>Submodules<a class="headerlink" href="#submodules" title="Permalink to this headline">¶</a></h2>\n',  # noqa: E501
                                    "</div>",
                                ],
                                "text/plain": ["<IPython.core.display.HTML object>"],
                            },
                            "execution_count": 1,
                            "metadata": {},
                            "output_type": "execute_result",
                        }
                    ],
                    "source": [""],
                }
            ),
            prepare_cell(
                {
                    "cell_type": "code",
                    "execution_count": 2,
                    "metadata": {},
                    "outputs": [
                        {
                            "data": {
                                "image/svg+xml": [
                                    '<svg height="100" width="100">\n',
                                    '  <circle cx="50" cy="50" fill="red" r="40" stroke="black" stroke-width="3"/></svg>\n',  # noqa: E501
                                    "",
                                ],
                                "text/plain": ["<IPython.core.display.SVG object>"],
                            },
                            "execution_count": 2,
                            "metadata": {},
                            "output_type": "execute_result",
                        }
                    ],
                    "source": [""],
                }
            ),
        ]
    )

    new_notebook, resources = beautifulsoup(notebook, {})
    assert resources["beautifulsoup"] == [
        "/cells/0/outputs/0/text/html",
        "/cells/1/outputs/0/image/svg+xml",
    ]
    new_notebook.nbformat_minor = None
    data_regression.check(mapping_to_dict(new_notebook))
