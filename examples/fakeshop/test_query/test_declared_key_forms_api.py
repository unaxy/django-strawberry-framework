"""Native key filters publish their stored-column scalar and validate raw key bounds over HTTP."""

import uuid
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from decimal import Decimal
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db import connection
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter, Filter
from graphql_client import JSONObject, JSONValue, graphql_payload, json_list, json_object, json_str
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from strawberry.types import Info

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.views import DjangoGraphQLView
from tests._filter_key_models import (
    _DecimalKeyed,
    _DecimalKeyedHolder,
    _UuidKeyed,
    _UuidKeyedProfile,
)
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-declared-keys/", _view)]


def _post(
    schema: DjangoSchema,
    document: str,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(document, variables=variables, url="/graphql-declared-keys/")
    finally:
        _CURRENT["schema"] = None


def _key(self: Model) -> str:
    return str(read_attr(self, "pk"))


def _output(source: type[Model], *, selected: type[FilterSet] | None = None) -> type[DjangoType]:
    return make_django_type(
        "KeyAliasOutput",
        source,
        (),
        node=selected is not None,
        meta_extra={"filterset_class": selected} if selected is not None else None,
        namespace_extra={"__annotations__": {"key": str}, "key": strawberry.field(resolver=_key)},
    )


def _published_schema(source: type[Model], leaf: Filter) -> DjangoSchema:
    selected = type(
        "KeyAliasFilter",
        (FilterSet,),
        {"leaf": leaf, "Meta": type("Meta", (), {"model": source, "fields": ()})},
    )
    output = _output(source, selected=selected)
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"rows": DjangoConnection[output]},
                "rows": DjangoConnectionField(output),
            },
        ),
    )
    finalize_django_types()
    return DjangoSchema(query=query, config=strawberry_config())


def _sdl(value: JSONObject) -> str:
    kind = json_str(value, "kind")
    if kind == "NON_NULL":
        return f"{_sdl(json_object(value, 'ofType'))}!"
    if kind == "LIST":
        return f"[{_sdl(json_object(value, 'ofType'))}]"
    return json_str(value, "name")


@pytest.mark.parametrize(
    (
        "source",
        "leaf",
        "lookup",
        "expected",
    ),
    [
        pytest.param(
            _DecimalKeyed,
            ListFilter(field_name="pk", lookup_expr="in"),
            "in",
            "[Decimal!]",
            id="decimal-pk-list",
        ),
        pytest.param(
            _DecimalKeyedHolder,
            ListFilter(field_name="owner__pk", lookup_expr="in"),
            "in",
            "[Decimal!]",
            id="decimal-related-pk-list",
        ),
        pytest.param(
            _UuidKeyed,
            ListFilter(field_name="pk", lookup_expr="in"),
            "in",
            "[UUID!]",
            id="uuid-pk-list",
        ),
        pytest.param(
            _UuidKeyedProfile,
            ListFilter(field_name="pk", lookup_expr="in"),
            "in",
            "[UUID!]",
            id="uuid-relation-valued-pk-list",
        ),
        pytest.param(_UuidKeyed, CharFilter(field_name="pk"), "exact", "UUID", id="uuid-pk-char"),
    ],
)
def test_declared_key_inputs_publish_the_real_decimal_or_uuid_column(
    source: type[Model],
    leaf: Filter,
    lookup: str,
    expected: str,
) -> None:
    """The public input publishes the stored column's scalar through pk and relation-pk aliases."""
    payload = _post(
        _published_schema(source, leaf),
        """
        {
          __type(name: "KeyAliasFilterLeafFilterInputType") {
            inputFields {
              name
              type { kind name ofType { kind name ofType { kind name } } }
            }
          }
        }
        """,
    )
    assert "errors" not in payload, payload
    fields = {
        json_str(field, "name"): _sdl(json_object(field, "type"))
        for field in json_list(payload, "data", "__type", "inputFields")
    }
    assert fields[lookup] == expected, payload


