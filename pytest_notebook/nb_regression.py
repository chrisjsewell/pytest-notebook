"""Jupyter Notebook Regression Test Class."""
import base64
import copy
import difflib
import re
import shutil
import tempfile
from typing import Any, Sequence

import attr
from attr.validators import instance_of, deep_iterable
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
import nbformat
from nbformat import NotebookNode
import numpy
from PIL import Image, ImageChops
import ruamel.yaml as yaml
from six import BytesIO

from .utils import autodoc, mapping_to_dict

META_TAG_RAISES = "raises-exception"
META_TAG_SKIP_ALL = "nbreg-skip-all"
META_TAG_SKIP_OUTPUTS = "nbreg-skip-compare"

RGX_CARRIAGERETURN = re.compile(r".*\r(?=[^\n])")
RGX_BACKSPACE = re.compile(r"[^\n]\b")


def coalesce_streams(outputs: Sequence[NotebookNode]) -> Sequence[NotebookNode]:
    """Merge all stream outputs with shared names into single streams.

    This ensure deterministic outputs.

    Adapted from:
    https://github.com/computationalmodelling/nbval/blob/master/nbval/plugin.py

    :param list outputs: cell outputs being processed

    """
    if not outputs:
        return outputs

    new_outputs = []
    streams = {}
    for output in outputs:
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

    return new_outputs


class RegressionYamlDumper(yaml.RoundTripDumper):
    """Custom YAML dumper aimed for regression testing.

    The differences to the usual YAML dumper, is that it doesn't support aliases,
    as they produce confusing results on regression tests.

    Adapted from: https://github.com/ESSS/pytest-regressions

    """

    def ignore_aliases(self, data):
        """Set ignore aliases to True."""
        return True

    @classmethod
    def add_custom_yaml_representer(cls, data_type, representer_fn):
        """Add custom representer to regression YAML dumper.

        It is polymorphic, so it works also for subclasses of `data_type`.

        :param type data_type: Type of objects.
        :param callable representer_fn: Function that receives ``(dumper, data)``
            type as argument and must must return a YAML-convertible representation.
        """
        # Use multi-representer instead of simple-representer
        # because it supports polymorphism.
        yaml.add_multi_representer(
            data_type, multi_representer=representer_fn, Dumper=cls
        )


@autodoc
@attr.s(slots=True, frozen=True)
class CheckRegression:
    """Class to store regression check results."""

    text: str = attr.ib(
        "",
        validator=instance_of(str),
        metadata={"help": "the text representation of the error"},
    )
    _html: str = attr.ib(
        "",
        validator=instance_of(str),
        metadata={"help": "the html representation of the error"},
        repr=False,
    )

    @property
    def failed_check(self):
        """Return if an error was recorded."""
        return len(self.text) > 0

    @property
    def html(self):
        """Return the html representation of the diff."""
        return self._html or "<p>{}</p>".format(self.text)


