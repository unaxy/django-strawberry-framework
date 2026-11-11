"""Live GraphQL HTTP tests for model input normalization and database storability.

The ``scalars`` app writes ``ScalarSpecimen.occurred_at`` (``DateTime``) and
``occurred_time`` (``Time``) through every write flavor: ``createScalarSpecimen`` /
``updateScalarSpecimen`` (``DjangoMutation``), their ``ViaForm`` siblings
(``DjangoModelFormMutation`` over ``ScalarSpecimenTemporalForm``) and their
``ViaSerializer`` siblings (``SerializerMutation`` over
``ScalarSpecimenTemporalSerializer``). A value each flavor's own parse and validation
accept can still be one the database cannot store: on SQLite an aware datetime whose
projection onto the connection's time zone leaves years 1..9999 (a naive one made
aware under a non-UTC ``TIME_ZONE`` included), any aware datetime under
``USE_TZ = False`` and an aware time; on PostgreSQL an aware datetime whose wall clock
in the session time zone leaves years 1..9999, which it stores but cannot load back, and
an aware datetime or time whose UTC offset the server refuses (16:00 or more either way,
or, bound as text as Django's default psycopg cursor binds, a fraction of a second).
Each is the field's ``invalid`` ``FieldError`` ("Enter a value the database can
represent.") with nothing written, on create and update, sync and async, never the
masked unexpected error. DRF's own ``overflow`` answer for an aware datetime it cannot
project onto the current time zone stands, and the serializer flavor answers the same
``overflow`` error for a datetime DRF cannot place: a naive one that leaves years 1..9999
once made aware under a non-UTC ``TIME_ZONE``, and an aware one whose UTC projection
leaves them under ``USE_TZ = False``. A value a flavor stores (the
serializer's naive projection under ``USE_TZ = False``, the serializer's projection of
an aware datetime onto the current time zone, an aware time whose offset PostgreSQL
accepts, there) is written.

``createScalarSpecimen`` / ``updateScalarSpecimen`` also write the bounded
``ScalarSpecimen.price``: a zero past PostgreSQL ``numeric``'s exponent limit
(``0E+9999999999``), which its ``DecimalValidator`` passes since it counts no digit for a
zero's positive exponent, is the field's ``invalid`` ``FieldError`` with nothing written on
PostgreSQL, where the server would refuse the bind, and is stored as zero on SQLite, which
stores a decimal as an integer or its nearest double. ``9999999999999999.9999``, which
SQLite stores as ``10000000000000000``, a digit past ``DecimalField(20, 4)`` that the
re-fetch cannot read back, is the same error with nothing written on SQLite and is stored
on PostgreSQL; ``9999999999999995.0000``, stored as the integer ``9999999999999996``, is
written and read back as it on Django 6.1, which reads an integer exactly, and refused on
Django 5.2 / 6.0, which round it to 15 digits.

The ``SplitForm`` pairs write ``occurred_at`` through a ``SplitDateTimeField``, whose
widget reads a date key and a time key: the datetime sent is stored on create and update
and kept when omitted, unprefixed, under the form's prefix and beside a ``get_form``'s own
prefixed copy. The ``ViaPosted`` pairs' ``get_form_kwargs`` binds each value as its text:
the temporal form's one-key ``DateTimeField`` parses and stores it, while the split
widget's ``decompress`` cannot split the text of a datetime, a ``ConfigurationError``
naming its keys before ``is_valid()``, masked on the wire, with nothing written on
create, update or an update omitting ``occurredAt``. A datetime whose wall clock in the
current time zone leaves years 1..9999 cannot be split either: the split form answers the
``occurredAt`` ``invalid`` ``FieldError`` ("Enter a value the current time zone can
represent."), even for ``0001-01-01T00:30:00+00:00``, which the database stores, on create,
update and an update omitting ``occurredAt`` over such a stored value, sync and async.

The ``DayInstantForm`` pair writes ``occurred_on`` through a ``clean_occurred_on`` answering
the aware midnight UTC of the date sent, which the ``DateField`` column stores as its date
in the default time zone. Under ``America/New_York`` the midnight of ``0001-01-01`` falls in
year 0 there, where Django's own conversion inside ``is_valid()`` would raise
``OverflowError``: the mutation answers the ``occurredOn`` ``invalid`` ``FieldError`` before
that conversion, with nothing written, sync and async, while ``UTC`` stores the date and an
in-range day is stored as its date in the default time zone.

``createNullableScalarSpecimenViaForm`` / ``updateNullableScalarSpecimenViaForm`` write the
``null=True`` ``NullableScalarSpecimen.flag`` through a checkbox
(``NullableScalarSpecimenFlagForm``), which reads a bound ``None`` as ``False``: an explicit
``flag: null`` on create and on update over ``true``, ``false`` or ``NULL``, and an update
omitting ``flag`` over a stored ``NULL``, store ``NULL`` with empty ``errors``, sync and
async, while ``true`` / ``false`` are written and an update omitting ``flag`` over a value
keeps it. The text column ``label`` sent ``null`` keeps the ``""`` its form field cleans the
``null`` to. The same form writes the ``null=True`` JSON column ``payload`` through a
``CharField``, which cleans ``null`` to ``""``: an explicit ``payload: null`` on create and on
update over a value or ``NULL``, and an update omitting it over ``NULL``, store ``NULL``, while
a string sent is stored as that JSON string and one stored is kept when omitted. ``payload`` is
the ``CharField``'s ``String``: an object, list, number or boolean sent is the variable
coercion error with nothing written, and the JSON text of an object is stored as that JSON
string. An update omitting ``label`` and ``payload`` keeps each column's stored value where
the form field's own cleaning would rewrite it: a ``"  padded  "`` label is not stripped, a
``NULL`` label is not written ``""``, and a JSON object or list is not written as its Python
text, sync and async.
The same form writes the ``null=True`` float column ``score`` through a ``CharField``, whose
``""`` the column cannot store: an explicit ``score: null`` on create and on update over a
value or ``NULL``, and a create omitting it, store ``NULL`` with empty ``errors``, sync and
async, where the column's ``null`` error would be false; an update omitting it keeps the
stored value. A create omitting ``flag`` or ``payload`` stores ``NULL`` too, while one
omitting the text column ``label`` keeps ``""``.

``createNullableScalarSpecimenViaJsonTextForm`` / ``updateNullableScalarSpecimenViaJsonTextForm``
write ``payload`` through ``NullableScalarSpecimenJsonTextForm``'s ``JsonTextField``, a
``CharField`` parsing JSON text, typed ``String``: the JSON text of an object, list, string,
number, boolean or ``null`` sent is stored as that JSON value, a raw object or list sent is the
variable coercion error and text that is no JSON the field's ``invalid`` error, nothing
written; an update omitting ``payload`` binds the field's presentation of the stored value,
its JSON text, and keeps a stored object, list, string, number or ``NULL``, sync and async.

``updateScalarSpecimenViaLockedStampForm`` writes through a form disabling ``occurred_at``,
``occurred_time`` and ``external_id``: an update keeps each one's stored value, the
microseconds the ``DateTimeInput`` / ``TimeInput`` presentation of a stored instant zeroes
included, whether it omits the field or sends a value Django ignores, sync and async.

The ``UniqueScalarSpecimen`` ``ViaForm`` and ``ViaSerializer`` pairs write columns each under
a uniqueness rule (``openedTime`` ``unique=True``, ``openedAt`` unique together with
``label``, ``amount`` a conditional ``UniqueConstraint``), which the ``ModelForm``'s
``validate_unique()`` / ``validate_constraints()`` and DRF's uniqueness validators bind in a
query inside ``is_valid()``. A value the database cannot store is the field's ``invalid``
``FieldError`` before that query, on create and update, with nothing written: on SQLite the
form's aware ``openedTime`` and, under ``USE_TZ = False``, aware ``openedAt``, the
serializer's ``validate_opened_at`` instant past year 9999 in UTC, and the serializer's aware
``openedTime``, and the form's and the serializer's ``amount`` sent
``9999999999999999.9999``, which SQLite stores past the column's digits; on PostgreSQL the
form's ``amount`` and the digitless ``amount`` of
``createUniqueScalarSpecimenViaUnboundedAmountSerializer`` sent a zero past ``numeric``'s
exponent limit. A value each flavor stores is written.

``createScalarSpecimenTagWithUniqueSpecimens`` writes a tag and a bundle of specimens, a nested
``specimens`` list of ``UniqueScalarSpecimenSerializer`` items, whose uniqueness validators
bind each item's ``openedTime`` and ``openedAt`` in a query inside ``is_valid()``. On SQLite
the second item's ``validate_opened_at`` instant past year 9999 in UTC is
``specimens.1.openedAt``'s ``invalid`` ``FieldError`` before that query, no tag and no specimen
written; PostgreSQL binds it and the serializer's own ``create()`` writes it. An aware
``openedTime``, whose bind DRF reads as no duplicate, reaches ``create()``, which stores its
wall clock; an in-range instant and a naive time are written; each with its exact statement
count.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import django
import pytest
from apps.scalars import models
from asgiref.sync import sync_to_async
from config import schema as config_schema
from django.db import DataError, connection, transaction
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.utils import timezone
from graphql_client import JSONObject, json_at, post_graphql, response_json

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import is_dict, is_list_or_tuple
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import AsyncDjangoGraphQLView

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http.response import HttpResponseBase

_UNSTORABLE = "Enter a value the database can represent."
_UNREPRESENTABLE_IN_ZONE = "Enter a value the current time zone can represent."

#: The input a flavor writes a column through, where it differs from the column's own name:
#: the serializer renames ``occurred_time`` to ``clock_time`` by ``source=``.
_RENAMED_INPUTS = {"serializer": {"occurredTime": "clockTime"}}


def _input_name(flavor: str, field: str) -> str:
    """The GraphQL input ``flavor`` writes the column ``field`` names through."""
    return _RENAMED_INPUTS.get(flavor, {}).get(field, field)


#: Each flavor's create and update root fields and their input types.
_FLAVORS = {
    "model": (
        "createScalarSpecimen",
        "ScalarSpecimenInput",
        "updateScalarSpecimen",
        "ScalarSpecimenPartialInput",
    ),
    "form": (
        "createScalarSpecimenViaForm",
        "ScalarSpecimenTemporalFormInput",
        "updateScalarSpecimenViaForm",
        "ScalarSpecimenTemporalFormPartialInput",
    ),
    "serializer": (
        "createScalarSpecimenViaSerializer",
        "ScalarSpecimenTemporalSerializerInput",
        "updateScalarSpecimenViaSerializer",
        "ScalarSpecimenTemporalSerializerPartialInput",
    ),
}

#: The stored row an update starts from, and the values a create supplies beside the cell's.
_STORED_AT = datetime.datetime(2020, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)
_STORED_TIME = datetime.time(3, 4, 5)
_CREATE_DATA: dict[str, object] = {
    "label": "written",
    "occurredOn": "2021-06-15",
    "occurredAt": "2021-06-15T09:30:00+00:00",
    "occurredTime": "09:30:00",
    "externalId": "12345678-1234-5678-1234-567812345678",
}

# Outcomes: the package's refusal, DRF's own ``overflow`` refusal, a written row.
_REFUSED = "refused"
_OVERFLOW = "overflow"
_STORED = "stored"


@contextmanager
def _database_time_zone(zone: str) -> Generator[None, None, None]:
    """Set the ``default`` connection's ``DATABASES`` ``TIME_ZONE`` (a SQLite / MySQL / Oracle key)."""
    saved = connection.settings_dict.copy()
    connection.settings_dict["TIME_ZONE"] = zone
    _ = connection.timezone, connection.timezone_name
    del connection.timezone, connection.timezone_name
    try:
        yield
    finally:
        connection.settings_dict.update(saved)
        _ = connection.timezone, connection.timezone_name
        del connection.timezone, connection.timezone_name


@contextmanager
def _configured(
    settings: Mapping[str, object],
    database_zone: str | None,
) -> Generator[None, None, None]:
    """Apply a cell's settings overrides and, when named, the connection's own time zone."""
    with override_settings(**settings):
        if database_zone is None:
            yield
            return
        with _database_time_zone(database_zone):
            yield


class _Cell:
    """One input the grid writes: its field, value, configuration and outcome per flavor."""

    def __init__(
        self,
        field: str,
        value: str,
        outcomes: Mapping[str, tuple[str, str]],
        *,
        settings: Mapping[str, object] | None = None,
        database_zone: str | None = None,
    ) -> None:
        self.field = field
        self.value = value
        self.outcomes = outcomes
        self.settings = dict(settings or {})
        self.database_zone = database_zone

    def outcome(self, flavor: str) -> str:
        """The outcome ``flavor`` answers on the database the suite runs on."""
        sqlite, postgresql = self.outcomes[flavor]
        return postgresql if connection.vendor == "postgresql" else sqlite


