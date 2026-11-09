"""Live model, ModelForm and serializer writes through SQLite column-name conversion.

A real ``db_column`` with a bracketed type label asks ``PARSE_COLNAMES`` for a
bytes-to-ASCII-text converter. The write-side decimal trial must select that same name.
An independent ORM read determines whether the supported SQLite engine renders the
near-capacity double with enough text precision for Django's bounded converter.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from decimal import Decimal, InvalidOperation
from functools import wraps

import django
import pytest
import strawberry
from django import forms
from django.db import connection, models
from django.db.models.expressions import Combinable
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from drf_serializers import ModelSerializerBase
from graphql_client import JSONObject, graphql_payload
from typing_extensions import override

from django_strawberry_framework import (
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = [
    pytest.mark.skipif(
        connection.vendor != "sqlite" or django.VERSION < (6, 1),
        reason="SQLite column-name text conversion needs Django 6.1's string read-back",
    ),
    pytest.mark.usefixtures("private_registry"),
]
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_BOUNDARY = "99999999999999.99"
_FIT = "12.50"
_MESSAGE = "Enter a value the database can represent."


class _NamedDecimal(models.Model):
    label: models.TextField[str | Combinable, str] = models.TextField()
    amount: models.DecimalField[str | float | Decimal | Combinable, Decimal] = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        db_column="amount [decimal_text]",
    )

    class Meta:
        app_label = "scalars"
        managed = False

    @override
    def __str__(self) -> str:
        return self.label


class _NamedDecimalForm(forms.ModelForm[_NamedDecimal]):
    class Meta:
        model = _NamedDecimal
        fields = ("label", "amount")


class _NamedDecimalSerializer(ModelSerializerBase[_NamedDecimal]):
    class Meta:
        model = _NamedDecimal
        fields = ("label", "amount")


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-decimal-column-name/", _view)]


@strawberry.type
class _Query:
    ping: int = 1


def _schema(flavor: str, operation: str) -> DjangoSchema:
    class NamedDecimalType(DjangoType):
        class Meta:
            model = _NamedDecimal
            fields = ("id", "label", "amount")

    selected_operation = operation
    if flavor == "model":

        class ModelWrite(DjangoMutation):
            class Meta:
                model = _NamedDecimal
                operation = selected_operation
                permission_classes = []

        write_field = DjangoMutationField(ModelWrite)

    elif flavor == "form":

        class FormWrite(DjangoModelFormMutation):
            class Meta:
                form_class = _NamedDecimalForm
                operation = selected_operation
                permission_classes = []

        write_field = DjangoMutationField(FormWrite)

    else:

        class SerializerWrite(SerializerMutation):
            class Meta:
                serializer_class = _NamedDecimalSerializer
                operation = selected_operation
                permission_classes = []

        write_field = DjangoMutationField(SerializerWrite)

    @strawberry.type
    class Mutation:
        write = write_field

    finalize_django_types()
    return DjangoSchema(query=_Query, mutation=Mutation, types=(NamedDecimalType,))


@pytest.fixture
def named_decimal_table(transactional_db: None) -> Generator[list[bytes], None, None]:
    """Create only a test table; restore the process-wide driver converter exactly."""
    _ = transactional_db
    with connection.schema_editor() as editor:
        editor.create_model(_NamedDecimal)
    seen: list[bytes] = []
    kept = sqlite3.converters.get("DECIMAL_TEXT")

    def _decode(raw: bytes) -> str:
        seen.append(raw)
        return raw.decode("ascii")

    sqlite3.register_converter("decimal_text", _decode)
    try:
        yield seen
    finally:
        if kept is None:
            del sqlite3.converters["DECIMAL_TEXT"]
        else:
            sqlite3.register_converter("decimal_text", kept)
        with connection.schema_editor() as editor:
            editor.delete_model(_NamedDecimal)


def _post(schema: DjangoSchema, amount: str, *, row_id: int | None) -> JSONObject:
    identifier = f'id: "{row_id}", ' if row_id is not None else ""
    document = (
        f'mutation {{ write({identifier}data: {{ label: "written", amount: "{amount}" }}) '
        "{ result { label amount } errors { field messages codes path } } }"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                url="/graphql-decimal-column-name/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("flavor", ["model", "form", "serializer"])
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("amount", [_FIT, _BOUNDARY], ids=["fitting", "boundary"])
def test_named_decimal_readback_matches_the_real_column_over_http(
    named_decimal_table: list[bytes],
    flavor: str,
    operation: str,
    amount: str,
) -> None:
    """A named converter's real read-back decides the write result in every flavor."""
    assert connection.get_connection_params()["detect_types"] & sqlite3.PARSE_COLNAMES

    # The probe is independent of the package guard: Django saves and then reads the
    # actual labeled column through its ordinary ORM converter chain.
    probe = _NamedDecimal.objects.create(label="probe", amount=Decimal(amount))
    try:
        expected = _NamedDecimal.objects.get(pk=saved_pk(probe)).amount
    except InvalidOperation:
        refused = True
        expected = None
    else:
        refused = False
    assert named_decimal_table
    named_decimal_table.clear()
    if amount == _FIT:
        assert expected == Decimal(_FIT)

    previous = (
        _NamedDecimal.objects.create(label="stored", amount=Decimal(_FIT))
        if operation == "update"
        else None
    )
    count_before = _NamedDecimal.objects.count()
    schema = _schema(flavor, operation)
    payload = _post(schema, amount, row_id=saved_pk(previous) if previous is not None else None)

    assert named_decimal_table
    if refused:
        assert payload == {
            "data": {
                "write": {
                    "result": None,
                    "errors": [
                        {
                            "field": "amount",
                            "messages": [_MESSAGE],
                            "codes": ["invalid"],
                            "path": ["amount"],
                        },
                    ],
                },
            },
        }
        assert _NamedDecimal.objects.count() == count_before
        if previous is not None:
            previous.refresh_from_db()
            assert (previous.label, previous.amount) == ("stored", Decimal(_FIT))
        return

    assert payload == {
        "data": {"write": {"result": {"label": "written", "amount": str(expected)}, "errors": []}},
    }
    assert _NamedDecimal.objects.count() == count_before + (operation == "create")
    written = (
        _NamedDecimal.objects.get(pk=saved_pk(previous))
        if previous is not None
        else _NamedDecimal.objects.exclude(pk=saved_pk(probe)).get()
    )
    assert (written.label, written.amount) == ("written", expected)
