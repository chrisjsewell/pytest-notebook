"""Execution of notebooks."""
import copy
import shutil
import tempfile
from typing import Tuple, Union

from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
from nbformat import NotebookNode


def execute_notebook(
    notebook: NotebookNode,
    cwd: Union[str, None] = None,
    timeout: int = 120,
    allow_errors: bool = False,
) -> Tuple[bool, NotebookNode]:
    """Execute a notebook.

    :param cwd: Path to the directory which the notebook will run in
        (default is temporary directory).
    :param timeout: The maximum time to wait (in seconds) for execution of each cell.
    :param allow_errors: If False, execution is stopped after the first unexpected
        exception (cells tagged ``raises-exception`` are expected)

    :returns: (errored, new_notebook)

    """
    new_notebook = copy.deepcopy(notebook)
    proc = ExecutePreprocessor(timeout=timeout, allow_errors=allow_errors)
    if not cwd:
        cwd_dir = tempfile.mkdtemp()
    resources = {
        "metadata": {"path": str(cwd) if cwd else cwd_dir}
    }  # metadata/path specifies the directory the kernel will run in
    exec_error = None
    try:
        proc.preprocess(new_notebook, resources)
    except CellExecutionError as err:
        exec_error = err
    finally:
        if not cwd:
            shutil.rmtree(cwd_dir)

    return exec_error, new_notebook
