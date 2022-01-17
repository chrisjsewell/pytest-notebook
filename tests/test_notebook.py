"""Tests for pytest_notebook.notebook."""
from pytest_notebook.notebook import (
    META_KEY,
    MetadataConfig,
    config_from_metadata,
    create_notebook,
    gather_json_paths,
    mapping_to_dict,
    prepare_cell,
    regex_replace_nb,
)


def test_gather_paths():
    """Test gathering paths in the notebook."""
    notebook = create_notebook()
    notebook.cells.extend(
        [
            prepare_cell(
                {
                    "cell_type": "code",
                    "execution_count": 2,
                    "metadata": {},
                    "outputs": [
                        {"name": "stdout", "output_type": "stream", "text": ["hallo\n"]}
                    ],
                    "source": ["print('hallo')\n"],
                }
            )
        ]
    )
    paths = []
    gather_json_paths(notebook, paths)
    assert paths == [
        ("nbformat",),
        ("nbformat_minor",),
        ("cells", 0, "cell_type"),
        ("cells", 0, "execution_count"),
        ("cells", 0, "outputs", 0, "name"),
        ("cells", 0, "outputs", 0, "output_type"),
        ("cells", 0, "outputs", 0, "text"),
        ("cells", 0, "source"),
    ]


def test_gather_paths_filter_str():
    """Test gathering paths in the notebook, filtering by only str objects."""
    notebook = create_notebook()
    notebook.cells.extend(
        [
            prepare_cell(
                {
                    "cell_type": "code",
                    "execution_count": 2,
                    "metadata": {},
                    "outputs": [
                        {"name": "stdout", "output_type": "stream", "text": ["hallo\n"]}
                    ],
                    "source": ["print('hallo')\n"],
                }
            )
        ]
    )
    paths = []
    gather_json_paths(notebook, paths, types=(str,))

    assert paths == [
        ("cells", 0, "cell_type"),
        ("cells", 0, "outputs", 0, "name"),
        ("cells", 0, "outputs", 0, "output_type"),
        ("cells", 0, "outputs", 0, "text"),
        ("cells", 0, "source"),
    ]


def test_regex_replace_nb_no_change():
    """Test that, if no replacements are made, the notebook remains the same."""
    notebook = create_notebook()
    notebook.cells.extend(
        [prepare_cell({"metadata": {}, "outputs": [], "source": ["print(1)\n"]})]
    )
    new_notebook = regex_replace_nb(notebook, [])
    assert notebook == new_notebook


def test_regex_replace_nb_source():
    """Test regex replacing notebook source."""
    notebook = create_notebook()
    notebook.cells.extend(
        [
            prepare_cell(
                {"metadata": {}, "outputs": [], "source": ["print(1)\n", "print(2)"]}
            ),
            prepare_cell(
                {"metadata": {}, "outputs": [], "source": ["print(1)\n", "print(2)"]}
            ),
        ]
    )
    new_notebook = regex_replace_nb(
        notebook, [("/cells/0/source", "p", "s"), ("/cells/1/source", "p", "t")]
    )
    new_notebook.nbformat_minor = None
    assert mapping_to_dict(new_notebook) == {
        "cells": [
            {"metadata": {}, "outputs": [], "source": "srint(1)\nsrint(2)"},
            {"metadata": {}, "outputs": [], "source": "trint(1)\ntrint(2)"},
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": None,
    }


def test_regex_replace_nb_output():
    """Test regex replacing notebook output."""
    notebook = create_notebook()
    notebook.cells.extend(
        [
            prepare_cell(
                {
                    "metadata": {},
                    "outputs": [
                        {
                            "name": "stdout",
                            "output_type": "stream",
                            "text": ["2019-08-11\n"],
                        }
                    ],
                    "source": ["from datetime import date\n", "print(date.today())"],
                }
            )
        ]
    )
    new_notebook = regex_replace_nb(
        notebook, [("/cells/0/outputs/0", r"\d{2,4}-\d{1,2}-\d{1,2}", "DATE-STAMP")]
    )
    new_notebook.nbformat_minor = None
    assert mapping_to_dict(new_notebook) == {
        "cells": [
            {
                "metadata": {},
                "outputs": [
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": ["DATE-STAMP\n"],
                    }
                ],
                "source": "from datetime import date\nprint(date.today())",
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": None,
    }


def test_regex_replace_nb_with_wildcard():
    """Test regex replacing notebook values."""
    notebook = create_notebook()
    notebook.cells.extend(
        [
            prepare_cell(
                {"metadata": {}, "outputs": [], "source": ["print(1)\n", "print(2)"]}
            ),
            prepare_cell(
                {"metadata": {}, "outputs": [], "source": ["print(1)\n", "print(2)"]}
            ),
        ]
    )
    new_notebook = regex_replace_nb(
        notebook, [("/cells/*/source", "p", "s"), ("/cells/0/source", "t", "y")]
    )
    new_notebook.nbformat_minor = None
    assert mapping_to_dict(new_notebook) == {
        "cells": [
            {"metadata": {}, "outputs": [], "source": "sriny(1)\nsriny(2)"},
            {"metadata": {}, "outputs": [], "source": "srint(1)\nsrint(2)"},
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": None,
    }


def test_config_from_metadata_none():
    """Test that, if no notebook metadata, the returned MetadataConfig is empty."""
    notebook = create_notebook()
    config = config_from_metadata(notebook)
    assert config == MetadataConfig()


def test_config_from_metadata():
    """Test extraction of configuration data from notebook metadata."""
    notebook = create_notebook()
    notebook.metadata[META_KEY] = {
        "diff_ignore": ["/", "/cells/*/outputs"],
        "diff_replace": [
            ["/cells/0/outputs/0", r"\d{2,4}-\d{1,2}-\d{1,2}", "DATE-STAMP"]
        ],
    }
    notebook.cells.extend(
        [
            prepare_cell({"metadata": {}}),
            prepare_cell({"metadata": {META_KEY: {"diff_ignore": ["/", "/outputs"]}}}),
            prepare_cell(
                {"metadata": {META_KEY: {"diff_replace": [["/source", "s", "p"]]}}}
            ),
        ]
    )

    config = config_from_metadata(notebook)

    assert config == MetadataConfig(
        diff_replace=(
            ("/cells/0/outputs/0", r"\d{2,4}-\d{1,2}-\d{1,2}", "DATE-STAMP"),
            ("/cells/2/source", "s", "p"),
        ),
        diff_ignore={"/", "/cells/*/outputs", "/cells/1/", "/cells/1/outputs"},
    )
