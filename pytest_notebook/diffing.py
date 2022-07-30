"""Diffing of notebooks."""
import copy
import operator
import re
from typing import List, Sequence, Union

from nbdime.diff_format import DiffEntry, SequenceDiffBuilder
from nbdime.diffing.generic import default_differs, default_predicates, diff
from nbdime.diffing.notebooks import diff_attachments, diff_single_outputs
from nbdime.prettyprint import PrettyPrintConfig, pretty_print_diff
from nbdime.utils import defaultdict2, join_path, split_path
from nbformat import NotebookNode

# TODO nbdime is currently hard coded to version 4 notebooks,
# this should be reviewed in new releases


def diff_sequence_simple(
    initial: Sequence,
    final: Sequence,
    path: str = "",
    predicates: Union[None, dict] = None,
    differs: Union[None, dict] = None,
) -> dict:
    """Compute diff of two lists with configurable behaviour.

    If the lists are of different lengths,
    we assume that items have been appended or removed from the end of the initial list.

    """

    if predicates is None:
        predicates = default_predicates()
    if differs is None:
        differs = default_differs()

    subpath = "/".join((path, "*"))
    diffit = differs[subpath]

    di = SequenceDiffBuilder()

    max_length = max(len(initial), len(final))
    for i, (aval, bval) in enumerate(zip(initial[:max_length], final[:max_length])):

        # if a/bval are outputs and the output_type's are different the diff will fail
        if isinstance(aval, dict) and isinstance(bval, dict):
            if aval.get("output_type", None) != bval.get("output_type", None):
                di.removerange(i, 1)
                di.addrange(i, [bval])
                continue

        cd = diffit(aval, bval, path=subpath, predicates=predicates, differs=differs)
        if cd:
            di.patch(i, cd)

    if len(initial) > len(final):
        di.removerange(len(initial), len(initial) - len(final))
    if len(initial) < len(final):
        di.addrange(len(initial), final[len(initial) :])

    return di.validated()


def diff_notebooks(
    initial: NotebookNode, final: NotebookNode, initial_path: str = ""
) -> List[DiffEntry]:
    """Compare two notebooks.

    This is a simplified version of ``nbdime.diff_notebooks()``, where we replace
    ``nbdime.diff_sequence_multilevel()`` with ``diff_sequence_simple()``
    to diff the cell and output lists.
    ``diff_sequence_multilevel`` use 'snakes' computation, to guess where cells have
    been inserted/removed. However, this can lead to longer diffs, where cells with
    changed outputs are assigned as removed/inserted, rather than simply modified.
    Moreover, since we are comparing the same notebook before/after execution,
    we shouldn't need to worry about insertions.

    """
    return diff(
        initial,
        final,
        path=initial_path,
        predicates=defaultdict2(lambda: [operator.__eq__], {}),
        differs=defaultdict2(
            lambda: diff,
            {
                "/cells": diff_sequence_simple,
                "/cells/*": diff,
                "/cells/*/outputs": diff_sequence_simple,
                "/cells/*/outputs/*": diff_single_outputs,
                "/cells/*/attachments": diff_attachments,
            },
        ),
    )


R_IS_INT = re.compile(r"^[-+]?\d+$")


def star_path(path):
    """Replace integers and integer-strings in a path with * ."""
    path = list(path)[:]
    for i, p in enumerate(path):
        if isinstance(p, int):
            path[i] = "*"
        else:
            if not isinstance(p, str):
                p = p.decode()
            if R_IS_INT.match(p):
                path[i] = "*"
    return path


def filter_diff(
    diff: List[DiffEntry], remove_paths: List[str], path: str = ""
) -> List[DiffEntry]:
    r"""Filter a notebook diff object, removing a list of paths.

    Paths are joined by '/' and may be starred, e.g. '/cells/\*/outputs'.
    """

    if isinstance(diff, list):
        new_diffs = []
        for dct in diff:
            output = filter_diff(dct, remove_paths, path)
            if output is not None:
                new_diffs.append(output)
        return new_diffs
    elif isinstance(diff, dict):
        path = "{}/{}".format(path, diff["key"])

        path_elements = split_path(path)
        for i in reversed(range(len(path_elements))):
            # iteratively star more elements from the right side
            new_path = join_path(path_elements[:i] + star_path(path_elements[i:]))
            if any(new_path.startswith(p) for p in remove_paths):
                return None

        new_diff = copy.deepcopy(diff)

        if "diff" in new_diff:
            sub_diffs = []
            for sub_diff in new_diff["diff"]:
                output = filter_diff(sub_diff, remove_paths, path)
                if output is not None:
                    sub_diffs.append(output)
            if sub_diffs:
                new_diff["diff"] = sub_diffs
            else:
                new_diff = None
        return new_diff
    return diff


def diff_to_string(
    notebook: NotebookNode,
    diff_obj: dict,
    use_git: bool = True,
    use_diff: bool = True,
    use_color: bool = True,
    color_words: bool = False,
) -> str:
    """Convert diff to formatted string.

    :param use_git: use git for formatting diff/merge text output
    :param use_diff: use diff/diff3 for formatting diff/merge text output
    :param use_color: whether to prevent use of ANSI color code escapes for text output
    :param color_words: whether to pass the --color-words flag
                        to any internal calls to git diff
    """

    class Printer:
        def __init__(self):
            self.string = "\n--- expected\n+++ obtained\n"

        def write(self, text):
            self.string += text

    printer = Printer()

    config = PrettyPrintConfig(
        out=printer,
        color_words=color_words,
        use_git=use_git,
        use_diff=use_diff,
        use_color=use_color,
    )

    pretty_print_diff(notebook, diff_obj, "", config)

    return printer.string
