from typing_extensions import assert_type

from dspy.utils.annotation import experimental


def test_experimental_decorator_on_function():
    @experimental
    def test_function():
        """A test function."""
        return "test"

    assert test_function.__doc__ is not None
    assert (
        "Experimental: This function may change or be removed in a future release without warning."
        in test_function.__doc__
    )
    assert "A test function." in test_function.__doc__
    assert test_function() == "test"


def test_experimental_decorator_on_function_with_version():
    @experimental(version="3.1.0")
    def test_function():
        """A test function with version."""
        return "versioned"

    assert test_function.__doc__ is not None
    assert "introduced in v3.1.0" in test_function.__doc__
    assert (
        "Experimental: This function may change or be removed in a future release without warning (introduced in v3.1.0)."
        in test_function.__doc__
    )
    assert "A test function with version." in test_function.__doc__
    assert test_function() == "versioned"


def test_experimental_decorator_on_class():
    @experimental
    class TestClass:
        """A test class."""

        def method(self):
            return "method"

    assert TestClass.__doc__ is not None
    assert "Experimental: This class may change or be removed in a future release without warning." in TestClass.__doc__
    assert "A test class." in TestClass.__doc__

    instance = TestClass()
    assert instance.method() == "method"


def test_experimental_decorator_on_class_with_version():
    @experimental(version="2.5.0")
    class TestClass:
        """A test class with version."""

        pass

    assert TestClass.__doc__ is not None
    assert "introduced in v2.5.0" in TestClass.__doc__
    assert (
        "Experimental: This class may change or be removed in a future release without warning (introduced in v2.5.0)."
        in TestClass.__doc__
    )
    assert "A test class with version." in TestClass.__doc__


def test_experimental_decorator_without_docstring():
    @experimental
    def test_function():
        return "no_doc"

    assert test_function.__doc__ is not None
    assert (
        test_function.__doc__
        == "Experimental: This function may change or be removed in a future release without warning."
    )
    assert test_function() == "no_doc"


def test_experimental_decorator_without_docstring_with_version():
    @experimental(version="1.0.0")
    def test_function():
        return "no_doc_version"

    assert test_function.__doc__ is not None
    assert (
        test_function.__doc__
        == "Experimental: This function may change or be removed in a future release without warning (introduced in v1.0.0)."
    )
    assert test_function() == "no_doc_version"


def test_experimental_decorator_with_callable_syntax():
    def test_function():
        """A test function."""
        return "callable"

    decorated = experimental(test_function)

    assert decorated.__doc__ is not None
    assert "Experimental:" in decorated.__doc__
    assert "A test function." in decorated.__doc__
    assert decorated() == "callable"


def test_experimental_decorator_with_version_callable_syntax():
    def test_function():
        """A test function."""
        return "callable_version"

    decorated = experimental(test_function, version="4.0.0")

    assert decorated.__doc__ is not None
    assert "introduced in v4.0.0" in decorated.__doc__
    assert "Experimental:" in decorated.__doc__
    assert decorated() == "callable_version"


def test_experimental_preserves_class_and_function_types():
    class Decision:
        @classmethod
        def __class_getitem__(cls, options: object) -> type["Decision"]:
            return cls

    def render(value: int) -> str:
        return str(value)

    direct: type[Decision] = experimental(Decision)
    configured: type[Decision] = experimental(version="3.4.1")(Decision)
    explicit_none: type[Decision] = experimental(None, version="3.4.1")(Decision)
    _ = assert_type(direct(), Decision)
    _ = assert_type(configured(), Decision)
    _ = assert_type(explicit_none(), Decision)
    _ = assert_type(experimental(render)(value=1), str)
    _ = assert_type(experimental(version="3.4.1")(render)(value=1), str)
    assert direct is configured is explicit_none is Decision
    assert direct["criteria"] is Decision
