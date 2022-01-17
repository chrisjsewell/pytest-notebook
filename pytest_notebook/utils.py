"""Utility functions."""
import os
import textwrap
import warnings

import attr


def running_as_test():
    """Check whether the notebook is being executed as a test.

    This function may be useful, when running notebooks as integration tests to
    ensure the runtime is not exceedingly long.

    Usage::

        if not running_as_test():
            output = call_very_long_process()
        else:
            output = "result"

    See:
    https://docs.pytest.org/en/latest/example/simple.html#pytest-current-test-environment-variable

    """
    return os.environ.get("PYTEST_CURRENT_TEST", None) is not None


def type_to_sphinx(typ, field_name):
    """Convert a type object to a string acceptable by Sphinx."""
    # TODO better implementation of type_to_sphinx
    if typ is None:
        field_type = "Any"
        warnings.warn(f'Field "{field_name}" has no declared type.')
    elif getattr(typ, "__module__", None) == "typing":
        field_type = str(typ).replace("typing.", "")
        if field_type.startswith("Union["):
            field_type = field_type[6:-1]
    elif (
        hasattr(typ, "__name__")
        and getattr(typ, "__module__", "builtins") != "builtins"
    ):
        field_type = f"{typ.__module__}.{typ.__name__}"
    elif hasattr(typ, "__name__"):
        field_type = typ.__name__
    else:
        warnings.warn(f'Field "{field_name}" type could not be converted.')
        field_type = "Any"
    return field_type


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

        field_type = type_to_sphinx(field.type, field_fn)

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
