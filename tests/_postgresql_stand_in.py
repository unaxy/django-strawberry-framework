"""Shared database alias that reads as PostgreSQL on every test tier, never opened.

``postgresql_stand_in`` registers an SQLite wrapper whose ``vendor`` is ``postgresql``,
on a stand-in driver module and the ``cursor_factory`` Django connects with, so a rule
that reads the connection's vendor and binding mode
(``django_strawberry_framework/utils/errors.py::refuses_utc_offset``) answers as it does
on PostgreSQL without a server. Its operations (``StoringOperations``) are SQLite's, so a
predicate compiles on it, except that they pass every datetime and time through, as
PostgreSQL's adapters do, so the value reaches the rule (a compiled predicate's
parameters included) rather than SQLite's own refusal, and a duration binds as the
``timedelta`` itself, PostgreSQL's native ``interval``. ``BINDING_MODES`` names each binding mode a
PostgreSQL connection can run in::

    driver, cursor_factory, client_side = BINDING_MODES["psycopg3-client"]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        ...
"""

from __future__ import annotations

from contextlib import contextmanager
from types import ModuleType
from typing import TYPE_CHECKING

from django.db import connections
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.backends.sqlite3.operations import DatabaseOperations as SQLiteOperations
from typing_extensions import override

if TYPE_CHECKING:
    import datetime
    from collections.abc import Generator


class StoringOperations(SQLiteOperations):
    """SQLite's operations, whose adapters pass datetimes, times and durations through.

    PostgreSQL's adapters pass all three through.
    """

    # basedpyright: django-stubs types the adapter ``str | None``; PostgreSQL's returns the
    # value itself, which this stand-in reproduces. It rejects the wider return
    @override
    def adapt_datetimefield_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        value: datetime.datetime | None,
    ) -> datetime.datetime | None:
        return value

    # basedpyright: django-stubs types the adapter ``str | None``; PostgreSQL's returns the
    # value itself, which this stand-in reproduces. It rejects the wider return
    @override
    def adapt_timefield_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        value: datetime.datetime | datetime.time | None,
    ) -> datetime.datetime | datetime.time | None:
        return value

    # basedpyright: django-stubs types the adapter ``int | None``; PostgreSQL's returns the
    # value itself, which this stand-in reproduces. It rejects the wider return
    @override
    def adapt_durationfield_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        value: datetime.timedelta | None,
    ) -> datetime.timedelta | None:
        return value


class ClientCursor:
    """psycopg 3's ``ClientCursor``: it binds every parameter into the query text."""


class DjangoClientCursor(ClientCursor):
    """Django's default psycopg 3 cursor class, a ``ClientCursor``."""


class ServerBindingCursor:
    """psycopg 3's ``Cursor``, which binds parameters on the server."""


def driver_module(**exports: type[object]) -> ModuleType:
    """A database driver module exporting ``exports``."""
    module = ModuleType("driver_stand_in")
    vars(module).update(exports)
    return module


#: Each binding mode a PostgreSQL connection can run in: its driver module, the
#: ``cursor_factory`` Django connects with (psycopg 2 exports no ``ClientCursor``; a
#: psycopg 3 ``cursor_factory`` of ``None`` is psycopg's own server-binding ``Cursor``),
#: and whether it binds parameters as text on the client.
BINDING_MODES = {
    "psycopg2": (driver_module(), DjangoClientCursor, True),
    "psycopg3-client": (driver_module(ClientCursor=ClientCursor), DjangoClientCursor, True),
    "psycopg3-server": (driver_module(ClientCursor=ClientCursor), ServerBindingCursor, False),
    "psycopg3-default-cursor": (driver_module(ClientCursor=ClientCursor), None, False),
}


@contextmanager
def postgresql_stand_in(
    driver: ModuleType,
    cursor_factory: type[object] | None,
) -> Generator[str, None, None]:
    """Register an alias that reads as PostgreSQL, on ``driver`` and ``cursor_factory``.

    Its adapters pass every datetime, time and duration through, as Django's PostgreSQL
    adapters do, its features name the native duration column (``has_native_duration_field``,
    which Django reads in place of the duration adapter on some releases), and it is never
    opened: the binding mode is read from its connection parameters. Its
    settings carry the ``TIME_ZONE`` key Django's connection handler fills in.
    """
    alias = "postgresql_stand_in"
    wrapper = SQLiteDatabaseWrapper(
        {"NAME": "stand-in", "TIME_ZONE": None, "OPTIONS": {"cursor_factory": cursor_factory}},
        alias,
    )
    wrapper.vendor = "postgresql"
    wrapper.Database = driver
    connections[alias] = wrapper
    stand_in = connections[alias]
    stand_in.ops = StoringOperations(stand_in)
    stand_in.features.has_native_duration_field = True
    try:
        yield alias
    finally:
        del connections[alias]