def _every(sqlite: str, postgresql: str) -> dict[str, tuple[str, str]]:
    return dict.fromkeys(_FLAVORS, (sqlite, postgresql))


_CELLS = {
    "in-range": _Cell("occurredAt", "2021-06-15T09:30:00+02:00", _every(_STORED, _STORED)),
    "before-year-one": _Cell(
        "occurredAt",
        "0001-01-01T00:00:00+01:00",
        {**_every(_REFUSED, _REFUSED), "serializer": (_OVERFLOW, _OVERFLOW)},
    ),
    "past-year-9999": _Cell(
        "occurredAt",
        "9999-12-31T23:00:00-01:00",
        {**_every(_REFUSED, _REFUSED), "serializer": (_OVERFLOW, _OVERFLOW)},
    ),
    "aware-time": _Cell("occurredTime", "09:30:00+02:00", _every(_REFUSED, _STORED)),
    "naive-year-one-under-tokyo": _Cell(
        "occurredAt",
        "0001-01-01T05:00:00",
        {**_every(_REFUSED, _REFUSED), "serializer": (_OVERFLOW, _OVERFLOW)},
        settings={"TIME_ZONE": "Asia/Tokyo"},
    ),
    "naive-past-year-9999-under-new-york": _Cell(
        "occurredAt",
        "9999-12-31T23:00:00",
        {"serializer": (_OVERFLOW, _OVERFLOW)},
        settings={"TIME_ZONE": "America/New_York"},
    ),
    "aware-year-one-under-tokyo": _Cell(
        "occurredAt",
        "0001-01-01T05:00:00+09:00",
        {**_every(_REFUSED, _REFUSED), "serializer": (_OVERFLOW, _OVERFLOW)},
        settings={"TIME_ZONE": "Asia/Tokyo"},
    ),
    "aware-without-time-zone-support": _Cell(
        "occurredAt",
        "2021-06-15T09:30:00+00:00",
        {**_every(_REFUSED, _STORED), "serializer": (_STORED, _STORED)},
        settings={"USE_TZ": False},
    ),
    "before-year-one-without-time-zone-support": _Cell(
        "occurredAt",
        "0001-01-01T00:00:00+01:00",
        {"serializer": (_OVERFLOW, _OVERFLOW)},
        settings={"USE_TZ": False},
    ),
    "past-year-9999-without-time-zone-support": _Cell(
        "occurredAt",
        "9999-12-31T23:00:00-01:00",
        {"serializer": (_OVERFLOW, _OVERFLOW)},
        settings={"USE_TZ": False},
    ),
    "past-year-9999-in-the-database-zone": _Cell(
        "occurredAt",
        "9999-12-31T20:00:00+00:00",
        _every(_REFUSED, _REFUSED),
        database_zone="Asia/Tokyo",
    ),
    "datetime-offset-16": _Cell(
        "occurredAt",
        "2021-06-15T09:30:00+16:00",
        {**_every(_STORED, _REFUSED), "serializer": (_STORED, _STORED)},
    ),
    "datetime-offset-minus-23-59": _Cell(
        "occurredAt",
        "2021-06-15T09:30:00-23:59",
        {**_every(_STORED, _REFUSED), "serializer": (_STORED, _STORED)},
    ),
    "time-offset-16": _Cell("occurredTime", "09:30:00+16:00", _every(_REFUSED, _REFUSED)),
    "time-offset-half-second": _Cell(
        "occurredTime",
        "09:30:00+01:00:00.500000",
        _every(_REFUSED, _REFUSED),
    ),
    "time-offset-whole-seconds": _Cell(
        "occurredTime",
        "09:30:00+01:00:30",
        _every(_REFUSED, _STORED),
    ),
}

_GRID = [
    pytest.param(flavor, operation, name, id=f"{flavor}-{operation}-{name}")
    for name, cell in _CELLS.items()
    for flavor in _FLAVORS
    if flavor in cell.outcomes
    for operation in ("create", "update")
]


def _document(flavor: str, operation: str) -> tuple[str, str]:
    """Return the mutation's root field and its document over ``$data`` (and ``$id``)."""
    create_field, create_input, update_field, update_input = _FLAVORS[flavor]
    if operation == "create":
        arguments, root = f"$data: {create_input}!", create_field
        call = f"{root}(data: $data)"
    else:
        arguments, root = f"$id: ID!, $data: {update_input}!", update_field
        call = f"{root}(id: $id, data: $data)"
    document = f"""
        mutation Write({arguments}) {{
          {call} {{
            result {{ label }}
            errors {{ field messages codes path }}
          }}
        }}
    """
    return root, document


def _seed() -> models.ScalarSpecimen:
    return models.ScalarSpecimen.objects.create(
        label="stored",
        occurred_on=datetime.date(2020, 1, 2),
        occurred_at=_STORED_AT,
        occurred_time=_STORED_TIME,
        external_id=uuid.uuid4(),
    )


def _variables(
    flavor: str,
    operation: str,
    cell: _Cell,
    specimen: models.ScalarSpecimen | None,
) -> dict[str, object]:
    field = _input_name(flavor, cell.field)
    if operation == "create":
        data = {_input_name(flavor, name): value for name, value in _CREATE_DATA.items()}
        return {"data": {**data, field: cell.value}}
    assert specimen is not None
    return {"id": str(specimen.pk), "data": {field: cell.value}}


def _expected(
    flavor: str,
    root: str,
    outcome: str,
    cell: _Cell,
    label: str,
) -> dict[str, object]:
    if outcome == _STORED:
        return {"data": {root: {"result": {"label": label}, "errors": []}}}
    message, code = (
        (_UNSTORABLE, "invalid")
        if outcome == _REFUSED
        else ("Datetime value out of range.", "overflow")
    )
    field = _input_name(flavor, cell.field)
    error = {
        "field": field,
        "messages": [message],
        "codes": [code],
        "path": [field],
    }
    return {"data": {root: {"result": None, "errors": [error]}}}


def _assert_rows(
    operation: str,
    outcome: str,
    specimen: models.ScalarSpecimen | None,
    cell: _Cell,
) -> None:
    """A refusal writes nothing: no created row, the updated row's stored values kept.

    Read under the suite's own settings, after the cell's configuration is restored.
    """
    labels = list(models.ScalarSpecimen.objects.order_by("label").values_list("label", flat=True))
    if operation == "create":
        assert labels == (["written"] if outcome == _STORED else []), labels
        return
    assert specimen is not None
    assert labels == ["stored"], labels
    stored = models.ScalarSpecimen.objects.values("occurred_at", "occurred_time").get(
        pk=specimen.pk,
    )
    if outcome != _STORED:
        assert stored == {"occurred_at": _STORED_AT, "occurred_time": _STORED_TIME}, stored
        return
    column = "occurred_at" if cell.field == "occurredAt" else "occurred_time"
    original = _STORED_AT if column == "occurred_at" else _STORED_TIME
    assert stored[column] != original, stored


@pytest.mark.django_db
@pytest.mark.parametrize(("flavor", "operation", "name"), _GRID)
def test_temporal_value_the_database_cannot_store_is_the_field_error(
    flavor: str,
    operation: str,
    name: str,
) -> None:
    """Each flavor refuses a datetime or time the database cannot store as the field's error.

    The refusal is the in-band ``invalid`` ``FieldError`` keyed to the input field, the
    result slot ``null``, nothing created and an updated row's stored values kept, on
    every flavor, create and update. On PostgreSQL a UTC offset of 16:00 or more either
    way, or a time's offset carrying a fraction of a second, is refused too. A value the
    database stores (``in-range``, the serializer's naive projection under
    ``USE_TZ = False``, the serializer's projection of an aware datetime onto the current
    time zone, which drops any offset, and on PostgreSQL an aware time whose offset it
    accepts) is written, and DRF's own ``overflow`` answer for an aware datetime it cannot
    project onto the current time zone stands. The serializer flavor answers that
    ``overflow`` error for every datetime DRF cannot place: a naive one made aware under a
    non-UTC ``TIME_ZONE`` and an aware one projected onto UTC under ``USE_TZ = False``,
    outside years 1..9999. The connection's own ``TIME_ZONE`` is a
    SQLite / MySQL / Oracle setting, so that cell runs on SQLite only.
    """
    cell = _CELLS[name]
    if cell.database_zone is not None and connection.vendor == "postgresql":
        pytest.skip("DATABASES TIME_ZONE is refused under USE_TZ on PostgreSQL")
    specimen = None if operation == "create" else _seed()
    root, document = _document(flavor, operation)
    with _configured(cell.settings, cell.database_zone):
        payload = response_json(
            post_graphql(document, variables=_variables(flavor, operation, cell, specimen)),
        )
    outcome = cell.outcome(flavor)
    label = "written" if operation == "create" else "stored"

    assert payload == _expected(flavor, root, outcome, cell, label)
    _assert_rows(operation, outcome, specimen, cell)


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_serializer_temporal_refusal_is_keyed_to_the_renamed_input(operation: str) -> None:
    """A serializer field renamed onto a temporal column by ``source=`` keys its refusal.

    ``clockTime`` writes ``occurred_time`` (DRF's ``source="occurred_time"``): an aware time
    SQLite cannot store is the ``invalid`` error under ``clockTime``, never under the column
    name, with nothing written, and a naive time sent the same way is stored in the column.
    PostgreSQL stores the aware time too, its offset being one the server accepts.
    """
    specimen = None if operation == "create" else _seed()
    root, document = _document("serializer", operation)
    refused = _Cell("occurredTime", "09:30:00+02:00", _every(_REFUSED, _STORED))
    payload = response_json(
        post_graphql(document, variables=_variables("serializer", operation, refused, specimen)),
    )
    outcome = refused.outcome("serializer")
    label = "written" if operation == "create" else "stored"

    assert payload == _expected("serializer", root, outcome, refused, label)
    if outcome == _REFUSED:
        assert json_at(payload, "data", root, "errors", 0, "field") == "clockTime"
    _assert_rows(operation, outcome, specimen, refused)

    stored = _Cell("occurredTime", "11:15:00", _every(_STORED, _STORED))
    models.ScalarSpecimen.objects.filter(label="written").delete()
    written = response_json(
        post_graphql(document, variables=_variables("serializer", operation, stored, specimen)),
    )
    assert written == _expected("serializer", root, _STORED, stored, label)
    assert models.ScalarSpecimen.objects.get(label=label).occurred_time == datetime.time(11, 15)


#: A zero whose written exponent PostgreSQL's ``numeric_in`` refuses ("value overflows
#: numeric format"), which ``price``'s bounded ``DecimalValidator`` passes: it counts no
#: digit for a zero's positive exponent.
_ZERO_PAST_NUMERIC = "0E+9999999999"

#: The ``price`` an updated row holds before the write.
_STORED_PRICE = Decimal("12.5000")


def _write_price(
    operation: str,
    price: str = _ZERO_PAST_NUMERIC,
) -> tuple[str, JSONObject, models.ScalarSpecimen | None]:
    """Send ``price`` through the model flavor's ``operation``."""
    specimen = None
    if operation == "update":
        specimen = _seed()
        specimen.price = _STORED_PRICE
        specimen.save(update_fields=["price"])
    root, document = _document("model", operation)
    variables = (
        {"data": {**_CREATE_DATA, "price": price}}
        if specimen is None
        else {"id": str(specimen.pk), "data": {"price": price}}
    )
    return root, response_json(post_graphql(document, variables=variables)), specimen


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_decimal_postgresql_cannot_bind_is_the_field_error(operation: str) -> None:
    """A decimal ``full_clean`` passes but PostgreSQL's ``numeric`` refuses is the field's error.

    The server would refuse the bind at ``save()`` with a ``DataError`` no save mapper
    owns, a masked top-level error; the write decode answers ``price``'s ``invalid``
    error instead, nothing created and an updated row's ``price`` kept.
    """
    root, payload, specimen = _write_price(operation)

    error = {
        "field": "price",
        "messages": [_UNSTORABLE],
        "codes": ["invalid"],
        "path": ["price"],
    }
    assert payload == {"data": {root: {"result": None, "errors": [error]}}}
    rows = list(models.ScalarSpecimen.objects.values_list("label", "price"))
    assert rows == ([] if specimen is None else [("stored", _STORED_PRICE)])


