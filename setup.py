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
    python_requires=">=3.6",
    include_package_data=True,
    install_requires=[
        "pytest>=3.5.0",
        "attrs<21,>=19",
        "jupyter_client",
        "nbconvert~=5.6.0",
        "nbdime",
        "nbformat",
        "jsonschema",
        "importlib_resources>=1.3.0",
    ],
    extras_require={
        "testing": [
            "coverage~=4.5.1",
            "pytest-cov",
            "pytest-regressions",
            "black==19.3b0",
            "beautifulsoup4==4.8.0",
        ],
        "code_style": [
            "pre-commit~=2.7.0",
            "doc8<0.9.0,>=0.8.0",
        ],
        "docs": [
            "sphinx>=2",
            "pyyaml",
            "sphinx-book-theme~=0.0.36",
            "myst-nb~=0.10.1",
            "coverage~=4.5.1",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
        "pytest11": ["nb_regression = pytest_notebook.plugin"],
        "nbreg.post_proc": [
            "coalesce_streams = pytest_notebook.post_processors:coalesce_streams",
            "blacken_code = pytest_notebook.post_processors:blacken_code",
            "beautifulsoup = pytest_notebook.post_processors:beautifulsoup",
        ],
    },
)
