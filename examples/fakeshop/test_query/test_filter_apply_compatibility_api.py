"""The public FilterSet.apply compatibility entry point returns rows or its exact sync recourse.

An ordinary JSON argument calls the unbound public wrapper from a synchronous
consumer resolver. An async-only target is refused for flat scalar and projected
method leaves, directly and through logical arms; a sync target remains usable.
"""

from functools import wraps

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.test import Client, override_settings
from django.urls import path
from django_filters import CharFilter
from graphql_client import JSONObject, graphql_payload, json_at, json_list
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


class _ConsumerContextView(DjangoGraphQLView[object, object]):
    @override
    def get_context(self, request: HttpRequest, response: HttpResponse) -> object:
        del response
        shape = request.headers["X-Context-Shape"]
        if shape == "request":
            return request
        return None if shape == "none" else object()


@wraps(_ConsumerContextView.as_view())
def _context_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return _ConsumerContextView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-filter-compatibility/", _graphql_view),
    path("graphql-filter-compatibility-context/", _context_graphql_view),
]


def _schema(*, async_target: bool = True, failure: type[Exception] | None = None) -> DjangoSchema:
    class ShelfChild(FilterSet):
        code_is = CharFilter(field_name="code", method="filter_code_is")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"], "topic": ["exact"]}

        def filter_code_is(
            self,
            queryset: QuerySet[models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[models.Shelf]:
            return queryset.filter(code=value)

    class BranchParent(FilterSet):
        shelves = RelatedFilter(ShelfChild, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"], "id": ["exact"]}

    def visible(
        _cls: type[DjangoType],
        queryset: QuerySet[models.Shelf],
        _info: object,
    ) -> QuerySet[models.Shelf]:
        if failure is not None:
            raise failure("consumer visibility failure")
        return queryset.exclude(topic="secret")

    async def visible_async(
        _cls: type[DjangoType],
        queryset: QuerySet[models.Shelf],
        _info: object,
    ) -> QuerySet[models.Shelf]:
        return await sync_to_async(lambda: queryset.exclude(topic="secret"))()

    target = type(
        "CompatibilityShelfScope",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": models.Shelf, "fields": ("code",)}),
            "get_queryset": classmethod(visible_async if async_target else visible),
        },
    )

    class BranchOutput(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("name",)

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[models.Branch]:
        del root
        return BranchParent.apply(where, models.Branch.objects.order_by("name"), info)

    def resolve_all(root: object) -> QuerySet[models.Branch]:
        del root
        return models.Branch.objects.order_by("name")

    @strawberry.type
    class Query:
        rows: QuerySet[models.Branch] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[BranchOutput],
        )
        all_rows: QuerySet[models.Branch] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[BranchOutput],
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[target],
        config=strawberry_config(),
        extensions=[lambda: extension],
        error_policy={"enabled": False},
    )


def _world() -> None:
    alpha = models.Branch.objects.create(name="alpha")
    models.Shelf.objects.create(branch=alpha, code="match", topic="open")
    beta = models.Branch.objects.create(name="beta")
    models.Shelf.objects.create(branch=beta, code="match", topic="secret")
    models.Branch.objects.create(name="gamma")


def _post(
    schema: DjangoSchema,
    where: JSONObject,
    *,
    context_shape: str | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
                variables={"where": where},
                client=Client(headers={"X-Context-Shape": context_shape})
                if context_shape
                else None,
                url="/graphql-filter-compatibility-context/"
                if context_shape
                else "/graphql-filter-compatibility/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "where",
    [
        {"shelves__code": "match"},
        {"or_": [{"shelves__code": "match"}]},
        {"shelves__code_is": "match"},
        {"and_": [{"or_": [{"shelves__code_is": "match"}]}]},
    ],
    ids=[
        "scalar",
        "scalar-or",
        "projected-method",
        "projected-method-and-or",
    ],
)
def test_sync_compatibility_apply_names_its_recourse_for_an_async_only_relation_target(
    where: JSONObject,
) -> None:
    """The wrapper reports its own actionable message after the actual sync visibility refusal."""
    _world()
    payload = _post(_schema(), where)
    assert json_at(payload, "data") is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    assert json_at(errors[0], "path") == ["rows"], payload
    assert json_at(errors[0], "message") == (
        "FilterSet.apply called against async get_queryset; use apply_async instead."
    ), payload


@pytest.mark.django_db
def test_compatibility_apply_keeps_the_synchronous_target_hook_and_root_universe() -> None:
    """A synchronous hook remains usable and hides its matching secret target without hiding roots."""
    _world()
    payload = _post(_schema(async_target=False), {"shelves__code_is": "match"})
    assert payload == {
        "data": {
            "rows": [{"name": "alpha"}],
            "allRows": [{"name": "alpha"}, {"name": "beta"}, {"name": "gamma"}],
        },
    }, payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    "failure",
    [ConfigurationError, RuntimeError],
    ids=["configuration", "runtime"],
)
def test_compatibility_apply_preserves_an_unrelated_consumer_exception(
    failure: type[Exception],
) -> None:
    """Only sync-misuse failures acquire the async recourse; an ordinary hook error stays itself."""
    _world()
    payload = _post(_schema(async_target=False, failure=failure), {"shelves__code": "match"})
    assert json_at(payload, "data") is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    assert json_at(errors[0], "path") == ["rows"], payload
    assert json_at(errors[0], "message") == "consumer visibility failure", payload


@pytest.mark.django_db
def test_compatibility_apply_refuses_invalid_raw_primary_key_form_input() -> None:
    """An ordinary JSON criterion reaches the numeric form and returns its structured field error."""
    _world()
    payload = _post(_schema(async_target=False), {"id": "not-an-integer"})
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "Invalid filter input",
                "locations": [{"line": 1, "column": 24}],
                "path": ["rows"],
                "extensions": {
                    "code": "FILTER_INVALID",
                    "errors": {"id": [{"message": "Enter a number.", "code": "invalid"}]},
                },
            },
        ],
    }, payload


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["request", "none", "opaque"])
def test_filter_apply_uses_or_refuses_the_context_returned_by_the_consumer_view(
    shape: str,
) -> None:
    """A view's bare request works; malformed contexts receive the typed filter diagnostic."""
    _world()
    payload = _post(_schema(async_target=False), {"name": "alpha"}, context_shape=shape)
    if shape == "request":
        assert payload == {
            "data": {
                "rows": [{"name": "alpha"}],
                "allRows": [{"name": name} for name in ("alpha", "beta", "gamma")],
            },
        }, payload
        return
    message = (
        "FilterSet requires `info.context`; received `info` without a context."
        if shape == "none"
        else "FilterSet could not resolve a Django HttpRequest from `info.context` (got object). "
        "Expected `info.context.request`, a bare HttpRequest, a mapping whose `request` is an "
        "HttpRequest, or a Strawberry Channels mapping context whose `request` carries an "
        'ASGI scope (`context["request"].consumer.scope` for the HTTP consumer, '
        '`context["request"].scope` for the WebSocket consumer).'
    )
    assert payload == {
        "data": None,
        "errors": [
            {"message": message, "locations": [{"line": 1, "column": 24}], "path": ["rows"]},
        ],
    }, payload
