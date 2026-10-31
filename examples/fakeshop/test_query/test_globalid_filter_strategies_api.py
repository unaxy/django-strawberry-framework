"""GlobalID filters accept only the target's configured emitted identifier spellings.

These native Relay types use real Meta strategies and emit identifiers over HTTP.
The JSON consumer applies its associated FilterSet; a typed GlobalID consumer uses
its bound public filter primitive to preserve Strawberry's already-decoded value.
"""

from collections.abc import Mapping
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
from strawberry import relay
from strawberry.scalars import JSON
from strawberry.types import Info
from strawberry.types.base import StrawberryList

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, GlobalIDFilter
from django_strawberry_framework.registry import registry
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_URL = "/graphql-globalid-strategies/"


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-globalid-strategies/", _view)]


def _branches() -> None:
    models.Branch.objects.create(name="Target", city="Boston")
    models.Branch.objects.create(name="Sibling", city="Boston")


def _schema(strategy: str | None) -> DjangoSchema:
    registry.clear()

    class BranchIdentityFilter(FilterSet):
        chosen = GlobalIDFilter(field_name="id")

        class Meta:
            model = models.Branch
            fields = []

    class BranchStrategyNode(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")
            if strategy is not None:
                interfaces = (relay.Node,)
                globalid_strategy = strategy
            filterset_class = BranchIdentityFilter

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            where: JSON | None = None,
        ) -> QuerySet[models.Branch]:
            rows = models.Branch.objects.order_by("pk")
            return rows if where is None else BranchIdentityFilter.apply_sync(where, rows, info)

        def _decoded(self, value: relay.GlobalID) -> QuerySet[models.Branch]:
            rows = models.Branch.objects.order_by("pk")
            filters = BranchIdentityFilter(queryset=rows)
            return filters.filters["chosen"].filter(rows, value)

        rows: QuerySet[models.Branch] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(BranchStrategyNode),
        )
        decoded: QuerySet[models.Branch] = strawberry.field(
            resolver=_decoded,
            graphql_type=StrawberryList(BranchStrategyNode),
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _post(
    schema: DjangoSchema,
    query: str,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url=_URL)
    finally:
        _CURRENT["schema"] = None


def _emitted_id(schema: DjangoSchema) -> str:
    payload = _post(schema, "{ rows { id name } }")
    assert "errors" not in payload, payload
    assert json_at(payload, "data", "rows", 0, "name") == "Target"
    assert json_at(payload, "data", "rows", 1, "name") == "Sibling"
    rows = json_list(json_object(payload, "data"), "rows")
    assert len(rows) == 2, payload
    value = json_at(payload, "data", "rows", 0, "id")
    assert isinstance(value, str), payload
    return value


def _filter(schema: DjangoSchema, value: object) -> JSONObject:
    return _post(
        schema,
        "query($where: JSON!) { rows(where: $where) { name } }",
        {"where": {"chosen": value}},
    )


def _accepts(payload: JSONObject, field: str = "rows") -> None:
    assert "errors" not in payload, payload
    assert payload["data"] == {field: [{"name": "Target"}]}, payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("emitter", "target", "accepted"),
    [
        pytest.param("type", "model", False, id="model-refuses-type-slot"),
        pytest.param("model", "type", False, id="type-refuses-model-slot"),
        pytest.param("model", "type+model", True, id="combined-accepts-model-slot"),
        pytest.param("type", "type+model", True, id="combined-accepts-type-slot"),
    ],
)
def test_globalid_filter_strategy_accepts_only_its_emitted_spellings(
    emitter: str,
    target: str,
    *,
    accepted: bool,
) -> None:
    """The same named Relay target accepts exactly its configured model/type spellings."""
    _branches()
    alternate_id = _emitted_id(_schema(emitter))
    receiving_schema = _schema(target)
    own_id = _emitted_id(receiving_schema)
    _accepts(_filter(receiving_schema, own_id))

    payload = _filter(receiving_schema, alternate_id)
    if accepted:
        _accepts(payload)
    else:
        assert payload["data"] is None, payload
        message = json_at(payload, "errors", 0, "message")
        assert isinstance(message, str), payload
        assert "GlobalID type mismatch" in message, payload


@pytest.mark.django_db
def test_a_bound_globalid_filter_accepts_a_typed_globalid_argument() -> None:
    """A typed emitted ID works without apply context at its associated public filter."""
    _branches()
    schema = _schema("type")
    value = _emitted_id(schema)

    payload = _post(
        schema,
        "query($value: ID!) { decoded(value: $value) { name } }",
        {"value": value},
    )

    _accepts(payload, "decoded")


@pytest.mark.django_db
def test_default_globalid_form_field_refuses_a_json_integer_before_reading_rows(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The default noncoercive form field preserves a malformed JSON integer for refusal."""
    _branches()
    schema = _schema("model")
    _accepts(_filter(schema, _emitted_id(schema)))
    statements = record_compiled_sql(models.Branch._meta.db_table)

    payload = _filter(schema, 42)

    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_INVALID", payload
    assert statements == []


@pytest.mark.django_db
def test_a_nonrelay_target_refuses_a_globalid_with_a_typed_error(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An associated non-Relay target refuses a real ID before it reads any branch rows."""
    _branches()
    emitting_schema = _schema("model")
    value = _emitted_id(emitting_schema)
    _accepts(_filter(emitting_schema, value))
    plain_schema = _schema(None)
    unfiltered = _post(plain_schema, "{ rows { name } }")
    assert "errors" not in unfiltered, unfiltered
    assert unfiltered["data"] == {"rows": [{"name": "Target"}, {"name": "Sibling"}]}
    statements = record_compiled_sql(models.Branch._meta.db_table)

    payload = _filter(plain_schema, value)

    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_UNVALIDATABLE", payload
    message = json_at(payload, "errors", 0, "message")
    assert isinstance(message, str), payload
    assert "no recorded globalid strategy" in message, payload
    assert statements == []
