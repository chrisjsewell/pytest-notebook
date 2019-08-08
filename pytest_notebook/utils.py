import attr
import textwrap
from typing import Any, Callable, Mapping, Union
import warnings

from nbformat import from_dict, NotebookNode


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


def autodoc(attrs_class):
    """Decorate an :class:`attr.s` class to update its docstring with attributes.

    The docstring will include the :class:`attributes <attr.ib>`,
    and emits warnings when partially undocumented attributes are found.

    If the class contains any attributes,
    they are documented as *constructor parameters* in a *Parameters* section,
    added at the end of the class' docstring.
    In order to extract the most information per parameter description, this
    decorator assumes that every attribute

    * Typed (either via the ``type`` argument, or via `PEP 526`_ type-annotations), and
    * Contains a metadata dictionary with the keys

        help:
            The string that describes the attribute,
            and will go in the description of the corresponding parameter.

    Default values are, of course, optional, and if provided,
    the parameter's description will inform this.
    Private attributes will have their names rendered correctly (no leading underscore),
    and non-private attributes help-text will be complemented with a reminder that
    the parameter's value can be later accessed via an attribute with that name.

    .. warning::

        Currently, there is no support for indicating that arguments are keyword-only,
        hashable, or validated.
        These and other exceptional conditions should be informed in the docstring.

    .. _PEP 526: https://www.python.org/dev/peps/pep-0526/
    """

    def fix_indent(docstring):
        lines = docstring.split("\n")

        if len(lines) > 1:
            for i in range(1, len(lines)):
                if lines[i]:
                    break
            parts = ["\n".join(lines[:i]), textwrap.dedent("\n".join(lines[i:]))]
            result = "\n".join(p for p in parts if p)
            return result
        else:
            return lines[0]

    def param_doc(field):
        field_fn = f"{attrs_class.__module__}.{attrs_class.__name__}.{field.name}"

        if field.name[0] == "_":
            name = field.name[1:]
            help_complement = ""
        else:
            name = field.name
            help_complement = (
                "This value is accessible, after initialization, "
                f"via the ``{field.name}`` attribute. "
            )

        if field.type is None:
            field_type = "Any"
            warnings.warn(f'Field "{field_fn}" has no declared type.')
        else:
            try:
                field_type = field.type.__name__
            except AttributeError:
                # this is required for types.Union
                field_type = ", ".join([a.__name__ for a in field.type.__args__])

        if field.default is not attr.NOTHING:
            optional = ""  # ", optional" this isn't accepted by sphinx
            help_complement += f"Default: {field.default}"
        else:
            optional = ""

        title = f"{name}: {field_type}{optional}"

        if "help" in field.metadata:
            description = textwrap.indent(
                textwrap.fill(
                    text=(field.metadata["help"] + " " + help_complement).strip(),
                    width=88,
                ),
                prefix=" " * 4,
            )
        else:
            description = help_complement
            warnings.warn(f"Field {field_fn} not documented.")

        return title + "\n" + description

    if attr.fields(attrs_class):
        params_section = (
            textwrap.dedent(
                """\
            Parameters
            ----------
            """
            )
            + "\n\n".join(param_doc(field) for field in attr.fields(attrs_class))
        )
    else:
        params_section = ""

    if attrs_class.__doc__ and params_section:
        attrs_class.__doc__ = (
            f"{fix_indent(attrs_class.__doc__).rstrip()}\n\n{params_section}"
        )
    elif params_section:
        attrs_class.__doc__ = params_section

    return attrs_class


def is_json_mime(mime):
    """Test if mime-type is JSON-like."""
    return mime == "application/json" or (
        mime.startswith("application/") and mime.endswith("+json")
    )


def rejoin_mimebundle(data):
    """Rejoin the multi-line string fields in a mimebundle (in-place)."""
    for key, value in list(data.items()):
        if (
            not is_json_mime(key)
            and isinstance(value, list)
            and all(isinstance(line, str) for line in value)
        ):
            data[key] = "".join(value)
    return data


def prepare_cell_v4(cell: dict) -> NotebookNode:
    """Convert raw notebook cell (in v4 format) to a ``NotebookNode``."""
    cell = from_dict(cell)
    for output in cell.get("outputs", []):
        output_type = output.get("output_type", "")
        if output_type in {"execute_result", "display_data"}:
            rejoin_mimebundle(output.get("data", {}))
        elif output_type:
            if isinstance(output.get("text", ""), list):
                output.text = "".join(output.text)
    return cell
