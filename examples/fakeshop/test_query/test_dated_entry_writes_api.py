"""Live GraphQL HTTP tests for Django's date checks and a text-mapped duration on every write flavor.

``DatedEntrySpecimen`` holds ``slug`` (``unique_for_date``), ``edition`` (``unique_for_year``)
and ``issue`` (``unique_for_month``), each against the ``DateTimeField`` ``published_at``, and
``span``, a ``TextDurationField`` the scalars schema maps to text through ``SCALAR_MAP``. Each
is written through ``createDatedEntrySpecimen`` / ``updateDatedEntrySpecimen``
(``DjangoMutation``), their ``ViaForm`` siblings (``DjangoModelFormMutation`` over
``DatedEntrySpecimenForm``) and their ``ViaSerializer`` siblings (``SerializerMutation`` over
``DatedEntrySpecimenSerializer``).

Django bounds a ``unique_for_date`` / ``unique_for_year`` check's year in the current time zone
(the zone ``timezone.activate`` set, not ``TIME_ZONE``) and SQLite projects each bound onto
UTC, so a storable ``publishedAt`` in year 9999 under a zone west of UTC, or in year 1 under
one east of it, is a year the check cannot bound. The model and form flavors answer the
``publishedAt`` ``invalid`` ``FieldError`` ("Enter a date whose whole year the current time
zone can represent."), once for both checks, with nothing written, on create, update, sync and
async; an update omitting ``publishedAt`` over such a stored value answers it under ``slug``,
the field the date check validates (and, on the form, which validates the whole row, under
``edition`` too). The serializer flavor's guarded DRF validators answer ``publishedAt``'s
``invalid`` error ("Enter a value the database can represent."). A ``unique_for_month`` check
binds no year bound: an update writing ``issue`` alone over such a stored value is written on
the model flavor. The last instant of year 9999 under UTC is written, and so is year 9999
under an activated UTC beside a ``TIME_ZONE`` west of it; a second entry for the same date is
still Django's or DRF's own ``unique_for_date`` error.

``span`` text past ``timedelta``'s range is the ``span`` ``overflow`` ``FieldError`` Django's
``forms.DurationField`` answers ("The number of days must be between -999999999 and
999999999."), the same on every flavor, with nothing written, sync and async; text that is no
duration keeps each flavor's own ``invalid`` error and an explicit ``null`` stores ``NULL``.
On SQLite a span at the 64-bit microsecond edge is written and one past it is the ``span``
``invalid`` error ("Enter a value the database can represent.") on every flavor.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping

import pytest
from apps.scalars import models
from asgiref.sync import sync_to_async
from config import schema as config_schema
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from django.utils.duration import duration_string
from graphql_client import JSONObject, SchemaMount, post_graphql, response_json

from django_strawberry_framework.testing import AsyncTestClient

_UNBOUNDED_YEAR = "Enter a date whose whole year the current time zone can represent."
_UNSTORABLE = "Enter a value the database can represent."
_DAYS_OVERFLOW = "The number of days must be between -999999999 and 999999999."
_MAX_MICROSECONDS = 2**63 - 1

#: Each flavor's create and update root fields and their input types.
_FLAVORS = {
    "model": (
        "createDatedEntrySpecimen",
        "DatedEntrySpecimenInput",
        "updateDatedEntrySpecimen",
        "DatedEntrySpecimenPartialInput",
    ),
    "form": (
        "createDatedEntrySpecimenViaForm",
        "DatedEntrySpecimenFormInput",
        "updateDatedEntrySpecimenViaForm",
        "DatedEntrySpecimenFormPartialInput",
    ),
    "serializer": (
        "createDatedEntrySpecimenViaSerializer",
        "DatedEntrySpecimenSerializerInput",
        "updateDatedEntrySpecimenViaSerializer",
        "DatedEntrySpecimenSerializerPartialInput",
    ),
}

_CREATE_DATA: dict[str, object] = {
    "slug": "written",
    "edition": "first",
    "issue": "june",
    "publishedAt": "2021-06-15T09:30:00+00:00",
}
_STORED_AT = datetime.datetime(2021, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)
#: A storable instant whose year 9999 a zone west of UTC cannot bound.
_LATE_AT = datetime.datetime(9999, 6, 1, tzinfo=datetime.timezone.utc)


def _document(flavor: str, operation: str) -> tuple[str, str]:
    """The root field and document writing ``operation`` through ``flavor``."""
    create_root, create_input, update_root, update_input = _FLAVORS[flavor]
    selection = "{ result { slug } errors { field messages codes } }"
    if operation == "create":
        return create_root, (
            f"mutation W($d: {create_input}!) {{ {create_root}(data: $d) {selection} }}"
        )
    return update_root, (
        f"mutation W($id: ID!, $d: {update_input}!) "
        f"{{ {update_root}(id: $id, data: $d) {selection} }}"
    )


def _stored(published_at: datetime.datetime = _STORED_AT) -> models.DatedEntrySpecimen:
    """Store the row an update starts from, as the ORM saves it (no validation)."""
    return models.DatedEntrySpecimen.objects.create(
        slug="stored",
        edition="stored",
        issue="stored",
        published_at=published_at,
    )


def _variables(
    data: Mapping[str, object],
    row: models.DatedEntrySpecimen | None,
) -> dict[str, object]:
    """The variables a create (the full input over ``data``) or an update (``data`` alone) sends."""
    if row is None:
        return {"d": {**_CREATE_DATA, **data}}
    return {"id": str(row.pk), "d": dict(data)}


def _write(
    flavor: str,
    operation: str,
    data: Mapping[str, object],
    row: models.DatedEntrySpecimen | None = None,
) -> tuple[str, JSONObject]:
    """Post ``operation`` through ``flavor`` and return its root field and response body."""
    root, document = _document(flavor, operation)
    return root, response_json(post_graphql(document, variables=_variables(data, row)))


def _refusal(
    root: str,
    field: str,
    message: str,
    code: str,
) -> JSONObject:
    """The response a write refused as one ``FieldError`` answers."""
    return {
        "data": {
            root: {
                "result": None,
                "errors": [{"field": field, "messages": [message], "codes": [code]}],
            },
        },
    }


def _written(root: str, slug: str) -> JSONObject:
    """The response a written row answers."""
    return {"data": {root: {"result": {"slug": slug}, "errors": []}}}


def _slugs() -> list[str]:
    return sorted(models.DatedEntrySpecimen.objects.values_list("slug", flat=True))


_SQLITE = pytest.mark.skipif(
    connection.vendor != "sqlite",
    reason="SQLite projects the year bound onto UTC",
)

#: (zone, publishedAt): a storable instant whose year the active zone cannot bound.
_UNBOUNDED_YEARS = {
    "west-9999": ("America/New_York", "9999-06-01T00:00:00+00:00"),
    "east-0001": ("Asia/Tokyo", "0001-06-01T00:00:00+00:00"),
}


def _unbounded_year(flavor: str, root: str) -> JSONObject:
    """Each flavor's answer to a ``publishedAt`` whose year the active zone cannot bound."""
    if flavor == "serializer":
        # DRF's date-check validators run under the serializer flavor's own query guard.
        return _refusal(root, "publishedAt", _UNSTORABLE, "invalid")
    return _refusal(root, "publishedAt", _UNBOUNDED_YEAR, "invalid")


