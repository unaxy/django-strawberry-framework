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

``numeric_refusing_postgresql`` instead opens one: an in-memory SQLite database that reads
as PostgreSQL, refuses each statement binding a decimal past PostgreSQL ``numeric``'s format
with the ``DataError`` the server raises, and stores the models routed to it, so a write
flavor runs end to end against the refusal::

    with numeric_refusing_postgresql(Model) as alias:
        ...
"""

from __future__ import annotations

from contextlib import contextmanager
from types import ModuleType
from typing import TYPE_CHECKING

from django.db import DEFAULT_DB_ALIAS, DataError, connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.backends.sqlite3.operations import DatabaseOperations as SQLiteOperations
from django.test import override_settings
from typing_extensions import override

from django_strawberry_framework.utils.errors import refuses_numeric_format

if TYPE_CHECKING:
    import datetime
    from collections.abc import Callable, Generator

    from django.db import models


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


class PostgreSQLVersionStandIn(SQLiteDatabaseWrapper):
    """A SQLite-backed test alias with an explicit PostgreSQL server version."""

    server_major = 16

    @override
    def get_database_version(self) -> tuple[int, int]:
        return self.server_major, 0


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
    *,
    server_major: int = 16,
) -> Generator[str, None, None]:
    """Register an alias that reads as PostgreSQL, on ``driver`` and ``cursor_factory``.

    Its adapters pass every datetime, time and duration through, as Django's PostgreSQL
    adapters do, its features name the native duration column (``has_native_duration_field``,
    which Django reads in place of the duration adapter on some releases), and it is never
    opened: the binding mode is read from its connection parameters. Its
    settings carry the ``TIME_ZONE`` key Django's connection handler fills in.
    ``server_major`` determines the PostgreSQL parser rule at its exponent endpoint.
    """
    alias = "postgresql_stand_in"
    wrapper = PostgreSQLVersionStandIn(
        {"NAME": "stand-in", "TIME_ZONE": None, "OPTIONS": {"cursor_factory": cursor_factory}},
        alias,
    )
    wrapper.server_major = server_major
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


class _RoutedTo:
    """A router sending reads and writes of ``routed`` to ``alias``; every other model is not its."""

    def __init__(self, alias: str, routed: tuple[type[models.Model], ...]) -> None:
        self.alias = alias
        self.routed = routed

    def db_for_read(self, model: type[models.Model], **_hints: object) -> str | None:
        """``alias`` for a routed model."""
        return self.alias if model in self.routed else None

    def db_for_write(self, model: type[models.Model], **_hints: object) -> str | None:
        """``alias`` for a routed model."""
        return self.alias if model in self.routed else None


@contextmanager
def numeric_refusing_postgresql(*routed: type[models.Model]) -> Generator[str, None, None]:
    """Open an alias that reads as PostgreSQL, refuses a decimal past ``numeric``, and holds ``routed``.

    An in-memory SQLite database relabelled ``postgresql``: before each statement runs,
    its parameters are held to ``utils/errors.py::refuses_numeric_format``, and a decimal
    past ``numeric``'s format raises the ``DataError`` PostgreSQL's ``numeric_in`` raises
    at the bind ("value overflows numeric format"). Storage is SQLite's, so only the
    refusal is PostgreSQL's. The tables of ``routed`` are created on it, and every read
    and write of those models is routed to it.
    """
    alias = "postgresql_numeric_stand_in"
    wrapper = PostgreSQLVersionStandIn(
        {**connections.databases[DEFAULT_DB_ALIAS], "NAME": ":memory:", "OPTIONS": {}},
        alias,
    )
    wrapper.vendor = "postgresql"

    def refuse(
        execute: Callable[
            [
                str,
                object,
                bool,
                dict[str, object],
            ],
            object,
        ],
        sql: str,
        params: object,
        many: bool,  # noqa: FBT001
        context: dict[str, object],
    ) -> object:
        if refuses_numeric_format(wrapper, [params]):
            message = "value overflows numeric format"
            raise DataError(message)
        return execute(sql, params, many, context)

    connections[alias] = wrapper
    try:
        with (
            wrapper.execute_wrapper(refuse),
            override_settings(DATABASE_ROUTERS=[_RoutedTo(alias, routed)]),
        ):
            with wrapper.schema_editor() as editor:
                for model in routed:
                    editor.create_model(model)
            yield alias
    finally:
        # SQLite's ``close()`` keeps an in-memory database open; the base close ends it.
        BaseDatabaseWrapper.close(wrapper)
        del connections[alias]