@autodoc
@attr.s
class NBRegression:
    """Class to perform Jupyter Notebook Regression tests."""

    check_cell_type: bool = attr.ib(
        True,
        instance_of(bool),
        metadata={"help": "check the ``cell_type`` field against expected"},
    )
    check_cell_metadata: bool = attr.ib(
        True,
        instance_of(bool),
        metadata={"help": "check the ``metadata`` field against expected"},
    )
    check_streams: bool = attr.ib(
        True,
        instance_of(bool),
        metadata={"help": "check the output streams against expected"},
    )
    check_errors: bool = attr.ib(
        True,
        instance_of(bool),
        metadata={"help": "check the output errors against expected"},
    )
    check_text_types: Sequence[str] = attr.ib(
        (
            "text/plain",
            "text/markdown",
            "text/latex",
            "text/html",
            "image/svg+xml",
            "application/json",
        ),
        deep_iterable(instance_of(str)),
        metadata={
            "help": (
                "compare these output mimetypes against expected, "
                "using ruamel.yaml & difflib"
            )
        },
    )
    check_image_types: Sequence[str] = attr.ib(
        ("image/png", "image/jpeg"),
        deep_iterable(instance_of(str)),
        metadata={"help": "compare these output mimetypes against expected, using PIL"},
    )
    image_diff_threshold: float = attr.ib(
        0.1, metadata={"help": "The maximum percentage of difference accepted"}
    )

    @image_diff_threshold.validator
    def validate_image_diff_threshold(self, attribute, value):
        """Validate image_diff_threshold."""
        if not 0 <= value < 100:
            raise ValueError("value out of bounds: [0, 100]")

    nb_version: int = attr.ib(
        4,
        instance_of(int),
        metadata={"help": "The version of the notebook format to use."},
    )
    run_exec: bool = attr.ib(
        True, instance_of(bool), metadata={"help": "Whether to execute the notebook"}
    )
    exec_allow_errors: bool = attr.ib(
        False,
        instance_of(bool),
        metadata={
            "help": (
                "If False, execution is stopped after the first unexpected exception "
                "(not tagged ``raises-exception``)."
            )
        },
    )
    exec_timeout: int = attr.ib(
        120,
        instance_of(int),
        metadata={
            "help": "The maximum time to wait (in seconds) for execution of each cell."
        },
    )
    max_source_lines: int = attr.ib(
        10,
        instance_of(int),
        metadata={
            "help": "The maximum source lines to show in the output error string"
        },
    )
    num_context_lines: int = attr.ib(
        3,
        instance_of(int),
        metadata={"help": "The number of context lines to show either side of a diff"},
    )
    max_compare_lines: int = attr.ib(
        50,
        instance_of(int),
        metadata={
            "help": "The maximum lines of comparison to show in the output error string"
        },
    )
    yaml_indent: int = attr.ib(
        2, instance_of(int), metadata={"help": "Indentation of comparison YAML strings"}
    )

    def __setattr__(self, key, value):
        """Add validation when setting attributes."""
        x_attr = getattr(attr.fields(self.__class__), key)
        if x_attr.validator:
            x_attr.validator(self, x_attr, value)

        super(NBRegression, self).__setattr__(key, value)

    def dump_as_yaml(self, obj: Any, strip_keys: Sequence[str] = ()) -> str:
        """Convert a JSON object, to a formatted yaml string."""
        dct = mapping_to_dict(
            obj,
            strip_keys=strip_keys,
            leaf_func=lambda o: o.text if isinstance(o, CheckRegression) else o,
        )
        # converts all strings that have a newline in them to block style strings
        format_map = yaml.compat.ordereddict()
        format_map["\n"] = yaml.scalarstring.preserve_literal
        format_map["\\e"] = yaml.scalarstring.FoldedScalarString
        yaml.scalarstring.walk_tree(dct, map=format_map)
        # use default_flow_style, so dict keys are on separate lines
        return "\n{}".format(
            yaml.round_trip_dump(
                dct,
                Dumper=RegressionYamlDumper,
                default_flow_style=False,
                allow_unicode=True,
                indent=self.yaml_indent,
                encoding="utf-8",
            )
        )

    def compare_text(
        self, obtained: str, expected: str, rstrip: bool = True
    ) -> CheckRegression:
        """Compare two pieces of text.

        :param str obtained: obtained text.
        :param str expected: expected text.

        """
        obtained_lines = [l.rstrip() if rstrip else l for l in obtained.splitlines()]
        expected_lines = [l.rstrip() if rstrip else l for l in expected.splitlines()]

        if obtained_lines != expected_lines:
            diff_lines = list(
                difflib.unified_diff(
                    expected_lines,
                    obtained_lines,
                    lineterm="",
                    n=self.num_context_lines,
                )
            )
            if len(diff_lines) <= self.max_compare_lines:
                differ = difflib.HtmlDiff()
                html_diff = differ.make_table(expected_lines, obtained_lines)
                return CheckRegression("\n".join(diff_lines), html_diff)
            else:
                return CheckRegression(
                    (
                        "Obtained is different, but diff is too big to show ({} lines)"
                    ).format(len(diff_lines))
                )
        return CheckRegression()

    def compare_cell_type(self, obtained, expected):
        """Compare cell types.

        :param nbformat.NotebookNode obtained: obtained cell.
        :param nbformat.NotebookNode expected: expected cell.

        """
        if obtained.cell_type != expected.cell_type:
            return CheckRegression(
                "{} != {}".format(obtained.cell_type, expected.cell_type)
            )
        return CheckRegression()

    def compare_cell_metadata(self, obtained, expected):
        """Compare cell metadata.

        :param nbformat.NotebookNode obtained: obtained cell.
        :param nbformat.NotebookNode expected: expected cell.

        """
        return self.compare_text(
            self.dump_as_yaml(obtained.metadata), self.dump_as_yaml(expected.metadata)
        )

    def compare_output_errors(self, obtained, expected):
        """Compare output errors.

        :param list[dict] obtained: obtained outputs.
        :param list[dict] obtained: expected outputs.

        """
        obtained = [o for o in obtained if o.output_type == "error"]
        expected = [o for o in expected if o.output_type == "error"]
        return self.compare_text(
            self.dump_as_yaml(obtained, strip_keys=["traceback"]),
            self.dump_as_yaml(expected, strip_keys=["traceback"]),
        )

    def compare_output_streams(self, obtained, expected):
        """Compare output streams.

        :param list[dict] obtained: obtained outputs.
        :param list[dict] obtained: expected outputs.

        """
        obtained = [o for o in obtained if o.output_type == "stream"]
        expected = [o for o in expected if o.output_type == "stream"]
        return self.compare_text(
            self.dump_as_yaml(obtained), self.dump_as_yaml(expected)
        )

    def compare_ouput_text(self, obtained, expected):
        """Compare output text type datas.

        :param list[dict] obtained: obtained outputs.
        :param list[dict] obtained: expected outputs.

        """
        otypes = ["execute_result", "display_data"]
        obtained = [
            {k: v for k, v in o.data.items() if k in self.check_text_types}
            for o in obtained
            if o.output_type in otypes
        ]
        expected = [
            {k: v for k, v in o.data.items() if k in self.check_text_types}
            for o in expected
            if o.output_type in otypes
        ]
        return self.compare_text(
            self.dump_as_yaml(obtained, strip_keys=["execution_count"]),
            self.dump_as_yaml(expected, strip_keys=["execution_count"]),
        )

    def _filter_images(self, outputs):
        """Filter outputs by image types, selecting the first type as preferential."""
        otypes = ["execute_result", "display_data"]
        result = {}
        for i, output in enumerate(outputs):
            if output.output_type not in otypes:
                continue
            for dtype in self.check_image_types:
                if dtype in output.data:
                    result[(i, dtype)] = output.data[dtype]
                    break
        return result

    def _compute_manhattan_distance(self, diff_image):
        """Compute a percentage of similarity of the difference image given.

        Adapted from:
        https://github.com/ESSS/pytest-regressions/blob/master/src/pytest_regressions/image_regression.py

        :param PIL.Image diff_image:
            An image in RGB mode computed from ImageChops.difference
        """
        number_of_pixels = diff_image.size[0] * diff_image.size[1]
        return (
            # To obtain a number in 0.0 -> 100.0
            100.0
            * (
                # Compute the sum of differences
                numpy.sum(diff_image)
                /
                # Divide by the number of channel differences RGB * Pixels
                float(3 * number_of_pixels)
            )
            # Normalize between 0.0 -> 1.0
            / 255.0
        )

    def compare_output_images(self, obtained, expected):
        """Compare output image type datas.

        :param list[dict] obtained: obtained outputs.
        :param list[dict] obtained: expected outputs.

        """
        obtained_data = self._filter_images(obtained)
        expected_data = self._filter_images(expected)

        if set(obtained_data.keys()) != set(expected_data.keys()):
            return "{} != {}".format(
                set(obtained_data.keys()), set(expected_data.keys())
            )

        errors = {}

        for key in obtained_data:
            error_key = "{0:02}_{1}".format(key[0], key[1])
            try:
                image1 = Image.open(BytesIO(base64.b64decode(obtained_data[key])))
                if image1.mode not in ("L" or "RGB"):
                    image1 = image1.convert("RGB")
            except IOError:
                errors[error_key] = CheckRegression("cannot read `obtained` image")
                continue
            try:
                image2 = Image.open(BytesIO(base64.b64decode(expected_data[key])))
                if image2.mode not in ("L" or "RGB"):
                    image2 = image2.convert("RGB")
            except IOError:
                errors[error_key] = CheckRegression("cannot read `expected` image")
                continue

            pixel_diff = ImageChops.difference(image1, image2)
            if pixel_diff.getbbox() is not None:
                manhattan_distance = self._compute_manhattan_distance(pixel_diff)
                if manhattan_distance > self.image_diff_threshold:
                    errors[error_key] = CheckRegression(
                        "images differ by {:.2f}%".format(manhattan_distance)
                    )

        return errors

    def compare_notebooks(
        self, obtained: NotebookNode, expected: NotebookNode, errors: dict = None
    ) -> dict:
        """Compare two notebooks.

        :param nbformat.NotebookNode obtained: obtained notebook.
        :param nbformat.NotebookNode expected: expected notebook.

        :return: errors
        :rtype: dict

        """
        if errors is None:
            errors = {}

        if len(expected.cells) != len(obtained.cells):
            errors.setdefault("notebook", {})["number_cells"] = "{} != {}".format(
                len(expected.cells), len(obtained.cells)
            )

        for i, obtained in enumerate(obtained.cells):
            key = "cell_{:04}".format(i + 1)
            if i >= len(expected.cells):
                errors.setdefault(key, {})[
                    "expected_finished"
                ] = "There are no more cells in the input notebook"
                break
            expected = expected.cells[i]
            cell_errors = self.compare_cell(obtained, expected)
            if cell_errors:
                # for an errored cell, show source lines (up to a maximum number)
                source = obtained.get("source", "")
                if len(source.splitlines()) <= self.max_source_lines:
                    cell_errors["_source"] = source
                else:
                    cell_errors["_source"] = (
                        "\n".join(source.splitlines()[: self.max_source_lines])
                        + "\n..."
                    )

                errors[key] = cell_errors

        return errors

    def compare_cell(self, obtained: NotebookNode, expected: NotebookNode) -> dict:
        """Compare two notebook cells.

        :param nbformat.NotebookNode obtained: obtained cell.
        :param nbformat.NotebookNode expected: expected cell.

        :return: errors
        :rtype: dict

        """
        errors = {}
        meta_tags = obtained.metadata.get("tags", [])

        if META_TAG_SKIP_ALL in meta_tags:
            return errors

        # check cell types are equal
        if self.check_cell_type:
            check_result = self.compare_cell_type(obtained, expected)
            if check_result.failed_check:
                errors["cell_type"] = check_result

        # check cell metadatas are equal
        if self.check_cell_metadata:
            check_result = self.compare_cell_metadata(obtained, expected)
            if check_result.failed_check:
                errors["metadata"] = check_result

        # prepare outputs
        obtained_outputs = coalesce_streams(obtained.get("outputs", []))
        expected_outputs = coalesce_streams(expected.get("outputs", []))

        obtained_outtypes = [o.output_type for o in obtained_outputs]
        expected_outtypes = [o.output_type for o in expected_outputs]

        # check an exception is present, if expected
        if META_TAG_RAISES in meta_tags and "error" not in obtained_outtypes:
            errors["raises-exception"] = CheckRegression("expected exception")

        # if there are no outputs, move to next cell
        if not obtained_outputs and not expected_outputs:
            return errors

        # check an exception is not present, if not expected
        output_errors = [o for o in obtained_outputs if o.output_type == "error"]
        if output_errors and META_TAG_RAISES not in meta_tags:
            errors["exception"] = CheckRegression(
                self.dump_as_yaml(output_errors)
            )  # TODO tracebacks to HTML

        # check the output types are consistent, if not move to next cell
        check_result = self.compare_text(
            self.dump_as_yaml(obtained_outtypes), self.dump_as_yaml(expected_outtypes)
        )
        if check_result.failed_check:
            errors["outputs_mismatch"] = check_result
            return errors

        if META_TAG_SKIP_OUTPUTS in meta_tags:
            return errors

        if self.check_errors:
            check_result = self.compare_output_errors(
                obtained_outputs, expected_outputs
            )
            if check_result.failed_check:
                errors["output_errors"] = check_result

        if self.check_streams:
            check_result = self.compare_output_streams(
                obtained_outputs, expected_outputs
            )
            if check_result.failed_check:
                errors["output_streams"] = check_result

        check_result = self.compare_ouput_text(obtained_outputs, expected_outputs)
        if check_result.failed_check:
            errors["output_text"] = check_result

        diff_dict = self.compare_output_images(obtained_outputs, expected_outputs)
        if diff_dict:
            errors["output_images"] = diff_dict

        # TODO hooks for other output types (like application/pdf)

        return errors

    def check(self, handle, cwd=None, raise_error=True):
        """Execute the Notebook and compare its old/new contents.

        :param handle: a file handle to read the notebook from.
        :param cwd: Path to the directory which the notebook will run in
                    (default is temporary directory).
        :param raise_error: if True and errors, raise an AssertionError

        :return: the new notebook and error str
        :rtype: (nbformat.NotebookNode, str)

        """
        __tracebackhide__ = True

        errors = {}

        # read notebook
        notebook = nbformat.read(
            handle, as_version=self.nb_version
        )  # type: nbformat.NotebookNode
        new_notebook = copy.deepcopy(notebook)

        # execute notebook
        if self.run_exec:
            proc = ExecutePreprocessor(
                timeout=self.exec_timeout, allow_errors=self.exec_allow_errors
            )
            if not cwd:
                cwd_dir = tempfile.mkdtemp()
            resources = {
                "metadata": {"path": cwd or cwd_dir}
            }  # metadata/path specifies the directory the kernel will run in
            try:
                proc.preprocess(new_notebook, resources)
            except CellExecutionError:
                errors.setdefault("notebook", {})[
                    "execution"
                ] = "Halted execution after CellExecutionError raised"
            finally:
                if not cwd:
                    shutil.rmtree(cwd_dir)

        errors = self.compare_notebooks(new_notebook, notebook, errors=errors)

        errors_str = ""
        if errors:
            if raise_error:
                errors_str = self.dump_as_yaml(errors)
                raise AssertionError(errors_str)

        return new_notebook, errors
