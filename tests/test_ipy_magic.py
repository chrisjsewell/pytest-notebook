from textwrap import dedent

import pytest

from pytest_notebook import ipy_magic


def test_parse_cell_content():
    cell = dedent(
        """\
    ---
    [pytest]
    addopts = -v
    ---
    ***
    (string, path)
    ***

    def test_something():
        assert True
    """
    )
    test, config, literals = ipy_magic.parse_cell_content(cell)
    assert literals == ["(string, path)"]
    assert config == ["[pytest]", "addopts = -v"]
    assert test == ["", "def test_something():", "    assert True"]


@pytest.mark.parametrize(
    "literal", ("", "()", "(1, 2)", "(a, 'b')", "('a', '/b')", "('a', 'b/c')")
)
def test_eval_literals_fail(literal):
    with pytest.raises(ValueError):
        list(ipy_magic.eval_literals([literal], locals()))


def test_eval_literals_success():
    a = "1"
    assert list(ipy_magic.eval_literals(["(a, '2')"], locals())) == [("1", "2")]


def test_call_pytest_line(capsys):
    ipy_magic.pytest(line="")
    captured = capsys.readouterr()
    assert "collected 0 items" in captured.out


def test_call_pytest_cell(capsys):
    cell = dedent(
        """\
    ---
    [pytest]
    addopts = -v
    ---

    def test_something():
        assert True
    """
    )
    ipy_magic.pytest(line="-v", cell=cell)
    captured = capsys.readouterr()
    assert ipy_magic.MAIN_FILE_NAME in captured.out
    assert "1 passed" in captured.out


def test_call_pytest_cell_with_literal(capsys):
    cell = dedent(
        """\
    ---
    [pytest]
    addopts = -v
    ---

    ***
    ("def test_other():\\n    assert True", "test_other.py")
    ***

    def test_something():
        assert True
    """
    )
    ipy_magic.pytest(line="-v", cell=cell)
    captured = capsys.readouterr()
    assert ipy_magic.MAIN_FILE_NAME in captured.out
    assert "test_other.py" in captured.out
    assert "2 passed" in captured.out
