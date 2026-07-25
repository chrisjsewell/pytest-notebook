"""Tests for pytest_notebook.normalizers."""

import pytest

from pytest_notebook.normalizers import (
    collapse_whitespace,
    list_normalizer_names,
    load_normalizer,
    mask_memory_addresses,
    mask_timestamps,
    mask_uuids,
    strip_ansi,
)
from pytest_notebook.notebook import create_notebook, prepare_cell


def make_notebook(text, traceback=None):
    """Create a notebook with a single code cell, with a stream text output."""
    outputs = [{"name": "stdout", "output_type": "stream", "text": text}]
    if traceback is not None:
        outputs.append(
            {
                "output_type": "error",
                "ename": "Error",
                "evalue": "",
                "traceback": traceback,
            }
        )
    notebook = create_notebook()
    notebook.cells.append(
        prepare_cell(
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": outputs,
                "source": "pass",
            }
        )
    )
    return notebook


def test_entry_points():
    """Test that all built-in normalizers are registered and loadable."""
    names = list_normalizer_names()
    for name in (
        "strip_ansi",
        "mask_timestamps",
        "mask_memory_addresses",
        "mask_uuids",
        "collapse_whitespace",
    ):
        assert name in names
        assert callable(load_normalizer(name))


def test_load_normalizer_unknown():
    """Test that loading an unknown normalizer raises an error."""
    with pytest.raises(ValueError, match="entry point 'unknown'"):
        load_normalizer("unknown")


def test_strip_ansi():
    notebook = make_notebook(
        "\x1b[32mpassed\x1b[0m\n", traceback=["\x1b[0;31mError\x1b[0m: bad"]
    )
    new_notebook = strip_ansi(notebook)
    assert new_notebook.cells[0].outputs[0]["text"] == "passed\n"
    assert new_notebook.cells[0].outputs[1]["traceback"] == ["Error: bad"]


def test_mask_timestamps():
    notebook = make_notebook("run at 2026-07-19 17:49:28.123 done\n")
    new_notebook = mask_timestamps(notebook)
    assert new_notebook.cells[0].outputs[0]["text"] == "run at DATE TIME done\n"


def test_mask_timestamps_iso():
    notebook = make_notebook("at 2026-07-19T17:49:28Z end\n")
    new_notebook = mask_timestamps(notebook)
    assert new_notebook.cells[0].outputs[0]["text"] == "at DATE TIMEZ end\n"


def test_mask_memory_addresses():
    notebook = make_notebook("<MyClass object at 0x7f2ec08a13a0>\n")
    new_notebook = mask_memory_addresses(notebook)
    assert new_notebook.cells[0].outputs[0]["text"] == "<MyClass object at 0xADDRESS>\n"


def test_mask_uuids():
    notebook = make_notebook("id: 123e4567-e89b-12d3-a456-426614174000\n")
    new_notebook = mask_uuids(notebook)
    assert new_notebook.cells[0].outputs[0]["text"] == "id: UUID\n"


def test_collapse_whitespace():
    notebook = make_notebook("   a    b\nc  \nd\n")
    new_notebook = collapse_whitespace(notebook)
    assert new_notebook.cells[0].outputs[0]["text"] == " a b\nc\nd\n"


def test_notebook_unchanged():
    """Test that the input notebook is not mutated."""
    notebook = make_notebook("\x1b[32mpassed\x1b[0m\n")
    strip_ansi(notebook)
    assert notebook.cells[0].outputs[0]["text"] == "\x1b[32mpassed\x1b[0m\n"
