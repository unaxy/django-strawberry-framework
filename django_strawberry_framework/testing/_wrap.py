"""Cooperative connection-method wrapping for consumer test instrumentation.

Guards against Django Trac #37064 at wrap time. Consumers (or
third-party libraries) that need to replace a method on
``django.db.connections[alias]`` between ``setUpClass`` and
``tearDownClass`` use :func:`safe_wrap_connection_method` to install
their wrapper. The helper refuses to wrap when Django's
``_DatabaseFailure`` is already in place - mirroring the pattern
``django-debug-toolbar`` ships in
:func:`debug_toolbar.panels.sql.tracking.wrap_cursor`.
"""

from typing import TYPE_CHECKING

from django.test.testcases import _DatabaseFailure

from django_strawberry_framework.utils._narrowing import read_attr

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.backends.base.base import BaseDatabaseWrapper


def _require_callable_wrapper(wrapper: object) -> None:
    """Refuse a non-callable ``wrapper`` with the ``TypeError`` the wrap site documents.

    The annotation is the contract; this is the boundary for a caller with no type
    checker, per GOAL.md "Trust boundary" configuration validation.
    """
    if not callable(wrapper):
        raise TypeError("safe_wrap_connection_method() received a non-callable wrapper")


def safe_wrap_connection_method(
    connection: "BaseDatabaseWrapper",
    method_name: str,
    wrapper: "Callable[..., object]",
) -> bool:
    """Wrap a connection method, declining if Django wrapped it first.

    Designed to be called by code that needs to monkey-patch a Django
    database-connection method (typically ``cursor``,
    ``chunked_cursor``, or ``create_cursor``) between ``setUpClass``
    and ``tearDownClass``. Examples include test ``setUp`` methods
    that swap a cursor for a mock, debug middleware that wraps a
    cursor to log queries, or instrumentation libraries that intercept
    SQL.

    The helper checks whether Django's ``_DatabaseFailure`` wrapper is
    already installed at the named method. If it is, the helper
    declines to install ``wrapper`` and returns ``False``; the
    connection method is left untouched. If it isn't, ``wrapper`` is
    installed and the helper returns ``True``.

    The reason this matters: Django's
    :meth:`django.test.testcases.SimpleTestCase._add_databases_failures`
    installs a ``_DatabaseFailure`` wrapper on every "disallowed"
    connection method at ``setUpClass``, and the symmetric
    ``_remove_databases_failures`` unwraps them at ``tearDownClass``
    by reading ``method.wrapped``. If any third-party code (or
    ``setUp``) overwrites that ``_DatabaseFailure`` with a plain
    callable, the upstream teardown crashes with
    ``AttributeError: 'function' object has no attribute 'wrapped'``
    (Django Trac #37064, closed ``wontfix`` -
    <https://code.djangoproject.com/ticket/37064>).

    This helper declines to clobber Django's wrapper in the first
    place. Mirror precedent: ``django-debug-toolbar``'s
    :func:`debug_toolbar.panels.sql.tracking.wrap_cursor` ships the
    same isinstance check at its own wrap site. See
    <https://github.com/django-commons/django-debug-toolbar/blob/main/debug_toolbar/panels/sql/tracking.py>.

    **Restoration semantics.** This helper handles only the wrap step.
    Consumers who need to restore the original method in ``tearDown``
    are responsible for saving it beforehand:

    .. code-block:: python

        from django.db import connections
        from django.test import TransactionTestCase
        from django_strawberry_framework.testing import safe_wrap_connection_method


        class _MyTest(TransactionTestCase):
            def setUp(self):
                super().setUp()
                self._connection = connections["default"]
                self._original_cursor = self._connection.cursor

                def my_wrapped_cursor(*args, **kwargs):
                    return self._original_cursor(*args, **kwargs)

                self._wrapped = safe_wrap_connection_method(
                    self._connection, "cursor", my_wrapped_cursor,
                )

            def tearDown(self):
                if self._wrapped:
                    self._connection.cursor = self._original_cursor
                super().tearDown()

    Omitting the ``tearDown`` restoration leaves ``wrapper`` in place
    over the slot Django's teardown unwraps, which crashes there
    (Trac #37064); restoring also lets debug-toolbar-style
    wrap-time-isinstance checks in OTHER libraries find a clean slot
    on the next ``setUpClass``.

    Args:
        connection: A Django ``BaseDatabaseWrapper`` instance (i.e.
            ``django.db.connections[alias]``).
        method_name: The attribute name to replace on ``connection``
            (e.g. ``"cursor"``, ``"chunked_cursor"``,
            ``"create_cursor"``).
        wrapper: The callable that should replace the named method.
            Will be installed only if Django's ``_DatabaseFailure``
            wrapper isn't already in place at the named attribute.

    Returns:
        ``True`` if ``wrapper`` was installed; ``False`` if Django's
        ``_DatabaseFailure`` was in place and the wrap was declined
        (the connection method is left untouched).

    Raises:
        TypeError: If ``wrapper`` is not callable. Validated at the
            wrap site so a typo (e.g. passing ``connection.cursor()``
            - the cursor object, not a callable - instead of
            ``lambda: connection.cursor()``) surfaces here rather than
            as a delayed ``TypeError`` deep inside Django's ORM
            machinery at the next ``connection.<method>()`` call.

    """
    _require_callable_wrapper(wrapper)
    current = read_attr(connection, method_name)
    if isinstance(current, _DatabaseFailure):
        return False
    setattr(connection, method_name, wrapper)
    return True
