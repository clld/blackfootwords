def test_home(app):
    """
    Tests the home page to ensure it is accessible.

    Args:
        app: A test application that provides a method to make HTTP requests.
    """
    app.get_html('/', status=200)
