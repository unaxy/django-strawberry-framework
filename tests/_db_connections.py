"""Close SQLite task and executor connections across every test tree.

Django's main-thread teardown cannot reach task-context or executor-thread
connection storage. Task handles are drained after their test; reusable executor
handles stay alive until session teardown. Retaining them also prevents a later
GC cycle from reporting an unclosed handle against an unrelated test.
"""

import asyncio
import contextlib
import sqlite3
import threading
from collections.abc import Iterator

import pytest
from django.db.backends.sqlite3 import base as sqlite_base

from django_strawberry_framework.utils._narrowing import require_instance
from django_strawberry_framework.utils.typing import object_result

# Task-local handles cannot be reused after the owning test task ends.
# Executor-thread handles can be reused, so hold those until session teardown.
# Both registries retain handles until their cleanup rather than letting GC
# attribute ResourceWarning to whichever unrelated test happens to run next.
_context_local_connections: list[sqlite3.Connection] = []
_executor_connections: list[sqlite3.Connection] = []

_original_get_new_connection = sqlite_base.DatabaseWrapper.get_new_connection


def _tracking_get_new_connection(
    self: sqlite_base.DatabaseWrapper,
    conn_params: object,
) -> sqlite3.Connection:
    """Retain task-local and executor handles under their actual lifetimes."""
    # django-stubs types ``get_new_connection`` as returning ``Any``; the SQLite backend
    # returns the ``sqlite3.Connection`` the teardown closes.
    connection = require_instance(
        object_result(_original_get_new_connection, self, conn_params),
        sqlite3.Connection,
    )
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        if threading.current_thread() is not threading.main_thread():
            _executor_connections.append(connection)
    else:
        _context_local_connections.append(connection)
    return connection


sqlite_base.DatabaseWrapper.get_new_connection = _tracking_get_new_connection


@pytest.fixture(autouse=True)
def _close_context_local_db_connections() -> Iterator[None]:
    """Close per-task SQLite connections an async test left open.

    Runs as a *sync* fixture so its teardown always executes (an ``async``
    fixture's teardown runs in a different contextvar context and could not see
    these connections anyway). By teardown the owning asyncio task is gone, so
    the connection will never be reused - closing the raw handle here simply
    pre-empts the GC finalizer that would otherwise trip ``ResourceWarning``.
    """
    yield
    while _context_local_connections:
        connection = _context_local_connections.pop()
        with contextlib.suppress(Exception):
            connection.close()


@pytest.fixture(autouse=True, scope="session")
def _close_executor_db_connections(django_db_setup: None) -> Iterator[None]:
    """Keep reusable executor handles alive, then close before database teardown."""
    del django_db_setup
    yield
    while _executor_connections:
        connection = _executor_connections.pop()
        with contextlib.suppress(sqlite3.Error):
            connection.close()
