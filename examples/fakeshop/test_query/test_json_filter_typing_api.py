"""Consumer filters over a JSON column publish and compare the kind their own form cleans.

Rung 3: the subject is consumer filter classes no fakeshop app would ship (an integer-cleaning
``Filter`` and its CSV ``in``, ``method=`` filters, one cleaning a JSON document, a form field
validating a date and cleaning its ISO text, a ``TypedMultipleChoiceFilter`` coercing to a
``tuple``), declared over ``ScalarSpecimen.payload`` and its key paths. The shipped filter
classes over the same column are declared on fakeshop's ``ScalarSpecimenFilter`` and live in
``test_scalars_filter_api.py``. All requests go over HTTP.
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
from django_filters import BaseInFilter, Filter, NumberFilter, TypedMultipleChoiceFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, graphql_payload, json_object
from strawberry import relay
from strawberry.types import Info
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

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


class JSONFormFilter(Filter):
    """A consumer filter whose form cleans a JSON document."""

    field_class = forms.JSONField


class IsoDateField(forms.DateField):
    """A consumer form field validating a date and cleaning it to its ISO text."""

    @override
    def clean(self, value: str | None) -> str | None:
        day = self.to_python(value)
        self.validate(day)
        self.run_validators(day)
        return None if day is None else day.isoformat()


class IsoDateFilter(Filter):
    """A consumer filter comparing a date as the ISO text its form cleans."""

    field_class = IsoDateField


class IsoDatesInFilter(BaseInFilter, IsoDateFilter):
    """A consumer CSV filter cleaning each member as the ISO text of a date."""


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
        own_json = JSONFormFilter(method="own_json_filter")
        iso_day = IsoDateFilter(field_name="payload__day")
        iso_days = IsoDatesInFilter(field_name="payload__day", lookup_expr="in")
        letters = TypedMultipleChoiceFilter(
            field_name="payload__letters",
            coerce=tuple,
            choices=[("abc", "letters")],
        )

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

        def own_json_filter(
            self,
            queryset: QuerySet[models.ScalarSpecimen],
            _name: str,
            value: object,
        ) -> QuerySet[models.ScalarSpecimen]:
            return queryset.filter(payload__n=value)

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
    """A number key, the same key as text, another number and an object; a day and letters."""
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
            (
                ("number", {"n": 5, "day": "2026-11-01", "letters": ["a", "b", "c"]}),
                ("text", {"n": "5", "day": "2026-11-02", "letters": ["x"]}),
                ("other", {"n": 6}),
                ("object", {"n": {"k": 1}}),
            ),
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
        pytest.param(("own_json", "exact"), "JSON", id="json-document-method"),
        pytest.param(("iso_day", "exact"), "Date", id="date-validated-iso-text"),
        pytest.param(("iso_days", "in_"), "Date", id="date-validated-iso-text-csv-member"),
        pytest.param(("letters", "exact"), "String", id="tuple-coerced-choice"),
    ],
)
def test_a_consumer_json_filter_publishes_the_scalar_its_own_form_cleans(
    python_path: tuple[str, str],
    type_name: str,
) -> None:
    """The JSON column converts nothing, so a consumer form's kind is the published one.

    A consumer ``IntegerField`` form publishes ``Int`` (each CSV member too), and a ``method=``
    filter publishes its form's scalar (a ``NumberFilter``'s ``Decimal``, a ``forms.JSONField``'s
    ``JSON``): the method owns what its value means. A ``DateField`` subclass publishes ``Date``
    (each CSV member too: django-filter's CSV field cleans each through it) and a
    ``TypedMultipleChoiceFilter`` its choices' ``String``; neither is refused, since one cleans
    ISO text and the other a ``tuple``, both kinds ``json.dumps`` encodes.
    """
    schema, _row_type = _holder()
    assert _leaf_type_name(schema, python_path) == type_name


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("python_path", "value", "labels"),
    [
        pytest.param(("int_n", "exact"), 5, ("number",), id="integer-matches-the-number"),
        pytest.param(("ints_n", "in_"), [5, 6], ("number", "other"), id="integer-csv"),
        pytest.param(("own_json", "exact"), {"k": 1}, ("object",), id="json-document-method"),
        pytest.param(("iso_day", "exact"), "2026-11-01", ("number",), id="iso-text-of-a-date"),
        pytest.param(
            ("iso_days", "in_"),
            ["2026-11-01", "2026-11-02"],
            ("number", "text"),
            id="iso-text-of-each-date",
        ),
        pytest.param(("letters", "exact"), ["abc"], ("number",), id="tuple-as-a-json-array"),
    ],
)
def test_a_consumer_json_filter_compares_the_kind_its_form_cleans(
    python_path: tuple[str, str],
    value: object,
    labels: tuple[str, ...],
) -> None:
    """Each value reaches the column as the kind its form cleans.

    The cleaned integer ``5`` matches the JSON number, never the text ``"5"``: those two rows
    are deliberate controls, matching the same rows before the rule, which a ``JSON`` leaf
    accepting ``5`` reached as well; the rule's proof is the published ``Int``. The object binds
    under the method filter's one form-data key, each date reaches the key as its ISO text, and
    the coerced ``("a", "b", "c")`` is compared as the JSON array ``["a", "b", "c"]``.
    """
    rows = _seed()
    schema, row_type = _holder()
    payload = _post(schema, _where(schema, python_path, value))

    assert payload == _expected(row_type, rows, labels), payload
