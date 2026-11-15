"""Connection-method wrapping tests for cooperative consumer instrumentation.

System-under-test:
:func:`django_strawberry_framework.testing.safe_wrap_connection_method` -
the wrap-time guard against Django Trac #37064. No GraphQL request can
observe whether a connection method was wrapped or declined; that is
connection-object identity, not a wire shape. There is no live sibling.

These tests don't require ``FAKESHOP_SHARDED=1``; the helper operates
on any Django connection, and the `default` alias is always present.
"""

from unittest import mock

import pytest
from django.db import connections
from django.db.backends.utils import CursorWrapper
from django.test.testcases import TransactionTestCase, _DatabaseFailure
from typing_extensions import override

from django_strawberry_framework.testing import safe_wrap_connection_method
from django_strawberry_framework.utils._narrowing import read_attr
from tests._idioms import call_remove_databases_failures


def _database_failure(wrapped: object) -> object:
    return _DatabaseFailure(wrapped, "test message")


def test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure() -> None:
    """Happy path: the helper installs the consumer's wrapper over a plain method.

    ``connection.<method>`` is NOT a ``_DatabaseFailure`` here.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    consumer_wrapper = mock.Mock(name="consumer_wrapper")

    try:
        installed = safe_wrap_connection_method(connection, "cursor", consumer_wrapper)

        assert installed is True
        assert connection.cursor is consumer_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_declines_when_database_failure_in_place(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Trac #37064 cooperative-wrap mirror: the helper refuses to clobber a failure.

    When Django has already installed ``_DatabaseFailure`` at the method, the helper
    leaves it in place and returns ``False``.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    django_wrapper = _database_failure(original_cursor)
    monkeypatch.setattr(connection, "cursor", django_wrapper)

    consumer_wrapper = mock.Mock(name="consumer_wrapper")

    try:
        installed = safe_wrap_connection_method(connection, "cursor", consumer_wrapper)

        assert installed is False
        # Django's wrapper was NOT replaced.
        assert connection.cursor is django_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_works_on_arbitrary_method_names() -> None:
    """Helper works for any disallowed-connection method, not just ``cursor``.

    Pinned so the helper doesn't accidentally become cursor-specific over time.
    """
    connection = connections["default"]
    original = connection.chunked_cursor

    chunked_wrapper = mock.Mock(name="chunked_wrapper")

    try:
        installed = safe_wrap_connection_method(
            connection,
            "chunked_cursor",
            chunked_wrapper,
        )

        assert installed is True
        assert connection.chunked_cursor is chunked_wrapper
    finally:
        connection.chunked_cursor = original


def test_safe_wrap_connection_method_leaves_djangos_teardown_a_clean_unwrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end composition of the helper with Django's setup/teardown pair.

    When a consumer uses :func:`safe_wrap_connection_method` while Django's
    ``_DatabaseFailure`` is in place, the helper declines, so Django's own
    ``_remove_databases_failures`` still finds its wrapper and restores the
    original method without any work from the consumer.

    The test wires up the full sequence: install a ``_DatabaseFailure`` on
    every method Django disallows (simulating ``_add_databases_failures``), have
    the consumer call ``safe_wrap_connection_method`` (which declines because
    the ``_DatabaseFailure`` is in place), then run Django's teardown method,
    which unwraps every one of them.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    sentinel_original = read_attr(mock.sentinel, "untouched_original")

    # Simulate Django's setUpClass installing its ``_DatabaseFailure`` wrappers.
    for name, _ in connection.features.disallowed_simple_test_case_connection_methods:
        if name != "cursor":
            monkeypatch.setattr(connection, name, _database_failure(read_attr(connection, name)))
    django_wrapper = _database_failure(sentinel_original)
    monkeypatch.setattr(connection, "cursor", django_wrapper)

    # The consumer attempts to wrap and is correctly declined - Django
    # already wrapped first.
    installed = safe_wrap_connection_method(
        connection,
        "cursor",
        mock.Mock(name="consumer_wrapper"),
    )
    assert installed is False
    assert connection.cursor is django_wrapper  # Django's wrapper intact

    # Now run Django's ``_remove_databases_failures`` against a synthetic
    # test class that disallows only ``default``. It restores the original
    # cursor cleanly.
    class _NarrowTest(TransactionTestCase):
        databases = set(connections) - {"default"}

    try:
        call_remove_databases_failures(_NarrowTest)
        # Wrapper unwrapped to the sentinel original.
        assert connection.cursor is sentinel_original
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_raises_on_non_callable_wrapper() -> None:
    """Wrap-time guard: a non-callable ``wrapper`` raises ``TypeError`` at the wrap site.

    It raises there instead of installing silently and failing at the next
    ``connection.<method>()`` invocation.

    Pins the wrap-time-vs-call-time silent-failure mode closed: the
    type annotation ``Callable[..., object]`` is enforced at runtime,
    so a typo (e.g. ``connection.cursor()`` - a cursor object, not
    callable - accidentally passed instead of
    ``lambda: connection.cursor()``) surfaces at the wrap site with a
    traceback pointing at the consumer's call.
    """
    connection = connections["default"]
    # The helper installs by ``setattr``, so "untouched" means the instance
    # ``__dict__`` slot is exactly as the guard found it. Comparing
    # ``connection.cursor`` instead would compare freshly-bound methods and
    # pass or fail on whether a NEIGHBOURING test left an instance attribute
    # behind. No try/finally: the guard raises before any mutation.
    installed_before = connection.__dict__.get("cursor")

    with pytest.raises(TypeError, match="non-callable wrapper"):
        # basedpyright: the non-callable wrapper is the hostile input under test;
        # safe_wrap_connection_method types the parameter as a callable
        safe_wrap_connection_method(connection, "cursor", 42)  # pyright: ignore[reportArgumentType]

    assert connection.__dict__.get("cursor") is installed_before


def test_safe_wrap_connection_method_keeps_type_error_boundary_for_hostile_repr() -> None:
    """A broken ``repr`` must not replace the documented non-callable ``TypeError``."""
    connection = connections["default"]
    installed_before = connection.__dict__.get("cursor")

    class _HostileRepr:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr exploded")

    with pytest.raises(TypeError, match="non-callable wrapper"):
        # basedpyright: the non-callable wrapper with a raising repr is the hostile input under
        # test; safe_wrap_connection_method types the parameter as a callable
        safe_wrap_connection_method(connection, "cursor", _HostileRepr())  # pyright: ignore[reportArgumentType]

    assert connection.__dict__.get("cursor") is installed_before


def test_safe_wrap_connection_method_accepts_callable_class_instance() -> None:
    """Any callable object (such as an instance with __call__) is accepted."""
    connection = connections["default"]
    original_cursor = connection.cursor

    class _CallableWrapper:
        def __call__(self, *args: object, **kwargs: object) -> CursorWrapper:
            return original_cursor(*args, **kwargs)

    instance = _CallableWrapper()
    try:
        installed = safe_wrap_connection_method(connection, "cursor", instance)
        assert installed is True
        assert connection.cursor is instance
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_raises_attribute_error_on_missing_method() -> None:
    """Attempting to wrap a non-existent connection method raises AttributeError."""
    connection = connections["default"]
    with pytest.raises(AttributeError):
        safe_wrap_connection_method(
            connection,
            "non_existent_method_on_connection",
            lambda: None,
        )
