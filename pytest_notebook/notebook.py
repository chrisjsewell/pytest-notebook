"""Module for working with notebook."""
import copy
from functools import lru_cache

try:
    # Python <= 3.8
    from importlib_resources import files
except ImportError:
    from importlib.resources import files

import json
import re
from typing import Any, Callable, Mapping, TextIO, Tuple, Union

import attr
from attr.validators import instance_of
import jsonschema
import nbformat
from nbformat import NotebookNode

from pytest_notebook import resources
from pytest_notebook.diffing import join_path, star_path
from pytest_notebook.utils import autodoc

DEFAULT_NB_VERSION = 4

META_KEY = "nbreg"


def mapping_to_dict(
    obj: Any, strip_keys: list = (), leaf_func: Union[Callable, None] = None
) -> dict:
    """Recursively convert mappable objects to dicts, including in lists and tuples.

    :param list[str] strip_keys: list of keys to strip from the output
    :param leaf_func: a function to apply to leaf values

    """

    if isinstance(obj, Mapping):
        return {
            k: mapping_to_dict(obj[k], strip_keys, leaf_func)
            for k in sorted(obj.keys())
            if k not in strip_keys
        }
    elif isinstance(obj, (list, tuple)):
        return [mapping_to_dict(i, strip_keys, leaf_func) for i in obj]
    elif leaf_func is not None:
        return leaf_func(obj)
    else:
        return obj