@_SQLITE
@pytest.mark.django_db
@pytest.mark.parametrize("flavor", list(_FLAVORS))
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("shape", list(_UNBOUNDED_YEARS))
def test_year_the_current_time_zone_cannot_bound_is_the_field_error(
    flavor: str,
    operation: str,
    shape: str,
) -> None:
    """A ``publishedAt`` whose year the activated zone cannot bound is its error, written nowhere.

    The ``unique_for_date`` and ``unique_for_year`` checks both bound that year: the model and
    form flavors answer the one ``publishedAt`` error, the serializer flavor DRF's validators'
    refusal. An update sends every column, which DRF's date checks require.
    """
    zone, published_at = _UNBOUNDED_YEARS[shape]
    row = None if operation == "create" else _stored()
    data = {**_CREATE_DATA, "publishedAt": published_at}
    with timezone.override(zone):
        root, payload = _write(flavor, operation, data, row)

    assert payload == _unbounded_year(flavor, root)
    assert _slugs() == ([] if row is None else ["stored"])


@_SQLITE
@pytest.mark.django_db
@pytest.mark.parametrize("flavor", ["model", "form"])
def test_update_omitting_a_stored_unbounded_year_is_the_validated_fields_error(
    flavor: str,
) -> None:
    """An update writing ``slug`` alone over a stored year 9999 under New York answers ``slug``.

    The ``unique_for_date`` check validates ``slug`` against the stored ``published_at``, whose
    year the zone cannot bound; the input names no date field, so ``slug`` carries the error.
    The form validates the whole row, so its ``unique_for_year`` check over the kept ``edition``
    answers under ``edition`` too; the model flavor skips a check no provided field joins.
    """
    row = _stored(_LATE_AT)
    with timezone.override("America/New_York"):
        root, payload = _write(flavor, "update", {"slug": "renamed"}, row)

    fields = ["slug", "edition"] if flavor == "form" else ["slug"]
    errors = [
        {"field": field, "messages": [_UNBOUNDED_YEAR], "codes": ["invalid"]} for field in fields
    ]
    assert payload == {"data": {root: {"result": None, "errors": errors}}}
    assert _slugs() == ["stored"]


