"""Consumer filters over a JSON column publish and compare the kind their own form cleans.

Rung 3: the subject is consumer filter classes no fakeshop app would ship (an integer-cleaning
``Filter`` and its CSV ``in``, a ``method=`` filter), declared over ``ScalarSpecimen.payload``
and its key paths. The shipped filter classes over the same column are declared on fakeshop's
``ScalarSpecimenFilter`` and live in ``test_scalars_filter_api.py``. All requests go over HTTP.
"""

from collections.abc import Sequence
from functools import wraps

import pytest
import strawberry
from apps.scalars import models
from django import forms
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django.utils import timezone
from django_filters import BaseInFilter, Filter, NumberFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, graphql_payload, json_object
from strawberry import relay
from strawberry.types import Info
from strawberry.types.base import StrawberryObjectDefinition

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


class IntFilter(Filter):
    """A consumer filter whose form cleans an integer, as no shipped filter does."""

    field_class = forms.IntegerField


class IntsInFilter(BaseInFilter, IntFilter):
    """A consumer CSV filter whose form cleans each member as an integer."""


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-json-filter-typing/", _graphql_view)]


def _holder() -> tuple[DjangoSchema, type[DjangoType]]:
    """Declare the JSON filters a consumer would, served by a connection over ``ScalarSpecimen``."""

    class JSONPayloadFilter(FilterSet):
        int_n = IntFilter(field_name="payload__n")
        ints_n = IntsInFilter(field_name="payload__n", lookup_expr="in")
        own_number = NumberFilter(field_name="payload", method="own_filter")

        class Meta:
            model = models.ScalarSpecimen
            fields = []

        def own_filter(
            self,
            queryset: QuerySet[models.ScalarSpecimen],
            _name: str,
            _value: object,
        ) -> QuerySet[models.ScalarSpecimen]:
            return queryset

    class JSONPayloadSpecimen(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("label",)
            interfaces = (relay.Node,)
            filterset_class = JSONPayloadFilter

    finalize_django_types()

    @strawberry.type
    class Query:
        def _rows(self, _info: Info) -> QuerySet[models.ScalarSpecimen]:
            return models.ScalarSpecimen.objects.order_by("pk")

        rows: DjangoConnection[JSONPayloadSpecimen] = DjangoConnectionField(
            JSONPayloadSpecimen,
            resolver=_rows,
        )

    return DjangoSchema(query=Query, config=strawberry_config()), JSONPayloadSpecimen


def _input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(schema: DjangoSchema, python_path: Sequence[str], value: object) -> JSONObject:
    """Ask the published definitions and NameConverter for each input field's actual name."""
    current = _input(schema)
    names: list[str] = []
    for index, name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == name)
        wire = schema.config.name_converter.from_field(field)
        names.append(wire)
        if index < len(python_path) - 1:
            child = get_named_type(graphql_type_of(graphql_input_fields(current)[wire]))
            assert isinstance(child, GraphQLInputObjectType)
            current = child
    result: JSONObject = {names[-1]: value}
    for name in reversed(names[:-1]):
        result = {name: result}
    return result


def _leaf_type_name(schema: DjangoSchema, python_path: tuple[str, str]) -> str:
    """Return the published scalar of one operator-bag leaf, named as the wire names it."""
    where = _where(schema, python_path, None)
    head = next(iter(where))
    lookup = next(iter(json_object(where, head)))
    bag = get_named_type(graphql_type_of(graphql_input_fields(_input(schema))[head]))
    assert isinstance(bag, GraphQLInputObjectType)
    return get_named_type(graphql_type_of(graphql_input_fields(bag)[lookup])).name


def _post(schema: DjangoSchema, where: JSONObject) -> JSONObject:
    document = (
        f"query($where: {_input(schema).name}!) {{ rows(filter: $where) "
        "{ edges { node { id label } } } }"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables={"where": where},
                url="/graphql-json-filter-typing/",
            )
    finally:
        _CURRENT["schema"] = None


def _seed() -> dict[str, models.ScalarSpecimen]:
    """A number key, the same key as text, and another number."""
    moment = timezone.now()
    return {
        label: models.ScalarSpecimen.objects.create(
            label=label,
            flag=False,
            payload=payload,
            occurred_on=moment.date(),
            occurred_at=moment,
            occurred_time=moment.time(),
            external_id=f"00000000-0000-0000-0000-00000000000{index}",
        )
        for index, (label, payload) in enumerate(
            (("number", {"n": 5}), ("text", {"n": "5"}), ("other", {"n": 6})),
            start=1,
        )
    }


def _expected(
    row_type: type[DjangoType],
    rows: dict[str, models.ScalarSpecimen],
    labels: tuple[str, ...],
) -> JSONObject:
    edges = [
        {"node": {"id": global_id_for(row_type, saved_pk(rows[label])), "label": label}}
        for label in labels
    ]
    return {"data": {"rows": {"edges": edges}}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("python_path", "type_name"),
    [
        pytest.param(("int_n", "exact"), "Int", id="consumer-integer-on-a-key"),
        pytest.param(("ints_n", "in_"), "Int", id="consumer-integer-csv-member"),
        pytest.param(("own_number", "exact"), "Decimal", id="decimal-method"),
    ],
)
def test_a_consumer_json_filter_publishes_the_scalar_its_own_form_cleans(
    python_path: tuple[str, str],
    type_name: str,
) -> None:
    """The JSON column converts nothing, so a consumer form's kind is the published one.

    A consumer ``IntegerField`` form publishes ``Int`` (each CSV member too), and a ``method=``
    filter publishes its ``NumberFilter``'s ``Decimal``: the method owns what its value means.
    """
    schema, _row_type = _holder()
    assert _leaf_type_name(schema, python_path) == type_name


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("python_path", "value", "labels"),
    [
        pytest.param(("int_n", "exact"), 5, ("number",), id="integer-matches-the-number"),
        pytest.param(("ints_n", "in_"), [5, 6], ("number", "other"), id="integer-csv"),
    ],
)
def test_a_consumer_json_filter_compares_the_kind_its_form_cleans(
    python_path: tuple[str, str],
    value: object,
    labels: tuple[str, ...],
) -> None:
    """The cleaned integer ``5`` matches the JSON number, never the text ``"5"``.

    Deliberate controls: each matched the same rows before the rule, which a ``JSON`` leaf
    accepting ``5`` reached as well; the rule's proof is the published ``Int``.
    """
    rows = _seed()
    schema, row_type = _holder()
    payload = _post(schema, _where(schema, python_path, value))

    assert payload == _expected(row_type, rows, labels), payload
