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
    """A subclass of ``nbconvert.ExecutePreprocessor`` that logs per cell execution."""

    def preprocess_cell(self, cell, resources, cell_index):
        """Execute a single code cell.

        See base.py for details.

        To execute all cells see :meth:`preprocess`.
        """
        if cell.cell_type != "code" or not cell.source.strip():
            return cell, resources

        logger.info(f"Executing cell {cell_index}")

        reply, outputs = self.run_cell(cell, cell_index)
        # Backwards compatability for processes that wrap run_cell
        cell.outputs = outputs

        cell_allows_errors = (
            self.allow_errors or "raises-exception" in cell.metadata.get("tags", [])
        )

        if self.force_raise_errors or not cell_allows_errors:
            for out in cell.outputs:
                if out.output_type == "error":
                    raise CellExecutionError.from_cell_and_msg(cell, out)
            if (reply is not None) and reply["content"]["status"] == "error":
                raise CellExecutionError.from_cell_and_msg(cell, reply["content"])
        return cell, resources


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
