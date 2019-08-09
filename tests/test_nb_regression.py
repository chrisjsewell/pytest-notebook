import nbformat

from pytest_notebook.nb_regression import (
    config_from_metadata,
    META_KEY,
    MetadataConfig,
    NBRegressionFixture,
)
from pytest_notebook.utils import prepare_cell_v4


def test_init_fixture():
    fixture = NBRegressionFixture(exec_timeout=10)
    assert fixture.exec_timeout == 10


def test_config_from_metadata_none():
    notebook = nbformat.v4.new_notebook()
    config = config_from_metadata(notebook)
    assert config == MetadataConfig()


def test_config_from_metadata():
    notebook = nbformat.v4.new_notebook()
    notebook.metadata[META_KEY] = {"diff_ignore": ["/", "/cells/*/outputs"]}
    notebook.cells.extend(
        [
            prepare_cell_v4({"metadata": {}}),
            prepare_cell_v4(
                {"metadata": {META_KEY: {"diff_ignore": ["/", "/outputs"]}}}
            ),
            prepare_cell_v4({"metadata": {}}),
        ]
    )

    config = config_from_metadata(notebook)
    print(config)
    assert config == MetadataConfig(
        {"/", "/cells/*/outputs", "/cells/1/", "/cells/1/outputs"}
    )
