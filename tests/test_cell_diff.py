import pytest

from pytest_notebook.diffing import diff_notebooks
from pytest_notebook.notebook import prepare_cell


def get_test_cell(type_name, variable="hallo"):

    cells = {
        "stdout": {
            "cell_type": "code",
            "execution_count": 3,
            "metadata": {},
            "outputs": [
                {"name": "stdout", "output_type": "stream", "text": [f"{variable}\n"]}
            ],
            "source": "".join(["# code cell + stdout\n", f"print('{variable}')"]),
        },
        "stderr": {
            "cell_type": "code",
            "execution_count": 5,
            "metadata": {},
            "outputs": [
                {"name": "stderr", "output_type": "stream", "text": [f"{variable}\n"]}
            ],
            "source": [
                "# code cell + stderr\n",
                f"print('{variable}', file=sys.stderr)",
            ],
        },
        "stdout_stderr": {
            "cell_type": "code",
            "execution_count": 8,
            "metadata": {},
            "outputs": [
                {"name": "stdout", "output_type": "stream", "text": ["hallo2\n"]},
                {"name": "stderr", "output_type": "stream", "text": [f"{variable}\n"]},
            ],
            "source": [
                "# code cell + stderr + stdout\n",
                "print('hallo1', file=sys.stderr)\n",
                "print('hallo2')",
            ],
        },
        "text/latex": {
            "cell_type": "code",
            "execution_count": 29,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "text/latex": [f"\\textit{{{variable}}}"],
                        "text/plain": ["<IPython.core.display.Latex object>"],
                    },
                    "execution_count": 29,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": [
                "# code cell + latex\n",
                f"display.Latex('\\\\textit{{{variable}}}')",
            ],
        },
        "text/html": {
            "cell_type": "code",
            "execution_count": 26,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "text/html": [
                            "\n",
                            '<div class="section" id="submodules">\n',
                            f'    <h2>{variable}<a class="headerlink" href="#submodules" title="Permalink to this headline">¶</a></h2>\n',  # noqa: E501
                            "</div>",
                        ],
                        "text/plain": ["<IPython.core.display.HTML object>"],
                    },
                    "execution_count": 26,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": [
                "# code cell + html\n",
                'display.HTML("""\n',
                '<div class="section" id="submodules">\n',
                f'    <h2>{variable}<a class="headerlink" href="#submodules" title="Permalink to this headline">¶</a></h2>\n',  # noqa: E501
                '</div>""")',
            ],
        },
        "application/json": {
            "cell_type": "code",
            "execution_count": 32,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "application/json": {
                            "a": [1, 2, 3, 4],
                            "b": {"inner1": f"{variable}", "inner2": "foobar"},
                        },
                        "text/plain": ["<IPython.core.display.JSON object>"],
                    },
                    "execution_count": 32,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": [
                "# code cell + json\n",
                (
                    f"display.JSON({{'a': [1, 2, 3, 4,], 'b': "
                    f"{{'inner1': '{variable}', 'inner2': 'foobar'}}}})"
                ),
            ],
        },
        "image/png": {
            "cell_type": "code",
            "execution_count": 4,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "image/png": "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\n",  # noqa: E501
                        "text/plain": ["<IPython.core.display.Image object>"],
                    },
                    "execution_count": 4,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": [
                "from IPython.display import Image\n",
                'Image(filename="128x128.png")',
            ],
        },
        "image/png_altered": {
            "cell_type": "code",
            "execution_count": 7,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "image/png": "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAD8GlDQ1BJQ0MgUHJvZmlsZQAAOI2NVd1v21QUP4lvXKQWP6Cxjg4Vi69VU1u5GxqtxgZJk6XpQhq5zdgqpMl1bhpT1za2021Vn/YCbwz4A4CyBx6QeEIaDMT2su0BtElTQRXVJKQ9dNpAaJP2gqpwrq9Tu13GuJGvfznndz7v0TVAx1ea45hJGWDe8l01n5GPn5iWO1YhCc9BJ/RAp6Z7TrpcLgIuxoVH1sNfIcHeNwfa6/9zdVappwMknkJsVz19HvFpgJSpO64PIN5G+fAp30Hc8TziHS4miFhheJbjLMMzHB8POFPqKGKWi6TXtSriJcT9MzH5bAzzHIK1I08t6hq6zHpRdu2aYdJYuk9Q/881bzZa8Xrx6fLmJo/iu4/VXnfH1BB/rmu5ScQvI77m+BkmfxXxvcZcJY14L0DymZp7pML5yTcW61PvIN6JuGr4halQvmjNlCa4bXJ5zj6qhpxrujeKPYMXEd+q00KR5yNAlWZzrF+Ie+uNsdC/MO4tTOZafhbroyXuR3Df08bLiHsQf+ja6gTPWVimZl7l/oUrjl8OcxDWLbNU5D6JRL2gxkDu16fGuC054OMhclsyXTOOFEL+kmMGs4i5kfNuQ62EnBuam8tzP+Q+tSqhz9SuqpZlvR1EfBiOJTSgYMMM7jpYsAEyqJCHDL4dcFFTAwNMlFDUUpQYiadhDmXteeWAw3HEmA2s15k1RmnP4RHuhBybdBOF7MfnICmSQ2SYjIBM3iRvkcMki9IRcnDTthyLz2Ld2fTzPjTQK+Mdg8y5nkZfFO+se9LQr3/09xZr+5GcaSufeAfAww60mAPx+q8u/bAr8rFCLrx7s+vqEkw8qb+p26n11Aruq6m1iJH6PbWGv1VIY25mkNE8PkaQhxfLIF7DZXx80HD/A3l2jLclYs061xNpWCfoB6WHJTjbH0mV35Q/lRXlC+W8cndbl9t2SfhU+Fb4UfhO+F74GWThknBZ+Em4InwjXIyd1ePnY/Psg3pb1TJNu15TMKWMtFt6ScpKL0ivSMXIn9QtDUlj0h7U7N48t3i8eC0GnMC91dX2sTivgloDTgUVeEGHLTizbf5Da9JLhkhh29QOs1luMcScmBXTIIt7xRFxSBxnuJWfuAd1I7jntkyd/pgKaIwVr3MgmDo2q8x6IdB5QH162mcX7ajtnHGN2bov71OU1+U0fqqoXLD0wX5ZM005UHmySz3qLtDqILDvIL+iH6jB9y2x83ok898GOPQX3lk3Itl0A+BrD6D7tUjWh3fis58BXDigN9yF8M5PJH4B8Gr79/F/XRm8m241mw/wvur4BGDj42bzn+Vmc+NL9L8GcMn8F1kAcXgSteGGAAABWWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS40LjAiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyI+CiAgICAgICAgIDx0aWZmOk9yaWVudGF0aW9uPjE8L3RpZmY6T3JpZW50YXRpb24+CiAgICAgIDwvcmRmOkRlc2NyaXB0aW9uPgogICA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgpMwidZAAAU80lEQVR4Ae2dB8zcRBaAJweIFiACREcQaihKInpvdyASShQ6SCiBiE7CISSIcpTQCTlAEEih9yZEyYUuEEWE3msQVfSWg4QmkWTPn7m3PM/aXttrj+3/3yet7BlPnzczb17bPg0PTBd67Qj8rdf2vNtxfwS6CNDLEaGLAF0E6OUj0Mu7390BugjQs0fg999/N2PHjjW//PJLz+5oxt716cnXwC+//NLstttu5v333zfrrbeeefzxx80KK6yQcah6ZrYeewQ8//zzZpNNNvEnn6kDCbbeemvz0UcfJZ7Jt956y9x6662J09cyITtAHeDNN99s8EsC1157bWOxxRZrLLLIIi2/FVdcsfHqq6/GFvPAAw80dt11Vz/vcsst1/jtt99i09f5o6lL4/fdd19/QpjAgw8+uMEk//jjjy3NHzNmTMuk24iwzDLLNB577LFAXso655xzGmuttVZLfurqqVALGgACbtVVVzW//vpryy67wQYbmJ122snsvvvu5pJLLjFP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\n",  # noqa: E501
                        "text/plain": ["<IPython.core.display.Image object>"],
                    },
                    "execution_count": 7,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": [
                "from IPython.display import Image\n",
                'Image(filename="128x128_altered.png")',
            ],
        },
        "image/jpeg": {
            "cell_type": "code",
            "execution_count": 6,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "image/jpeg": "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\n",  # noqa: E501
                        "text/plain": ["<IPython.core.display.Image object>"],
                    },
                    "execution_count": 6,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": ['Image(filename="128x128.jpg")'],
        },
        "image/jpeg_altered": {
            "cell_type": "code",
            "execution_count": 8,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "image/jpeg": "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\n",  # noqa: E501
                        "text/plain": ["<IPython.core.display.Image object>"],
                    },
                    "execution_count": 8,
                    "metadata": {},
                    "output_type": "execute_result",
                }
            ],
            "source": ['Image(filename="128x128_altered.jpg")'],
        },
    }

    return prepare_cell(cells[type_name])