def _forms_schema(source: type[Model]) -> DjangoSchema:
    selected = type(
        "RawKeyForms",
        (FilterSet,),
        {
            "pk_span": RangeFilter(field_name="pk", lookup_expr="range"),
            "pk_among": ListFilter(field_name="pk", lookup_expr="in"),
            "Meta": type("Meta", (), {"model": source, "fields": ()}),
        },
    )
    output = _output(source)

    def resolve_rows(root: object, info: Info[object, object], where: JSON) -> QuerySet[Model]:
        del root
        return selected.apply_sync(where, source._default_manager.order_by("pk"), info)

    @strawberry.type
    class Query:
        rows: QuerySet[Model] = strawberry.field(resolver=resolve_rows, graphql_type=list[output])

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@contextmanager
def _key_tables(source: type[Model]) -> Generator[None]:
    tables = (
        (_UuidKeyed, _UuidKeyedProfile)
        if source is _UuidKeyedProfile
        else (source,)
        if source in {_DecimalKeyed, _UuidKeyed}
        else ()
    )
    with connection.schema_editor() as editor:
        for model in tables:
            editor.create_model(model)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(tables):
                editor.delete_model(model)


def _seed_keys(source: type[Model]) -> tuple[str | int, str | int]:
    if source is _DecimalKeyed:
        for key in (Decimal("1.50"), Decimal("3.00")):
            _DecimalKeyed.objects.create(code=key)
        return "1.50", "3.00"
    if source is _UuidKeyed:
        for value in (1, 2):
            _UuidKeyed.objects.create(code=uuid.UUID(int=value))
        return str(uuid.UUID(int=1)), str(uuid.UUID(int=2))
    if source is _UuidKeyedProfile:
        for value in (1, 2):
            _UuidKeyedProfile.objects.create(
                owner=_UuidKeyed.objects.create(code=uuid.UUID(int=value)),
            )
        return str(uuid.UUID(int=1)), str(uuid.UUID(int=2))
    if source is models.LendingDesk:
        kept = models.LendingDesk.objects.create(name="Keep")
        other = models.LendingDesk.objects.create(name="Other")
        return saved_pk(kept), saved_pk(other)
    patrons = [models.Patron.objects.create(name=name) for name in ("Keep", "Other")]
    profiles = [models.PatronProfile.objects.create(patron=patron) for patron in patrons]
    return saved_pk(profiles[0]), saved_pk(profiles[1])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("admitted", [False, True], ids=["refused", "admitted-control"])
@pytest.mark.parametrize(
    (
        "source",
        "field",
        "bad",
        "message",
    ),
    [
        pytest.param(
            _DecimalKeyed,
            "pk_span",
            {"range": {"start": "NaN", "end": "Infinity"}},
            "Enter a number.",
            id="decimal-range",
        ),
        pytest.param(
            _DecimalKeyed,
            "pk_among",
            ["1.5", "NaN"],
            "Enter a number.",
            id="decimal-list",
        ),
        pytest.param(
            _UuidKeyed,
            "pk_span",
            {"range": {"start": "not-a-uuid", "end": ""}},
            "Enter a valid UUID.",
            id="uuid-range",
        ),
        pytest.param(
            _UuidKeyed,
            "pk_among",
            ["not-a-uuid"],
            "Enter a valid UUID.",
            id="uuid-list",
        ),
        pytest.param(
            _UuidKeyedProfile,
            "pk_among",
            ["not-a-uuid"],
            "Enter a valid UUID.",
            id="uuid-relation-valued-key-list",
        ),
        pytest.param(
            models.LendingDesk,
            "pk_span",
            {"range": {"start": "abc", "end": "2"}},
            "Enter a number.",
            id="mti-key-range",
        ),
        pytest.param(
            models.PatronProfile,
            "pk_among",
            ["abc"],
            "Enter a number.",
            id="integer-relation-valued-key-list",
        ),
    ],
)
def test_raw_declared_key_forms_refuse_values_the_stored_key_cannot_clean(
    source: type[Model],
    field: str,
    bad: JSONValue,
    message: str,
    *,
    admitted: bool,
) -> None:
    """Raw JSON reaches the unbound set's column-cleaning form, including relation-valued keys."""
    with _key_tables(source):
        first, _other = _seed_keys(source)
        control: JSONValue = (
            {"range": {"start": first, "end": first}} if field == "pk_span" else [str(first)]
        )
        payload = _post(
            _forms_schema(source),
            "query($where: JSON!) { rows(where: $where) { key } }",
            {"where": {field: control if admitted else bad}},
        )
        if admitted:
            assert payload == {"data": {"rows": [{"key": str(first)}]}}, payload
        else:
            assert payload["data"] is None, payload
            assert len(json_list(payload, "errors")) == 1, payload
            error = json_object(payload, "errors", 0)
            assert error["path"] == ["rows"], payload
            assert error["extensions"] == {
                "code": "FILTER_INVALID",
                "errors": {field: [{"message": message, "code": "invalid"}]},
            }, payload