@pytest.mark.skipif(connection.vendor != "sqlite", reason="pins how SQLite stores a decimal")
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_decimal_postgresql_cannot_bind_stores_as_its_nearest_double_on_sqlite(
    operation: str,
) -> None:
    """On SQLite the same decimal is written as the nearest double, here zero.

    Django binds the decimal as its text, which the ``NUMERIC`` column stores as an integer
    or its nearest double, so the zero is written as ``0`` and read back as ``0.0000``.
    """
    root, payload, specimen = _write_price(operation)

    label = "written" if specimen is None else "stored"
    assert payload == {"data": {root: {"result": {"label": label}, "errors": []}}}
    assert list(models.ScalarSpecimen.objects.values_list("label", "price")) == [
        (label, Decimal("0.0000")),
    ]


#: A ``price`` SQLite stores as ``10000000000000000``: the nearest double carries into a 17th
#: digit before the point, past the 16 ``DecimalField(20, 4)`` holds.
_PRICE_CARRIED_PAST_THE_COLUMN = "9999999999999999.9999"

#: A ``price`` whose nearest double is the integer ``9999999999999996``, which SQLite stores as
#: an integer: Django 6.1 reads it back exactly, Django 5.2 / 6.0 round it to 15 digits and
#: carry into a 17th.
_PRICE_STORED_AS_AN_INTEGER = "9999999999999995.0000"


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    ("price", "sqlite_reads_back", "read_back"),
    [
        pytest.param(_PRICE_CARRIED_PAST_THE_COLUMN, False, None, id="carried-past-the-column"),
        pytest.param(
            _PRICE_STORED_AS_AN_INTEGER,
            django.VERSION >= (6, 1),
            Decimal("9999999999999996.0000"),
            id="stored-as-an-integer",
        ),
    ],
)
def test_decimal_sqlite_cannot_read_back_is_the_field_error(
    operation: str,
    price: str,
    *,
    sqlite_reads_back: bool,
    read_back: Decimal | None,
) -> None:
    """A decimal SQLite stores as a value the re-fetch cannot read back is the field's error.

    ``price``'s ``DecimalValidator`` passes each value, which SQLite stores as an integer or
    the nearest double. The re-fetch would read it back through Django's converter, which
    quantizes it to the column's digits and raises ``InvalidOperation`` for a digit the
    double carried into, a masked top-level error with the write rolled back. The write
    decode answers ``price``'s ``invalid`` error instead, nothing created and an updated
    row's ``price`` kept. A value the converter reads back is written, as is every value on
    PostgreSQL, whose ``numeric`` keeps the decimal's own digits.
    """
    root, payload, specimen = _write_price(operation, price)

    rows = list(models.ScalarSpecimen.objects.values_list("label", "price"))
    if connection.vendor == "sqlite" and not sqlite_reads_back:
        assert payload == _field_refusal(root, "price", _UNSTORABLE)
        assert rows == ([] if specimen is None else [("stored", _STORED_PRICE)])
        return
    label = "written" if specimen is None else "stored"
    assert payload == {"data": {root: {"result": {"label": label}, "errors": []}}}
    stored = Decimal(price) if connection.vendor == "postgresql" else read_back
    assert rows == [(label, stored)]


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_shipped_graphql_view(request: HttpRequest) -> HttpResponseBase:
    return await AsyncDjangoGraphQLView.as_view(schema=config_schema.schema)(request)


urlpatterns = [path("graphql-async/", _async_shipped_graphql_view)]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("flavor", "name"),
    [
        pytest.param("model", "before-year-one", id="model"),
        pytest.param("form", "past-year-9999", id="form"),
        pytest.param("serializer", "aware-time", id="serializer"),
        pytest.param("model", "datetime-offset-16", id="model-utc-offset"),
    ],
)
async def test_async_write_holds_the_same_temporal_rule(flavor: str, name: str) -> None:
    """The async pipeline answers a temporal value the database cannot store the same way.

    Each flavor's async surface runs the sync write body under ``sync_to_async``, so the
    create over ``/graphql-async/`` is the same field error with nothing written (an
    aware time whose offset PostgreSQL accepts stores there, and a datetime offset of
    16:00, which SQLite projects onto UTC, stores on SQLite).
    """
    cell = _CELLS[name]
    root, document = _document(flavor, "create")
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient().query(
            document,
            variables=_variables(flavor, "create", cell, None),
            assert_no_errors=False,
            url="/graphql-async/",
        )
    payload = response_json(result.response)
    outcome = cell.outcome(flavor)

    assert payload == _expected(flavor, root, outcome, cell, "written")
    await sync_to_async(_assert_rows)("create", outcome, None, cell)


#: The split-stamp form surfaces: create and update root fields and their input types.
_SPLIT_FORMS = {
    "unprefixed": (
        "createScalarSpecimenViaSplitForm",
        "ScalarSpecimenSplitStampFormInput",
        "updateScalarSpecimenViaSplitForm",
        "ScalarSpecimenSplitStampFormPartialInput",
    ),
    "prefixed": (
        "createScalarSpecimenViaPrefixedSplitForm",
        "PrefixedScalarSpecimenSplitStampFormInput",
        "updateScalarSpecimenViaPrefixedSplitForm",
        "PrefixedScalarSpecimenSplitStampFormPartialInput",
    ),
    "rekeyed": (
        "createScalarSpecimenViaRekeyedSplitForm",
        "PrefixedScalarSpecimenSplitStampFormInput",
        "updateScalarSpecimenViaRekeyedSplitForm",
        "PrefixedScalarSpecimenSplitStampFormPartialInput",
    ),
}

_SENT_AT = datetime.datetime(2022, 7, 8, 10, 11, 12, tzinfo=datetime.timezone.utc)


@pytest.mark.django_db
@pytest.mark.parametrize("form", list(_SPLIT_FORMS))
@pytest.mark.parametrize("operation", ["create", "update", "update-omitted"])
def test_split_datetime_form_field_writes_the_datetime_sent(form: str, operation: str) -> None:
    """A ``SplitDateTimeField`` over ``occurred_at`` writes the datetime sent, and keeps it when omitted.

    Its ``SplitDateTimeWidget`` reads a date key and a time key, so the package binds the
    datetime split by the widget's own ``decompress`` under both: unprefixed
    (``occurred_at_0`` / ``occurred_at_1``), under the form's prefix
    (``specimen-occurred_at_0`` / ``_1``), and beside the whole value a ``get_form`` keyed
    ``specimen-occurred_at`` itself. A create and an update naming ``occurredAt`` store it;
    an update omitting it binds the stored datetime the same way and keeps it.
    """
    create_field, create_input, update_field, update_input = _SPLIT_FORMS[form]
    selection = "{ result { label occurredAt } errors { field messages codes path } }"
    if operation == "create":
        root = create_field
        document = f"mutation Write($data: {create_input}!) {{ {root}(data: $data) {selection} }}"
        variables: dict[str, object] = {
            "data": {**_CREATE_DATA, "occurredAt": _SENT_AT.isoformat()},
        }
        label, stored_at = "written", _SENT_AT
    else:
        specimen = _seed()
        root = update_field
        document = (
            f"mutation Write($id: ID!, $data: {update_input}!) "
            f"{{ {root}(id: $id, data: $data) {selection} }}"
        )
        data: dict[str, object] = {"label": "renamed"}
        if operation == "update":
            data["occurredAt"] = _SENT_AT.isoformat()
        variables = {"id": str(specimen.pk), "data": data}
        label = "renamed"
        stored_at = _SENT_AT if operation == "update" else _STORED_AT

    payload = response_json(post_graphql(document, variables=variables))

    assert payload == {
        "data": {
            root: {"result": {"label": label, "occurredAt": stored_at.isoformat()}, "errors": []},
        },
    }
    rows = list(models.ScalarSpecimen.objects.values_list("label", "occurred_at"))
    assert rows == [(label, stored_at)]


_SPLIT_SELECTION = "{ result { label occurredAt } errors { field messages codes path } }"


def _split_write(
    operation: str,
    data: dict[str, object],
) -> tuple[str, JSONObject, models.ScalarSpecimen | None]:
    """Write ``data`` through the unprefixed split form: its root, payload and the seeded row.

    A create sends ``data`` beside ``_CREATE_DATA``; an update sends it over a seeded row.
    """
    create_field, create_input, update_field, update_input = _SPLIT_FORMS["unprefixed"]
    if operation == "create":
        document = (
            f"mutation Write($data: {create_input}!) "
            f"{{ {create_field}(data: $data) {_SPLIT_SELECTION} }}"
        )
        variables: dict[str, object] = {"data": {**_CREATE_DATA, **data}}
        return create_field, response_json(post_graphql(document, variables=variables)), None
    specimen = _seed()
    document = (
        f"mutation Write($id: ID!, $data: {update_input}!) "
        f"{{ {update_field}(id: $id, data: $data) {_SPLIT_SELECTION} }}"
    )
    variables = {"id": str(specimen.pk), "data": data}
    return update_field, response_json(post_graphql(document, variables=variables)), specimen


def _field_refusal(root: str, field: str, message: str) -> JSONObject:
    """The payload refusing ``field`` with its ``invalid`` ``message``, the result ``null``."""
    error = {
        "field": field,
        "messages": [message],
        "codes": ["invalid"],
        "path": [field],
    }
    return {"data": {root: {"result": None, "errors": [error]}}}


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    ("zone", "sent", "outcome"),
    [
        pytest.param("UTC", "0001-01-01T00:30:00+01:00", _REFUSED, id="utc-before-year-one"),
        pytest.param("UTC", "9999-12-31T23:30:00-01:00", _REFUSED, id="utc-past-year-9999"),
        pytest.param(
            "America/New_York",
            "0001-01-01T00:30:00+00:00",
            _REFUSED,
            id="new-york-year-one-in-utc",
        ),
        pytest.param("UTC", "0001-01-01T00:30:00+00:00", _STORED, id="utc-year-one-in-utc"),
    ],
)
def test_split_datetime_the_current_time_zone_cannot_present_is_the_field_error(
    operation: str,
    zone: str,
    sent: str,
    outcome: str,
) -> None:
    """A datetime whose wall clock in the current time zone leaves years 1..9999 is refused.

    ``SplitDateTimeWidget.decompress`` splits the datetime into the current time zone's
    date and time, which it cannot do for one whose wall clock there falls in year 0 or
    10000: the ``occurredAt`` ``invalid`` ``FieldError`` ("Enter a value the current time
    zone can represent."), nothing created and an updated row kept, even for
    ``0001-01-01T00:30:00+00:00``, which the database stores under ``UTC``.
    """
    with override_settings(TIME_ZONE=zone):
        root, payload, specimen = _split_write(operation, {"occurredAt": sent})
    label = "written" if operation == "create" else "stored"
    sent_at = datetime.datetime.fromisoformat(sent)
    stored = outcome == _STORED

    if stored:
        assert payload == {
            "data": {
                root: {"result": {"label": label, "occurredAt": sent}, "errors": []},
            },
        }
    else:
        assert payload == _field_refusal(root, "occurredAt", _UNREPRESENTABLE_IN_ZONE)
    rows = list(models.ScalarSpecimen.objects.values_list("label", "occurred_at"))
    if specimen is None:
        assert rows == ([(label, sent_at)] if stored else []), rows
    else:
        assert rows == [(label, sent_at if stored else _STORED_AT)], rows


_YEAR_ONE_IN_UTC = datetime.datetime(1, 1, 1, 0, 30, tzinfo=datetime.timezone.utc)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("zone", "outcome"),
    [
        pytest.param("America/New_York", _REFUSED, id="new-york"),
        pytest.param("UTC", _STORED, id="utc"),
    ],
)
def test_split_update_omitting_a_stored_datetime_the_zone_cannot_present_is_the_field_error(
    zone: str,
    outcome: str,
) -> None:
    """An update omitting ``occurredAt`` over a stored value the zone cannot split is refused.

    The update binds the stored ``0001-01-01T00:30:00+00:00`` through the split widget like
    a value sent, so under ``America/New_York``, where its wall clock falls in year 0, the
    update is the ``occurredAt`` ``invalid`` ``FieldError`` and the row is kept: the caller
    supplies a valid replacement in the same request. Under ``UTC`` the update keeps it.
    """
    specimen = _seed()
    models.ScalarSpecimen.objects.filter(pk=specimen.pk).update(occurred_at=_YEAR_ONE_IN_UTC)
    _, _, update_field, update_input = _SPLIT_FORMS["unprefixed"]
    document = (
        f"mutation Write($id: ID!, $data: {update_input}!) "
        f"{{ {update_field}(id: $id, data: $data) {_SPLIT_SELECTION} }}"
    )
    variables = {"id": str(specimen.pk), "data": {"label": "renamed"}}
    with override_settings(TIME_ZONE=zone):
        payload = response_json(post_graphql(document, variables=variables))
    kept = outcome == _STORED

    if kept:
        result = {"label": "renamed", "occurredAt": _YEAR_ONE_IN_UTC.isoformat()}
        assert payload == {"data": {update_field: {"result": result, "errors": []}}}
    else:
        assert payload == _field_refusal(update_field, "occurredAt", _UNREPRESENTABLE_IN_ZONE)
    rows = list(models.ScalarSpecimen.objects.values_list("label", "occurred_at"))
    assert rows == [("renamed" if kept else "stored", _YEAR_ONE_IN_UTC)], rows


