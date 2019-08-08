"""Jupyter Notebook Regression Test Class."""
import copy
import os
from typing import List, TextIO, Union

import attr
from attr.validators import instance_of
from nbconvert.preprocessors import CellExecutionError
import nbformat
from nbformat import NotebookNode

from pytest_notebook.diffing import diff_notebooks, diff_to_string, filter_diff
from pytest_notebook.execution import execute_notebook
from pytest_notebook.post_processors import (
    ENTRY_POINT_NAME,
    list_processor_names,
    load_processor,
)
from pytest_notebook.utils import autodoc

HELP_EXEC_CWD = "Path to the directory which the notebook will run in."
HELP_EXEC_TIMEOUT = "The maximum time to wait (in seconds) for execution of each cell."
HELP_EXEC_ALLOW_ERRORS = (
    "Do not stop execution after the first unexpected exception "
    "(where cell is not tagged ``raises-exception``)."
)
HELP_DIFF_IGNORE = (
    "List of diff paths to ignore, e.g. '/cells/1/outputs' or '/cells/\\*/metadata'."
)
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

    diff_ignore: tuple = attr.ib(
        ("/cells/*/outputs/*/traceback",), metadata={"help": HELP_DIFF_IGNORE}
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
    ) -> (NotebookNode, List, Union[None, CellExecutionError]):
        """Execute the Notebook and compare its old/new contents.

        if self.force_regen is True, the new notebook will be written to path

        :raise nbconvert.preprocessors.CellExecutionError: if error in execution
        :raise NBRegressionError: if diffs present

        """
        __tracebackhide__ = True
        nb_initial = nbformat.read(path, as_version=4)
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

        regen_exc = None
        if self.force_regen and not exec_error:
            if hasattr(path, "close") and hasattr(path, "name"):
                path.close()
                with open(path.name, "w") as handle:
                    nbformat.write(nb_final, handle)
                abspath = os.path.abspath(path.name)
            else:
                nbformat.write(nb_final, str(path))
                abspath = os.path.abspath(str(path))
            regen_exc = NBRegressionError(
                "--nb-force-regen set, regenerating file at: {}".format(abspath)
            )

        diff = diff_notebooks(nb_initial, nb_final)

        # TODO include filters from metadata nb/cells
        diff = filter_diff(diff, self.diff_ignore)

        if not raise_errors:
            pass
        elif diff:
            # TODO optionally write diff to file
            try:
                raise NBRegressionError(diff_to_string(nb_initial, diff))
            except NBRegressionError:
                if regen_exc:
                    raise regen_exc
                raise
        elif regen_exc:
            raise regen_exc
        elif exec_error:
            raise exec_error

        return nb_final, diff, exec_error
