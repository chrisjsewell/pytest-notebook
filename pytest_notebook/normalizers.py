"""Plugins to normalize notebooks before diffing.

Unlike post-processors (which are applied only to the notebook produced
by execution), normalizers are applied to *both* the stored and the executed
notebook, before they are diffed.
They are intended to remove insignificant differences in outputs,
such as ANSI colour codes, timestamps and memory addresses.

All functions should take a notebook as input, and output a new notebook.
"""

import functools
from importlib.metadata import entry_points

from nbformat import NotebookNode

from pytest_notebook.notebook import regex_replace_nb

ENTRY_POINT_NAME = "nbreg.diff_normalize"

TEXT_PATHS = (
    "/cells/*/outputs/*/text",
    "/cells/*/outputs/*/data/text/plain",
)
ERROR_PATHS = (
    "/cells/*/outputs/*/traceback",
    "/cells/*/outputs/*/evalue",
)

RGX_ANSI = r"\x1b\[[0-9;?]*[a-zA-Z]"
RGX_DATE = r"\b\d{4}-\d{2}-\d{2}\b"
RGX_TIME = r"\b\d{1,2}:\d{2}:\d{2}(\.\d+)?\b"
RGX_MEMORY_ADDRESS = r"\b0x[0-9a-fA-F]{4,}\b"
RGX_UUID = (
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


@functools.lru_cache
def list_normalizer_names():
    """List entry point names for diff normalizers."""
    return [ep.name for ep in entry_points().select(group=ENTRY_POINT_NAME)]


@functools.lru_cache
def load_normalizer(name: str):
    """Get a diff normalizer for an entry point name."""
    try:
        (entry_point,) = entry_points().select(group=ENTRY_POINT_NAME, name=name)
    except ValueError:
        raise ValueError(
            f"entry point '{name}' for group '{ENTRY_POINT_NAME}' not found"
        )
    return entry_point.load()


def strip_ansi(notebook: NotebookNode) -> NotebookNode:
    """Remove ANSI escape sequences from text outputs and tracebacks."""
    return regex_replace_nb(
        notebook,
        [(path, RGX_ANSI, "") for path in TEXT_PATHS + ERROR_PATHS],
    )


def mask_timestamps(notebook: NotebookNode) -> NotebookNode:
    """Replace dates (YYYY-MM-DD) and times (HH:MM:SS) in text outputs."""
    return regex_replace_nb(
        notebook,
        [(path, RGX_DATE, "DATE") for path in TEXT_PATHS]
        + [(path, RGX_TIME, "TIME") for path in TEXT_PATHS],
    )


def mask_memory_addresses(notebook: NotebookNode) -> NotebookNode:
    """Replace memory addresses (0x...) in text outputs and tracebacks."""
    return regex_replace_nb(
        notebook,
        [(path, RGX_MEMORY_ADDRESS, "0xADDRESS") for path in TEXT_PATHS + ERROR_PATHS],
    )


def mask_uuids(notebook: NotebookNode) -> NotebookNode:
    """Replace UUIDs in text outputs and tracebacks."""
    return regex_replace_nb(
        notebook,
        [(path, RGX_UUID, "UUID") for path in TEXT_PATHS + ERROR_PATHS],
    )


def collapse_whitespace(notebook: NotebookNode) -> NotebookNode:
    """Collapse runs of spaces/tabs, and remove trailing whitespace, in text outputs.

    This is useful for e.g. pandas DataFrame text representations,
    whose column-alignment whitespace can change between pandas versions.
    """
    return regex_replace_nb(
        notebook,
        [(path, r"[ \t]+(?=\n|$)", "") for path in TEXT_PATHS]
        + [(path, r"[ \t]{2,}", " ") for path in TEXT_PATHS],
    )
