"""Execution of notebooks."""
import copy
import logging
import shutil
import tempfile
from typing import Tuple, Union

from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
from nbformat import NotebookNode

logger = logging.getLogger(__name__)


class ExecutePreprocessorLogging(ExecutePreprocessor):
    """A subclass of ``nbconvert.ExecutePreprocessor`` with additional logging."""

    def preprocess(self, nb, resources, km=None):
        """Preprocess notebook executing each code cell."""
        logger.info(f"About to execute notebook with {len(nb.cells)} cells")
        return super().preprocess(nb, resources, km)

    def preprocess_cell(self, cell, resources, cell_index):
        """Execute a single code cell."""
        if cell.cell_type == "code" and cell.source.strip():
            logger.info(f"Executing cell {cell_index}")
        return super().preprocess_cell(cell, resources, cell_index)


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
    proc = ExecutePreprocessorLogging(timeout=timeout, allow_errors=allow_errors)

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
