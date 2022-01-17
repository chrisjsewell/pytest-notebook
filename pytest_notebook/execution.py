"""Execution of notebooks."""
from contextlib import nullcontext
import copy
import json
import logging
from pathlib import Path
import tempfile
from textwrap import dedent
from typing import List, Optional, Union

import attr
from attr.validators import instance_of
from nbclient.client import CellExecutionError, NotebookClient, ensure_async
from nbclient.exceptions import CellTimeoutError
from nbclient.util import run_sync
from nbformat import NotebookNode
import traitlets

from pytest_notebook.notebook import create_cell
from pytest_notebook.utils import autodoc

logger = logging.getLogger(__name__)

HELP_COVERAGE = "Record coverage data, with coverage.py."
HELP_COVERAGE_CONFIG = "Determines what coverage configuration file to read."
HELP_COVERAGE_SOURCE = "A list of file paths or package names to measure coverage for."

COVERAGE_KEY = "coverage_data"


def coverage_code_setup(
    source: Optional[str], config_file: Union[None, str, Path]
) -> str:
    source = f"{source!r}" if source else "None"
    config_file = f"{config_file!r}" if config_file else "None"
    return dedent(
        f"""\
        import coverage as __coverage
        __cov = __coverage.Coverage(
            data_file=None,
            source={source},
            config_file={config_file},
            # auto_data=True,
            data_suffix=True,
            )
        # __cov.load()
        __cov.start()
        __cov._warn_no_data = False
        __cov._warn_unimported_source = False
        """
    )


def coverage_code_teardown() -> str:
    return dedent(
        """\
        import json
        __cov.stop()
        # __cov.save()
        data = __cov.get_data()
        print(json.dumps({name: data.lines(name) for name in data.measured_files()}))
        """
    )


class CoverageNotebookClient(NotebookClient):
    """A NotebookClient that records coverage data.

    Code coverage is recorded using coverage.py:

    - Before running any cells, we run a mock cell, containing coverage setup code.
    - After execution, we run a mock cell, containing code to teardown the coverage,
      and print the coverage data to ``/cell/output/0/text``.
    - Coverage data is then saved in resources["coverage_data"]

    :raises CoverageError: If a coverage cell execution errors.
    """

    coverage = traitlets.Bool(default_value=False, help=HELP_COVERAGE).tag(config=True)
    cov_config_file = traitlets.Unicode(
        default_value=None, allow_none=True, help=HELP_COVERAGE_CONFIG
    ).tag(config=True)
    cov_source = traitlets.List(
        traitlets.Unicode(),
        default_value=None,
        allow_none=True,
        help=HELP_COVERAGE_SOURCE,
    ).tag(config=True)

    async def async_execute(self, reset_kc: bool = False, **kwargs) -> NotebookNode:
        if reset_kc and self.owns_km:
            await self._async_cleanup_kernel()
        self.reset_execution_trackers()

        async with self.async_setup_kernel(**kwargs):
            assert self.kc is not None
            self.log.info("Executing notebook with kernel: %s" % self.kernel_name)
            msg_id = await ensure_async(self.kc.kernel_info())
            info_msg = await self.async_wait_for_reply(msg_id)
            if info_msg is not None:
                if "language_info" in info_msg["content"]:
                    self.nb.metadata["language_info"] = info_msg["content"][
                        "language_info"
                    ]
                else:
                    raise RuntimeError(
                        'Kernel info received message content has no "language_info" key. '
                        "Content is:\n" + str(info_msg["content"])
                    )
            if self.coverage and self.kernel_name.startswith("python"):
                await self.coverage_setup()
            for index, cell in enumerate(self.nb.cells):
                await self.async_execute_cell(
                    cell, index, execution_count=self.code_cells_executed + 1
                )
            self.set_widgets_metadata()
            if self.coverage and self.kernel_name.startswith("python"):
                await self.coverage_teardown()

        return self.nb

    execute = run_sync(async_execute)

    async def coverage_setup(self) -> None:
        """Set up coverage, by executing a code cell."""
        self.log.info("Recording coverage for notebook")
        source = coverage_code_setup(self.cov_source, self.cov_config_file)
        cell = create_cell(source, cell_type="code", as_version=self.nb.nbformat)
        self.nb.cells.insert(0, cell)
        allow_error = self.allow_errors
        self.allow_errors = True
        try:
            await self.async_execute_cell(cell, 0, execution_count=None)
        finally:
            self.allow_errors = allow_error
            self.nb.cells.pop(0)
            self.code_cells_executed = 0
        for out in cell.outputs or []:
            if out.output_type == "error":
                raise CoverageError.from_cell_output("start-up", out)

    async def coverage_teardown(self) -> str:
        """Tear down coverage, by executing a code cell."""
        self.log.info("Recording coverage for notebook")
        source = coverage_code_teardown()
        cell = create_cell(source, cell_type="code", as_version=self.nb.nbformat)
        self.nb.cells.append(cell)
        allow_error = self.allow_errors
        self.allow_errors = True
        try:
            await self.async_execute_cell(
                cell, len(self.nb.cells) - 1, execution_count=None
            )
        finally:
            self.allow_errors = allow_error
            self.nb.cells.pop()
            self.code_cells_executed = 0
        for out in cell.outputs or []:
            if out.output_type == "error":
                raise CoverageError.from_cell_output("teardown", out)
        if (
            len(cell.outputs) != 1
            or cell.outputs[0]["output_type"] != "stream"
            or cell.outputs[0]["name"] != "stdout"
        ):
            raise CoverageError(
                "The teardown coverage cell did not produce the expected output: "
                f"{cell.outputs}"
            )
        self.resources[COVERAGE_KEY] = cell.outputs[0]["text"]