#: The day-instant form surface: create and update root fields and their input types.
_DAY_INSTANT_FORM = (
    "createScalarSpecimenViaDayInstantForm",
    "ScalarSpecimenDayInstantFormInput",
    "updateScalarSpecimenViaDayInstantForm",
    "ScalarSpecimenDayInstantFormPartialInput",
)


def _day_instant_write(
    operation: str,
    day: str,
) -> tuple[str, JSONObject, models.ScalarSpecimen | None]:
    """Send ``occurredOn: day`` through the day-instant form: its root, payload and seeded row."""
    create_field, create_input, update_field, update_input = _DAY_INSTANT_FORM
    selection = "{ result { label occurredOn } errors { field messages codes path } }"
    if operation == "create":
        document = (
            f"mutation Write($data: {create_input}!) {{ {create_field}(data: $data) {selection} }}"
        )
        variables: dict[str, object] = {"data": {**_CREATE_DATA, "occurredOn": day}}
        return create_field, response_json(post_graphql(document, variables=variables)), None
    specimen = _seed()
    document = (
        f"mutation Write($id: ID!, $data: {update_input}!) "
        f"{{ {update_field}(id: $id, data: $data) {selection} }}"
    )
    variables = {"id": str(specimen.pk), "data": {"occurredOn": day}}
    return update_field, response_json(post_graphql(document, variables=variables)), specimen


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    ("zone", "day", "stored_day"),
    [
        pytest.param("America/New_York", "0001-01-01", None, id="new-york-year-one"),
        pytest.param("UTC", "0001-01-01", "0001-01-01", id="utc-year-one"),
        pytest.param("America/New_York", "2021-06-15", "2021-06-14", id="new-york-in-range"),
    ],
)
def test_clean_hook_datetime_the_date_column_cannot_store_is_the_field_error(
    operation: str,
    zone: str,
    day: str,
    stored_day: str | None,
) -> None:
    """A ``clean_<field>`` hook's aware datetime whose date leaves years 1..9999 is refused.

    ``ScalarSpecimenDayInstantForm.clean_occurred_on`` answers the aware midnight UTC of the
    date sent, which the ``DateField`` column stores as its date in the default time zone:
    Django's own conversion of it inside ``is_valid()`` would raise ``OverflowError`` where
    that date falls in year 0 (``0001-01-01`` under ``America/New_York``), so the mutation is
    the ``occurredOn`` ``invalid`` ``FieldError`` ("Enter a value the database can
    represent.") before that conversion, with nothing created and an updated row kept. Under
    ``UTC`` the date is stored, and an in-range day is stored as its date in the default time
    zone (``2021-06-14``).
    """
    with override_settings(TIME_ZONE=zone):
        root, payload, specimen = _day_instant_write(operation, day)
    label = "written" if operation == "create" else "stored"

    if stored_day is None:
        assert payload == _field_refusal(root, "occurredOn", _UNSTORABLE)
    else:
        assert payload == {
            "data": {root: {"result": {"label": label, "occurredOn": stored_day}, "errors": []}},
        }
    rows = list(models.ScalarSpecimen.objects.values_list("label", "occurred_on"))
    if stored_day is not None:
        expected = [(label, datetime.date.fromisoformat(stored_day))]
    else:
        expected = [] if specimen is None else [(label, specimen.occurred_on)]
    assert rows == expected, rows


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "root",
        "input_type",
        "data",
        "field",
        "message",
    ),
    [
        pytest.param(
            _SPLIT_FORMS["unprefixed"][0],
            _SPLIT_FORMS["unprefixed"][1],
            {"occurredAt": "0001-01-01T00:30:00+00:00"},
            "occurredAt",
            _UNREPRESENTABLE_IN_ZONE,
            id="split",
        ),
        pytest.param(
            _DAY_INSTANT_FORM[0],
            _DAY_INSTANT_FORM[1],
            {"occurredOn": "0001-01-01"},
            "occurredOn",
            _UNSTORABLE,
            id="day-instant",
        ),
    ],
)
async def test_async_form_write_holds_the_zone_and_hook_refusals(
    root: str,
    input_type: str,
    data: dict[str, object],
    field: str,
    message: str,
) -> None:
    """The async form pipeline refuses the split zone and hook overflow values the same way.

    Under ``America/New_York`` the split widget cannot present ``0001-01-01T00:30:00+00:00``
    and the day-instant hook's midnight UTC of ``0001-01-01`` falls in year 0, so each create
    over ``/graphql-async/`` is the field's ``invalid`` error with nothing written.
    """
    selection = "{ result { label } errors { field messages codes path } }"
    document = f"mutation Write($data: {input_type}!) {{ {root}(data: $data) {selection} }}"
    with override_settings(ROOT_URLCONF=__name__, TIME_ZONE="America/New_York"):
        result = await AsyncTestClient().query(
            document,
            variables={"data": {**_CREATE_DATA, **data}},
            assert_no_errors=False,
            url="/graphql-async/",
        )

    assert response_json(result.response) == _field_refusal(root, field, message)
    assert await models.ScalarSpecimen.objects.acount() == 0


#: The ``ViaPosted`` surfaces, binding posted text: create and update root fields and inputs.
_POSTED_FORMS = {
    "temporal": (
        "createScalarSpecimenViaPostedForm",
        "ScalarSpecimenTemporalFormInput",
        "updateScalarSpecimenViaPostedForm",
        "ScalarSpecimenTemporalFormPartialInput",
    ),
    "split": (
        "createScalarSpecimenViaPostedSplitForm",
        "ScalarSpecimenSplitStampFormInput",
        "updateScalarSpecimenViaPostedSplitForm",
        "ScalarSpecimenSplitStampFormPartialInput",
    ),
}


def _posted_write(form: str, operation: str) -> tuple[str, str, JSONObject, datetime.datetime]:
    """Write through a ``ViaPosted`` form: its root, document, payload and the datetime bound.

    A create sends ``_SENT_AT``; an update renames the seeded row and sends ``_SENT_AT``
    or, ``update-omitted``, omits ``occurredAt``, so its stored ``_STORED_AT`` is bound.
    """
    create_field, create_input, update_field, update_input = _POSTED_FORMS[form]
    selection = "{ result { label occurredAt } errors { field messages codes path } }"
    if operation == "create":
        root = create_field
        document = f"mutation Write($data: {create_input}!) {{ {root}(data: $data) {selection} }}"
        variables: dict[str, object] = {
            "data": {**_CREATE_DATA, "occurredAt": _SENT_AT.isoformat()},
        }
        bound = _SENT_AT
    else:
        specimen = _seed()
        root = update_field
        document = (
            f"mutation Write($id: ID!, $data: {update_input}!) "
            f"{{ {root}(id: $id, data: $data) {selection} }}"
        )
        data: dict[str, object] = {"label": "renamed"}
        if operation == "update":
            data["occurredAt"] = _SENT_AT.isoformat()
        variables = {"id": str(specimen.pk), "data": data}
        bound = _SENT_AT if operation == "update" else _STORED_AT
    return root, document, response_json(post_graphql(document, variables=variables)), bound


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update", "update-omitted"])
def test_posted_text_over_a_one_key_datetime_widget_is_parsed_and_stored(operation: str) -> None:
    """A ``get_form_kwargs`` binding each value as its text writes through a one-key widget.

    ``ScalarSpecimenTemporalForm``'s ``DateTimeField`` reads ``occurred_at`` alone and
    parses the text of the datetime, so the hook's posted text is stored on create and
    update, and an update omitting ``occurredAt`` keeps the stored datetime.
    """
    root, _document, payload, bound = _posted_write("temporal", operation)
    label = "written" if operation == "create" else "renamed"

    assert payload == {
        "data": {
            root: {"result": {"label": label, "occurredAt": bound.isoformat()}, "errors": []},
        },
    }
    rows = list(models.ScalarSpecimen.objects.values_list("label", "occurred_at"))
    assert rows == [(label, bound)]


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update", "update-omitted"])
def test_posted_text_over_a_split_datetime_widget_is_a_masked_configuration_error(
    operation: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The text of a datetime has no parts ``SplitDateTimeWidget.decompress`` can split.

    ``decompress`` takes the field's value, a ``datetime``: the hook's posted text for
    ``occurred_at`` (the datetime sent, or on an update omitting it the stored one) is a
    ``ConfigurationError`` naming ``occurred_at`` and the widget's ``occurred_at_0`` /
    ``occurred_at_1``, never the value's text, raised while the form is bound, before
    ``is_valid()``. The client gets the error policy's masked top-level error and
    nothing is written: no row created, the updated row's label and datetime kept.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    root, document, payload, bound = _posted_write("split", operation)
    correlation_id = json_at(payload, "errors", 0, "extensions", "correlationId")

    assert isinstance(correlation_id, str), payload
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "An unexpected error occurred.",
                "locations": [{"line": 1, "column": document.index(root) + 1}],
                "path": [root],
                "extensions": {"correlationId": correlation_id},
            },
        ],
    }
    [logged] = [
        record.exc_info
        for record in caplog.records
        if record.name == "django_strawberry_framework" and record.exc_info is not None
    ]
    assert isinstance(logged[1], ConfigurationError), logged
    message = str(logged[1])
    assert message.startswith(
        "SplitDateTimeWidget.decompress cannot split the str bound under 'occurred_at' "
        "into the parts the widget reads ('occurred_at_0', 'occurred_at_1'): it raised "
        "AttributeError",
    ), message
    assert str(bound) not in message, message
    rows = list(models.ScalarSpecimen.objects.values_list("label", "occurred_at"))
    assert rows == ([] if operation == "create" else [("stored", _STORED_AT)])


def _create_model_value(data: Mapping[str, object]) -> JSONObject:
    """Create through the shipped model mutation and return its entire HTTP envelope."""
    _root, document = _document("model", "create")
    response = post_graphql(document, variables={"data": data})
    assert response.status_code == 200
    return response_json(response)


_MODEL_CREATE_SUCCESS: JSONObject = {
    "data": {"createScalarSpecimen": {"result": {"label": "written"}, "errors": []}},
}


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_omitting_empty_value_default_field_succeeds_on_create_and_update(operation: str) -> None:
    """Create and update leave an omitted JSON default out of client-input validation."""
    specimen = None if operation == "create" else _seed()
    root, document = _document("model", operation)
    variables: dict[str, object] = (
        {"data": _CREATE_DATA} if specimen is None else {"id": str(specimen.pk), "data": {}}
    )
    label = "written" if operation == "create" else "stored"

    response = post_graphql(document, variables=variables)

    assert response.status_code == 200
    assert response_json(response) == {"data": {root: {"result": {"label": label}, "errors": []}}}
    assert list(models.ScalarSpecimen.objects.values_list("label", "payload")) == [(label, {})]
    if specimen is not None:
        assert models.ScalarSpecimen.objects.get().pk == specimen.pk


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@override_settings(USE_TZ=True, TIME_ZONE="UTC")
@timezone.override(ZoneInfo("America/New_York"))
def test_naive_datetime_input_is_made_timezone_aware_on_create_and_update(operation: str) -> None:
    """Both writes store a naive datetime at the current zone's instant without a warning."""
    specimen = None if operation == "create" else _seed()
    root, document = _document("model", operation)
    value = "2021-06-15T09:30:00"
    variables = (
        {"data": {**_CREATE_DATA, "occurredAt": value}}
        if specimen is None
        else {"id": str(specimen.pk), "data": {"occurredAt": value}}
    )
    label = "written" if operation == "create" else "stored"

    response = post_graphql(document, variables=variables)

    assert response.status_code == 200
    assert response_json(response) == {"data": {root: {"result": {"label": label}, "errors": []}}}
    expected = datetime.datetime(2021, 6, 15, 13, 30, tzinfo=datetime.timezone.utc)
    assert list(models.ScalarSpecimen.objects.values_list("label", "occurred_at")) == [
        (label, expected),
    ]
    if specimen is not None:
        assert models.ScalarSpecimen.objects.get().pk == specimen.pk


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "value",
        "field",
        "message",
        "code",
    ),
    [
        pytest.param(
            {"tags": ["ok", "\ud800"]},
            "payload.tags.1",
            "Text contains invalid Unicode (unpaired surrogate code points).",
            "invalid",
            id="surrogate-value",
        ),
        pytest.param(
            {"tags": ["ok", "a\x00b"]},
            "payload.tags.1",
            "Null characters are not allowed.",
            "null_characters_not_allowed",
            id="nul-value",
        ),
        pytest.param(
            {"co\x00lor": "red"},
            "payload",
            "Null characters are not allowed.",
            "null_characters_not_allowed",
            id="nul-key",
        ),
    ],
)
def test_create_unstorable_json_text_is_a_path_keyed_error_before_save(
    value: dict[str, object],
    field: str,
    message: str,
    code: str,
) -> None:
    """Invalid Unicode and NUL text in JSON keys or values are refused at their input path."""
    with CaptureQueriesContext(connection) as queries:
        payload = _create_model_value({**_CREATE_DATA, "payload": value})

    table = connection.ops.quote_name(models.ScalarSpecimen._meta.db_table).upper()
    writes = [
        query["sql"]
        for query in queries.captured_queries
        if query["sql"].lstrip().upper().startswith(("INSERT ", "UPDATE "))
        and table in query["sql"].upper()
    ]
    assert writes == [], writes
    assert payload == {
        "data": {
            "createScalarSpecimen": {
                "result": None,
                "errors": [
                    {
                        "field": field,
                        "messages": [message],
                        "codes": [code],
                        "path": field.split("."),
                    },
                ],
            },
        },
    }
    assert not models.ScalarSpecimen.objects.exists()


