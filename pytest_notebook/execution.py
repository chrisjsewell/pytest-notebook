"""Execution of notebooks."""
import copy
from io import StringIO
import json
import logging
import re
import shutil
import tempfile
from textwrap import dedent
from typing import List, Union

import attr
from attr.validators import instance_of
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
from nbformat import NotebookNode
import traitlets

from pytest_notebook.notebook import create_cell, DEFAULT_NB_VERSION
from pytest_notebook.utils import autodoc

logger = logging.getLogger(__name__)

HELP_COVERAGE = "Record coverage data, with coverage.py."
HELP_COVERAGE_CONFIG = "Determines what coverage configuration file to read."
HELP_COVERAGE_SOURCE = "A list of file paths or package names to measure coverage for."

COVERAGE_KEY = "coverage_data"


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


class ExecuteCoveragePreprocessor(ExecutePreprocessor):
    """A subclass of ``ExecutePreprocessor`` that can record python code coverage.

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

    def coverage_setup(self, nb_version):
        """Set up coverage, by running a code cell."""
        config_file = None
        if self.cov_config_file is not None:
            config_file = f'"{self.cov_config_file}"'
        reply, outputs = self.run_cell(
            # TODO: strictly we could set the data_file to a temporary file,
            # but there should never actually be any read/write access to it
            create_cell(
                dedent(
                    f"""\
                    import coverage as __coverage
                    __cov = __coverage.Coverage(
                        data_file=None,
                        source={self.cov_source},
                        config_file={config_file},
                        # auto_data=True,
                        data_suffix=True,
                        )
                    # __cov.load()
                    __cov.start()
                    __cov._warn_no_data = False
                    __cov._warn_unimported_source = False
                    """
                ),
                as_version=nb_version,
            ),
            store_history=False,
        )
        for out in outputs:
            if out.output_type == "error":
                raise CoverageError.from_cell_output("start-up", out)
        if (reply is not None) and reply["content"]["status"] == "error":
            raise CoverageError.from_exec_reply("start-up", reply)

    def coverage_teardown(self, nb_version, resources):
        """Teardown coverage, by running a code cell, and recording the output."""
        reply, outputs = self.run_cell(
            create_cell(
                dedent(
                    """\
                    from io import StringIO as __StringIO
                    __cov.stop()
                    # __cov.save()
                    __stream = __StringIO()
                    __cov.get_data().write_fileobj(__stream)
                    print(__stream.getvalue())
                    """
                ),
                as_version=nb_version,
            )
        )
        for output in outputs:
            if output.output_type == "error":
                raise CoverageError.from_cell_output("teardown", output)
        if (reply is not None) and reply["content"]["status"] == "error":
            raise CoverageError.from_exec_reply("teardown", reply)
        if (
            len(outputs) != 1
            or outputs[0]["output_type"] != "stream"
            or outputs[0]["name"] != "stdout"
        ):
            raise CoverageError(
                "The teardown coverage cell did not produce the expected output: "
                f"{outputs}"
            )
        resources[COVERAGE_KEY] = outputs[0]["text"]
        return resources

    def preprocess(self, nb, resources, km=None):
        """Preprocess notebook executing each code cell."""
        self.log.info(f"About to execute notebook with {len(nb.cells)} cells")
        if not resources:
            resources = {}
        nb_version = nb.get("nbformat", DEFAULT_NB_VERSION)

        with self.setup_preprocessor(nb, resources, km=km):
            self.log.info(f"Executing notebook with kernel: {self.kernel_name}")
            if self.coverage and self.kernel_name.startswith("python"):
                self.log.info("Recording coverage for notebook")
                self.coverage_setup(nb_version)
            try:
                nb, resources = super(ExecutePreprocessor, self).preprocess(
                    nb, resources
                )
            finally:
                if self.coverage and self.kernel_name.startswith("python"):
                    resources = self.coverage_teardown(nb_version, resources)
            info_msg = self._wait_for_reply(self.kc.kernel_info())
            nb.metadata["language_info"] = info_msg["content"]["language_info"]
            self.set_widgets_metadata()

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        """Execute a single code cell."""
        if cell.cell_type == "code" and cell.source.strip():
            self.log.info(f"Executing cell {cell_index}")
        return super().preprocess_cell(cell, resources, cell_index)


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

    def coverage_data(self, debug=None):
        """Return coverage.py coverage data as `coverage.CoverageData`."""
        coverage_str = self.resources.get(COVERAGE_KEY, None)
        if not coverage_str:
            return None
        from coverage import CoverageData

        coverage_data = CoverageData(debug=debug)
        coverage_data.read_fileobj(StringIO(coverage_str))
        return coverage_data

    @property
    def coverage_dict(self) -> dict:
        """Return coverage.py coverage data as a dict."""
        coverage_str = self.resources.get(COVERAGE_KEY, None)
        if not coverage_str:
            return None
        match = re.findall("^[^\\{]*(\\{.+\\})$", coverage_str)
        if match:
            return json.loads(match[0])


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
    proc = ExecuteCoveragePreprocessor(
        timeout=timeout,
        allow_errors=allow_errors,
        coverage=with_coverage,
        cov_config_file=cov_config_file,
        cov_source=cov_source,
        log=logger,
    )

    cwd_dir = cwd or tempfile.mkdtemp()
    resources = resources or {}
    # metadata/path specifies the directory the kernel will run in
    resources.setdefault("metadata", {})["path"] = str(cwd_dir)
    exec_error = None
    try:
        proc.preprocess(new_notebook, resources)
    except (CellExecutionError, CoverageError) as err:
        exec_error = err
    finally:
        if not cwd:
            shutil.rmtree(cwd_dir)

    return ExecuteResult(exec_error, new_notebook, resources)