@_SQLITE
@pytest.mark.django_db
def test_month_check_over_a_stored_unbounded_year_binds_no_year() -> None:
    """A model update writing ``issue`` alone runs the ``unique_for_month`` check alone: written."""
    row = _stored(_LATE_AT)
    with timezone.override("America/New_York"):
        root, payload = _write("model", "update", {"issue": "july"}, row)

    assert payload == _written(root, "stored")
    assert list(models.DatedEntrySpecimen.objects.values_list("issue", flat=True)) == ["july"]


@pytest.mark.django_db
@pytest.mark.parametrize("flavor", list(_FLAVORS))
@pytest.mark.parametrize(
    ("time_zone", "active", "published_at"),
    [
        pytest.param("UTC", "UTC", "9999-12-31T23:59:59.999999+00:00", id="last-instant-utc"),
        pytest.param("America/New_York", "UTC", "9999-06-01T00:00:00+00:00", id="active-utc"),
    ],
)
def test_year_the_active_zone_bounds_is_written(
    flavor: str,
    time_zone: str,
    active: str,
    published_at: str,
) -> None:
    """A year the activated zone bounds is written, whatever ``TIME_ZONE`` names."""
    with override_settings(TIME_ZONE=time_zone), timezone.override(active):
        root, payload = _write(flavor, "create", {"publishedAt": published_at})

    assert payload == _written(root, "written")
    assert _slugs() == ["written"]


@pytest.mark.django_db
@pytest.mark.parametrize("flavor", list(_FLAVORS))
def test_second_entry_for_the_date_is_the_date_checks_own_error(flavor: str) -> None:
    """The guarded date check still finds a duplicate: Django's or DRF's own error on ``slug``."""
    _ = _write(flavor, "create", {"edition": "first", "issue": "june"})
    root, payload = _write(flavor, "create", {"edition": "second", "issue": "july"})

    message = (
        'This field must be unique for the "published_at" date.'
        if flavor == "serializer"
        else "Slug must be unique for Published at date."
    )
    code = "unique" if flavor == "serializer" else "unique_for_date"
    assert payload == _refusal(root, "slug", message, code)
    assert _slugs() == ["written"]


