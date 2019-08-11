"""Jupyter Notebook Regression Test Class."""
import copy
import os
import re
import sys
from typing import List, TextIO, Union

import attr
from attr.validators import instance_of
from nbdime.diff_format import DiffEntry
import nbformat
from nbformat import NotebookNode

from pytest_notebook.diffing import diff_notebooks, diff_to_string, filter_diff
from pytest_notebook.execution import execute_notebook
from pytest_notebook.notebook import load_notebook_with_config, regex_replace_nb
from pytest_notebook.post_processors import (
    ENTRY_POINT_NAME,
    list_processor_names,
    load_processor,
)
from pytest_notebook.utils import autodoc

HELP_EXEC_CWD = (
    "Path to the directory which the notebook will run in "
    "(defaults to directory of notebook)."
)
HELP_EXEC_TIMEOUT = "The maximum time to wait (in seconds) for execution of each cell."
HELP_EXEC_ALLOW_ERRORS = (
    "Do not stop execution after the first unexpected exception "
    "(where cell is not tagged ``raises-exception``)."
)
HELP_DIFF_REPLACE = (
    "A list of regex replacements to apply before diffing, "
    r"e.g. ``[('/cells/*/outputs', '\d{2,4}-\d{1,2}-\d{1,2}', 'DATE-STAMP')]``."
)
HELP_DIFF_IGNORE = (
    "List of diff paths to ignore, e.g. '/cells/1/outputs' or '/cells/\\*/metadata'."
)
HELP_DIFF_USE_COLOR = "Use ANSI color code escapes for text output."
HELP_DIFF_COLOR_WORDS = "Highlight changed words using only colors."
HELP_FORCE_REGEN = (
    "Re-generate notebook files, if no unexpected execution errors, "
    "and an output path has been supplied."
)
HELP_POST_PROCS = (
    "post-processors to apply to the new workbook, "
    f"relating to entry points in the '{ENTRY_POINT_NAME}' group"
)


class NBRegressionError(Exception):
    """Exception to signal a regression test fail."""


@autodoc
@attr.s(frozen=True, slots=True, repr=False)
class NBRegressionResult:
    """A class to store the result of ``NBRegressionFixture.check``."""

    nb_initial: NotebookNode = attr.ib(
        validator=instance_of(NotebookNode), metadata={"help": "Initial notebook."}
    )
    nb_final: NotebookNode = attr.ib(
        validator=instance_of(NotebookNode),
        metadata={"help": "Notebook after execution and post-processing."},
    )

    diff_full: List[DiffEntry] = attr.ib(
        metadata={"help": "Full diff of initial/final notebooks."}
    )
    diff_filtered: List[DiffEntry] = attr.ib(
        metadata={
            "help": (
                "Diff of initial/final notebooks, "
                "filtered according to the parsed configuration."
            )
        }
    )
    diff_string: str = attr.ib(
        validator=instance_of(str),
        metadata={"help": "The formatte string of diff_filtered."},
    )

    def __repr__(self):
        """Represent the class instance."""
        return (
            f"NBRegressionResult(diff_full_length={len(self.diff_full)},"
            f"diff_filtered_length={len(self.diff_filtered)})"
        )