@pytest.mark.django_db
def test_create_json_text_keeps_representable_unicode() -> None:
    """The JSON preflight accepts ordinary Unicode text and leaves its stored value intact."""
    value = {"tags": ["ok", "caf\u00e9"]}
    payload = _create_model_value({**_CREATE_DATA, "payload": value})

    assert payload == _MODEL_CREATE_SUCCESS
    assert models.ScalarSpecimen.objects.get(label="written").payload == value


#: The checkbox ``flag`` form's create and update root fields and their input types.
_FLAG_FORM = (
    "createNullableScalarSpecimenViaForm",
    "NullableScalarSpecimenFlagFormInput",
    "updateNullableScalarSpecimenViaForm",
    "NullableScalarSpecimenFlagFormPartialInput",
)

#: ``(operation, stored, data, expected)``: the stored ``flag`` an update starts from, the
#: ``flag`` input sent (absent when ``data`` omits it) and the ``flag`` the row holds after.
_FLAG_WRITES = [
    pytest.param("create", None, {"flag": None}, None, id="create-null"),
    pytest.param("create", None, {}, None, id="create-omitted"),
    pytest.param("update", True, {"flag": None}, None, id="update-null-over-true"),
    pytest.param("update", False, {"flag": None}, None, id="update-null-over-false"),
    pytest.param("update", None, {"flag": None}, None, id="update-null-over-null"),
    pytest.param("update", None, {}, None, id="update-omitted-over-null"),
    pytest.param("create", None, {"flag": True}, True, id="create-true"),
    pytest.param("create", None, {"flag": False}, False, id="create-false"),
    pytest.param("update", None, {"flag": True}, True, id="update-true-over-null"),
    pytest.param("update", None, {"flag": False}, False, id="update-false-over-null"),
    pytest.param("update", True, {}, True, id="update-omitted-over-true"),
    pytest.param("update", False, {}, False, id="update-omitted-over-false"),
]


def _flag_document(
    operation: str,
    selection: str = "label flag",
    *,
    form: tuple[str, str, str, str] = _FLAG_FORM,
) -> tuple[str, str]:
    """Return ``form``'s (the checkbox form's) mutation root field and its document over ``$data``."""
    create_field, create_input, update_field, update_input = form
    if operation == "create":
        arguments, root = f"$data: {create_input}!", create_field
        call = f"{root}(data: $data)"
    else:
        arguments, root = f"$id: ID!, $data: {update_input}!", update_field
        call = f"{root}(id: $id, data: $data)"
    document = f"""
        mutation Write({arguments}) {{
          {call} {{
            result {{ {selection} }}
            errors {{ field messages codes path }}
          }}
        }}
    """
    return root, document


def _flag_variables(
    operation: str,
    data: Mapping[str, object],
    *,
    stored: bool | None,
) -> dict[str, object]:
    """Seed the row an update starts from (``label`` ``stored``) and build the variables.

    Every write names ``label``, so an update's save writes the row whatever ``flag`` is.
    """
    if operation == "create":
        return {"data": {"label": "written", **data}}
    specimen = models.NullableScalarSpecimen.objects.create(label="stored", flag=stored)
    return {"id": str(specimen.pk), "data": {"label": "renamed", **data}}


def _assert_flag_written(root: str, payload: JSONObject, *, expected: bool | None) -> None:
    """The write succeeded and the one row holds ``expected`` in ``flag``."""
    label = "written" if root == _FLAG_FORM[0] else "renamed"
    assert payload == {
        "data": {root: {"result": {"label": label, "flag": expected}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen.objects.values_list("label", "flag"))
    assert rows == [(label, expected)], rows


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "operation",
        "stored",
        "data",
        "expected",
    ),
    _FLAG_WRITES,
)
def test_checkbox_over_a_nullable_boolean_stores_null_for_null(
    operation: str,
    data: Mapping[str, object],
    *,
    stored: bool | None,
    expected: bool | None,
) -> None:
    """A checkbox over the ``null=True`` ``flag`` stores ``NULL`` for an explicit or kept ``null``.

    The declared ``forms.BooleanField(required=False)`` reads a bound ``None`` or an absent
    key as ``False``. An explicit ``flag: null`` on create, on update over ``true``,
    ``false`` or ``NULL``, and a create omitting ``flag`` (the column has no default)
    store ``NULL``, as the model flavor does, with empty ``errors``, and an update omitting
    ``flag`` over a stored ``NULL`` keeps it. ``true`` and ``false`` are written as sent,
    and an update omitting ``flag`` over a stored ``true`` or ``false`` keeps it.
    """
    root, document = _flag_document(operation)

    payload = response_json(
        post_graphql(document, variables=_flag_variables(operation, data, stored=stored)),
    )

    _assert_flag_written(root, payload, expected=expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("operation", "data", "expected"),
    [
        pytest.param("create", {"label": None}, "", id="create-null"),
        pytest.param("create", {}, "", id="create-omitted"),
        pytest.param("update", {"label": None}, "", id="update-null"),
        pytest.param("update", {"label": "kept"}, "kept", id="update-value"),
    ],
)
def test_text_column_under_the_flag_form_keeps_the_empty_string_for_null(
    operation: str,
    data: Mapping[str, object],
    expected: str,
) -> None:
    """``label: null`` on the ``null=True`` text column ``label`` stores ``""``, never ``NULL``.

    The column's own ``CharField`` cleans ``None`` and a create's absent key to ``""``,
    Django's empty value for a text column, and the form flavor writes it as cleaned; a
    value sent is written.
    """
    root, document = _flag_document(operation)
    if operation == "create":
        variables: dict[str, object] = {"data": {"flag": True, **data}}
    else:
        specimen = models.NullableScalarSpecimen.objects.create(label="stored", flag=True)
        variables = {"id": str(specimen.pk), "data": dict(data)}

    payload = response_json(post_graphql(document, variables=variables))

    assert payload == {
        "data": {root: {"result": {"label": expected, "flag": True}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen.objects.values_list("label", "flag"))
    assert rows == [(expected, True)], rows


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "operation",
        "stored",
        "data",
        "expected",
    ),
    [
        pytest.param("create", None, {"flag": None}, None, id="create-null"),
        pytest.param("create", None, {}, None, id="create-omitted"),
        pytest.param("update", True, {"flag": None}, None, id="update-null-over-true"),
        pytest.param("update", None, {}, None, id="update-omitted-over-null"),
        pytest.param("update", True, {}, True, id="update-omitted-over-true"),
    ],
)
async def test_async_checkbox_over_a_nullable_boolean_stores_null_for_null(
    operation: str,
    data: Mapping[str, object],
    *,
    stored: bool | None,
    expected: bool | None,
) -> None:
    """The async pipeline stores ``NULL`` for the checkbox ``flag``'s ``null`` the same way."""
    root, document = _flag_document(operation)
    variables = await sync_to_async(_flag_variables)(operation, data, stored=stored)
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient().query(
            document,
            variables=variables,
            assert_no_errors=False,
            url="/graphql-async/",
        )

    await sync_to_async(_assert_flag_written)(
        root,
        response_json(result.response),
        expected=expected,
    )


#: ``(operation, stored, data, expected)``: the stored ``payload`` an update starts from, the
#: ``payload`` input sent (absent when ``data`` omits it) and the ``payload`` the row holds.
_PAYLOAD_WRITES = [
    pytest.param("create", None, {"payload": None}, None, id="create-null"),
    pytest.param("create", None, {}, None, id="create-omitted"),
    pytest.param("update", "x", {"payload": None}, None, id="update-null-over-value"),
    pytest.param("update", None, {"payload": None}, None, id="update-null-over-null"),
    pytest.param("update", None, {}, None, id="update-omitted-over-null"),
    pytest.param("create", None, {"payload": "y"}, "y", id="create-string"),
    pytest.param("update", None, {"payload": "y"}, "y", id="update-string-over-null"),
    pytest.param("update", "x", {}, "x", id="update-omitted-over-string"),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "operation",
        "stored",
        "data",
        "expected",
    ),
    _PAYLOAD_WRITES,
)
def test_char_field_over_a_nullable_json_column_stores_null_for_null(
    operation: str,
    stored: str | None,
    data: Mapping[str, object],
    expected: str | None,
) -> None:
    """A ``CharField`` over the ``null=True`` JSON ``payload`` stores ``NULL`` for ``null``.

    The declared ``forms.CharField(required=False)`` cleans a bound ``None`` to ``""``,
    which the ``JSONField`` would store as the JSON string; the column is no text column
    (``empty_strings_allowed`` is false), so an explicit ``payload: null`` on create and on
    update over a value or ``NULL``, and a create omitting it (the column has no default),
    store ``NULL`` with empty ``errors``, and an update
    omitting it over ``NULL`` keeps it. A string sent is stored as that JSON string, and an
    update omitting ``payload`` over a stored string keeps it.
    """
    root, document = _flag_document(operation)
    if operation == "create":
        variables: dict[str, object] = {"data": {"label": "written", "flag": True, **data}}
    else:
        specimen = models.NullableScalarSpecimen.objects.create(
            label="stored",
            flag=True,
            payload=stored,
        )
        variables = {"id": str(specimen.pk), "data": {"label": "renamed", **data}}

    payload = response_json(post_graphql(document, variables=variables))

    label = "written" if operation == "create" else "renamed"
    assert payload == {
        "data": {root: {"result": {"label": label, "flag": True}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen.objects.values_list("label", "payload"))
    assert rows == [(label, expected)], rows


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("operation", "sent", "shown"),
    [
        pytest.param("create", {"a": 1}, "{'a': 1}", id="create-object"),
        pytest.param("update", [1, 2], "[1, 2]", id="update-list"),
        pytest.param("create", 5, "5", id="create-number"),
        pytest.param("update", True, "True", id="update-bool"),
    ],
)
def test_char_field_over_a_json_column_refuses_a_non_string_value(
    operation: str,
    sent: object,
    shown: str,
) -> None:
    """``payload`` takes ``String``: a JSON object, list, number or boolean is refused, nothing written.

    The ``CharField`` reads text and the column stores the text it cleans as a JSON string,
    so the input publishes the form field's ``String``, never the column's ``JSON``, whose
    decoded object the field would store as its Python text (``"{'a': 1}"``).
    """
    _root, document = _flag_document(operation)
    variables = _flag_variables(operation, {"payload": sent}, stored=True)

    payload = response_json(post_graphql(document, variables=variables))

    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "message") == (
        "Variable '$data' has invalid value at .payload: "
        f"String cannot represent a non string value: {shown}"
    ), payload
    stored = [] if operation == "create" else [("stored", None)]
    assert list(models.NullableScalarSpecimen.objects.values_list("label", "payload")) == stored


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_char_field_over_a_json_column_stores_the_text_sent(operation: str) -> None:
    """The JSON text of an object sent to ``payload`` is stored as that JSON string.

    The ``CharField`` cleans the text it reads and the column stores it as given, as a
    ``ModelForm`` bound to an HTML post of the same text does; a form reading JSON text
    parses it in its own ``to_python`` or ``clean_payload``.
    """
    root, document = _flag_document(operation, "label payload")
    variables = _flag_variables(operation, {"payload": '{"a": 1}'}, stored=True)

    payload = response_json(post_graphql(document, variables=variables))

    label = "written" if operation == "create" else "renamed"
    assert payload == {
        "data": {root: {"result": {"label": label, "payload": '{"a": 1}'}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen.objects.values_list("label", "payload"))
    assert rows == [(label, '{"a": 1}')], rows


#: ``(operation, stored, data, expected)``: the stored ``score`` an update starts from, the
#: ``score`` input sent (absent when ``data`` omits it) and the ``score`` the row holds.
_SCORE_WRITES = [
    pytest.param("create", None, {"score": None}, None, id="create-null"),
    pytest.param("create", None, {}, None, id="create-omitted"),
    pytest.param("update", 1.5, {"score": None}, None, id="update-null-over-value"),
    pytest.param("update", None, {"score": None}, None, id="update-null-over-null"),
    pytest.param("update", 1.5, {}, 1.5, id="update-omitted-over-value"),
    pytest.param("update", None, {}, None, id="update-omitted-over-null"),
    pytest.param("create", None, {"score": 2.5}, 2.5, id="create-value"),
    pytest.param("update", 1.5, {"score": 2.5}, 2.5, id="update-value-over-value"),
]


def _score_variables(
    operation: str,
    data: Mapping[str, object],
    *,
    stored: float | None,
) -> dict[str, object]:
    """Seed the row an update starts from (``score`` ``stored``) and build the variables."""
    if operation == "create":
        return {"data": {"label": "written", **data}}
    specimen = models.NullableScalarSpecimen.objects.create(label="stored", score=stored)
    return {"id": str(specimen.pk), "data": {"label": "renamed", **data}}


def _assert_score_written(root: str, payload: JSONObject, *, expected: float | None) -> None:
    """The write succeeded and the one row, read through the base manager, holds ``expected``."""
    label = "written" if root == _FLAG_FORM[0] else "renamed"
    assert payload == {
        "data": {root: {"result": {"label": label, "score": expected}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen._base_manager.values_list("label", "score"))
    assert rows == [(label, expected)], rows


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "operation",
        "stored",
        "data",
        "expected",
    ),
    _SCORE_WRITES,
)
def test_char_field_over_a_nullable_float_column_stores_null_for_null(
    operation: str,
    data: Mapping[str, object],
    *,
    stored: float | None,
    expected: float | None,
) -> None:
    """A ``CharField`` over the ``null=True`` float ``score`` stores ``NULL`` for ``null``.

    The declared ``forms.CharField(required=False)`` cleans a bound ``None`` and a
    create's absent key to ``""``, which the float column cannot store; its input stays
    ``Float``, so the client never sends ``""``. An explicit ``score: null`` on create and
    on update over a value or ``NULL``, and a create omitting it (the column has no
    default), store ``NULL`` with empty ``errors``, never the column's ``null`` error, as
    the model flavor and Django's own form field do. An update omitting ``score`` keeps the
    stored value, and a value sent is written.
    """
    root, document = _flag_document(operation, "label score")

    payload = response_json(
        post_graphql(document, variables=_score_variables(operation, data, stored=stored)),
    )

    _assert_score_written(root, payload, expected=expected)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "operation",
        "stored",
        "data",
        "expected",
    ),
    _SCORE_WRITES,
)
async def test_async_char_field_over_a_nullable_float_column_stores_null_for_null(
    operation: str,
    data: Mapping[str, object],
    *,
    stored: float | None,
    expected: float | None,
) -> None:
    """The async pipeline stores ``NULL`` for the ``CharField`` ``score``'s ``null`` the same way."""
    root, document = _flag_document(operation, "label score")
    variables = await sync_to_async(_score_variables)(operation, data, stored=stored)
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient().query(
            document,
            variables=variables,
            assert_no_errors=False,
            url="/graphql-async/",
        )

    await sync_to_async(_assert_score_written)(
        root,
        response_json(result.response),
        expected=expected,
    )


