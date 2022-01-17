"""Module to provide an IPython magic for running pytest.

Load via: ``%load_ext pytest_notebook.ipy_magic``,
then ``%pytest`` and ``%%pytest`` can be accessed.

"""
# TODO post solution to stackoverflow:
# https://stackoverflow.com/questions/41304311/running-pytest-test-functions-inside-a-jupyter-notebook
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from typing import List, Tuple, Union

EXEC_NAME = "pytest"
CONFIG_FILE_NAME = "pytest.ini"
MAIN_FILE_NAME = "test_ipycell.py"


def parse_cell_content(
    cell: Union[str, None]
) -> Tuple[List[str], List[str], List[str]]:
    """Parse the cell contents.

    :returns: (test_content, config_content, literals_content)
    """
    test_content = []
    config_content = []
    literals_content = []

    if cell is None:
        return test_content, config_content, literals_content

    in_config, in_literals = False, False
    for i, line in enumerate(cell.splitlines()):
        if line.startswith("---") and not in_literals:
            if in_config:
                in_config = False
            elif config_content:
                raise IOError(f"Line {i}: found second config file section")
            else:
                in_config = True
        elif in_config:
            config_content.append(line)
        elif line.startswith("***") and not in_config:
            if in_literals:
                in_literals = False
            elif literals_content:
                raise IOError(f"Line {i}: found second literals section")
            else:
                in_literals = True
        elif in_literals:
            literals_content.append(line)
        else:
            test_content.append(line)

    if in_config:
        raise IOError("found start of config section, but not end")
    if in_literals:
        raise IOError("found start of literals section, but not end")

    return test_content, config_content, literals_content


def eval_literals(
    literals: List[str], local_ns: Union[dict, None]
) -> List[Tuple[str, str]]:
    """Evaluate and yield literal items."""
    for literal in literals:
        literal = literal.strip()
        if not (literal.startswith("(") and literal.endswith(")")):
            raise ValueError(f"The literal must be a tuple: '{literal}'")
        try:
            # Note to get global namespace, would need to use
            # @magics_class and self.shell.user_ns,
            # see https://ipython.readthedocs.io/en/stable/config/custommagics.html
            evaluated = eval(literal, {}, local_ns)
        except Exception as err:
            raise ValueError(
                f"The literal could not be evaluated: '{literal}'; '{err}'"
            ) from None
        if (
            len(evaluated) != 2
            or not isinstance(evaluated[0], str)
            or not isinstance(evaluated[1], str)
        ):
            raise ValueError(
                f"The literal is not a tuple of two strings: '{evaluated}'"
            )
        if evaluated[1] != os.path.basename(evaluated[1]):
            raise ValueError(
                f"'{evaluated[1]}' should be a filename, with no directory component"
            )
        # this is only required, if we allow sub directories
        # if os.path.isabs(evaluated[1]):
        #     raise ValueError(f"the path {evaluated[1]} is absolute")

        yield evaluated


def write_file(content: List[str], file_name: str, temp_dir: Union[str, Path]):
    """Write file to the ``temp_dir``."""
    if content:
        if isinstance(temp_dir, str):
            temp_dir = Path(temp_dir)
        if content[-1].strip():
            content.append("")
        temp_dir.joinpath(file_name).write_text("\n".join(content))


def run_pytest(args: List[str], cwd: Union[str, Path, None] = None):
    """Run pytest, with live output.

    Adapted from https://stackoverflow.com/a/18422264/5033292

    Note: originally this used ``pytest.main`` to run pytest,
    however, there was issues with multiple calls to it (see:
    https://docs.pytest.org/en/latest/usage.html#calling-pytest-from-python-code).
    """
    os.environ["COLUMNS"] = os.environ.get("COLUMNS", "80")
    process = subprocess.Popen(
        [EXEC_NAME] + args,
        cwd=str(cwd) if cwd else None,
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for c in iter(lambda: process.stdout.read(1), b""):
        sys.stdout.write(c.decode(sys.stdout.encoding or "utf8", "ignore"))


def pytest(
    line: str = "", cell: Union[str, None] = None, local_ns: Union[dict, None] = None
):
    """Run pytest.

    ``%pytest arg1 arg2 ...`` will run pytest in a temporary directory.

    ``%%pytest arg1 arg2 ...`` will additionally write the cell contents
    to a test module in the temporary directory.

    The cell content can optionally contain a fenced sections:

    - ``---``: lines extracted and written as ``pytest.ini``
    - ``***``: each line should be able to be evaluated as a tuple of two strings,
      (file_content, file_name), that will be written to the temporary directory.
      Any variables in the notebook scope can be used in these expressions.

    Example::

        %%pytest -v

        ---
        [pytest]
        adopts = --disable-warning
        ---

        ***
        (content_string, "test_other.py")
        ***

        def test_something():
            assert True

    Note: to change output width, se the 'COLUMNS' environmental variable::

        import os
        os.environ["COLUMNS"] = "80"

    """
    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = Path(temp_dir)

        args = shlex.split(line)
        if cell:
            test_content, config_content, literals_content = parse_cell_content(cell)
            write_file(test_content, MAIN_FILE_NAME, temp_dir)
            write_file(config_content, CONFIG_FILE_NAME, temp_dir)
            for content, file_name in eval_literals(literals_content, local_ns or {}):
                write_file(content.splitlines(), file_name, temp_dir)

        run_pytest(args, cwd=str(temp_dir))


def load_ipython_extension(ipython):
    """Load the ipython magic, when the module is called via ``%load_ext``."""
    from IPython.core.magic import needs_local_scope, register_line_cell_magic

    register_line_cell_magic(needs_local_scope(pytest))