@autodoc
@attr.s
class NBRegressionFixture:
    """Class to perform Jupyter Notebook Regression tests."""

    exec_cwd: Union[str, None] = attr.ib(None, metadata={"help": HELP_EXEC_CWD})

    @exec_cwd.validator
    def _validate_exec_cwd(self, attribute, value):
        if value is None:
            return
        if not isinstance(value, str):
            raise TypeError("exec_cwd must be None or a string")
        if not os.path.isdir(value):
            raise IOError("exec_cwd='{}' is not an existing directory".format(value))

    exec_allow_errors: bool = attr.ib(
        False, instance_of(bool), metadata={"help": HELP_EXEC_ALLOW_ERRORS}
    )
    exec_timeout: int = attr.ib(120, metadata={"help": HELP_EXEC_TIMEOUT})

    @exec_timeout.validator
    def _validate_exec_timeout(self, attribute, value):
        if not isinstance(value, int):
            raise TypeError("exec_timeout must be an integer")
        if value <= 0:
            raise ValueError("exec_timeout must be larger than 0")

    post_processors: tuple = attr.ib(
        ("coalesce_streams",), metadata={"help": HELP_POST_PROCS}
    )

    @post_processors.validator
    def _validate_post_processors(self, attribute, values):
        if not isinstance(values, tuple):
            raise TypeError(f"post_processors must be a tuple: {values}")
        for name in values:
            if name not in list_processor_names():
                raise TypeError(
                    f"name '{name}' not found in entry points: {list_processor_names()}"
                )

    post_proc_resources: dict = attr.ib(
        attr.Factory(dict),
        instance_of(dict),
        metadata={"help": "Resources to parse to post processor functions."},
    )

    diff_replace: tuple = attr.ib((), metadata={"help": HELP_DIFF_REPLACE})

    @diff_replace.validator
    def _validate_diff_replace(self, attribute, values):
        if not isinstance(values, tuple):
            raise TypeError(f"diff_replace must be a tuple: {values}")
        for i, args in enumerate(values):
            if not isinstance(args, tuple):
                raise TypeError(f"diff_replace[{i}] must be a tuple: {args}")

            if not isinstance(args[0], str):
                raise TypeError(f"diff_replace[{i}] address '{args[0]}' must a string")
            if not args[0].startswith("/"):
                raise ValueError(
                    f"diff_ignore[{i}] address '{args[0]}' must start with '/'"
                )
            if not isinstance(args[1], str):
                raise TypeError(f"diff_replace[{i}] regex '{args[1]}' must a string")
            try:
                re.compile(args[1])
            except Exception as err:
                raise TypeError(
                    f"diff_replace[{i}] '{args[1]}' is not a valid regex: {err}"
                )
            if not isinstance(args[2], str):
                raise TypeError(
                    f"diff_replace[{i}] replacement '{args[2]}' must a string"
                )

    diff_ignore: tuple = attr.ib(
        # TODO replace this default with a diff_replace one?
        ("/cells/*/outputs/*/traceback",),
        metadata={"help": HELP_DIFF_IGNORE},
    )

    @diff_ignore.validator
    def _validate_diff_ignore(self, attribute, values):
        if not isinstance(values, tuple):
            raise TypeError(f"diff_ignore must be a tuple: {values}")
        for item in values:
            if not isinstance(item, str):
                raise TypeError(f"diff_ignore item '{item}' must a strings")
            if not item.startswith("/"):
                raise ValueError(f"diff_ignore item '{item}' must start with '/'")

    diff_use_color: bool = attr.ib(
        True, instance_of(bool), metadata={"help": HELP_DIFF_USE_COLOR}
    )
    diff_color_words: bool = attr.ib(
        False, instance_of(bool), metadata={"help": HELP_DIFF_COLOR_WORDS}
    )

    force_regen: bool = attr.ib(
        False, instance_of(bool), metadata={"help": HELP_FORCE_REGEN}
    )

    def __setattr__(self, key, value):
        """Add validation when setting attributes."""
        x_attr = getattr(attr.fields(self.__class__), key)
        if x_attr.validator:
            x_attr.validator(self, x_attr, value)

        super(NBRegressionFixture, self).__setattr__(key, value)

    def check(
        self, path: Union[TextIO, str], raise_errors: bool = True
    ) -> NBRegressionResult:
        """Execute the Notebook and compare its initial vs. final contents.

        if ``force_regen`` is True, the new notebook will be written to ``path``

        if ``raise_errors`` is True:

        :raise nbconvert.preprocessors.CellExecutionError: if error in execution
        :raise NBConfigValidationError: if the notebook metadata is invalid
        :raise NBRegressionError: if diffs present

        :rtype: NBRegressionResult

        """
        __tracebackhide__ = True
        if hasattr(path, "name"):
            abspath = os.path.abspath(path.name)
        else:
            abspath = os.path.abspath(str(path))

        nb_initial, nb_config = load_notebook_with_config(path)

        if not self.exec_cwd:
            self.exec_cwd = os.path.dirname(abspath)
        exec_error, nb_final = execute_notebook(
            nb_initial,
            cwd=self.exec_cwd,
            timeout=self.exec_timeout,
            allow_errors=self.exec_allow_errors,
        )

        resources = copy.deepcopy(self.post_proc_resources)
        for proc_name in self.post_processors:
            post_proc = load_processor(proc_name)
            nb_final, resources = post_proc(nb_final, resources)

        if self.diff_replace:
            nb_initial_replace = regex_replace_nb(nb_initial, self.diff_replace)
            nb_final_replace = regex_replace_nb(nb_final, self.diff_replace)
        else:
            nb_initial_replace = nb_initial
            nb_final_replace = nb_final

        full_diff = diff_notebooks(nb_initial_replace, nb_final_replace)

        diff_ignore = copy.deepcopy(nb_config.diff_ignore)
        diff_ignore.update(self.diff_ignore)
        filtered_diff = filter_diff(full_diff, diff_ignore)

        diff_string = diff_to_string(
            nb_initial_replace,
            filtered_diff,
            use_color=self.diff_use_color,
            color_words=self.diff_color_words,
        )
        # TODO optionally write diff to file

        regen_exc = None
        if filtered_diff and self.force_regen and not exec_error:

            if hasattr(path, "close") and hasattr(path, "name"):
                path.close()
                with open(path.name, "w") as handle:
                    nbformat.write(nb_final, handle)
            else:
                nbformat.write(nb_final, str(path))

            regen_exc = NBRegressionError(
                f"Files differ and --nb-force-regen set, "
                f"regenerating file at:\n- {abspath}"
            )

        if not raise_errors:
            pass
        elif exec_error:
            print("Diff up to exception:\n" + diff_string, file=sys.stderr)
            raise exec_error
        elif regen_exc:
            print("Diff before regeneration:\n" + diff_string, file=sys.stderr)
            raise regen_exc
        elif filtered_diff:
            raise NBRegressionError(diff_string)

        return NBRegressionResult(
            nb_initial, nb_final, full_diff, filtered_diff, diff_string
        )
