"""Live GraphQL HTTP tests for temporal writes the database cannot store.

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

The ``SplitForm`` pairs write ``occurred_at`` through a ``SplitDateTimeField``, whose
widget reads a date key and a time key: the datetime sent is stored on create and update
and kept when omitted, unprefixed, under the form's prefix and beside a ``get_form``'s own
prefixed copy.
"""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest
from apps.scalars import models
from asgiref.sync import sync_to_async
from config import schema as config_schema
from django.db import connection
from django.test import override_settings
from django.urls import path
from graphql_client import json_at, post_graphql, response_json

from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http.response import HttpResponseBase

_UNSTORABLE = "Enter a value the database can represent."

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