def gather_json_paths(
    obj: Any, paths: list, types: Union[Tuple, None] = None, curr_path: tuple = ()
) -> Any:
    """Recursively gather paths to non dict/list elements of a json-like object.

    :param paths: a mutable container for the paths
    :param types: only return paths for these element types

    Examples
    --------
    >> dct = {"a": [{"b": 2}, {"c": "x"}]}
    >> paths = []
    >> gather_json_paths(dct, paths)
    >> paths
    [('a', 0, 'b'), ('a', 1, 'c')]
    >> paths = []
    >> gather_json_paths(dct, paths, (str,))
    >> paths
    [('a', 1, 'c')]

    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            gather_json_paths(v, paths, types, curr_path=tuple(list(curr_path) + [k]))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            gather_json_paths(v, paths, types, curr_path=tuple(list(curr_path) + [i]))
    elif types is None or isinstance(obj, types):
        paths.append(curr_path)


def regex_replace_nb(
    notebook: NotebookNode, replacements: Tuple[Tuple[str, str, str]]
) -> NotebookNode:
    """Return a new notebook with string regex replacements applied.

    :param replacements: list of (path, regex, replacement), path is a string of form
        '/cells/0/outputs', and can contain * wildcards for integer parts
    """
    nb_paths = []
    gather_json_paths(notebook, nb_paths, types=(str,))
    new_notebook = copy.deepcopy(notebook)
    for nb_path in nb_paths:
        # iteratively star more elements from the right side
        compare_paths = {
            join_path(list(nb_path[:i]) + star_path(nb_path[i:]))
            for i in reversed(range(len(nb_path)))
        }
        for path_str, regex, replace in replacements:
            if not any(p.startswith(path_str) for p in compare_paths):
                continue

            nb_element = new_notebook
            for key in nb_path[:-1]:
                nb_element = nb_element[key]
            nb_element[nb_path[-1]] = re.sub(regex, replace, nb_element[nb_path[-1]])

    return new_notebook


class NBConfigValidationError(Exception):
    """Exception to signal a validation error in the notebook metadata."""


def validate_regex_replace(args, index):
    """Validate a single regex replace item.

    Should be of the form (<nb_path>, <regex_pattern>, <replacement>)
    """
    if not isinstance(args, tuple):
        raise TypeError(f"diff_replace[{index}] must be a tuple: {args}")
    if len(args) != 3:
        raise ValueError(
            f"diff_replace[{index}] should contain "
            f"'<nb_address> <regex> <replacement>': {args}"
        )
    if not isinstance(args[0], str):
        raise TypeError(f"diff_replace[{index}] address '{args[0]}' must a string")
    if not args[0].startswith("/"):
        raise ValueError(
            f"diff_ignore[{index}] address '{args[0]}' must start with '/'"
        )
    if not isinstance(args[1], str):
        raise TypeError(f"diff_replace[{index}] regex '{args[1]}' must a string")
    try:
        re.compile(args[1])
    except Exception as err:
        raise TypeError(
            f"diff_replace[{index}] '{args[1]}' is not a valid regex: {err}"
        )
    if not isinstance(args[2], str):
        raise TypeError(f"diff_replace[{index}] replacement '{args[2]}' must a string")


@lru_cache()
def _load_validator():
    schema = json.loads(
        files(resources).joinpath("nb_metadata.schema.json").read_text(encoding="utf-8")
    )
    validator_cls = jsonschema.validators.validator_for(schema)
    return validator_cls(schema=schema)


def validate_metadata(data, path):
    """Validate notebook and cell metadata against the required config schema.

    :raises NBRegressionError: if validation fails
    """
    __tracebackhide__ = True
    validator = _load_validator()
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        raise NBConfigValidationError(
            "\n".join(
                [path]
                + [
                    "- {} [key path: '{}']".format(
                        error.message, "/".join([str(p) for p in error.path])
                    )
                    for error in errors
                ]
            )
        )


@autodoc
@attr.s(frozen=True, slots=True)
class MetadataConfig:
    """A class to store configuration data, obtained from the notebook metadata."""

    diff_replace: tuple = attr.ib(
        (),
        validator=instance_of(tuple),
        metadata={"help": "Notebook paths to regex replace before diffing."},
    )

    @diff_replace.validator
    def _validate_diff_replace(self, attribute, values):
        if not isinstance(values, tuple):
            raise TypeError(f"diff_replace must be a tuple: {values}")
        for i, args in enumerate(values):
            validate_regex_replace(args, i)

    diff_ignore: set = attr.ib(
        attr.Factory(set), metadata={"help": "Notebook paths to ignore during diffing."}
    )

    @diff_ignore.validator
    def _validate_diff_ignore(self, attribute, values):
        if not isinstance(values, set):
            raise TypeError(f"diff_ignore not a set: {values}")
        if not all(isinstance(v, str) for v in values):
            raise TypeError(f"diff_ignore items not all strings: {values}")

    skip: bool = attr.ib(
        False,
        validator=instance_of(bool),
        metadata={"help": "Skip testing of this notebook."},
    )
    skip_reason: str = attr.ib(
        "",
        validator=instance_of(str),
        metadata={"help": "Reason for skipping testing of this notebook."},
    )


def config_from_metadata(nb: NotebookNode) -> dict:
    """Extract configuration data from notebook/cell metadata."""
    nb_metadata = nb.get("metadata", {}).get(META_KEY, {})
    validate_metadata(nb_metadata, "/metadata")

    diff_replace = [tuple(d) for d in nb_metadata.get("diff_replace", [])]
    diff_ignore = set(nb_metadata.get("diff_ignore", []))

    for i, cell in enumerate(nb.get("cells", [])):
        cell_metadata = cell.get("metadata", {}).get(META_KEY, {})
        validate_metadata(cell_metadata, f"/cells/{i}/metadata")

        diff_replace.extend(
            [
                (f"/cells/{i}{p}", x, r)
                for p, x, r in cell_metadata.get("diff_replace", [])
            ]
        )
        diff_ignore.update(
            [f"/cells/{i}{p}" for p in cell_metadata.get("diff_ignore", [])]
        )

    return MetadataConfig(
        tuple(diff_replace),
        diff_ignore,
        nb_metadata.get("skip", False),
        nb_metadata.get("skip_reason", ""),
    )


def load_notebook(
    path: Union[TextIO, str], as_version=DEFAULT_NB_VERSION
) -> NotebookNode:
    """Load the notebook from file."""
    return nbformat.read(path, as_version=as_version)


def load_notebook_with_config(
    path: Union[TextIO, str], as_version=DEFAULT_NB_VERSION
) -> Tuple[NotebookNode, MetadataConfig]:
    """Load the notebook from file, and scan its metadata for config data."""
    notebook = nbformat.read(path, as_version=as_version)
    nb_config = config_from_metadata(notebook)
    return notebook, nb_config


def prepare_nb(dct: dict, as_version=DEFAULT_NB_VERSION) -> NotebookNode:
    """Convert raw (disc-format) notebook to a ``NotebookNode``."""
    if as_version != 4:
        raise NotImplementedError(f"notebook version: {as_version}")
    return nbformat.v4.to_notebook(dct)


def prepare_cell(cell: dict, as_version=DEFAULT_NB_VERSION) -> NotebookNode:
    """Convert raw (disc-format) notebook cell to a ``NotebookNode``."""
    if as_version != 4:
        raise NotImplementedError(f"notebook version: {as_version}")
    nb = nbformat.v4.to_notebook({"cells": [cell], "metadata": {}})
    return nb["cells"][0]


def create_notebook(as_version: int = DEFAULT_NB_VERSION, **kwargs):
    """Create a new notebook."""
    if as_version == 1:
        notebook = nbformat.v1.new_notebook(**kwargs)
    elif as_version == 2:
        notebook = nbformat.v2.new_notebook(**kwargs)
    elif as_version == 3:
        notebook = nbformat.v3.new_notebook(**kwargs)
    elif as_version == 4:
        notebook = nbformat.v4.new_notebook(**kwargs)
    else:
        raise NotImplementedError(f"notebook version: {as_version}")
    return notebook


def create_cell(
    source: str = "",
    cell_type: str = "code",
    as_version: int = DEFAULT_NB_VERSION,
    **kwargs,
) -> NotebookNode:
    """Create a new notebook cell."""
    if not as_version == 4:
        raise NotImplementedError("cell not version 4")
    if cell_type == "code":
        return nbformat.v4.new_code_cell(source=source, **kwargs)
    if cell_type == "markdown":
        return nbformat.v4.new_markdown_cell(source=source, **kwargs)
    if cell_type == "raw":
        return nbformat.v4.new_raw_cell(source=source, **kwargs)
    raise ValueError(f"cell_type '{cell_type}' not recognised.")


def dump_notebook(nb: NotebookNode, as_version=nbformat.NO_CONVERT) -> NotebookNode:
    """Dump the notebook to a string."""
    return nbformat.writes(nb, version=as_version)
