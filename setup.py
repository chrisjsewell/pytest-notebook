#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importlib import import_module
from setuptools import setup, find_packages


setup(
    name="pytest-notebook",
    version=import_module("pytest_notebook").__version__,
    author="Chris Sewell",
    author_email="chrisj_sewell@hotmail.com",
    maintainer="Chris Sewell",
    maintainer_email="chrisj_sewell@hotmail.com",
    license="BSD-3",
    url="https://github.com/chrisjsewell/pytest-notebook",
    description="A pytest plugin for testing Jupyter Notebooks",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.5",
    include_package_data=True,
    install_requires=[
        "pytest>=3.5.0",
        "attrs",
        "jupyter_client",
        "nbconvert",
        "nbdime",
        "nbformat",
        "jsonschema",
        "importlib_resources",
        # "numpy",
        # "pillow",
        # "ruamel.yaml",
    ],
    extras_require={
        "testing": ["coverage", "pytest-cov", "pytest-regressions", "black==19.3b0"],
        "code_style": [
            "black",
            "pre-commit==1.17.0",
            "flake8<3.8.0,>=3.7.0",
            "doc8<0.9.0,>=0.8.0",
        ],
        "flake8_plugins": [
            "flake8-comprehensions",
            "flake8-docstrings",
            "flake8_builtins",
            "import-order",
        ],
        "docs": [
            "sphinx>=1.6",
            "sphinx_rtd_theme",
            "ipypublish>=0.10.7",
            "ruamel.yaml.clib",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
        "pytest11": ["nb_regression = pytest_notebook.plugin"],
        "nbreg.post_proc": [
            "coalesce_streams = pytest_notebook.post_processors:coalesce_streams",
            "blacken_code = pytest_notebook.post_processors:blacken_code",
        ],
    },
)
