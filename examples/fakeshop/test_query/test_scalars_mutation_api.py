"""Live GraphQL HTTP tests for model input normalization and temporal database storability.

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
prefixed copy. The ``ViaPosted`` pairs' ``get_form_kwargs`` binds each value as its text:
the temporal form's one-key ``DateTimeField`` parses and stores it, while the split
widget's ``decompress`` cannot split the text of a datetime, a ``ConfigurationError``
naming its keys before ``is_valid()``, masked on the wire, with nothing written on
create, update or an update omitting ``occurredAt``.

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
a string sent is stored as that JSON string and one stored is kept when omitted. An update
omitting ``label`` and ``payload`` keeps each column's stored value where the form field's own
cleaning would rewrite it: a ``"  padded  "`` label is not stripped, a ``NULL`` label is not
written ``""``, and a JSON object or list is not written as its Python text, sync and async.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pytest
from apps.scalars import models
from asgiref.sync import sync_to_async
from config import schema as config_schema
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.utils import timezone
from graphql_client import JSONObject, json_at, post_graphql, response_json

from django_strawberry_framework.exceptions import ConfigurationError
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


def _flag_document(operation: str) -> tuple[str, str]:
    """Return the checkbox form mutation's root field and its document over ``$data``."""
    create_field, create_input, update_field, update_input = _FLAG_FORM
    if operation == "create":
        arguments, root = f"$data: {create_input}!", create_field
        call = f"{root}(data: $data)"
    else:
        arguments, root = f"$id: ID!, $data: {update_input}!", update_field
        call = f"{root}(id: $id, data: $data)"
    document = f"""
        mutation Write({arguments}) {{
          {call} {{
            result {{ label flag }}
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

    The declared ``forms.BooleanField(required=False)`` reads a bound ``None`` as ``False``.
    An explicit ``flag: null`` on create, on update over ``true``, ``false`` or ``NULL``
    stores ``NULL``, as the model flavor does, with empty ``errors``, and an update omitting
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
    ("operation", "value", "expected"),
    [
        pytest.param("create", None, "", id="create-null"),
        pytest.param("update", None, "", id="update-null"),
        pytest.param("update", "kept", "kept", id="update-value"),
    ],
)
def test_text_column_under_the_flag_form_keeps_the_empty_string_for_null(
    operation: str,
    value: str | None,
    expected: str,
) -> None:
    """``label: null`` on the ``null=True`` text column ``label`` stores ``""``, never ``NULL``.

    The column's own ``CharField`` cleans ``None`` to ``""``, Django's empty value for a
    text column, and the form flavor writes it as cleaned; a value sent is written.
    """
    root, document = _flag_document(operation)
    if operation == "create":
        variables: dict[str, object] = {"data": {"label": value, "flag": True}}
    else:
        specimen = models.NullableScalarSpecimen.objects.create(label="stored", flag=True)
        variables = {"id": str(specimen.pk), "data": {"label": value}}

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
    update over a value or ``NULL`` stores ``NULL`` with empty ``errors``, and an update
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


#: ``(stored, ...)``: the ``label`` / ``payload`` the row an update omitting both starts from.
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