#: ``(stored, ...)``: the ``label`` / ``payload`` the row an update omitting both starts from.
#: The JSON-text form's create and update root fields and their input types.
_JSON_TEXT_FORM = (
    "createNullableScalarSpecimenViaJsonTextForm",
    "NullableScalarSpecimenJsonTextFormInput",
    "updateNullableScalarSpecimenViaJsonTextForm",
    "NullableScalarSpecimenJsonTextFormPartialInput",
)


def _json_text_write(
    operation: str,
    data: Mapping[str, object],
    stored: object = None,
) -> tuple[str, str, dict[str, object]]:
    """Seed the row an update starts from (``payload`` ``stored``); return root, document, variables."""
    root, document = _flag_document(operation, "label payload", form=_JSON_TEXT_FORM)
    if operation == "create":
        return root, document, {"data": {"label": "written", **data}}
    specimen = models.NullableScalarSpecimen.objects.create(label="stored", payload=stored)
    return root, document, {"id": str(specimen.pk), "data": {"label": "renamed", **data}}


def _assert_json_written(root: str, payload: JSONObject, expected: object) -> None:
    """The write succeeded and the one row holds the JSON value ``expected`` in ``payload``."""
    label = "written" if root == _JSON_TEXT_FORM[0] else "renamed"
    assert payload == {
        "data": {root: {"result": {"label": label, "payload": expected}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen.objects.values_list("label", "payload"))
    assert rows == [(label, expected)], rows


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    ("sent", "expected"),
    [
        pytest.param('{"a": 1}', {"a": 1}, id="object"),
        pytest.param("[1, 2]", [1, 2], id="list"),
        pytest.param('"s"', "s", id="string"),
        pytest.param("5", 5, id="number"),
        pytest.param("true", True, id="boolean"),
        pytest.param("null", None, id="null"),
    ],
)
def test_json_text_field_stores_the_json_value_its_text_spells(
    operation: str,
    sent: str,
    expected: object,
) -> None:
    """A field parsing JSON text over the JSON ``payload`` stores the value the text spells.

    ``payload`` is the ``JsonTextField``'s ``String``, so the form reads the text sent as an
    HTML post carries it and its ``to_python`` parses it: an object, list, string, number,
    boolean or ``null`` spelled as JSON text is stored as that JSON value (``null`` as
    ``NULL``), on create and on update over a stored object.
    """
    root, document, variables = _json_text_write(operation, {"payload": sent}, {"k": "v"})

    payload = response_json(post_graphql(document, variables=variables))

    _assert_json_written(root, payload, expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("operation", "sent", "shown"),
    [
        pytest.param("create", {"a": 1}, "{'a': 1}", id="create-object"),
        pytest.param("update", [1, 2], "[1, 2]", id="update-list"),
    ],
)
def test_json_text_field_refuses_a_json_value_sent_raw(
    operation: str,
    sent: object,
    shown: str,
) -> None:
    """A JSON object or list sent to the ``String`` ``payload`` is refused, nothing written."""
    root, document, variables = _json_text_write(operation, {"payload": sent}, {"k": "v"})

    payload = response_json(post_graphql(document, variables=variables))

    assert payload["data"] is None, (root, payload)
    assert json_at(payload, "errors", 0, "message") == (
        "Variable '$data' has invalid value at .payload: "
        f"String cannot represent a non string value: {shown}"
    ), payload
    stored = [] if operation == "create" else [("stored", {"k": "v"})]
    assert list(models.NullableScalarSpecimen.objects.values_list("label", "payload")) == stored


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_json_text_field_refuses_text_that_is_no_json(operation: str) -> None:
    """Text the field cannot parse is its ``invalid`` ``FieldError``, nothing written."""
    root, document, variables = _json_text_write(operation, {"payload": "{bad"}, {"k": "v"})

    payload = response_json(post_graphql(document, variables=variables))

    assert payload == _field_refusal(root, "payload", "Enter valid JSON text."), payload
    stored = [] if operation == "create" else [("stored", {"k": "v"})]
    assert list(models.NullableScalarSpecimen.objects.values_list("label", "payload")) == stored


#: The JSON value an update omitting ``payload`` starts from, and keeps.
_STORED_JSON = [
    pytest.param({"k": "v"}, id="object"),
    pytest.param(["x", 1], id="list"),
    pytest.param("s", id="string"),
    pytest.param(5, id="number"),
    pytest.param(None, id="null"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("stored", _STORED_JSON)
def test_update_omitting_a_json_text_field_reads_its_presentation_back(stored: object) -> None:
    """An update omitting ``payload`` binds the field's presentation and keeps the stored value.

    The field reads text and the stored value is a JSON value, so the update binds the field's
    ``prepare_value`` of the form's initial, the stored value's JSON text an HTML form posts
    back for an unchanged field, which the field parses back to the stored value: an
    object, list, string, number and ``NULL`` are each kept.
    """
    root, document, variables = _json_text_write("update", {}, stored)

    payload = response_json(post_graphql(document, variables=variables))

    _assert_json_written(root, payload, stored)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param({"payload": '{"a": 1}'}, {"a": 1}, id="sent"),
        pytest.param({}, {"k": "v"}, id="omitted"),
    ],
)
async def test_async_json_text_field_writes_the_same_way(
    data: Mapping[str, object],
    expected: object,
) -> None:
    """The async pipeline parses the JSON text sent and keeps an omitted stored value the same way."""
    root, document, variables = await sync_to_async(_json_text_write)("update", data, {"k": "v"})
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient().query(
            document,
            variables=variables,
            assert_no_errors=False,
            url="/graphql-async/",
        )

    await sync_to_async(_assert_json_written)(root, response_json(result.response), expected)


_KEPT_COLUMNS = [
    pytest.param({"label": "  padded  "}, id="padded-label"),
    pytest.param({"label": None}, id="null-label"),
    pytest.param({"label": "s", "payload": {"a": 1}}, id="json-object"),
    pytest.param({"label": "s", "payload": [1, 2]}, id="json-list"),
]


def _kept_columns_variables(stored: Mapping[str, object]) -> dict[str, object]:
    """Seed a row with ``stored`` and ``flag`` ``true``; the update sends ``flag: false`` only."""
    specimen = models.NullableScalarSpecimen.objects.create(flag=True, **stored)
    return {"id": str(specimen.pk), "data": {"flag": False}}


def _assert_columns_kept(root: str, payload: JSONObject, stored: Mapping[str, object]) -> None:
    """The update wrote ``flag`` and kept the omitted ``label`` and ``payload`` as stored."""
    label = stored["label"]
    assert payload == {
        "data": {root: {"result": {"label": label, "flag": False}, "errors": []}},
    }
    rows = list(models.NullableScalarSpecimen.objects.values_list("label", "flag", "payload"))
    assert rows == [(label, False, stored.get("payload"))], rows


@pytest.mark.django_db
@pytest.mark.parametrize("stored", _KEPT_COLUMNS)
def test_update_omitting_a_column_keeps_its_stored_value(stored: Mapping[str, object]) -> None:
    """An update omitting ``label`` and ``payload`` keeps each column's stored value.

    The reconstruction binds each omitted column's stored value, so the form validates
    the whole row, and the form's own cleaning of it would rewrite the column: the
    ``label`` ``CharField`` strips ``"  padded  "`` and cleans a stored ``NULL`` to ``""``,
    the ``payload`` ``CharField`` turns a JSON object or list into its Python text. The
    instance gets the stored value back before the save, so the row keeps it, ``NULL``
    included; an explicit ``label: null`` still stores ``""``
    (``test_text_column_under_the_flag_form_keeps_the_empty_string_for_null``).
    """
    root, document = _flag_document("update")

    payload = response_json(post_graphql(document, variables=_kept_columns_variables(stored)))

    _assert_columns_kept(root, payload, stored)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("stored", _KEPT_COLUMNS[:2])
async def test_async_update_omitting_a_column_keeps_its_stored_value(
    stored: Mapping[str, object],
) -> None:
    """The async pipeline keeps an omitted column's stored value the same way."""
    root, document = _flag_document("update")
    variables = await sync_to_async(_kept_columns_variables)(stored)
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient().query(
            document,
            variables=variables,
            assert_no_errors=False,
            url="/graphql-async/",
        )

    await sync_to_async(_assert_columns_kept)(root, response_json(result.response), stored)


_LOCKED_AT = datetime.datetime(2020, 1, 2, 3, 4, 5, 123456, tzinfo=datetime.timezone.utc)
_LOCKED_TIME = datetime.time(3, 4, 5, 654321)
_LOCKED_DOCUMENT = """
    mutation Locked($id: ID!, $data: ScalarSpecimenLockedStampFormPartialInput!) {
      updateScalarSpecimenViaLockedStampForm(id: $id, data: $data) {
        result { label occurredAt occurredTime }
        errors { field messages }
      }
    }
"""


def _locked_variables(sent: Mapping[str, object]) -> tuple[dict[str, object], uuid.UUID]:
    """Seed a row whose stamp carries microseconds; the update renames it and sends ``sent``."""
    external_id = uuid.uuid4()
    specimen = models.ScalarSpecimen.objects.create(
        label="stored",
        occurred_on=datetime.date(2020, 1, 2),
        occurred_at=_LOCKED_AT,
        occurred_time=_LOCKED_TIME,
        external_id=external_id,
    )
    return {"id": str(specimen.pk), "data": {"label": "renamed", **sent}}, external_id


def _assert_locked_kept(payload: JSONObject, external_id: uuid.UUID) -> None:
    """The update wrote ``label`` and kept each disabled column as stored."""
    assert payload == {
        "data": {
            "updateScalarSpecimenViaLockedStampForm": {
                "result": {
                    "label": "renamed",
                    "occurredAt": "2020-01-02T03:04:05.123456+00:00",
                    "occurredTime": "03:04:05.654321",
                },
                "errors": [],
            },
        },
    }
    rows = list(
        models.ScalarSpecimen.objects.values_list(
            "label",
            "occurred_at",
            "occurred_time",
            "external_id",
        ),
    )
    assert rows == [
        (
            "renamed",
            _LOCKED_AT,
            _LOCKED_TIME,
            external_id,
        ),
    ], rows


_LOCKED_SENT = [
    pytest.param({}, id="omitted"),
    pytest.param(
        {
            "occurredAt": "2030-05-06T07:08:09.654321+00:00",
            "occurredTime": "10:11:12.654321",
            "externalId": str(uuid.UUID(int=1)),
        },
        id="sent",
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("sent", _LOCKED_SENT)
def test_update_through_disabled_fields_keeps_their_stored_values(
    sent: Mapping[str, object],
) -> None:
    """An update keeps each disabled field's stored value, microseconds included.

    Django cleans a disabled field's initial, the stored value, and ignores a value the
    input sends for it; ``DateTimeInput`` and ``TimeInput`` present that initial with its
    microseconds zeroed, so the form field's own cleaning of ``occurred_at`` and
    ``occurred_time`` drops them. The instance gets each stored value back before the save,
    whether the input omits the field or sends one.
    """
    variables, external_id = _locked_variables(sent)

    payload = response_json(post_graphql(_LOCKED_DOCUMENT, variables=variables))

    _assert_locked_kept(payload, external_id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sent", _LOCKED_SENT)
async def test_async_update_through_disabled_fields_keeps_their_stored_values(
    sent: Mapping[str, object],
) -> None:
    """The async pipeline keeps a disabled field's stored value the same way, omitted or sent."""
    variables, external_id = await sync_to_async(_locked_variables)(sent)
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient().query(
            _LOCKED_DOCUMENT,
            variables=variables,
            assert_no_errors=False,
            url="/graphql-async/",
        )

    await sync_to_async(_assert_locked_kept)(response_json(result.response), external_id)


#: The ``UniqueScalarSpecimen`` surface: each flavor's create and update root fields and input
#: types.
_UNIQUE_FLAVORS = {
    "form": (
        "createUniqueScalarSpecimenViaForm",
        "UniqueScalarSpecimenFormInput",
        "updateUniqueScalarSpecimenViaForm",
        "UniqueScalarSpecimenFormPartialInput",
    ),
    "serializer": (
        "createUniqueScalarSpecimenViaSerializer",
        "UniqueScalarSpecimenSerializerInput",
        "updateUniqueScalarSpecimenViaSerializer",
        "UniqueScalarSpecimenSerializerPartialInput",
    ),
}

#: The values a ``UniqueScalarSpecimen`` create supplies beside the cell's.
_UNIQUE_CREATE_DATA: dict[str, object] = {
    "label": "written",
    "openedTime": "11:00:00",
    "openedAt": "2021-06-15T09:30:00+00:00",
    "amount": "7.5",
    "active": True,
}

#: The stored ``UniqueScalarSpecimen`` an update starts from.
_UNIQUE_STORED = {
    "label": "stored",
    "opened_time": datetime.time(3, 4, 5),
    "opened_at": _STORED_AT,
    "amount": Decimal("12.5000"),
}


def _unique_seed() -> models.UniqueScalarSpecimen:
    return models.UniqueScalarSpecimen.objects.create(**_UNIQUE_STORED)


def _unique_write(
    root_fields: tuple[str, str, str, str],
    specimen: models.UniqueScalarSpecimen | None,
    field: str,
    value: str,
) -> tuple[str, JSONObject]:
    """Send ``field: value`` through a create, or an update of ``specimen``; root and payload."""
    create_field, create_input, update_field, update_input = root_fields
    selection = (
        "{ result { label openedTime openedAt amount } errors { field messages codes path } }"
    )
    if specimen is None:
        document = (
            f"mutation Write($data: {create_input}!) {{ {create_field}(data: $data) {selection} }}"
        )
        variables: dict[str, object] = {"data": {**_UNIQUE_CREATE_DATA, field: value}}
        return create_field, response_json(post_graphql(document, variables=variables))
    document = (
        f"mutation Write($id: ID!, $data: {update_input}!) "
        f"{{ {update_field}(id: $id, data: $data) {selection} }}"
    )
    variables = {"id": str(specimen.pk), "data": {field: value}}
    return update_field, response_json(post_graphql(document, variables=variables))


def _unique_rows() -> list[tuple[object, ...]]:
    return list(
        models.UniqueScalarSpecimen.objects.order_by("label").values_list(
            "label",
            "opened_time",
            "opened_at",
            "amount",
        ),
    )


def _assert_nothing_written(specimen: models.UniqueScalarSpecimen | None) -> None:
    """A refusal creates no row and keeps an updated row's stored values."""
    expected = (
        []
        if specimen is None
        else [
            (
                _UNIQUE_STORED["label"],
                _UNIQUE_STORED["opened_time"],
                _UNIQUE_STORED["opened_at"],
                _UNIQUE_STORED["amount"],
            ),
        ]
    )
    assert _unique_rows() == expected


#: Each ``UniqueScalarSpecimen`` input field's column and the parse of its wire value.
_UNIQUE_COLUMNS: dict[str, tuple[str, Callable[[str], object]]] = {
    "openedTime": ("opened_time", datetime.time.fromisoformat),
    "openedAt": ("opened_at", datetime.datetime.fromisoformat),
    "amount": ("amount", Decimal),
}


def _native_unique_round_trip(column: str, value: object) -> object:
    """Store ``value`` in ``column`` through the ORM, read it back, then roll that row back."""
    with transaction.atomic():
        native = models.UniqueScalarSpecimen.objects.create(
            **{
                "label": "native-control",
                "opened_time": datetime.time(12, 13),
                "opened_at": _STORED_AT,
                "amount": Decimal(0),
                "active": False,
                column: value,
            },
        )
        native.refresh_from_db()
        stored = object_result(getattr, native, column)
        transaction.set_rollback(True)
    return stored


class _UniqueCell:
    """One value a uniqueness check would bind: its flavor, field, value, settings and outcome."""

    def __init__(
        self,
        flavor: str,
        field: str,
        value: str,
        outcomes: tuple[str, str],
        *,
        stored: str | None = None,
        settings: Mapping[str, object] | None = None,
    ) -> None:
        self.flavor = flavor
        self.field = field
        self.value = value
        self.outcomes = outcomes
        self.stored = stored
        self.settings = dict(settings or {})

    def outcome(self) -> str:
        """The outcome on the database the suite runs on."""
        sqlite, postgresql = self.outcomes
        return postgresql if connection.vendor == "postgresql" else sqlite

    def stored_value(self) -> object:
        """The column value a stored write reads back.

        A cell naming no ``stored`` value asks the database: Django's own write of the sent
        value, read back through the ORM (PostgreSQL's ``time`` keeps an aware time's wall
        clock and drops its offset).
        """
        column, parse = _UNIQUE_COLUMNS[self.field]
        if self.stored is not None:
            return parse(self.stored)
        return _native_unique_round_trip(column, parse(self.value))


_UNIQUE_CELLS = {
    "form-aware-unique-time": _UniqueCell(
        "form",
        "openedTime",
        "09:30:00+02:00",
        (_REFUSED, _STORED),
    ),
    "form-naive-unique-time": _UniqueCell("form", "openedTime", "09:30:00", (_STORED, _STORED)),
    "form-aware-unique-together-datetime-without-time-zone-support": _UniqueCell(
        "form",
        "openedAt",
        "2021-06-15T09:30:00+00:00",
        (_REFUSED, _STORED),
        settings={"USE_TZ": False},
    ),
    "form-naive-unique-together-datetime-without-time-zone-support": _UniqueCell(
        "form",
        "openedAt",
        "2021-06-15T09:30:00",
        (_STORED, _STORED),
        settings={"USE_TZ": False},
    ),
    "serializer-aware-unique-time": _UniqueCell(
        "serializer",
        "openedTime",
        "09:30:00+02:00",
        (_REFUSED, _STORED),
    ),
    "serializer-hook-unique-together-datetime-past-year-9999": _UniqueCell(
        "serializer",
        "openedAt",
        "9999-12-31T23:30:00",
        (_REFUSED, _REFUSED),
    ),
    "form-decimal-carried-past-the-column": _UniqueCell(
        "form",
        "amount",
        _PRICE_CARRIED_PAST_THE_COLUMN,
        (_REFUSED, _STORED),
    ),
    "serializer-decimal-carried-past-the-column": _UniqueCell(
        "serializer",
        "amount",
        _PRICE_CARRIED_PAST_THE_COLUMN,
        (_REFUSED, _STORED),
    ),
    "serializer-hook-unique-together-datetime-in-range": _UniqueCell(
        "serializer",
        "openedAt",
        "2021-06-15T09:30:00",
        (_STORED, _STORED),
        stored="2021-06-15T10:30:00+00:00",
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("name", list(_UNIQUE_CELLS))
def test_value_a_uniqueness_check_would_bind_is_the_field_error(operation: str, name: str) -> None:
    """A value the database cannot store is refused before a uniqueness check binds it.

    ``openedTime`` is ``unique=True`` and ``openedAt`` unique together with ``label``, so the
    ``ModelForm``'s ``validate_unique()`` and DRF's ``UniqueTogetherValidator`` would bind each
    value in a query inside ``is_valid()``, where the database's own refusal escapes as a masked
    top-level error: SQLite's adapter ``ValueError`` for an aware time, and for an aware
    datetime under ``USE_TZ = False``, on the form; the ``OverflowError`` of an instant past
    year 9999 in UTC, which the serializer's ``validate_opened_at`` makes of
    ``9999-12-31T23:30:00`` read as shop time, on the serializer. Each, and the serializer's
    aware time, is the field's ``invalid`` ``FieldError`` instead, nothing created and an
    updated row kept. ``amount`` is unique among active rows, and SQLite stores
    ``9999999999999999.9999`` as ``10000000000000000``, which the re-fetch could not read back
    into ``DecimalField(20, 4)``: the form and the serializer refuse it before that
    constraint's check binds it. PostgreSQL stores the aware time, the decimal and, under
    ``USE_TZ = False``, the aware datetime. A naive time, a
    naive datetime under ``USE_TZ = False`` and an in-range hook instant are stored. A stored
    write's payload and row carry what Django's own write of the sent value reads back on that
    database, or the hook's instant.
    """
    cell = _UNIQUE_CELLS[name]
    specimen = None if operation == "create" else _unique_seed()
    column, parse = _UNIQUE_COLUMNS[cell.field]
    with override_settings(**cell.settings):
        stored = None if cell.outcome() == _REFUSED else cell.stored_value()
        root, payload = _unique_write(
            _UNIQUE_FLAVORS[cell.flavor],
            specimen,
            cell.field,
            cell.value,
        )
        if cell.outcome() == _REFUSED:
            assert payload == _field_refusal(root, cell.field, _UNSTORABLE)
        else:
            assert json_at(payload, "data", root, "errors") == [], payload
            wire = json_at(payload, "data", root, "result", cell.field)
            assert isinstance(wire, str), payload
            assert parse(wire) == stored
            assert (
                object_result(getattr, models.UniqueScalarSpecimen.objects.get(), column) == stored
            )

    if cell.outcome() == _REFUSED:
        _assert_nothing_written(specimen)
    else:
        assert models.UniqueScalarSpecimen.objects.count() == 1


def _native_numeric_accepts(wire: str) -> bool:
    """Ask the real server to store and read the spelling, then roll that row back."""
    try:
        with transaction.atomic():
            native = models.UniqueScalarSpecimen.objects.create(
                label="native-control",
                opened_time=datetime.time(12, 13),
                opened_at=_STORED_AT,
                amount=Decimal(wire),
                active=True,
            )
            native.refresh_from_db()
            assert native.amount == Decimal(0)
            transaction.set_rollback(True)
    except DataError:
        return False
    return True


@contextmanager
def _amount_select_decimal_spellings() -> Generator[list[tuple[str, ...]], None, None]:
    """Record Decimal parameters before adaptation, forwarding every real statement."""
    observed: list[tuple[str, ...]] = []

    def observe(
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
        many: bool,  # noqa: FBT001 - Django execute_wrapper signature
        context: dict[str, object],
    ) -> object:
        if (
            sql.lstrip().upper().startswith("SELECT")
            and '"scalars_uniquescalarspecimen"' in sql
            and '"amount"' in sql
        ):
            values: Iterable[object]
            if is_dict(params):
                values = params.values()
            elif is_list_or_tuple(params):
                values = params
            else:
                values = ()
            observed.append(tuple(str(value) for value in values if isinstance(value, Decimal)))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(observe):
        yield observed


_NUMERIC_ZERO_ENDPOINTS = [
    pytest.param("0E+1073741822", 14, id="below-endpoint"),
    pytest.param("0E+1073741823", 16, id="at-endpoint"),
    pytest.param("0E+1073741824", None, id="past-endpoint"),
]


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(("wire", "accepted_from"), _NUMERIC_ZERO_ENDPOINTS)
def test_form_decimal_postgresql_numeric_endpoint_under_a_conditional_constraint(
    operation: str,
    wire: str,
    accepted_from: int | None,
) -> None:
    """The real server controls the form's endpoint answer before its constraint query.

    ``amount`` is unique among active rows (a conditional ``UniqueConstraint``), whose check
    inside ``is_valid()`` binds the sent value. A refused spelling is ``amount``'s
    ``invalid`` error, while a spelling the native ORM stores succeeds.
    """
    accepted = accepted_from is not None and connection.get_database_version()[0] >= accepted_from
    assert _native_numeric_accepts(wire) is accepted
    specimen = None if operation == "create" else _unique_seed()
    root, payload = _unique_write(
        _UNIQUE_FLAVORS["form"],
        specimen,
        "amount",
        wire,
    )

    if accepted:
        assert json_at(payload, "data", root, "errors") == [], payload
        assert Decimal(str(json_at(payload, "data", root, "result", "amount"))) == 0
        assert [row[3] for row in _unique_rows()] == [Decimal(0)]
    else:
        assert payload == _field_refusal(root, "amount", _UNSTORABLE)
        _assert_nothing_written(specimen)


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize(("wire", "accepted_from"), _NUMERIC_ZERO_ENDPOINTS)
def test_serializer_decimal_postgresql_numeric_endpoint_with_a_digitless_field(
    wire: str,
    accepted_from: int | None,
) -> None:
    """A digitless field accepts each spelling; the server decides its storage boundary.

    The native ORM control is independent of the framework's numeric predicate. An
    accepted spelling reaches the explicit two-field validator and stores zero; a refused
    spelling is the field's error with no row written.
    """
    accepted = accepted_from is not None and connection.get_database_version()[0] >= accepted_from
    assert _native_numeric_accepts(wire) is accepted
    root = "createUniqueScalarSpecimenViaUnboundedAmountSerializer"
    _, payload = _unique_write(
        (
            root,
            "UniqueScalarSpecimenUnboundedAmountSerializerInput",
            "",
            "",
        ),
        None,
        "amount",
        wire,
    )

    if accepted:
        assert json_at(payload, "data", root, "errors") == [], payload
        assert Decimal(str(json_at(payload, "data", root, "result", "amount"))) == 0
        assert [row[3] for row in _unique_rows()] == [Decimal(0)]
    else:
        assert payload == _field_refusal(root, "amount", _UNSTORABLE)
        _assert_nothing_written(None)


@pytest.mark.pg
@pytest.mark.django_db
def test_serializer_decimal_field_hook_operand_is_checked_at_uniqueness_query() -> None:
    """A fitting input becomes unbindable after conversion and before the query."""
    root = "createUniqueScalarSpecimenViaUnboundedAmountSerializer"
    fields = (
        root,
        "UniqueScalarSpecimenUnboundedAmountSerializerInput",
        "",
        "",
    )
    with _amount_select_decimal_spellings() as observed:
        _, payload = _unique_write(fields, None, "amount", "7")
    assert all("0E+1073741824" not in spellings for spellings in observed)
    assert payload == _field_refusal(root, "amount", _UNSTORABLE)
    _assert_nothing_written(None)


@pytest.mark.pg
@pytest.mark.django_db
def test_serializer_decimal_two_field_validator_rejects_a_fitting_duplicate() -> None:
    """A normal duplicate proves the declared serializer uniqueness validator runs."""
    _ = models.UniqueScalarSpecimen.objects.create(
        label="existing",
        opened_time=datetime.time(12, 13),
        opened_at=_STORED_AT,
        amount=Decimal(8),
        active=True,
    )
    root = "createUniqueScalarSpecimenViaUnboundedAmountSerializer"
    fields = (
        root,
        "UniqueScalarSpecimenUnboundedAmountSerializerInput",
        "",
        "",
    )
    with _amount_select_decimal_spellings() as observed:
        _, payload = _unique_write(fields, None, "amount", "8")
    assert any("8" in spellings for spellings in observed)
    assert json_at(payload, "data", root, "result") is None
    assert json_at(payload, "data", root, "errors", 0, "codes") == ["unique"]
    assert models.UniqueScalarSpecimen.objects.count() == 1


#: The first ``createScalarSpecimenTagWithUniqueSpecimens`` item, a value each column stores.
_FIRST_NESTED_SPECIMEN = (
    '{ label: "first", openedTime: "08:00:00", openedAt: "2021-01-01T00:00:00",'
    ' amount: "1.0000", active: true }'
)


#: The ``openedTime`` the second nested specimen sends beside the value under test.
_SECOND_OPENED_TIME = datetime.time(8, 30)


class _NestedCell:
    """One value sent on the second nested specimen: its field, value and outcome per backend.

    ``binds`` counts, per backend, the uniqueness statements binding the sent field's
    ``column``: one per specimen whose value the database binds.
    """

    def __init__(
        self,
        field: str,
        value: str,
        outcomes: tuple[str, str],
        binds: tuple[int, int],
        *,
        column: str,
        stored_time: datetime.time = _SECOND_OPENED_TIME,
    ) -> None:
        self.field = field
        self.value = value
        self.outcomes = outcomes
        self.binds = binds
        self.column = column
        self.stored_time = stored_time

    def outcome(self) -> str:
        """The outcome on the database the suite runs on."""
        sqlite, postgresql = self.outcomes
        return postgresql if connection.vendor == "postgresql" else sqlite

    def bind_count(self) -> int:
        """The statements binding ``column`` the write runs on the database the suite runs on."""
        sqlite, postgresql = self.binds
        return postgresql if connection.vendor == "postgresql" else sqlite

    def bound(self, statements: Sequence[str]) -> list[str]:
        """The SELECTs among ``statements`` comparing the specimen table's ``column``."""
        quote = connection.ops.quote_name
        compared = f"{quote(models.UniqueScalarSpecimen._meta.db_table)}.{quote(self.column)}"
        return [sql for sql in statements if sql.startswith("SELECT ") and compared in sql]


_NESTED_CELLS = {
    "hook-unique-together-datetime-past-year-9999": _NestedCell(
        "openedAt",
        "9999-12-31T23:30:00",
        (_REFUSED, _STORED),
        (1, 2),
        column="opened_at",
    ),
    "hook-unique-together-datetime-in-range": _NestedCell(
        "openedAt",
        "2021-06-15T09:30:00",
        (_STORED, _STORED),
        (2, 2),
        column="opened_at",
    ),
    "aware-unique-time": _NestedCell(
        "openedTime",
        "09:30:00+02:00",
        (_STORED, _STORED),
        (1, 2),
        column="opened_time",
        stored_time=datetime.time(9, 30),
    ),
    "naive-unique-time": _NestedCell(
        "openedTime",
        "09:30:00",
        (_STORED, _STORED),
        (2, 2),
        column="opened_time",
        stored_time=datetime.time(9, 30),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("name", list(_NESTED_CELLS))
def test_nested_value_a_uniqueness_validator_cannot_bind_is_the_item_field_error(
    name: str,
) -> None:
    """A nested item's value its uniqueness validator cannot bind is the item field's error.

    ``createScalarSpecimenTagWithUniqueSpecimens`` validates each ``specimens`` item through
    ``UniqueScalarSpecimenSerializer``, whose ``UniqueValidator`` / ``UniqueTogetherValidator``
    bind ``openedTime`` and ``openedAt`` in a query inside ``is_valid()``. On SQLite the
    ``validate_opened_at`` instant past year 9999 in UTC raises ``OverflowError`` there, which
    DRF's ``qs_exists`` does not catch; it is ``specimens.1.openedAt``'s ``invalid``
    ``FieldError`` instead, no tag and no specimen written. PostgreSQL binds that instant, so
    the serializer's own ``create()`` writes it. An aware time binds as the reading of a failed
    query as no duplicate expects (Django's ``ValueError``), so it reaches ``create()``,
    which stores its wall clock with the offset dropped; an in-range instant and a naive
    time are written too. SQLite runs no uniqueness query for the aware time, whose bind
    Django refuses before the statement. Only the statements comparing the sent field's
    column are counted: the validators DRF derives for the model's other constraints (the
    conditional ``amount`` one) differ between DRF releases.
    """
    cell = _NESTED_CELLS[name]
    document = (
        "mutation Write($second: UniqueScalarSpecimenSerializerInput!) {"
        " createScalarSpecimenTagWithUniqueSpecimens("
        f'data: {{ label: "tag", specimens: [{_FIRST_NESTED_SPECIMEN}, $second] }}'
        ") { result { label } errors { field messages codes path } } }"
    )
    second = {
        "label": "second",
        "openedTime": "08:30:00",
        "openedAt": "2021-01-01T00:00:00",
        "amount": "2.0000",
        "active": True,
        cell.field: cell.value,
    }
    with CaptureQueriesContext(connection) as queries:
        payload = response_json(post_graphql(document, variables={"second": second}))

    root = "createScalarSpecimenTagWithUniqueSpecimens"
    specimens = list(
        models.UniqueScalarSpecimen.objects.order_by("label").values_list("label", "opened_time"),
    )
    tags = list(models.ScalarSpecimenTag.objects.values_list("label", flat=True))
    if cell.outcome() == _REFUSED:
        path = ["specimens", "1", cell.field]
        assert payload == {
            "data": {
                root: {
                    "result": None,
                    "errors": [
                        {
                            "field": ".".join(path),
                            "messages": [_UNSTORABLE],
                            "codes": ["invalid"],
                            "path": path,
                        },
                    ],
                },
            },
        }
        assert (specimens, tags) == ([], [])
    else:
        assert payload == {"data": {root: {"result": {"label": "tag"}, "errors": []}}}
        assert specimens == [("first", datetime.time(8)), ("second", cell.stored_time)]
        assert tags == ["tag"]
    statements = [query["sql"] for query in queries.captured_queries]
    assert len(cell.bound(statements)) == cell.bind_count(), statements


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("opened_at", "refused"),
    [("9999-12-31T23:30:00", True), ("2021-06-15T09:30:00", False)],
)
def test_nested_uniqueness_uses_read_only_default_before_binding(
    opened_at: str,
    refused: bool,  # noqa: FBT001
) -> None:
    """A read-only default completes the pair DRF queries; the refused value is field keyed."""
    document = (
        "mutation Write($openedAt: DateTime!) {"
        " createScalarSpecimenTagWithReadOnlyLabelSpecimens(data: {"
        ' label: "tag", specimens: [{ openedAt: $openedAt, openedTime: "08:30:00",'
        ' amount: "2.0000", active: true }]'
        " }) { result { label } errors { field messages codes path } } }"
    )
    payload = response_json(post_graphql(document, variables={"openedAt": opened_at}))
    root = "createScalarSpecimenTagWithReadOnlyLabelSpecimens"
    if refused and connection.vendor == "sqlite":
        assert payload == {
            "data": {
                root: {
                    "result": None,
                    "errors": [
                        {
                            "field": "specimens.0.openedAt",
                            "messages": [_UNSTORABLE],
                            "codes": ["invalid"],
                            "path": ["specimens", "0", "openedAt"],
                        },
                    ],
                },
            },
        }
        assert not models.ScalarSpecimenTag.objects.exists()
        assert not models.UniqueScalarSpecimen.objects.exists()
    else:
        assert payload == {"data": {root: {"result": {"label": "tag"}, "errors": []}}}
        assert list(models.UniqueScalarSpecimen.objects.values_list("label", flat=True)) == [
            "defaulted",
        ]