@pytest.mark.parametrize(
    "cell_type",
    (
        "stdout",
        "stderr",
        "stdout_stderr",
        "text/latex",
        "text/html",
        "application/json",
        "image/png",
        "image/jpeg",
    ),
)
def test_compare_cells_equal(cell_type):
    """Test comparing cells that are equal."""
    diff = diff_notebooks(
        get_test_cell(cell_type), get_test_cell(cell_type), initial_path="/cells/0"
    )
    assert diff == []


@pytest.mark.parametrize(
    "cell_type",
    (
        "stdout",
        "stderr",
        "stdout_stderr",
        "text/latex",
        "text/html",
        "application/json",
    ),
)
def test_compare_cells_text_unequal(cell_type):
    """Test comparing cells that contain text and are unequal."""
    diff = diff_notebooks(
        get_test_cell(cell_type, "variable1"),
        get_test_cell(cell_type, "variable2"),
        initial_path="/cells/0",
    )
    assert diff != []


@pytest.mark.parametrize(
    "cell_in,cell_out",
    (("image/png", "image/png_altered"), ("image/jpeg", "image/jpeg_altered")),
)
def test_compare_cells_image_unequal(cell_in, cell_out):
    """Test comparing cells that contain images and are unequal."""
    diff = diff_notebooks(
        get_test_cell(cell_in), get_test_cell(cell_out), initial_path="/cells/0"
    )
    assert diff != []
