"""Plugins to post process notebooks.

All functions should take (notebook, resources) as input,
and output a (new notebook, resources).
"""
import copy
import functools
import logging
import re
import textwrap
from typing import Tuple

from nbformat import NotebookNode
import pkg_resources

logger = logging.getLogger(__name__)

ENTRY_POINT_NAME = "nbreg.post_proc"


@functools.lru_cache()
def list_processor_names():
    """List entry point names for  post-processors."""
    return [ep.name for ep in pkg_resources.iter_entry_points(ENTRY_POINT_NAME)]


@functools.lru_cache()
def load_processor(name: str):
    """Get a post-processors for an entry point name."""
    matches = [
        ep
        for ep in pkg_resources.iter_entry_points(ENTRY_POINT_NAME)
        if ep.name == name
    ]
    if not matches:
        raise ValueError(
            "entry point '{}' for group '{}' not found".format(name, ENTRY_POINT_NAME)
        )
    return matches[0].load()


def document_processors():
    """Create formatted string of all preprocessor docstrings."""
    return "\n\n".join(
        [
            f"{n}:\n{textwrap.indent(load_processor(n).__doc__, '  ').rstrip()}"
            for n in sorted(list_processor_names())
        ]
    )


def cell_preprocessor(function):
    """Wrap a function to be executed on all cells of a notebook.

    The wrapped function should have these parameters:

    cell : NotebookNode cell
        Notebook cell being processed
    resources : dictionary
        Additional resources used in the conversion process.
    index : int
        Index of the cell being processed
    """

    @functools.wraps(function)
    def wrappedfunc(nb: NotebookNode, resources: dict) -> (NotebookNode, dict):
        new_nb = copy.deepcopy(nb)
        for index, cell in enumerate(new_nb.cells):
            new_nb.cells[index], resources = function(cell, resources, index)
        return new_nb, resources

    return wrappedfunc


RGX_CARRIAGERETURN = re.compile(r".*\r(?=[^\n])")
RGX_BACKSPACE = re.compile(r"[^\n]\b")


@cell_preprocessor
def coalesce_streams(
    cell: NotebookNode, resources: dict, index: int
) -> Tuple[NotebookNode, dict]:
    """Merge all stream outputs with shared names into single streams.

    This ensure deterministic outputs.

    Adapted from:
    https://github.com/computationalmodelling/nbval/blob/master/nbval/plugin.py.
    """

    if "outputs" not in cell:
        return cell, resources

    new_outputs = []
    streams = {}
    for output in cell.outputs:
        if output.output_type == "stream":
            if output.name in streams:
                streams[output.name].text += output.text
            else:
                new_outputs.append(output)
                streams[output.name] = output
        else:
            new_outputs.append(output)

    # process \r and \b characters
    for output in streams.values():
        old = output.text
        while len(output.text) < len(old):
            old = output.text
            # Cancel out anything-but-newline followed by backspace
            output.text = RGX_BACKSPACE.sub("", output.text)
        # Replace all carriage returns not followed by newline
        output.text = RGX_CARRIAGERETURN.sub("", output.text)

    # We also want to ensure stdout and stderr are always in the same consecutive order,
    # because they are asynchronous, so order isn't guaranteed.
    for i, output in enumerate(new_outputs):
        if output.output_type == "stream" and output.name == "stderr":
            if (
                len(new_outputs) >= i + 2
                and new_outputs[i + 1].output_type == "stream"
                and new_outputs[i + 1].name == "stdout"
            ):
                stdout = new_outputs.pop(i + 1)
                new_outputs.insert(i, stdout)

    cell.outputs = new_outputs

    return cell, resources


@cell_preprocessor
def blacken_code(
    cell: NotebookNode, resources: dict, index: int
) -> Tuple[NotebookNode, dict]:
    """Format python source code with black (see https://black.readthedocs.io)."""
    try:
        import black
    except ImportError:
        raise ImportError("black not installed: see https://black.readthedocs.io")

    if cell.get("cell_type", None) != "code":
        return cell, resources

    # TODO use metadata to set target versions and whether to raise on exceptions
    # i.e. black.FileMode(target_versions, {black.TargetVersion.PY36})
    try:
        cell.source = black.format_str(cell.source, mode=black.FileMode())
    except (SyntaxError, black.InvalidInput):
        logger.debug(f"cell {index} could not be formatted by black.")

    # code cells don't require a trailing new line
    cell.source = cell.source.rstrip()

    return cell, resources


@cell_preprocessor
def beautifulsoup(
    cell: NotebookNode, resources: dict, index: int
) -> Tuple[NotebookNode, dict]:
    """Format text/html and image/svg+xml outputs with beautiful-soup.

    See: https://beautiful-soup-4.readthedocs.io.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "bs4 not installed: see https://beautiful-soup-4.readthedocs.io"
        )

    if cell.get("cell_type", None) != "code":
        return cell, resources

    if "outputs" not in cell:
        return cell, resources

    for i, output in enumerate(cell.outputs):
        if output.output_type not in ["execute_result", "display_data"]:
            continue
        for mimetype, value in output.get("data", {}).items():
            if mimetype not in ["text/html", "image/svg+xml"]:
                continue
            path = f"/cells/{index}/outputs/{i}/{mimetype}"
            # TODO use metadata to set builder and whether to raise on exceptions
            try:
                output["data"][mimetype] = BeautifulSoup(
                    output["data"][mimetype], "html.parser"
                ).prettify()
                # record which paths have been formatted (mainly for testing)
                resources.setdefault("beautifulsoup", []).append(path)
            except Exception:  # TODO what exceptions might be raised?
                logger.debug(f"{path} could not be formatted by beautiful-soup.")

    return cell, resources
