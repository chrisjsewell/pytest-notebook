"""Plugins to post process notebooks.

All functions should take a notebook as input and output a new notebook.
"""
import copy
import functools
import pkg_resources
import re

from nbformat import NotebookNode


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


def coalesce_streams(notebook: NotebookNode) -> NotebookNode:
    """Merge all stream outputs with shared names into single streams.

    This ensure deterministic outputs.

    Adapted from:
    https://github.com/computationalmodelling/nbval/blob/master/nbval/plugin.py

    :param list outputs: cell outputs being processed

    """
    RGX_CARRIAGERETURN = re.compile(r".*\r(?=[^\n])")
    RGX_BACKSPACE = re.compile(r"[^\n]\b")

    new_notebook = copy.deepcopy(notebook)

    for cell in new_notebook.cells:
        if "outputs" not in cell:
            continue

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

        cell.outputs = new_outputs

    return new_notebook