#: ``span`` text and each flavor's refusal of it, ``(message, code)``.
_SPANS: dict[str, tuple[str, dict[str, tuple[str, str]]]] = {
    "past-timedelta": (
        "1000000000 00:00:00",
        dict.fromkeys(_FLAVORS, (_DAYS_OVERFLOW, "overflow")),
    ),
    "no-duration": (
        "soon",
        {
            "model": (
                (
                    "\u201csoon\u201d value has an invalid format. "
                    "It must be in [DD] [[HH:]MM:]ss[.uuuuuu] format."
                ),
                "invalid",
            ),
            "form": ("Enter a valid duration.", "invalid"),
            "serializer": (
                (
                    "Duration has wrong format. Use one of these formats instead: "
                    "[DD] [HH:[MM:]]ss[.uuuuuu]."
                ),
                "invalid",
            ),
        },
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("flavor", list(_FLAVORS))
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("shape", list(_SPANS))
def test_span_text_no_timedelta_holds_is_the_field_error(
    flavor: str,
    operation: str,
    shape: str,
) -> None:
    """``span`` text past ``timedelta``'s range is Django's ``overflow`` error on every flavor.

    Text that is no duration keeps each flavor's own ``invalid`` error.
    """
    text, answers = _SPANS[shape]
    answer = answers[flavor]
    row = None if operation == "create" else _stored()
    data = {**_CREATE_DATA, "span": text}
    root, payload = _write(flavor, operation, data, row)

    assert payload == _refusal(root, "span", *answer)
    assert _slugs() == ([] if row is None else ["stored"])


@pytest.mark.skipif(connection.vendor != "sqlite", reason="64-bit microsecond binding")
@pytest.mark.django_db
@pytest.mark.parametrize("flavor", list(_FLAVORS))
@pytest.mark.parametrize(
    ("microseconds", "stored"),
    [(_MAX_MICROSECONDS, True), (-(2**63), True), (_MAX_MICROSECONDS + 1, False)],
    ids=["max", "min", "past-max"],
)
def test_span_at_the_64_bit_edge(flavor: str, microseconds: int, *, stored: bool) -> None:
    """A span SQLite binds in 64 bits of microseconds is written; one past it is refused."""
    span = datetime.timedelta(microseconds=microseconds)
    root, payload = _write(flavor, "create", {"span": duration_string(span)})

    if stored:
        assert payload == _written(root, "written")
        assert list(models.DatedEntrySpecimen.objects.values_list("span", flat=True)) == [span]
        return
    assert payload == _refusal(root, "span", _UNSTORABLE, "invalid")
    assert _slugs() == []


@pytest.mark.django_db
@pytest.mark.parametrize("flavor", list(_FLAVORS))
def test_span_null_is_written(flavor: str) -> None:
    """An explicit ``span: null`` stores ``NULL``: no text reaches the duration parse."""
    root, payload = _write(flavor, "create", {"span": None})

    assert payload == _written(root, "written")
    assert list(models.DatedEntrySpecimen.objects.values_list("span", flat=True)) == [None]


_MOUNT = SchemaMount(__name__, async_route="graphql-async/")
urlpatterns = _MOUNT.urlpatterns


@_SQLITE
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("flavor", list(_FLAVORS))
@pytest.mark.parametrize("shape", ["unbounded-year", "past-timedelta"])
async def test_async_write_answers_the_same_errors(flavor: str, shape: str) -> None:
    """The async pipeline answers an unbounded year and an overflowing span the same way."""
    root, document = _document(flavor, "create")
    if shape == "unbounded-year":
        data: dict[str, object] = {"publishedAt": "9999-06-01T00:00:00+00:00"}
        expected = _unbounded_year(flavor, root)
    else:
        data = {"span": "1000000000 00:00:00"}
        expected = _refusal(root, "span", _DAYS_OVERFLOW, "overflow")
    with _MOUNT.serving(config_schema.schema), timezone.override("America/New_York"):
        result = await AsyncTestClient().query(
            document,
            variables=_variables(data, None),
            assert_no_errors=False,
            url="/graphql-async/",
        )

    assert response_json(result.response) == expected
    assert await sync_to_async(_slugs)() == []
