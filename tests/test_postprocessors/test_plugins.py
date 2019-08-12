from pytest_notebook.post_processors import document_processors


def test_documentation(file_regression):
    """Test all the plugins are loading, by generating combined documentation."""
    file_regression.check(document_processors() + "\n")