class CoverageError(Exception):
    """Exception for errors involving coverage."""

    @classmethod
    def from_exec_reply(cls, phase, reply):
        """Instantiate from an execution reply."""
        return cls(
            f"An error occurred while executing coverage {phase}:\n"
            f"{reply['content']}"
        )

    @classmethod
    def from_cell_output(cls, phase, output):
        """Instantiate from a code cell output."""
        traceback = "\n".join(output.get("traceback", []))
        return cls(
            f"An error occurred while executing coverage {phase}:\n"
            f"{traceback}\n"
            f"{output.get('ename', '<Error>')}: { output.get('evalue', '')}"
        )


@autodoc
@attr.s(frozen=True, slots=True)
class ExecuteResult:
    """Result of notebook execution."""

    exec_error: Union[None, Exception] = attr.ib(
        validator=instance_of((type(None), Exception)),
        metadata={"help": "Execution exception."},
    )
    notebook: NotebookNode = attr.ib(
        validator=instance_of(NotebookNode), metadata={"help": "Executed notebook."}
    )
    resources: dict = attr.ib(
        validator=instance_of(dict), metadata={"help": "Resources dictionary."}
    )

    @property
    def has_coverage(self):
        """Return whether coverage information is available."""
        return COVERAGE_KEY in self.resources

    def coverage_data(self, debug=None, no_disk=True):
        """Return coverage.py coverage data as `coverage.CoverageData`."""
        coverage_str = self.resources.get(COVERAGE_KEY, None)
        if not coverage_str:
            return None
        from coverage import CoverageData

        coverage_data = CoverageData(debug=debug, no_disk=no_disk)
        coverage_data.add_lines(json.loads(coverage_str))
        return coverage_data

    @property
    def coverage_dict(self) -> dict:
        """Return coverage.py coverage data as a dict."""
        coverage_str = self.resources.get(COVERAGE_KEY, None)
        if not coverage_str:
            return None
        return json.loads(coverage_str)


def execute_notebook(
    notebook: NotebookNode,
    *,
    resources: Union[dict, None] = None,
    cwd: Union[str, None] = None,
    timeout: int = 120,
    allow_errors: bool = False,
    with_coverage: bool = False,
    cov_config_file: Union[str, None] = None,
    cov_source: Union[List[str], None] = None,
) -> ExecuteResult:
    """Execute a notebook.

    :param cwd: Path to the directory which the notebook will run in
        (default is temporary directory).
    :param timeout: The maximum time to wait (in seconds) for execution of each cell.
    :param allow_errors: If False, execution is stopped after the first unexpected
        exception (cells tagged ``raises-exception`` are expected)
    :param with_coverage: Record code coverage with coverage.py
    :param cov_config_file: Determines what coverage configuration file to read.
    :param cov_source: A list of file paths or package names to measure coverage for.

    :returns: (exception or None, new_notebook, resources)

    """
    new_notebook = copy.deepcopy(notebook)
    resources = resources or {}
    cwd_context = nullcontext(cwd) if cwd is not None else tempfile.TemporaryDirectory()
    exec_error = None
    with cwd_context as cwd_dir:
        resources.setdefault("metadata", {})["path"] = cwd_dir
        client = CoverageNotebookClient(
            new_notebook,
            timeout=timeout,
            allow_errors=allow_errors,
            log=logger,
            resources=resources,
            record_timing=False,
            coverage=with_coverage,
            cov_config_file=cov_config_file,
            cov_source=cov_source,
        )
        try:
            client.execute()
        except (CellExecutionError, CellTimeoutError, CoverageError) as err:
            exec_error = err

    return ExecuteResult(exec_error, new_notebook, resources)
